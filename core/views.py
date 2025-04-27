# --- START OF FILE views.py (settings import qo'shilgan) ---

import uuid # Sertifikat ID uchun
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin # Class-based viewlar uchun
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView, ListView, DetailView
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.db import transaction
from django.utils import timezone # Enrollment uchun
from django.utils.translation import gettext_lazy as _
from django.conf import settings # <--- YANGI: settings import qilindi
from django.db import models # Prefetch uchun

# Modellar
from core.models import (
    Module, Course, Test, Question, Answer, Enrollment,
    UserCourseProgress, UserTestResult, Certificate,
    CourseSyllabus, CourseImage, ExternalActivity
)

# Formular
from .forms import CustomAuthenticationForm, TestSubmissionForm, CustomUserCreationForm

# Yordamchi funksiyalar
try:
    from .utils import (
        can_user_access_test, calculate_test_score, has_user_completed_module,
        can_user_view_course, has_user_completed_course, is_user_enrolled
    )
except ImportError:
    raise ImportError("core/utils.py fayli yoki undagi kerakli funksiyalar topilmadi.")


def handler404(request, exception):
    return render(request, '404.html', status=404)

# --- Authentication Views ---

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('core:module_list')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Muvaffaqiyatli roʻyxatdan oʻtdingiz va tizimga kirdingiz!'))
        return super().form_valid(form)

    def form_invalid(self, form):
        error_message = _('Roʻyxatdan oʻtishda xatolik yuz berdi. Iltimos, quyidagi xatolarni tuzating:')
        messages.error(self.request, error_message)
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'registration/login.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        # settings endi mavjud
        return reverse_lazy(settings.LOGIN_REDIRECT_URL or 'core:module_list')

    def form_valid(self, form):
        messages.success(self.request, _('Tizimga muvaffaqiyatli kirdingiz!'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Foydalanuvchi nomi yoki parol xato.'))
        return super().form_invalid(form)


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, _('Tizimdan muvaffaqiyatli chiqdingiz.'))
    return redirect('core:login')


# --- Learning Content Views ---

@login_required
def module_list_view(request):
    modules = Module.objects.order_by('order').prefetch_related('courses')
    context = {
        'modules': modules
    }
    return render(request, 'learning_platform/module_list.html', context) # Shablon yo'li to'g'ri


@login_required
def module_detail_view(request, pk):
    module = get_object_or_404(
        Module.objects.prefetch_related(
            'courses',
            'test',
            models.Prefetch(
                'courses__enrollments',
                queryset=Enrollment.objects.filter(user=request.user),
                to_attr='user_enrollments'
            )
        ),
        pk=pk
    )

    user_completed_courses_pks = set()
    user_enrolled_courses_pks = set()
    for course in module.courses.all():
        enrollment = next((e for e in getattr(course, 'user_enrollments', []) if e.user_id == request.user.id), None)
        if enrollment:
            user_enrolled_courses_pks.add(course.pk)
            if enrollment.status == Enrollment.COMPLETED:
                user_completed_courses_pks.add(course.pk)
        elif UserCourseProgress.objects.filter(user=request.user, course=course).exists():
             user_completed_courses_pks.add(course.pk)


    module_completed = has_user_completed_module(request.user, module)
    test_instance = getattr(module, 'test', None)
    test_available = test_instance is not None
    can_take_test = test_available and can_user_access_test(request.user, module)

    last_test_result = None
    if test_instance:
        last_test_result = UserTestResult.objects.filter(
            user=request.user, test=test_instance
        ).order_by('-created_at').first()

    context = {
        'module': module,
        'user_enrolled_courses_pks': user_enrolled_courses_pks,
        'user_completed_courses_pks': user_completed_courses_pks,
        'module_completed': module_completed,
        'test_available': test_available,
        'can_take_test': can_take_test,
        'test_instance': test_instance,
        'last_test_result': last_test_result,
    }
    return render(request, 'learning_platform/module_detail.html', context) # Shablon yo'li to'g'ri


@login_required
def my_courses_view(request):
    """ Foydalanuvchining yozilgan kurslarini ko'rsatadi """
    enrollments = Enrollment.objects.filter(user=request.user)\
                                   .select_related('course', 'course__module')\
                                   .order_by('course__module__order', 'course__order') # Modul va kurs tartibi bo'yicha

    context = {
        'enrollments': enrollments
    }
    return render(request, 'learning_platform/my_courses.html', context)


@login_required
def my_results_view(request):
    """ Foydalanuvchining barcha test natijalarini ko'rsatadi """
    results = UserTestResult.objects.filter(user=request.user)\
                                    .select_related('test', 'test__module')\
                                    .order_by('-created_at') # Oxirgi urinishlar birinchi

    context = {
        'results': results
    }
    return render(request, 'learning_platform/my_results.html', context)


@login_required
def course_detail_view(request, pk):
    course = get_object_or_404(
        Course.objects.select_related('module').prefetch_related(
            'syllabi', 'images', 'external_activities',
            models.Prefetch(
                'enrollments',
                queryset=Enrollment.objects.filter(user=request.user),
                to_attr='user_enrollment_list'
            )
        ),
        pk=pk
    )

    user_enrollment = next((e for e in getattr(course, 'user_enrollment_list', []) if e.user_id == request.user.id), None)
    can_view = False
    is_enrolled = user_enrollment is not None
    is_completed = False

    if course.is_free and not course.module.is_premium:
        can_view = True
        if not is_enrolled and request.user.is_authenticated:
            user_enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
            if created:
                 messages.info(request, _("Siz '{course_title}' bepul kursiga avtomatik yozildingiz.").format(course_title=course.title))
            is_enrolled = True
    elif is_enrolled:
        can_view = True

    if not can_view and request.user.is_authenticated: # Avtorizatsiyadan o'tgan bo'lsa va ko'ra olmasa
        messages.warning(request, _("Bu kursni ko'rish uchun avval unga yozilishingiz kerak."))
        return redirect('core:module_detail', pk=course.module.pk)
    elif not can_view and not request.user.is_authenticated: # Avtorizatsiyasiz va ko'ra olmasa
         # Kirish sahifasiga yo'naltirish
         login_url = reverse('core:login')
         return redirect(f'{login_url}?next={request.path}')


    if user_enrollment and user_enrollment.status == Enrollment.COMPLETED:
        is_completed = True
    elif UserCourseProgress.objects.filter(user=request.user, course=course).exists():
         is_completed = True

    syllabi = course.syllabi.all()
    images = course.images.all()
    external_activities = course.external_activities.order_by('order')

    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'is_completed': is_completed,
        'syllabi': syllabi,
        'images': images,
        'external_activities': external_activities,
    }
    return render(request, 'learning_platform/course_detail.html', context) # Shablon yo'li to'g'ri


