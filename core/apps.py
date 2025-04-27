# --- START OF FILE apps.py ---

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

# O'chirildi:
# class CoreConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'core'

class LearningPlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Ilova nomini 'core' qoldiramiz, chunki papka nomi shunday
    name = 'core'
    verbose_name = _("O'quv Platformasi") # Admin panelda ko'rinadigan nom

    def ready(self):
        """
        Django ishga tushganda signallarni import qilish va ulash.
        """
        # print("Importing signals for core...") # Tekshirish uchun o'zgartirildi
        import core.signals # Signallar faylini import qilamiz
        # print("Signals imported.")

# --- END OF FILE apps.py ---