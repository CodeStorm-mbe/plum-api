"""
Service de gestion des images pour la classification de prunes.
"""

import os
import io
import uuid
import logging
from PIL import Image
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from plum_classifier.models import PlumImage, ClassificationResult
from plum_classifier.services.model_service import ModelService
from api.websocket_utils import send_classification_result

# Configuration du logging
logger = logging.getLogger(__name__)

class ImageService:
    """
    Service pour gérer les images de prunes et leur classification.
    """
    
    @staticmethod
    def save_image(image_data, user, location=None, notes=None, ground_truth=None):
        """
        Sauvegarde une image de prune dans le système.
        
        Args:
            image_data: Données de l'image (fichier, bytes ou PIL.Image)
            user: Utilisateur qui a uploadé l'image
            location: Lieu où la photo a été prise (optionnel)
            notes: Notes sur l'image (optionnel)
            ground_truth: Vérité terrain (optionnel)
            
        Returns:
            PlumImage: Instance du modèle PlumImage créée
        """
        try:
            # Générer un nom de fichier unique
            filename = f"plum_{uuid.uuid4().hex}.jpg"
            path = os.path.join('plum_images', filename)
            
            # Convertir les données en image PIL si nécessaire
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            elif isinstance(image_data, str) and os.path.isfile(image_data):
                image = Image.open(image_data)
            elif isinstance(image_data, Image.Image):
                image = image_data
            else:
                raise ValueError("Format d'image non pris en charge")
            
            # Convertir en JPEG et optimiser
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Sauvegarder l'image
            img_io = io.BytesIO()
            image.save(img_io, format='JPEG', quality=85, optimize=True)
            img_io.seek(0)
            
            # Créer l'entrée dans la base de données
            plum_image = PlumImage.objects.create(
                user=user,
                location=location,
                notes=notes,
                ground_truth=ground_truth
            )
            
            # Sauvegarder le fichier
            plum_image.image.save(filename, ContentFile(img_io.read()), save=True)
            
            logger.info(f"Image sauvegardée: {plum_image.id}")
            return plum_image
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'image: {e}")
            raise
    
    @staticmethod
    def classify_image(plum_image, save_result=True, send_realtime=True):
        """
        Classifie une image de prune.
        
        Args:
            plum_image: Instance du modèle PlumImage à classifier
            save_result: Si True, sauvegarde le résultat dans la base de données
            send_realtime: Si True, envoie le résultat en temps réel via WebSocket
            
        Returns:
            dict: Résultat de la classification
        """
        try:
            # Charger le service de modèle
            model_service = ModelService()
            
            # Ouvrir l'image
            image_path = plum_image.image.path
            
            # Classifier l'image
            result = model_service.predict(image_path)
            
            if save_result:
                # Créer l'entrée dans la base de données
                classification_result = ClassificationResult.objects.create(
                    plum_image=plum_image,
                    predicted_class=result['class_name'],
                    confidence=result['confidence'],
                    is_plum=result['est_prune'],
                    prob_bonne_qualite=result['probabilities'][0],
                    prob_non_mure=result['probabilities'][1],
                    prob_tachetee=result['probabilities'][2],
                    prob_fissuree=result['probabilities'][3],
                    prob_meurtrie=result['probabilities'][4],
                    prob_pourrie=result['probabilities'][5],
                    model_version="1.0",  # À adapter selon la version du modèle
                    processing_time=result['processing_time']
                )
                
                # Ajouter l'ID du résultat au dictionnaire
                result['result_id'] = str(classification_result.id)
            
            # Envoyer le résultat en temps réel si demandé
            if send_realtime:
                send_classification_result(
                    user_id=str(plum_image.user.id),
                    image_id=str(plum_image.id),
                    predicted_class=result['class_name'],
                    confidence=result['confidence'],
                    probabilities={
                        'bonne_qualite': result['probabilities'][0],
                        'non_mure': result['probabilities'][1],
                        'tachetee': result['probabilities'][2],
                        'fissuree': result['probabilities'][3],
                        'meurtrie': result['probabilities'][4],
                        'pourrie': result['probabilities'][5]
                    },
                    processing_time=result['processing_time']
                )
            
            logger.info(f"Image classifiée: {plum_image.id}, classe: {result['class_name']}, confiance: {result['confidence']}")
            return result
        
        except Exception as e:
            logger.error(f"Erreur lors de la classification de l'image: {e}")
            raise
    
    @staticmethod
    def process_batch(batch_job):
        """
        Traite un lot d'images pour classification.
        
        Args:
            batch_job: Instance du modèle BatchClassificationJob à traiter
            
        Returns:
            bool: True si le traitement a réussi, False sinon
        """
        from plum_classifier.models import BatchClassificationJob
        from api.websocket_utils import send_batch_progress
        
        try:
            # Mettre à jour le statut du lot
            batch_job.status = BatchClassificationJob.PROCESSING
            batch_job.save(update_fields=['status', 'updated_at'])
            
            # Envoyer une mise à jour de progression
            send_batch_progress(
                user_id=str(batch_job.user.id),
                batch_id=str(batch_job.id),
                total_images=batch_job.total_images,
                processed_images=batch_job.processed_images,
                status=batch_job.status
            )
            
            # Récupérer les images à traiter
            images = PlumImage.objects.filter(user=batch_job.user)
            
            # Mettre à jour le nombre total d'images
            batch_job.total_images = images.count()
            batch_job.save(update_fields=['total_images'])
            
            # Traiter chaque image
            for image in images:
                try:
                    # Vérifier si l'image a déjà été classifiée
                    if not ClassificationResult.objects.filter(plum_image=image).exists():
                        # Classifier l'image
                        ImageService.classify_image(image, save_result=True, send_realtime=True)
                        batch_job.success_count += 1
                    
                    # Incrémenter le compteur d'images traitées
                    batch_job.processed_images += 1
                    batch_job.save(update_fields=['processed_images', 'success_count'])
                    
                    # Envoyer une mise à jour de progression
                    send_batch_progress(
                        user_id=str(batch_job.user.id),
                        batch_id=str(batch_job.id),
                        total_images=batch_job.total_images,
                        processed_images=batch_job.processed_images,
                        status=batch_job.status
                    )
                
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de l'image {image.id} dans le lot {batch_job.id}: {e}")
                    batch_job.error_count += 1
                    batch_job.save(update_fields=['error_count'])
            
            # Mettre à jour le statut du lot
            batch_job.status = BatchClassificationJob.COMPLETED
            batch_job.save(update_fields=['status', 'updated_at'])
            
            # Envoyer une mise à jour de progression finale
            send_batch_progress(
                user_id=str(batch_job.user.id),
                batch_id=str(batch_job.id),
                total_images=batch_job.total_images,
                processed_images=batch_job.processed_images,
                status=batch_job.status
            )
            
            logger.info(f"Lot traité: {batch_job.id}, images: {batch_job.processed_images}, succès: {batch_job.success_count}, erreurs: {batch_job.error_count}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du lot {batch_job.id}: {e}")
            
            # Mettre à jour le statut du lot
            batch_job.status = BatchClassificationJob.FAILED
            batch_job.save(update_fields=['status', 'updated_at'])
            
            # Envoyer une mise à jour de progression finale
            send_batch_progress(
                user_id=str(batch_job.user.id),
                batch_id=str(batch_job.id),
                total_images=batch_job.total_images,
                processed_images=batch_job.processed_images,
                status=batch_job.status
            )
            
            return False
