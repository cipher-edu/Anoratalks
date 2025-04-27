# --- START OF FILE models.py ---

import uuid
import re
import os # Fayl nomini olish uchun
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.core.exceptions import ValidationError
from django.utils import timezone # Enrollment uchun

# --------------------------------------------------------------------------
# Abstrakt Modellar
# --------------------------------------------------------------------------

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(_("Yaratilgan vaqti"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Yangilangan vaqti"), auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

# --------------------------------------------------------------------------
# Asosiy Modellar
# --------------------------------------------------------------------------

class Module(TimestampedModel):
    title = models.CharField(_("Modul sarlavhasi"), max_length=200, unique=True)
    description = models.TextField(_("Modul tavsifi"), blank=True, null=True)
    image = models.ImageField(_("Rasm"), upload_to='modul_images/%Y/%m/')
    order = models.PositiveIntegerField(_("Tartib raqami"), default=0, help_text=_("Modullarni ko'rsatish tartibi."))
    # QIMCHA: Modul pullik yoki so'rov talab qiladimi? (Kurs darajasida ham bo'lishi mumkin)O'SH
    is_premium = models.BooleanField(_("Premium Modul"), default=False, help_text=_("Agar belgilansa, bu modulga yozilish pullik yoki maxsus ruxsat talab qiladi."))

    class Meta:
        verbose_name = _("Modul")
        verbose_name_plural = _("Modullar")
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

class Course(TimestampedModel):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_("Modul")
    )
    title = models.CharField(_("Kurs sarlavhasi"), max_length=255)
    content = models.TextField(_("Kontent (mavzu)"), blank=True, help_text=_("Kursning asosiy matnli mazmuni.")) # Blank=True qo'shildi
    video_url = models.URLField(_("Video havolasi (YouTube)"), blank=True, null=True, help_text=_("Agar mavjud bo'lsa, YouTube video havolasi."))
    order = models.PositiveIntegerField(_("Tartib raqami"), default=0, help_text=_("Modul ichidagi kurslarni ko'rsatish tartibi."))
    # YANGI MAYDON: Kurs bepulmi? Agar modul is_premium bo'lsa, bu maydon ahamiyatsiz bo'lishi mumkin.
    # Yoki yanada moslashuvchan qilish uchun buni qoldiramiz.
    is_free = models.BooleanField(_("Bepul Kurs"), default=True, help_text=_("Agar belgilansa, foydalanuvchilar ushbu kursga avtomatik yozilishi mumkin (agar modul premium bo'lmasa)."))

    @property
    def get_youtube_embed_url(self):
        # ... (mavjud kod o'zgarishsiz qoladi) ...
        if not self.video_url:
            return None
        video_id = None
        # Qo'shimcha patternlar bilan mustahkamlangan regex
        patterns = [
            r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
            r"youtu\.be/([a-zA-Z0-9_-]+)(?:\?.*)?", # Query parametrlarni ham hisobga olish
            r"youtube\.com/embed/([a-zA-Z0-9_-]+)",
            r"youtube\.com/shorts/([a-zA-Z0-9_-]+)", # Shorts uchun
        ]
        for pattern in patterns:
            match = re.search(pattern, self.video_url)
            if match:
                video_id = match.group(1)
                break
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return None

    @property
    def is_accessible_to_user(self, user):
        """
        Bu kurs foydalanuvchi uchun ochiqmi (yozilganmi)?
        Helper property. Buni view'larda ishlatish mumkin.
        """
        if not user or not user.is_authenticated:
            return self.is_free and not self.module.is_premium # Avtorizatsiyadan o'tmaganlar faqat bepul modullardagi bepul kurslarni ko'rishi mumkin (agar ruxsat berilsa)

        # Agar modul premium bo'lmasa va kurs bepul bo'lsa, hamma uchun ochiq
        if self.is_free and not self.module.is_premium:
             return True

        # Agar yozilgan bo'lsa, ochiq
        return Enrollment.objects.filter(user=user, course=self, status=Enrollment.ENROLLED).exists()


    class Meta:
        verbose_name = _("Kurs")
        verbose_name_plural = _("Kurslar")
        ordering = ['module__order', 'order', 'title']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

# --- Fayl va Rasm Modellar (O'zgarishsiz) ---

class CourseSyllabus(TimestampedModel):
    # ... (mavjud kod o'zgarishsiz qoladi) ...
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='syllabi', verbose_name=_("Kurs"))
    title = models.CharField(_("Fayl sarlavhasi"), max_length=150, blank=True, help_text=_("Masalan, '1-dars syllabusi'. Bo'sh qolsa fayl nomi ishlatiladi."))
    file = models.FileField(_("Syllabus Fayli (PDF)"), upload_to='course_syllabi/%Y/%m/', help_text=_("Faqat PDF formatidagi fayllarni yuklang."))

    @property
    def filename(self): return os.path.basename(self.file.name)
    class Meta: verbose_name = _("Kurs Syllabusi"); verbose_name_plural = _("Kurs Syllabuslari"); ordering = ['course', 'created_at']
    def __str__(self): return self.title or self.filename
    def clean(self):
        super().clean()
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext != '.pdf': raise ValidationError(_("Yuklangan fayl formati noto'g'ri. Faqat PDF fayllarni yuklash mumkin."))

