# --- START OF FILE utils.py ---

from django.utils import timezone
from django.db.models import Q # Murakkab filterlar uchun

# Modellarni import qilish
# UserCourseProgress o'rniga yoki u bilan birga Enrollment ishlatamiz
from .models import Enrollment, Module, Course, UserCourseProgress, Answer

def is_user_enrolled(user, course: Course) -> bool:
    """Foydalanuvchi ushbu kursga 'enrolled' statusida yozilganligini tekshiradi."""
    if not user or not user.is_authenticated:
        return False
    return Enrollment.objects.filter(
        user=user,
        course=course,
        status=Enrollment.ENROLLED
    ).exists()

def has_user_completed_course(user, course: Course) -> bool:
    """Foydalanuvchi ushbu kursni tugatganligini Enrollment statusi orqali tekshiradi."""
    if not user or not user.is_authenticated:
        return False
    # Birinchi Enrollment orqali tekshiramiz
    completed_enrollment = Enrollment.objects.filter(
        user=user,
        course=course,
        status=Enrollment.COMPLETED
    ).exists()
    if completed_enrollment:
        return True
    # Agar Enrollment (completed) topilmasa, UserCourseProgress orqali ham tekshiramiz (eski tizim uchun)
    return UserCourseProgress.objects.filter(user=user, course=course).exists()


def can_user_view_course(user, course: Course) -> bool:
    """Foydalanuvchi kurs mazmunini ko'ra oladimi?"""
    # Agar kurs/modul bepul bo'lsa, hamma ko'rishi mumkin (hatto avtorizatsiyasiz)
    if course.is_free and not course.module.is_premium:
        return True
    # Agar avtorizatsiyadan o'tmagan bo'lsa va kurs bepul bo'lmasa, ko'ra olmaydi
    if not user or not user.is_authenticated:
        return False
    # Agar yozilgan bo'lsa (har qanday statusda, chunki yozilgan bo'lsa ko'rishi kerak)
    # Yoki status='enrolled' bo'lishi kerakmi? Hozircha har qanday yozilganlikka ruxsat beramiz.
    return Enrollment.objects.filter(user=user, course=course).exists()


def has_user_completed_module(user, module: Module) -> bool:
    """
    Foydalanuvchi berilgan modulning *barcha* kurslarini tugatganligini tekshiradi.
    Enrollment statusiga asoslanadi.
    """
    if not user or not user.is_authenticated:
        return False

    # Moduldagi barcha kurslar (kerakli kurslar)
    required_courses = module.courses.all()
    total_courses_in_module = required_courses.count()

    if total_courses_in_module == 0:
        return True # Kursi yo'q modul tugatilgan hisoblanadi

    # Foydalanuvchi tomonidan ushbu modulda 'completed' statusidagi Enrollmentlar soni
    completed_enrollments_count = Enrollment.objects.filter(
        user=user,
        course__in=required_courses, # Faqat shu moduldagi kurslar
        status=Enrollment.COMPLETED
    ).count()

    # Agar Enrollment orqali topilmasa, UserCourseProgress orqali ham tekshiramiz
    if completed_enrollments_count < total_courses_in_module:
         completed_progress_count = UserCourseProgress.objects.filter(
              user=user,
              course__in=required_courses
         ).count()
         return completed_progress_count >= total_courses_in_module

    return completed_enrollments_count >= total_courses_in_module


def can_user_access_test(user, module: Module) -> bool:
    """
    Foydalanuvchi modul testiga kira oladimi yoki yo'qligini tekshiradi.
    1. Modul premium bo'lsa, foydalanuvchi unga qandaydir yo'l bilan kirgan bo'lishi kerak (hozircha tekshirilmaydi).
    2. Modulning barcha kurslari tugatilgan bo'lishi kerak.
    """
    # 1. Modul premium statusini tekshirish (kelajakda qo'shilishi mumkin)
    # if module.is_premium:
    #     # Foydalanuvchining modulga kirish huquqini tekshirish logikasi
    #     # Masalan: if not has_module_access(user, module): return False
    #     pass # Hozircha o'tkazib yuboramiz

    # 2. Barcha kurslar tugatilganligini tekshirish
    return has_user_completed_module(user, module)


def calculate_test_score(test, user_answers: dict) -> tuple[int, bool]:
    """
    Foydalanuvchi javoblariga asoslanib test natijasini (foizda) hisoblaydi.
    user_answers formati: {'question_pk_1': 'answer_pk_1', ...}
    Returns: (score_percent, passed)
    (Bu funksiya o'zgarishsiz qoladi)
    """
    if not test:
        return 0, False

    # Savollar va to'g'ri javoblarni oldindan yuklash
    questions = test.questions.prefetch_related('answers')
    total_questions = questions.count()
    if total_questions == 0:
        return 100, True # Savol yo'q bo'lsa, o'tgan hisoblanadi

    # To'g'ri javob PKlarini bir marta olish
    correct_answer_pks = set(str(pk) for pk in Answer.objects.filter(
        question__test=test, is_correct=True
    ).values_list('pk', flat=True))

    correct_answers_count = 0
    for question in questions:
        question_pk_str = str(question.pk)
        user_answer_pk_str = user_answers.get(question_pk_str) # string sifatida olamiz

        if user_answer_pk_str and user_answer_pk_str in correct_answer_pks:
            correct_answers_count += 1

    score_percent = round((correct_answers_count / total_questions) * 100) if total_questions > 0 else 0
    passed = score_percent >= test.passing_score_percent

    return score_percent, passed

# --- END OF FILE utils.py ---