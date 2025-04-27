# --- START OF FILE signals.py ---

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone # Enrollment uchun
from django.utils.translation import gettext_lazy as _ # Agar xabar kerak bo'lsa

# Modellarni import qilish
from core.models import UserTestResult, Certificate, Module, Enrollment, UserCourseProgress
from django.conf import settings # Foydalanuvchi modelini olish uchun

@receiver(post_save, sender=UserTestResult)
@transaction.atomic
def create_certificate_on_pass(sender, instance: UserTestResult, created: bool, **kwargs):
    """
    Agar foydalanuvchi testdan muvaffaqiyatli o'tsa (`passed=True`)
    va uning shu modul uchun hali sertifikati bo'lmasa, yangi sertifikat yaratadi.
    """
    if instance.passed:
        user = instance.user
        try:
            module = instance.test.module
        except Module.DoesNotExist:
             print(f"Xatolik: Test ID {instance.test.pk} hech qanday modulga bog'lanmagan.")
             return

        # get_or_create atomiklikni ta'minlaydi
        certificate, cert_created = Certificate.objects.get_or_create(
            user=user,
            module=module,
            # created_at/issued_at avtomatik TimestampedModel tomonidan qo'shiladi
        )

        if cert_created:
            print(f"Sertifikat {user.username} uchun '{module.title}' moduliga yaratildi.")


# YANGI SIGNAL: UserCourseProgress saqlanganda Enrollment statusini yangilash
@receiver(post_save, sender=UserCourseProgress)
@transaction.atomic
def update_enrollment_on_progress_completion(sender, instance: UserCourseProgress, created: bool, **kwargs):
    """
    UserCourseProgress yaratilganda (ya'ni kurs tugatilganda),
    tegishli Enrollment obyektining statusini 'completed' ga o'zgartiradi.
    Agar Enrollment mavjud bo'lmasa (bu bo'lmasligi kerak), yangi 'completed' statusli enrollment yaratadi.
    """
    if created: # Faqat yangi UserCourseProgress yaratilganda ishlaydi
        user = instance.user
        course = instance.course

        # Tegishli Enrollment obyektini topish yoki yaratish (agar yo'q bo'lsa, completed status bilan)
        enrollment, enroll_created = Enrollment.objects.get_or_create(
            user=user,
            course=course,
            defaults={'status': Enrollment.COMPLETED} # Agar yo'q bo'lsa, tugatilgan deb yarat
        )

        # Agar Enrollment mavjud bo'lsa va statusi 'completed' bo'lmasa, yangilaymiz
        if not enroll_created and enrollment.status != Enrollment.COMPLETED:
            enrollment.status = Enrollment.COMPLETED
            # enrollment.completed_at = timezone.now() # Agar alohida maydon bo'lsa
            enrollment.save(update_fields=['status', 'updated_at']) # 'completed_at' ham
            print(f"Enrollment status for {user.username} in {course.title} updated to COMPLETED.")
        elif enroll_created:
             print(f"Enrollment created with COMPLETED status for {user.username} in {course.title} (via progress signal).")


# --- END OF FILE signals.py ---