class CourseImage(TimestampedModel):
    # ... (mavjud kod o'zgarishsiz qoladi) ...
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='images', verbose_name=_("Kurs"))
    image = models.ImageField(_("Rasm"), upload_to='course_images/%Y/%m/')
    caption = models.CharField(_("Rasm tavsifi"), max_length=255, blank=True, null=True, help_text=_("Rasm ostida ko'rinadigan qisqa izoh."))

    @property
    def filename(self): return os.path.basename(self.image.name)
    class Meta: verbose_name = _("Kurs Rasmi"); verbose_name_plural = _("Kurs Rasmlari"); ordering = ['course', 'created_at']
    def __str__(self): return f"Rasm: {self.course.title} - {self.caption or self.filename}"

class ExternalActivity(TimestampedModel):
    # ... (mavjud kod o'zgarishsiz qoladi, get_learningapps_embed_url ham) ...
    LEARNINGAPPS = 'LA'; KAHOOT = 'KH'; OTHER = 'OT'
    ACTIVITY_TYPE_CHOICES = [(LEARNINGAPPS, _("LearningApps")), (KAHOOT, _("Kahoot!")), (OTHER, _("Boshqa"))]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='external_activities', verbose_name=_("Kurs"))
    title = models.CharField(_("Mashg'ulot sarlavhasi"), max_length=200, help_text=_("Masalan, 'Lug'atlarni mustahkamlash'"))
    activity_type = models.CharField(_("Mashg'ulot turi"), max_length=2, choices=ACTIVITY_TYPE_CHOICES, default=OTHER)
    url = models.URLField(_("Mashg'ulot manzili (URL)"), max_length=500, help_text=_("LearningApps uchun 'Share' yoki 'Embed' linkini kiriting (masalan, .../display?id=... yoki .../watch?v=...). Kahoot yoki boshqa platformalar uchun to'g'ridan-to'g'ri havolani kiriting."))
    order = models.PositiveIntegerField(_("Tartib raqami"), default=0, help_text=_("Mashg'ulotlarni ko'rsatish tartibi."))

    class Meta: verbose_name = _("Tashqi Mashg'ulot"); verbose_name_plural = _("Tashqi Mashg'ulotlar"); ordering = ['course', 'order', 'title']
    def __str__(self): return f"{self.course.title} - {self.title} ({self.get_activity_type_display()})"
    @property
    def get_learningapps_embed_url(self):
        if self.activity_type != self.LEARNINGAPPS or not self.url: return None
        watch_match = re.search(r"learningapps\.org/watch\?v=([a-zA-Z0-9_-]+)", self.url)
        if watch_match: return self.url.split('&')[0]
        id_match = re.search(r"learningapps\.org/(?:display\?id=|view(?:/)?)([a-zA-Z0-9_-]+)", self.url)
        if id_match: return f"https://learningapps.org/watch?v={id_match.group(1)}"
        return None

