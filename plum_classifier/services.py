import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional, Union

import torch
import numpy as np
from PIL import Image
from django.conf import settings

from plum_classifier.models import ModelVersion
from plum_classifier.model_architecture import EnhancedPlumClassifier

logger = logging.getLogger(__name__)

class PlumClassifierService:
    """
    Service pour l'intégration du modèle de classification des prunes.
    
    Cette classe est conçue comme un singleton pour éviter de charger
    plusieurs instances du modèle en mémoire.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Retourne l'instance unique du service, ou en crée une nouvelle si nécessaire.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """
        Initialise le service de classification.
        
        Le modèle n'est pas chargé immédiatement, mais seulement lors de la première
        utilisation via la méthode lazy_load_model().
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.model_version = None
        self.idx_to_class = None
        self.transform = None
        self.model_loaded = False
        self.model_path = None
        self.metadata_path = None
        
        # Créer le répertoire des modèles s'il n'existe pas
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        
        logger.info(f"PlumClassifierService initialisé. Appareil: {self.device}")
    
    def lazy_load_model(self) -> bool:
        """
        Charge le modèle à la demande, seulement s'il n'est pas déjà chargé.
        
        Returns:
            bool: True si le modèle a été chargé avec succès, False sinon.
        """
        if self.model_loaded:
            return True
        
        try:
            # Rechercher le modèle actif dans la base de données
            active_model = ModelVersion.objects.filter(is_active=True).first()
            
            if active_model:
                self.model_path = active_model.file_path
                self.metadata_path = active_model.metadata_path
                self.model_version = active_model
            else:
                # Rechercher un fichier .pt dans le répertoire des modèles
                model_files = [f for f in os.listdir(settings.MODEL_DIR) if f.endswith('.pt')]
                if not model_files:
                    logger.error("Aucun modèle trouvé dans le répertoire des modèles.")
                    return False
                
                # Utiliser le premier modèle trouvé
                model_file = model_files[0]
                self.model_path = os.path.join(settings.MODEL_DIR, model_file)
                
                # Rechercher le fichier de métadonnées correspondant
                metadata_file = model_file.replace('.pt', '_metadata.json')
                metadata_path = os.path.join(settings.MODEL_DIR, metadata_file)
                
                if os.path.exists(metadata_path):
                    self.metadata_path = metadata_path
                else:
                    logger.warning(f"Fichier de métadonnées non trouvé pour {model_file}.")
                    # Créer des métadonnées par défaut
                    self.metadata_path = None
            
            # Charger le modèle
            return self._load_model()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            return False
    
    def _load_model(self) -> bool:
        """
        Charge le modèle à partir du fichier .pt et des métadonnées.
        
        Returns:
            bool: True si le modèle a été chargé avec succès, False sinon.
        """
        try:
            if not os.path.exists(self.model_path):
                logger.error(f"Le fichier de modèle n'existe pas: {self.model_path}")
                return False
            
            # Charger les métadonnées si disponibles
            metadata = {}
            if self.metadata_path and os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Configurer les paramètres du modèle
            num_classes = metadata.get('num_classes', 6)
            confidence_threshold = metadata.get('confidence_threshold', 0.7)
            model_name = metadata.get('model_name', 'efficientnet_b4')
            dropout_rate = metadata.get('dropout_rate', 0.4)
            
            # Charger le mapping des indices aux classes
            self.idx_to_class = metadata.get('idx_to_class', {
                '0': 'bonne_qualite',
                '1': 'non_mure',
                '2': 'tachetee',
                '3': 'fissuree',
                '4': 'meurtrie',
                '5': 'pourrie'
            })
            
            # Créer l'instance du modèle avec l'architecture correcte
            try:
                # Installer timm si nécessaire
                import importlib
                try:
                    importlib.import_module('timm')
                except ImportError:
                    logger.info("Installation du package timm...")
                    import subprocess
                    import sys
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "timm"])
                
                # Créer l'instance du modèle
                self.model = EnhancedPlumClassifier(
                    num_classes=num_classes,
                    model_name=model_name,
                    pretrained=False,  # Nous allons charger nos propres poids
                    dropout_rate=dropout_rate,
                    confidence_threshold=confidence_threshold
                )
                
                # Charger les poids du modèle
                state_dict = torch.load(self.model_path, map_location=self.device)
                
                # Vérifier si le state_dict est encapsulé dans un module PyTorch Lightning
                if 'state_dict' in state_dict:
                    # Extraire le state_dict du modèle
                    state_dict = state_dict['state_dict']
                    
                    # Supprimer les préfixes 'model.' si présents
                    new_state_dict = {}
                    for key, value in state_dict.items():
                        if key.startswith('model.'):
                            new_key = key[6:]  # Supprimer 'model.'
                            new_state_dict[new_key] = value
                        else:
                            new_state_dict[key] = value
                    
                    state_dict = new_state_dict
                
                # Charger les poids dans le modèle
                self.model.load_state_dict(state_dict)
                
                # Mettre le modèle en mode évaluation
                self.model.eval()
                
                # Déplacer le modèle sur le bon appareil (CPU/GPU)
                self.model = self.model.to(self.device)
                
                logger.info(f"Architecture du modèle et poids chargés avec succès")
                
            except Exception as e:
                logger.error(f"Erreur lors du chargement de l'architecture du modèle: {str(e)}")
                logger.info("Tentative de chargement direct du modèle...")
                
                # Fallback: charger directement le modèle complet
                self.model = torch.load(self.model_path, map_location=self.device)
                
                # Mettre le modèle en mode évaluation
                self.model.eval()
            
            # Configurer la transformation d'image
            self._setup_transform(metadata.get('input_size', 320))
            
            self.model_loaded = True
            logger.info(f"Modèle chargé avec succès: {self.model_path}")
            
            # Si le modèle n'est pas enregistré dans la base de données, l'enregistrer
            if not self.model_version:
                self._register_model_in_db(metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            return False
    
    def _setup_transform(self, input_size: int = 320):
        """
        Configure la transformation d'image pour le prétraitement.
        
        Args:
            input_size (int): Taille d'entrée du modèle.
        """
        try:
            import albumentations as A
            from albumentations.pytorch import ToTensorV2
            
            self.transform = A.Compose([
                A.Resize(height=input_size, width=input_size),
                A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ToTensorV2(),
            ])
            
        except ImportError:
            logger.warning("Albumentations non disponible. Utilisation de transformations PyTorch de base.")
            
            from torchvision import transforms
            
            self.transform = transforms.Compose([
                transforms.Resize((input_size, input_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
    
    def _register_model_in_db(self, metadata: Dict[str, Any]):
        """
        Enregistre le modèle dans la base de données.
        
        Args:
            metadata (Dict[str, Any]): Métadonnées du modèle.
        """
        try:
            # Extraire les informations du modèle
            model_name = metadata.get('model_name', 'plum_classifier')
            version = metadata.get('version', '1.0.0')
            num_classes = metadata.get('num_classes', 6)
            confidence_threshold = metadata.get('confidence_threshold', 0.7)
            input_shape = metadata.get('input_shape', [1, 3, 320, 320])
            
            # Créer une entrée dans la base de données
            model_version = ModelVersion.objects.create(
                name=model_name,
                version=version,
                file_path=self.model_path,
                metadata_path=self.metadata_path,
                model_type=metadata.get('model_type', 'efficientnet'),
                num_classes=num_classes,
                input_shape=input_shape,
                confidence_threshold=confidence_threshold,
                accuracy=metadata.get('accuracy'),
                f1_score=metadata.get('f1_score'),
                precision=metadata.get('precision'),
                recall=metadata.get('recall'),
                training_date=metadata.get('training_date'),
                training_duration=metadata.get('training_duration'),
                dataset_size=metadata.get('dataset_size'),
                is_active=True,
                is_production=False
            )
            
            self.model_version = model_version
            logger.info(f"Modèle enregistré dans la base de données: {model_version.id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du modèle dans la base de données: {str(e)}")
    
    def classify_image(self, image_path: str, tta: bool = False) -> Dict[str, Any]:
        """
        Classifie une image de prune.
        
        Args:
            image_path (str): Chemin vers l'image à classifier.
            tta (bool): Utiliser Test Time Augmentation pour améliorer la précision.
            
        Returns:
            Dict[str, Any]: Résultats de la classification.
        """
        start_time = time.time()
        
        # Charger le modèle si nécessaire
        if not self.model_loaded and not self.lazy_load_model():
            return {
                'error': 'Impossible de charger le modèle',
                'class_name': 'unknown',
                'confidence': 0.0,
                'est_prune': False,
                'processing_time': time.time() - start_time
            }
        
        try:
            # Charger et prétraiter l'image
            image = Image.open(image_path).convert('RGB')
            
            if tta:
                # Test Time Augmentation
                predictions = self._predict_with_tta(image)
            else:
                # Prédiction standard
                predictions = self._predict_single(image)
            
            # Ajouter le temps de traitement
            predictions['processing_time'] = time.time() - start_time
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification de l'image: {str(e)}")
            return {
                'error': str(e),
                'class_name': 'error',
                'confidence': 0.0,
                'est_prune': False,
                'processing_time': time.time() - start_time
            }
    
    def _predict_single(self, image: Image.Image) -> Dict[str, Any]:
        """
        Effectue une prédiction sur une seule image.
        
        Args:
            image (Image.Image): Image PIL à classifier.
            
        Returns:
            Dict[str, Any]: Résultats de la classification.
        """
        # Prétraiter l'image
        if hasattr(self.transform, 'transforms'):
            # Albumentations
            image_np = np.array(image)
            transformed = self.transform(image=image_np)
            image_tensor = transformed['image'].unsqueeze(0).to(self.device)
        else:
            # Torchvision
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Prédiction
        with torch.no_grad():
            # Vérifier si le modèle utilise la méthode predict_with_confidence
            if hasattr(self.model, 'predict_with_confidence'):
                # Utiliser la méthode dédiée du modèle
                results = self.model.predict_with_confidence(image_tensor)
                
                # Adapter le format des résultats pour correspondre à l'API
                return {
                    'class_name': results['class_name'],
                    'confidence': results['confidence'],
                    'est_prune': results['est_prune'],
                    'all_probabilities': {
                        self.idx_to_class.get(str(i), f'class_{i}'): prob
                        for i, prob in enumerate(results['probabilities'])
                    }
                }
            else:
                # Méthode générique pour d'autres modèles
                if isinstance(self.model, torch.nn.Module):
                    # Modèle PyTorch standard
                    outputs = self.model(image_tensor)
                    
                    # Gérer différents formats de sortie
                    if isinstance(outputs, tuple) and len(outputs) == 2:
                        # Format (logits, confidence)
                        logits, confidence = outputs
                        probabilities = torch.nn.functional.softmax(logits, dim=1)[0]
                        confidence = confidence.squeeze().item()
                    else:
                        # Format logits uniquement
                        probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
                        confidence = None
                    
                    # Obtenir la classe prédite et la confiance
                    max_prob, predicted_class = torch.max(probabilities, 0)
                    
                    # Si pas de confiance explicite, utiliser la probabilité maximale
                    if confidence is None:
                        confidence = max_prob.item()
                    
                    # Convertir en valeurs Python
                    predicted_class = predicted_class.item()
                    
                    # Obtenir le nom de la classe
                    class_name = self.idx_to_class.get(str(predicted_class), 'unknown')
                    
                    # Déterminer si c'est une prune (toutes les classes sauf 'unknown')
                    est_prune = class_name != 'unknown'
                    
                    # Préparer les résultats
                    results = {
                        'class_name': class_name,
                        'confidence': confidence,
                        'est_prune': est_prune,
                        'all_probabilities': {
                            self.idx_to_class.get(str(i), f'class_{i}'): prob.item()
                            for i, prob in enumerate(probabilities)
                        }
                    }
                    
                    return results
    
    def _predict_with_tta(self, image: Image.Image) -> Dict[str, Any]:
        """
        Effectue une prédiction avec Test Time Augmentation.
        
        Args:
            image (Image.Image): Image PIL à classifier.
            
        Returns:
            Dict[str, Any]: Résultats de la classification.
        """
        # Créer différentes versions de l'image
        augmentations = [
            image,  # Original
            image.transpose(Image.FLIP_LEFT_RIGHT),  # Flip horizontal
            image.transpose(Image.FLIP_TOP_BOTTOM),  # Flip vertical
            image.rotate(90),  # Rotation 90°
            image.rotate(270),  # Rotation 270°
        ]
        
        # Vérifier si le modèle utilise la méthode predict_with_confidence
        if hasattr(self.model, 'predict_with_confidence'):
            # Prédire sur chaque version et moyenner les résultats
            all_probabilities = []
            all_confidences = []
            
            for aug_image in augmentations:
                # Prétraiter l'image
                if hasattr(self.transform, 'transforms'):
                    # Albumentations
                    image_np = np.array(aug_image)
                    transformed = self.transform(image=image_np)
                    image_tensor = transformed['image'].unsqueeze(0).to(self.device)
                else:
                    # Torchvision
                    image_tensor = self.transform(aug_image).unsqueeze(0).to(self.device)
                
                # Prédiction
                with torch.no_grad():
                    results = self.model.predict_with_confidence(image_tensor)
                    all_probabilities.append(results['probabilities'])
                    all_confidences.append(results['confidence'])
            
            # Moyenner les probabilités et confidences
            avg_probabilities = np.mean(all_probabilities, axis=0)
            avg_confidence = np.mean(all_confidences)
            
            # Obtenir la classe prédite
            predicted_class = np.argmax(avg_probabilities)
            
            # Obtenir le nom de la classe
            class_name = self.idx_to_class.get(str(predicted_class), 'unknown')
            
            # Déterminer si c'est une prune
            est_prune = class_name != 'unknown'
            
            # Préparer les résultats
            results = {
                'class_name': class_name,
                'confidence': float(avg_confidence),
                'est_prune': est_prune,
                'all_probabilities': {
                    self.idx_to_class.get(str(i), f'class_{i}'): float(prob)
                    for i, prob in enumerate(avg_probabilities)
                },
                'tta_used': True
            }
            
            return results
        else:
            # Méthode générique pour d'autres modèles
            all_probabilities = []
            
            for aug_image in augmentations:
                # Prétraiter l'image
                if hasattr(self.transform, 'transforms'):
                    # Albumentations
                    image_np = np.array(aug_image)
                    transformed = self.transform(image=image_np)
                    image_tensor = transformed['image'].unsqueeze(0).to(self.device)
                else:
                    # Torchvision
                    image_tensor = self.transform(aug_image).unsqueeze(0).to(self.device)
                
                # Prédiction
                with torch.no_grad():
                    outputs = self.model(image_tensor)
                    
                    # Gérer différents formats de sortie
                    if isinstance(outputs, tuple) and len(outputs) == 2:
                        # Format (logits, confidence)
                        logits, _ = outputs
                        probabilities = torch.nn.functional.softmax(logits, dim=1)[0]
                    else:
                        # Format logits uniquement
                        probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
                    
                    all_probabilities.append(probabilities.cpu().numpy())
            
            # Moyenner les probabilités
            avg_probabilities = np.mean(all_probabilities, axis=0)
            
            # Obtenir la classe prédite et la confiance
            predicted_class = np.argmax(avg_probabilities)
            confidence = avg_probabilities[predicted_class]
            
            # Obtenir le nom de la classe
            class_name = self.idx_to_class.get(str(predicted_class), 'unknown')
            
            # Déterminer si c'est une prune
            est_prune = class_name != 'unknown'
            
            # Préparer les résultats
            results = {
                'class_name': class_name,
                'confidence': float(confidence),
                'est_prune': est_prune,
                'all_probabilities': {
                    self.idx_to_class.get(str(i), f'class_{i}'): float(prob)
                    for i, prob in enumerate(avg_probabilities)
                },
                'tta_used': True
            }
            
            return results
    
    def switch_model(self, model_version_id: int) -> bool:
        """
        Change le modèle actif.
        
        Args:
            model_version_id (int): ID de la version du modèle à charger.
            
        Returns:
            bool: True si le changement a réussi, False sinon.
        """
        try:
            # Récupérer la version du modèle
            model_version = ModelVersion.objects.get(id=model_version_id)
            
            # Vérifier que le fichier existe
            if not os.path.exists(model_version.file_path):
                logger.error(f"Le fichier de modèle n'existe pas: {model_version.file_path}")
                return False
            
            # Mettre à jour les attributs
            self.model_path = model_version.file_path
            self.metadata_path = model_version.metadata_path
            self.model_version = model_version
            self.model_loaded = False
            
            # Recharger le modèle
            return self.lazy_load_model()
            
        except ModelVersion.DoesNotExist:
            logger.error(f"Version du modèle non trouvée: {model_version_id}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors du changement de modèle: {str(e)}")
            return False
    
    def reload_model(self) -> bool:
        """
        Recharge le modèle actif.
        
        Returns:
            bool: True si le rechargement a réussi, False sinon.
        """
        self.model_loaded = False
        return self.lazy_load_model()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur le modèle chargé.
        
        Returns:
            Dict[str, Any]: Informations sur le modèle.
        """
        if not self.model_loaded and not self.lazy_load_model():
            return {'error': 'Aucun modèle chargé'}
        
        info = {
            'model_loaded': self.model_loaded,
            'device': str(self.device),
            'model_path': self.model_path,
            'metadata_path': self.metadata_path,
            'model_architecture': self.model.__class__.__name__,
        }
        
        if self.model_version:
            info.update({
                'id': self.model_version.id,
                'name': self.model_version.name,
                'version': self.model_version.version,
                'model_type': self.model_version.model_type,
                'num_classes': self.model_version.num_classes,
                'confidence_threshold': self.model_version.confidence_threshold,
                'accuracy': self.model_version.accuracy,
                'f1_score': self.model_version.f1_score,
                'precision': self.model_version.precision,
                'recall': self.model_version.recall,
                'training_date': self.model_version.training_date,
                'is_active': self.model_version.is_active,
                'is_production': self.model_version.is_production,
            })
        
        # Ajouter des informations sur les classes
        info['classes'] = self.idx_to_class
        
        return info