@login_required
@transaction.atomic
def mark_course_complete_view(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden(_("Faqat POST so'rovlariga ruxsat etilgan."))

    course = get_object_or_404(Course, pk=pk)
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()

    if not enrollment:
        if course.is_free and not course.module.is_premium:
             enrollment = Enrollment.objects.create(user=request.user, course=course, status=Enrollment.ENROLLED)
             print(f"Auto-enrolled user {request.user.username} to course {course.title} before completion.")
        else:
             messages.error(request, _("Bu kursni tugatish uchun avval unga yozilishingiz kerak."))
             return redirect('core:course_detail', pk=course.pk)

    progress, created = UserCourseProgress.objects.get_or_create(
        user=request.user,
        course=course
    )

    if created:
        messages.success(request, _("'{course_title}' kursi muvaffaqiyatli tugatildi deb belgilandi.").format(course_title=course.title))
    else:
        if enrollment and enrollment.status != Enrollment.COMPLETED:
             enrollment.status = Enrollment.COMPLETED
             enrollment.save(update_fields=['status', 'updated_at'])
        messages.info(request, _("Siz '{course_title}' kursini avvalroq tugatgansiz.").format(course_title=course.title))

    return redirect('core:module_detail', pk=course.module.pk)


# --- Test Views ---

@login_required
def take_test_view(request, module_pk):
    module = get_object_or_404(Module.objects.prefetch_related('test__questions__answers'), pk=module_pk)
    test_instance = getattr(module, 'test', None)

    if not test_instance:
        messages.error(request, _("Bu modul uchun test topilmadi."))
        return redirect('core:module_detail', pk=module.pk)

    if not can_user_access_test(request.user, module):
        messages.warning(request, _("Testni topshirish uchun avval modulning barcha kurslarini tugatishingiz kerak."))
        return redirect('core:module_detail', pk=module.pk)

    if not test_instance.questions.exists():
         messages.warning(request, _("Bu testda hali savollar qo'shilmagan."))
         return redirect('core:module_detail', pk=module.pk)

    if request.method == 'POST':
        form = TestSubmissionForm(request.POST, test=test_instance)
        if form.is_valid():
            user_answers = form.get_user_answers()
            score, passed = calculate_test_score(test_instance, user_answers)

            with transaction.atomic():
                result = UserTestResult.objects.create(
                    user=request.user,
                    test=test_instance,
                    score=score,
                    passed=passed
                )
            messages.success(request, _("Test muvaffaqiyatli topshirildi! Natijangizni ko'ring."))
            return redirect('core:test_result', pk=result.pk)
        else:
            error_msg = _("Iltimos, barcha savollarga javob bering.")
            if form.errors:
                first_error_field = list(form.errors.keys())[0]
                error_msg = form.errors[first_error_field][0]
            messages.error(request, error_msg)
            context = {'test': test_instance, 'form': form, 'module': module}
            return render(request, 'learning_platform/take_test.html', context) # Shablon yo'li to'g'ri
    else:
        form = TestSubmissionForm(test=test_instance)

    context = {
        'test': test_instance,
        'form': form,
        'module': module,
    }
    return render(request, 'learning_platform/take_test.html', context) # Shablon yo'li to'g'ri


@login_required
def test_result_view(request, pk):
    result = get_object_or_404(
        UserTestResult.objects.select_related('user', 'test__module'),
        pk=pk,
        user=request.user
    )

    certificate = None
    if result.passed:
        certificate = Certificate.objects.filter(user=request.user, module=result.test.module).first()

    context = {
        'result': result,
        'certificate': certificate,
    }
    return render(request, 'learning_platform/test_result.html', context) # Shablon yo'li to'g'ri


# --- Certificate Views ---

@login_required
def my_certificates_view(request):
    certificates = Certificate.objects.filter(user=request.user).select_related('module').order_by('-created_at')
    context = {
        'certificates': certificates
    }
    return render(request, 'learning_platform/my_certificates.html', context) # Shablon yo'li to'g'ri

@login_required
def certificate_view(request, certificate_id):
    try:
        valid_uuid = uuid.UUID(str(certificate_id))
        certificate = get_object_or_404(
            Certificate.objects.select_related('user', 'module'),
            certificate_id=valid_uuid
        )
    except (ValueError, TypeError, Http404):
        raise Http404(_("Bunday ID bilan sertifikat topilmadi yoki ID formati noto'g'ri."))

    if certificate.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden(_("Sizga bu sertifikatni ko'rishga ruxsat yo'q."))

    context = {
        'certificate': certificate
    }
    return render(request, 'learning_platform/certificate_detail.html', context) # Shablon yo'li to'g'ri


# --- END OF FILE views.py (settings import qo'shilgan) ---