# --------------------------------------------------------------------------
# Test va Savollar Modeli (O'zgarishsiz)
# --------------------------------------------------------------------------

class Test(TimestampedModel):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='test', verbose_name=_("Modul"))
    title = models.CharField(_("Test sarlavhasi"), max_length=255)
    description = models.TextField(_("Test tavsifi"), blank=True, null=True)
    passing_score_percent = models.PositiveIntegerField(_("O'tish bali (foizda)"), default=70, help_text=_("Testdan muvaffaqiyatli o'tish uchun talab qilinadigan minimal foiz (0-100)."))
    class Meta: verbose_name = _("Test"); verbose_name_plural = _("Testlar"); ordering = ['module__order', 'module__title']
    def __str__(self): return f"{self.module.title} - Test"

class Question(TimestampedModel):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', verbose_name=_("Test"))
    text = models.TextField(_("Savol matni"))
    order = models.PositiveIntegerField(_("Tartib raqami"), default=0)
    class Meta: verbose_name = _("Savol"); verbose_name_plural = _("Savollar"); ordering = ['test', 'order']
    def __str__(self): return f"{self.test.title} - Savol {self.order}: {self.text[:50]}..."

class Answer(TimestampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name=_("Savol"))
    text = models.CharField(_("Javob matni"), max_length=255)
    is_correct = models.BooleanField(_("To'g'ri javob"), default=False, help_text=_("Agar bu javob to'g'ri bo'lsa belgilang."))
    class Meta: verbose_name = _("Javob"); verbose_name_plural = _("Javoblar"); ordering = ['question', 'id']
    def __str__(self): correct_marker = " (To'g'ri)" if self.is_correct else ""; return f"{self.question.text[:30]}... - Javob: {self.text}{correct_marker}"

# --------------------------------------------------------------------------
# YANGI: Foydalanuvchi Yozilishi Modeli (Enrollment)
# --------------------------------------------------------------------------

class Enrollment(TimestampedModel):
    """Foydalanuvchining qaysi kursga yozilganligini va statusini kuzatadi."""
    ENROLLED = 'enrolled'
    COMPLETED = 'completed'
    # PENDING = 'pending' # Kelajakda so'rovlar uchun
    # CANCELLED = 'cancelled' # Kelajakda

    STATUS_CHOICES = [
        (ENROLLED, _("Yozilgan")),
        (COMPLETED, _("Tugatilgan")),
        # (PENDING, _("Kutilmoqda")),
        # (CANCELLED, _("Bekor qilingan")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_("Foydalanuvchi")
    )
    # Hozircha Kursga yozilishni qo'llaymiz. Modulga yozilish ham bo'lishi mumkin.
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_("Kurs")
    )
    enrolled_at = models.DateTimeField(_("Yozilgan vaqti"), default=timezone.now) # auto_now_add o'rniga default
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=STATUS_CHOICES,
        default=ENROLLED
    )
    # completed_at = models.DateTimeField(_("Tugatilgan vaqti"), null=True, blank=True) # Agar status='completed' bo'lsa

    class Meta:
        verbose_name = _("Kursga Yozilish")
        verbose_name_plural = _("Kurslarga Yozilishlar")
        unique_together = ('user', 'course') # Bir foydalanuvchi bir kursga bir marta yoziladi
        ordering = ['user', '-enrolled_at']

    def __str__(self):
        return f"{self.user.username} -> {self.course.title} ({self.get_status_display()})"

    def mark_as_completed(self):
        """Yozilish statusini 'Tugatilgan'ga o'zgartiradi."""
        if self.status != self.COMPLETED:
            self.status = self.COMPLETED
            # self.completed_at = timezone.now() # Agar kerak bo'lsa
            self.save(update_fields=['status', 'updated_at']) # 'completed_at' ham

