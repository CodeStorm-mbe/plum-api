import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class SEBlock(nn.Module):
    """
    Squeeze-and-Excitation block pour l'attention de canal.
    """
    def __init__(self, channel, reduction=16):
        super(SEBlock, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)

class EnhancedPlumClassifier(nn.Module):
    """
    Modèle amélioré de classification des prunes basé sur EfficientNet.
    Utilise des intervalles de confiance pour déterminer si un échantillon est une prune ou non.
    Inclut des mécanismes d'attention et des connexions résiduelles.
    """
    def __init__(self, num_classes=6, model_name='efficientnet_b4', pretrained=True, dropout_rate=0.4, confidence_threshold=0.7):
        """
        Initialise le modèle de classification amélioré.
        
        Args:
            num_classes (int): Nombre de classes (6 catégories de prunes)
            model_name (str): Nom du modèle de base à utiliser
            pretrained (bool): Si True, utilise des poids pré-entraînés
            dropout_rate (float): Taux de dropout
            confidence_threshold (float): Seuil de confiance pour les prédictions
        """
        super(EnhancedPlumClassifier, self).__init__()
        
        self.num_classes = num_classes
        self.confidence_threshold = confidence_threshold
        
        # Chargement du modèle de base
        try:
            import timm
            self.base_model = timm.create_model(model_name, pretrained=pretrained, features_only=True)
        except ImportError:
            raise ImportError("Le package 'timm' est requis pour ce modèle. Installez-le avec 'pip install timm'.")
        
        # Récupération des dimensions des features de sortie
        dummy_input = torch.randn(1, 3, 320, 320)
        with torch.no_grad():
            features = self.base_model(dummy_input)
        
        # Utilisation des features de la dernière couche
        last_channel = features[-1].shape[1]
        
        # Global Average Pooling
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        
        # Squeeze-and-Excitation block
        self.se_block = SEBlock(last_channel)
        
        # Couches de classification avec connexions résiduelles
        self.dropout1 = nn.Dropout(dropout_rate)
        self.fc1 = nn.Linear(last_channel, 1024)
        self.bn1 = nn.BatchNorm1d(1024)
        
        self.dropout2 = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(1024, 512)
        self.bn2 = nn.BatchNorm1d(512)
        
        # Connexion résiduelle
        self.shortcut = nn.Linear(last_channel, 512)
        
        # Couche finale de classification
        self.dropout3 = nn.Dropout(dropout_rate)
        self.fc3 = nn.Linear(512, num_classes)
        
        # Couche de confiance (pour estimer la fiabilité de la prédiction)
        self.confidence_fc = nn.Linear(512, 1)
        
        # Mapping des indices aux noms de classes
        self.idx_to_class = {
            0: 'bonne_qualite',
            1: 'non_mure',
            2: 'tachetee',
            3: 'fissuree',
            4: 'meurtrie',
            5: 'pourrie'
        }
    
    def forward(self, x):
        """
        Passe avant du modèle.
        
        Args:
            x (torch.Tensor): Batch d'images
            
        Returns:
            tuple: (logits, confidence)
        """
        # Extraction des features
        features = self.base_model(x)
        x = features[-1]  # Utiliser les features de la dernière couche
        
        # Appliquer l'attention
        x = self.se_block(x)
        
        # Global Average Pooling
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        # Sauvegarde pour la connexion résiduelle
        residual = self.shortcut(x)
        
        # Première couche fully connected
        x = self.dropout1(x)
        x = self.fc1(x)
        x = self.bn1(x)
        x = F.relu(x)
        
        # Deuxième couche fully connected
        x = self.dropout2(x)
        x = self.fc2(x)
        x = self.bn2(x)
        
        # Ajouter la connexion résiduelle
        x = x + residual
        x = F.relu(x)
        
        # Couche finale pour la classification
        features_for_confidence = x  # Sauvegarder les features pour la confiance
        
        x = self.dropout3(x)
        logits = self.fc3(x)
        
        # Score de confiance
        confidence = torch.sigmoid(self.confidence_fc(features_for_confidence))
        
        return logits, confidence
    
    def predict_with_confidence(self, x):
        """
        Prédit la classe avec un score de confiance.
        Utilise les intervalles de confiance pour déterminer si un échantillon est une prune ou non.
        
        Args:
            x (torch.Tensor): Batch d'images
            
        Returns:
            dict: Dictionnaire contenant les résultats de la prédiction
        """
        self.eval()
        with torch.no_grad():
            logits, confidence = self(x)
            
            # Probabilités de classe
            probs = F.softmax(logits, dim=1)
            
            # Classe prédite et probabilité maximale
            max_prob, predicted = torch.max(probs, 1)
            
            # Ajustement de la confiance en fonction de la probabilité maximale
            adjusted_confidence = confidence.squeeze() * max_prob
            
            # Déterminer si l'échantillon est une prune en utilisant l'intervalle de confiance
            est_prune = adjusted_confidence >= self.confidence_threshold
            
            # Récupérer le nom de la classe
            class_idx = predicted.item()
            class_name = self.idx_to_class[class_idx]
            
            # Retourner les résultats sous forme de dictionnaire
            results = {
                'class_idx': class_idx,
                'confidence': adjusted_confidence.item(),
                'class_name': class_name,
                'est_prune': est_prune.item(),
                'probabilities': probs.squeeze().tolist()
            }
            
            return results
