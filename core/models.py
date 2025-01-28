from django.db import models

class Course(models.Model):
    LEVEL_CHOICES = [
        ('Boshlang‘ich', 'Boshlang‘ich'),
        ('O‘rta', 'O‘rta'),
        ('Yuqori', 'Yuqori'),
    ]

    name = models.CharField(max_length=255, verbose_name="Kurs nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Kurs tavsifi")
    category = models.CharField(max_length=100, verbose_name="Kurs kategoriyasi")
    duration = models.IntegerField(verbose_name="Kurs davomiyligi")
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES, verbose_name="Kurs darajasi")
    price = models.FloatField(blank=True, null=True, verbose_name="Kurs narxi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
        ordering = ['name']

class Video(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="videos", verbose_name="Kurs nomi")
    title = models.CharField(max_length=255, verbose_name="Video nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Video tavsifi")
    file = models.FileField(upload_to="videos/", verbose_name="Video fayli")
    section = models.CharField(max_length=100, verbose_name="Video bo‘limi")
    section_order = models.IntegerField(verbose_name="Bo‘lim tartibi")
    duration = models.IntegerField(verbose_name="Video davomiyligi", blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True, verbose_name="Video tili")
    quality = models.CharField(max_length=50, blank=True, null=True, verbose_name="Video sifati")
    thumbnail = models.ImageField(upload_to="video_thumbnails/", blank=True, null=True, verbose_name="Video mini-rasm")
    is_visible = models.BooleanField(default=True, verbose_name="Video ko‘rinishi")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuklangan sana")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videolar"
        ordering = ['section_order', 'title']