# --------------------------------------------------------------------------
# Foydalanuvchi Progressi va Sertifikat Modeli (O'zgarishlar bo'lishi mumkin)
# --------------------------------------------------------------------------

class UserCourseProgress(TimestampedModel):
    """Foydalanuvchining qaysi kursni tugatganligini kuzatib boradi."""
    # Bu model Enrollment bilan qisman takrorlanishi mumkin.
    # Balki buni Enrollment.status='completed' orqali almashtirish kerakdir?
    # Hozircha qoldiramiz, lekin kelajakda refaktor qilish mumkin.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_progress',
        verbose_name=_("Foydalanuvchi")
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name=_("Kurs")
    )
    # completed_at TimestampedModel dan keladi (created_at sifatida)
    # completed_at = models.DateTimeField(_("Tugatilgan vaqti"), auto_now_add=True) # Buni olib tashlaymiz, chunki TimestampedModel da bor

    class Meta:
        verbose_name = _("Foydalanuvchi Kurs Progressi")
        verbose_name_plural = _("Foydalanuvchilar Kurs Progresslari")
        unique_together = ('user', 'course') # Bir foydalanuvchi bir kursni bir marta belgilaydi
        ordering = ['user', '-created_at'] # updated_at emas, created_at muhimroq

    def __str__(self):
        # Buni completed_at ga o'zgartirish kerak edi, endi created_at
        return f"{self.user.username} - {self.course.title} (Tugatildi: {self.created_at.strftime('%Y-%m-%d')})"

    # QO'SHIMCHA: UserCourseProgress saqlanganda Enrollment statusini ham yangilash uchun signal
    # Buni signals.py da qilish yaxshiroq


class UserTestResult(TimestampedModel):
    """Foydalanuvchining test natijalarini saqlaydi."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_results',
        verbose_name=_("Foydalanuvchi")
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='user_results',
        verbose_name=_("Test")
    )
    score = models.PositiveIntegerField(_("To'plangan ball (foizda)"), default=0)
    passed = models.BooleanField(_("O'tdi"), default=False)
    # attempted_at TimestampedModel dan keladi (created_at sifatida)
    # attempted_at = models.DateTimeField(_("Urinish vaqti"), auto_now_add=True) # Buni olib tashlaymiz

    class Meta:
        verbose_name = _("Foydalanuvchi Test Natijasi")
        verbose_name_plural = _("Foydalanuvchilar Test Natijalari")
        ordering = ['user', 'test', '-created_at'] # attempted_at o'rniga created_at

    def __str__(self):
        status = "O'tdi" if self.passed else "Yiqildi"
        return f"{self.user.username} - {self.test.title} - {self.score}% ({status})"

class Certificate(TimestampedModel):
    """Modulni muvaffaqiyatli tugatgan foydalanuvchilarga beriladigan sertifikat."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name=_("Foydalanuvchi")
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='certificates_issued',
        verbose_name=_("Modul")
    )
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_("Sertifikat ID"))
    # issued_at TimestampedModel dan keladi (created_at sifatida)
    # issued_at = models.DateTimeField(_("Berilgan vaqti"), auto_now_add=True) # Buni olib tashlaymiz
    # certificate_file = models.FileField(_("Sertifikat Fayli"), upload_to='certificates/', blank=True, null=True)

    class Meta:
        verbose_name = _("Sertifikat")
        verbose_name_plural = _("Sertifikatlar")
        unique_together = ('user', 'module') # Bitta modul uchun bitta sertifikat
        ordering = ['user', '-created_at'] # issued_at o'rniga created_at

    def __str__(self):
        return f"Sertifikat №{str(self.certificate_id)[:8]}... - {self.user.username} - {self.module.title}"

# --- END OF FILE models.py ---