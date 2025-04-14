from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg, Count
from django.utils.safestring import mark_safe

from .models import PlumBatch, PlumClassification, Notification, ModelVersion

@admin.register(PlumBatch)
class PlumBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm_link', 'created_by_link', 'status', 'total_plums', 'quality_distribution_summary', 'created_at')
    list_filter = ('status', 'farm', 'created_at')
    search_fields = ('name', 'description', 'farm__name', 'created_by__username')
    readonly_fields = ('classification_summary', 'total_plums', 'quality_distribution', 'created_at', 'updated_at', 'quality_chart')
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'farm', 'created_by', 'status')
        }),
        ('Statistiques de classification', {
            'fields': ('total_plums', 'quality_distribution', 'classification_summary', 'quality_chart')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def farm_link(self, obj):
        url = reverse("admin:users_farm_change", args=[obj.farm.id])
        return format_html('<a href="{}">{}</a>', url, obj.farm.name)
    farm_link.short_description = 'Ferme'
    
    def created_by_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.created_by.id])
        return format_html('<a href="{}">{}</a>', url, obj.created_by.username)
    created_by_link.short_description = 'Créé par'
    
    def quality_distribution_summary(self, obj):
        if not obj.quality_distribution:
            return "Aucune donnée"
        
        summary = []
        for class_name, data in obj.quality_distribution.items():
            summary.append(f"{class_name}: {data['percentage']}%")
        
        return ", ".join(summary)
    quality_distribution_summary.short_description = 'Distribution de qualité'
    
    def quality_chart(self, obj):
        if not obj.quality_distribution:
            return "Aucune donnée disponible pour générer un graphique"
        
        # Créer un graphique simple en HTML/CSS
        html = """
        <div style="width: 100%; max-width: 800px;">
            <h3>Distribution de qualité</h3>
            <div style="display: flex; flex-direction: column; gap: 10px;">
        """
        
        colors = {
            'bonne_qualite': '#4CAF50',  # Vert
            'non_mure': '#FFC107',       # Jaune
            'tachetee': '#FF9800',       # Orange
            'fissuree': '#F44336',       # Rouge
            'meurtrie': '#9C27B0',       # Violet
            'pourrie': '#795548'         # Marron
        }
        
        for class_name, data in obj.quality_distribution.items():
            percentage = data['percentage']
            count = data['count']
            color = colors.get(class_name, '#2196F3')  # Bleu par défaut
            
            html += f"""
            <div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 120px;">{class_name}</div>
                    <div style="flex-grow: 1; background-color: #e0e0e0; height: 20px; border-radius: 4px;">
                        <div style="width: {percentage}%; height: 100%; background-color: {color}; border-radius: 4px;"></div>
                    </div>
                    <div style="width: 80px;">{percentage}% ({count})</div>
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return mark_safe(html)
    quality_chart.short_description = 'Graphique de qualité'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('farm', 'created_by')
        return queryset


@admin.register(PlumClassification)
class PlumClassificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'image_preview', 'class_name_display', 'confidence_score', 'is_plum', 'uploaded_by_link', 'farm_link', 'batch_link', 'created_at')
    list_filter = ('class_name', 'is_plum', 'farm', 'batch', 'created_at')
    search_fields = ('original_filename', 'uploaded_by__username', 'farm__name', 'batch__name')
    readonly_fields = ('image_full', 'classification_result', 'processing_time', 'created_at')
    fieldsets = (
        ('Image', {
            'fields': ('image_full', 'original_filename', 'image_path')
        }),
        ('Classification', {
            'fields': ('class_name', 'confidence_score', 'is_plum', 'classification_result')
        }),
        ('Relations', {
            'fields': ('uploaded_by', 'farm', 'batch')
        }),
        ('Métadonnées', {
            'fields': ('processing_time', 'device_info', 'geo_location', 'created_at')
        }),
    )
    
    def image_preview(self, obj):
        return format_html('<img src="/media/{}" style="max-height: 50px; max-width: 50px;" />', 
                          obj.image_path.replace('/home/ubuntu/plum_api/media/', ''))
    image_preview.short_description = 'Image'
    
    def image_full(self, obj):
        return format_html('<img src="/media/{}" style="max-height: 300px; max-width: 300px;" />', 
                          obj.image_path.replace('/home/ubuntu/plum_api/media/', ''))
    image_full.short_description = 'Image'
    
    def class_name_display(self, obj):
        class_colors = {
            'bonne_qualite': '#4CAF50',  # Vert
            'non_mure': '#FFC107',       # Jaune
            'tachetee': '#FF9800',       # Orange
            'fissuree': '#F44336',       # Rouge
            'meurtrie': '#9C27B0',       # Violet
            'pourrie': '#795548'         # Marron
        }
        color = class_colors.get(obj.class_name, '#2196F3')
        return format_html('<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>', 
                          color, obj.get_class_name_display())
    class_name_display.short_description = 'Classe'
    
    def uploaded_by_link(self, obj):
        if not obj.uploaded_by:
            return "-"
        url = reverse("admin:users_user_change", args=[obj.uploaded_by.id])
        return format_html('<a href="{}">{}</a>', url, obj.uploaded_by.username)
    uploaded_by_link.short_description = 'Téléchargé par'
    
    def farm_link(self, obj):
        if not obj.farm:
            return "-"
        url = reverse("admin:users_farm_change", args=[obj.farm.id])
        return format_html('<a href="{}">{}</a>', url, obj.farm.name)
    farm_link.short_description = 'Ferme'
    
    def batch_link(self, obj):
        if not obj.batch:
            return "-"
        url = reverse("admin:plum_classifier_plumbatch_change", args=[obj.batch.id])
        return format_html('<a href="{}">{}</a>', url, obj.batch.name)
    batch_link.short_description = 'Lot'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('uploaded_by', 'farm', 'batch')
        return queryset


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_link', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)
    
    def user_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user')
        return queryset


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'model_type', 'is_active', 'is_production', 'accuracy', 'created_at')
    list_filter = ('model_type', 'is_active', 'is_production', 'created_at')
    search_fields = ('name', 'version', 'model_type')
    readonly_fields = ('created_at', 'updated_at', 'metrics_chart')
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'version', 'model_type', 'is_active', 'is_production')
        }),
        ('Fichiers', {
            'fields': ('file_path', 'metadata_path')
        }),
        ('Configuration', {
            'fields': ('num_classes', 'input_shape', 'confidence_threshold')
        }),
        ('Métriques de performance', {
            'fields': ('accuracy', 'f1_score', 'precision', 'recall', 'metrics_chart')
        }),
        ('Informations d\'entraînement', {
            'fields': ('training_date', 'training_duration', 'dataset_size')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['activate_model', 'set_production']
    
    def activate_model(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Vous ne pouvez activer qu'un seul modèle à la fois.", level='error')
            return
        
        # Désactiver tous les modèles
        ModelVersion.objects.all().update(is_active=False)
        
        # Activer le modèle sélectionné
        model = queryset.first()
        model.is_active = True
        model.save()
        
        # Recharger le modèle dans le service
        from .services import PlumClassifierService
        classifier = PlumClassifierService.get_instance()
        success = classifier.switch_model(model.id)
        
        if success:
            self.message_user(request, f"Le modèle {model.name} v{model.version} a été activé avec succès.")
        else:
            self.message_user(request, f"Erreur lors de l'activation du modèle. Vérifiez les logs pour plus d'informations.", level='error')
    activate_model.short_description = "Activer le modèle sélectionné"
    
    def set_production(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Vous ne pouvez définir qu'un seul modèle comme modèle de production.", level='error')
            return
        
        # Désactiver tous les modèles de production
        ModelVersion.objects.all().update(is_production=False)
        
        # Définir le modèle sélectionné comme modèle de production
        model = queryset.first()
        model.is_production = True
        model.save()
        
        self.message_user(request, f"Le modèle {model.name} v{model.version} a été défini comme modèle de production.")
    set_production.short_description = "Définir comme modèle de production"
    
    def metrics_chart(self, obj):
        if not all([obj.accuracy, obj.precision, obj.recall, obj.f1_score]):
            return "Métriques incomplètes, impossible de générer un graphique"
        
        # Créer un graphique simple en HTML/CSS
        html = """
        <div style="width: 100%; max-width: 600px;">
            <h3>Métriques de performance</h3>
            <div style="display: flex; flex-direction: column; gap: 10px;">
        """
        
        metrics = {
            'Précision (Accuracy)': obj.accuracy,
            'Précision (Precision)': obj.precision,
            'Rappel (Recall)': obj.recall,
            'Score F1': obj.f1_score
        }
        
        for name, value in metrics.items():
            percentage = value * 100
            html += f"""
            <div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 180px;">{name}</div>
                    <div style="flex-grow: 1; background-color: #e0e0e0; height: 20px; border-radius: 4px;">
                        <div style="width: {percentage}%; height: 100%; background-color: #2196F3; border-radius: 4px;"></div>
                    </div>
                    <div style="width: 60px;">{percentage:.2f}%</div>
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return mark_safe(html)
    metrics_chart.short_description = 'Graphique des métriques'
