from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import  random
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin, User
class UserProfile(models.Model):
    first_name = models.CharField(max_length=50,verbose_name="Ism")
    last_name = models.CharField(max_length=50,verbose_name="Familiya")
    middle_name = models.CharField(max_length=50, blank=True, null=True,verbose_name="Otasining ismi")
    birth_date = models.DateField(verbose_name="Tug'ilgan sana")
    address = models.CharField(max_length=255,verbose_name="Manzil")
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqami")
    username = models.CharField(max_length=100, unique=True,verbose_name="Foydalanuvchi nomi")
    password = models.CharField(max_length=100, default='Anora2025*')

    def clean(self):
        """
        Bu metodda `first_name`, `last_name` va `middle_name` bo'yicha noyoblikni
        ta'minlash uchun kerakli tekshiruv o'rnatamiz.
        """
        # Agar ism, familiya va otasining ismi bir xil bo'lsa, xatolik qaytaring
        if UserProfile.objects.filter(
                first_name=self.first_name,
                last_name=self.last_name,
                middle_name=self.middle_name
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                _('Bunday ism, familiya va otasining ismi bilan foydalanuvchi allaqachon mavjud.')
            )

    def save(self, *args, **kwargs):
        # Tasdiqni bajarish
        self.clean()

        # Django User modelidan avtomatik foydalanuvchi yaratish
        user, created = User.objects.get_or_create(username=self.username, defaults={
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_staff': True,  # Avtomatik `staff` bo'lishiga ruxsat
            'is_active': True  # Tizimga kirish uchun faollik
        })

        if created:
            # Yaratilgan foydalanuvchilar uchun parolni generatsiya qilish
            user.set_password(self.password)  # Parolni xavfsiz tarzda qo'shish
            user.save()

        # Modelni saqlash
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
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
