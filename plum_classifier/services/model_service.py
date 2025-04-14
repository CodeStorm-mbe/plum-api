"""
Service de chargement et d'utilisation du modèle d'IA pour la classification de prunes.
"""

import os
import io
import torch
import numpy as np
import logging
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2
from django.conf import settings
from datetime import datetime
import time

# Configuration du logging
logger = logging.getLogger(__name__)

class ModelService:
    """
    Service pour charger et utiliser le modèle d'IA de classification de prunes.
    """
    _instance = None
    _model = None
    _transform = None
    _device = None
    _idx_to_class = {
        0: 'bonne_qualite',
        1: 'non_mure',
        2: 'tachetee',
        3: 'fissuree',
        4: 'meurtrie',
        5: 'pourrie'
    }
    _class_to_idx = {v: k for k, v in _idx_to_class.items()}
    
    def __new__(cls):
        """
        Implémentation du pattern Singleton pour éviter de charger le modèle plusieurs fois.
        """
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """
        Initialise le service en chargeant le modèle et en configurant les transformations.
        """
        # Déterminer le device (CPU ou GPU)
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Utilisation du device: {self._device}")
        
        # Configurer les transformations pour le prétraitement des images
        self._transform = A.Compose([
            A.Resize(height=settings.IMAGE_SIZE, width=settings.IMAGE_SIZE),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ])
        
        # Charger le modèle
        self._load_model()
    
    def _load_model(self):
        """
        Charge le modèle à partir du fichier .pt.
        """
        model_path = settings.AI_MODEL_PATH
        
        if not os.path.exists(model_path):
            logger.error(f"Le fichier du modèle n'existe pas: {model_path}")
            raise FileNotFoundError(f"Le fichier du modèle n'existe pas: {model_path}")
        
        try:
            logger.info(f"Chargement du modèle depuis {model_path}")
            self._model = torch.load(model_path, map_location=self._device)
            
            # Mettre le modèle en mode évaluation
            self._model.eval()
            logger.info("Modèle chargé avec succès")
            
            # Journaliser les informations sur le modèle
            logger.info(f"Nombre de classes: {self._model.num_classes if hasattr(self._model, 'num_classes') else 'Non spécifié'}")
            logger.info(f"Seuil de confiance: {self._model.confidence_threshold if hasattr(self._model, 'confidence_threshold') else settings.CONFIDENCE_THRESHOLD}")
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            raise
    
    def preprocess_image(self, image_data):
        """
        Prétraite une image pour la classification.
        
        Args:
            image_data: Données de l'image (fichier, bytes ou PIL.Image)
            
        Returns:
            torch.Tensor: Tensor de l'image prétraitée
        """
        try:
            # Convertir les données en image PIL
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data)).convert('RGB')
            elif isinstance(image_data, str) and os.path.isfile(image_data):
                image = Image.open(image_data).convert('RGB')
            elif isinstance(image_data, Image.Image):
                image = image_data.convert('RGB')
            else:
                raise ValueError("Format d'image non pris en charge")
            
            # Convertir l'image PIL en numpy array
            image_np = np.array(image)
            
            # Appliquer les transformations
            transformed = self._transform(image=image_np)
            image_tensor = transformed['image']
            
            # Ajouter la dimension du batch
            image_tensor = image_tensor.unsqueeze(0)
            
            # Déplacer le tensor sur le device approprié
            image_tensor = image_tensor.to(self._device)
            
            return image_tensor
        except Exception as e:
            logger.error(f"Erreur lors du prétraitement de l'image: {e}")
            raise
    
    def predict(self, image_data):
        """
        Prédit la classe d'une image de prune.
        
        Args:
            image_data: Données de l'image (fichier, bytes ou PIL.Image)
            
        Returns:
            dict: Résultat de la classification
        """
        try:
            # Mesurer le temps de traitement
            start_time = time.time()
            
            # Prétraiter l'image
            image_tensor = self.preprocess_image(image_data)
            
            # Désactiver le calcul du gradient pour l'inférence
            with torch.no_grad():
                # Vérifier si le modèle a la méthode predict_with_confidence
                if hasattr(self._model, 'predict_with_confidence'):
                    result = self._model.predict_with_confidence(image_tensor)
                else:
                    # Utiliser la méthode forward standard
                    logits, confidence = self._model(image_tensor)
                    probs = torch.nn.functional.softmax(logits, dim=1)
                    max_prob, predicted = torch.max(probs, 1)
                    
                    # Ajuster la confiance en fonction de la probabilité maximale
                    adjusted_confidence = confidence.squeeze() * max_prob
                    
                    # Déterminer si l'échantillon est une prune
                    confidence_threshold = getattr(self._model, 'confidence_threshold', settings.CONFIDENCE_THRESHOLD)
                    est_prune = adjusted_confidence >= confidence_threshold
                    
                    # Récupérer le nom de la classe
                    class_idx = predicted.item()
                    class_name = self._idx_to_class.get(class_idx, f"unknown_{class_idx}")
                    
                    # Créer le dictionnaire de résultat
                    result = {
                        'class_idx': class_idx,
                        'confidence': adjusted_confidence.item(),
                        'class_name': class_name,
                        'est_prune': est_prune.item() if isinstance(est_prune, torch.Tensor) else bool(est_prune),
                        'probabilities': probs.squeeze().tolist()
                    }
            
            # Calculer le temps de traitement
            processing_time = (time.time() - start_time) * 1000  # en millisecondes
            result['processing_time'] = processing_time
            
            # Ajouter un horodatage
            result['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {e}")
            raise
    
    def predict_batch(self, image_data_list):
        """
        Prédit les classes d'un lot d'images de prunes.
        
        Args:
            image_data_list: Liste de données d'images
            
        Returns:
            list: Liste des résultats de classification
        """
        results = []
        for image_data in image_data_list:
            try:
                result = self.predict(image_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur lors de la prédiction d'une image du lot: {e}")
                results.append({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def get_model_info(self):
        """
        Récupère les informations sur le modèle chargé.
        
        Returns:
            dict: Informations sur le modèle
        """
        if self._model is None:
            return {'error': 'Modèle non chargé'}
        
        return {
            'num_classes': getattr(self._model, 'num_classes', len(self._idx_to_class)),
            'confidence_threshold': getattr(self._model, 'confidence_threshold', settings.CONFIDENCE_THRESHOLD),
            'idx_to_class': self._idx_to_class,
            'device': str(self._device),
            'image_size': settings.IMAGE_SIZE,
            'model_path': settings.AI_MODEL_PATH,
            'model_loaded': self._model is not None
        }
    
    def reload_model(self):
        """
        Recharge le modèle à partir du fichier .pt.
        
        Returns:
            bool: True si le rechargement a réussi, False sinon
        """
        try:
            self._load_model()
            return True
        except Exception as e:
            logger.error(f"Erreur lors du rechargement du modèle: {e}")
            return False
