# --- START OF FILE admin.py (To'liq va Tuzatilgan) ---

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Standart UserAdminni import qilish
from django.contrib.auth.models import User # Standart User modelini import qilish
from django.core.mail import send_mass_mail # Ommaviy email yuborish uchun
from django.template.loader import render_to_string # Email shablonini render qilish uchun (ixtiyoriy)
from django.conf import settings # EMAIL_HOST_USER olish uchun
from django.contrib import messages # Foydalanuvchiga xabar ko'rsatish uchun
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, TextField
from django.contrib.admin import widgets as admin_widgets
from django.utils.translation import gettext_lazy as _

# Modellar
from .models import (
    Module, Course, CourseSyllabus, CourseImage, ExternalActivity,
    Test, Question, Answer,
    Enrollment, UserCourseProgress, UserTestResult, Certificate
)

# --- Inlines ---
class CourseSyllabusInline(admin.TabularInline):
    model = CourseSyllabus
    fields = ('title', 'file')
    extra = 1
    verbose_name = _("Syllabus Fayli")
    verbose_name_plural = _("Syllabus Fayllari")

class CourseImageInline(admin.TabularInline):
    model = CourseImage
    fields = ('image_preview', 'image', 'caption')
    readonly_fields = ('image_preview',)
    extra = 1
    verbose_name = _("Kurs Rasmi")
    verbose_name_plural = _("Kurs Rasmlari")

    # Dekorator va funksiya yangi qatorlarda
    @admin.display(description=_('Rasm (Koʻrish)'))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="max-height: 100px; max-width: 150px;" /></a>',
                obj.image.url
            )
        return _("Rasm yo'q")

class ExternalActivityInline(admin.TabularInline):
    model = ExternalActivity
    fields = ('title', 'activity_type', 'url', 'order')
    extra = 1
    ordering = ('order',)
    verbose_name = _("Tashqi Mashg'ulot")
    verbose_name_plural = _("Tashqi Mashg'ulotlar")

class CourseInline(admin.TabularInline):
    model = Course
    fields = ('title', 'order', 'is_free', 'video_url')
    extra = 1; ordering = ('order',); show_change_link = True
    verbose_name = _("Modul kursi")
    verbose_name_plural = _("Modul kurslari")

class TestInline(admin.StackedInline):
    model = Test
    fields = ('title', 'description', 'passing_score_percent')
    can_delete = False; verbose_name = _("Modul testi")
    verbose_name_plural = _("Modul Testi")

class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ('text', 'is_correct'); extra = 3

class QuestionInline(admin.StackedInline):
    model = Question
    fields = ('text', 'order'); extra = 1; ordering = ('order',); show_change_link = True
    verbose_name = _("Test savoli")
    verbose_name_plural = _("Test savollari")


# --- Foydalanuvchilarga Email Yuborish Action ---
@admin.action(description=_("Tanlangan foydalanuvchilarga email yuborish"))
def send_custom_email_to_users(modeladmin, request, queryset):
    """
    Admin panelidan tanlangan foydalanuvchilarga email yuborish uchun action.
    """
    subject = _("AnorEdu Platformasidan Muhim Xabar")
    message_plain = _("""Hurmatli foydalanuvchi,

Platformamizdagi yangiliklar yoki siz uchun muhim bo'lgan ma'lumotlar bilan tanishib boring.

Batafsil ma'lumot uchun saytimizga tashrif buyuring: [Sayt manzili]

Hurmat bilan,
AnorEdu Jamoasi
""")
    # message_html = render_to_string('emails/admin_bulk_email.html', {})
    from_email = settings.EMAIL_HOST_USER

    messages_to_send = []
    recipient_count = 0
    skipped_count = 0

    for user in queryset:
        if user.email:
            message_tuple = (subject, message_plain, from_email, [user.email])
            messages_to_send.append(message_tuple)
            recipient_count += 1
        else:
            skipped_count += 1

    try:
        sent_count = send_mass_mail(messages_to_send, fail_silently=False)
        if sent_count > 0:
            modeladmin.message_user(request, _("%(count)d ta foydalanuvchiga email muvaffaqiyatli yuborildi.") % {'count': sent_count}, messages.SUCCESS)
        if skipped_count > 0:
             modeladmin.message_user(request, _("%(count)d ta foydalanuvchining email manzili mavjud emasligi uchun xabar yuborilmadi.") % {'count': skipped_count}, messages.WARNING)
        if sent_count == 0 and recipient_count > 0 and skipped_count == 0:
             modeladmin.message_user(request, _("Email yuborishda noma'lum xatolik yuz berdi. Sozlamalarni tekshiring."), messages.ERROR)

    except Exception as e:
        modeladmin.message_user(request, _("Email yuborishda xatolik yuz berdi: %(error)s") % {'error': e}, messages.ERROR)


# --- Standart UserAdminni kengaytirish ---
class CustomUserAdmin(BaseUserAdmin):
    actions = [send_custom_email_to_users] # Yangi actionni qo'shish
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email') # Qidiruv maydonlari

# Standart UserAdminni qayta ro'yxatdan o'tkazish
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# --- ModelAdmin Classlari ---

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'list_image_preview', 'display_course_count', 'is_premium', 'display_has_test', 'created_at_formatted')
    list_filter = ('is_premium', 'created_at',)
    search_fields = ('title', 'description')
    ordering = ('order', 'title')
    fieldsets = (
        (None, {'fields': ('title', 'order', 'is_premium', 'description', 'image', 'image_preview')}),
        (_('Vaqt Belgilari'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)})
    )
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    inlines = [CourseInline, TestInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).annotate(course_count_annotation=Count('courses', distinct=True)) # distinct=True qo'shildi
        return queryset

    @admin.display(description=_('Kurslar soni'), ordering='course_count_annotation')
    def display_course_count(self, obj): return obj.course_count_annotation

    @admin.display(description=_('Test mavjud'), boolean=True)
    def display_has_test(self, obj): return hasattr(obj, 'test') and obj.test is not None

    @admin.display(description=_('Yaratilgan sana'), ordering='created_at')
    def created_at_formatted(self, obj): return obj.created_at.strftime('%d-%m-%Y %H:%M') if obj.created_at else '-'

    @admin.display(description=_('Joriy Rasm'))
    def image_preview(self, obj):
        if obj.image: return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height: 150px; max-width: 200px;" /></a>', obj.image.url)
        return _("Rasm yuklanmagan")

    @admin.display(description=_('Rasm'))
    def list_image_preview(self, obj):
         if obj.image: return format_html('<img src="{0}" style="max-height: 40px; max-width: 60px; border-radius: 4px;" />', obj.image.url)
         return "-"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'module_link', 'order', 'is_free', 'has_video', 'created_at_formatted')
    list_filter = ('is_free', 'module__title', 'created_at');
    search_fields = ('title', 'content', 'module__title')
    ordering = ('module__order', 'order', 'title')
    fieldsets = (
        (None, {'fields': ('module', 'title', 'order', 'is_free', 'video_url')}),
        (_('Kurs Mazmuni'), {'fields': ('content',)}),
        (_('Vaqt Belgilari'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('module',)
    formfield_overrides = {TextField: {'widget': admin_widgets.AdminTextareaWidget(attrs={'rows': 15, 'cols': 80})}}
    inlines = [CourseSyllabusInline, CourseImageInline, ExternalActivityInline]

    @admin.display(description=_('Modul'), ordering='module__title')
    def module_link(self, obj):
        if obj.module: link = reverse("admin:core_module_change", args=[obj.module.id]); return format_html('<a href="{}">{}</a>', link, obj.module.title)
        return "-"
    @admin.display(description=_('Video mavjud'), boolean=True)
    def has_video(self, obj): return bool(obj.video_url)
    created_at_formatted = ModuleAdmin.created_at_formatted # Reuse

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'module_link', 'display_question_count', 'passing_score_percent')
    list_filter = ('module__title',);
    search_fields = ('title', 'description', 'module__title')
    ordering = ('module__order', 'title')
    fields = ('module', 'title', 'description', 'passing_score_percent')
    inlines = [QuestionInline]; list_select_related = ('module',)

    @admin.display(description=_('Modul'), ordering='module__title')
    def module_link(self, obj: Test):
        if obj.module: link = reverse("admin:core_module_change", args=[obj.module.id]); return format_html('<a href="{}">{}</a>', link, obj.module.title)
        return "-"
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(question_count_annotation=Count('questions', distinct=True)) # distinct=True qo'shildi
    @admin.display(description=_('Savollar soni'), ordering='question_count_annotation')
    def display_question_count(self, obj): return obj.question_count_annotation

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'test_link', 'order', 'display_answer_count')
    list_filter = ('test__module__title', 'test__title')
    search_fields = ('text', 'test__title')
    fields = ('test', 'text', 'order')
    inlines = [AnswerInline]; list_select_related = ('test', 'test__module')

    @admin.display(description=_('Savol matni (qisqa)'), ordering='text')
    def short_text(self, obj): return mark_safe(f"{obj.text[:70]}...") if len(obj.text) > 70 else obj.text
    @admin.display(description=_('Test'), ordering='test__title')
    def test_link(self, obj):
        if obj.test and obj.test.module: link = reverse("admin:core_test_change", args=[obj.test.id]); return format_html('<a href="{}">{} ({})</a>', link, obj.test.title, obj.test.module.title)
        elif obj.test: link = reverse("admin:core_test_change", args=[obj.test.id]); return format_html('<a href="{}">{}</a>', link, obj.test.title)
        return "-"
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(answer_count_annotation=Count('answers', distinct=True)) # distinct=True qo'shildi
    @admin.display(description=_('Javoblar soni'), ordering='answer_count_annotation')
    def display_answer_count(self, obj): return obj.answer_count_annotation

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'course_link', 'module_title', 'status', 'enrolled_at_formatted', 'updated_at_formatted')
    list_filter = ('status', 'course__module__title', 'enrolled_at', 'user__username')
    search_fields = ('user__username', 'course__title', 'course__module__title')
    ordering = ('-enrolled_at',)
    readonly_fields = ('user', 'course', 'enrolled_at', 'created_at', 'updated_at')
    list_select_related = ('user', 'course', 'course__module')
    list_editable = ('status',)

    @admin.display(description=_('Foydalanuvchi'), ordering='user__username')
    def user_link(self, obj):
        if obj.user: user_admin_url = reverse("admin:auth_user_change", args=[obj.user.id]); return format_html('<a href="{}">{}</a>', user_admin_url, obj.user.username)
        return "-"
    @admin.display(description=_('Kurs'), ordering='course__title')
    def course_link(self, obj):
        if obj.course: link = reverse("admin:core_course_change", args=[obj.course.id]); return format_html('<a href="{}">{}</a>', link, obj.course.title)
        return "-"
    @admin.display(description=_('Modul'), ordering='course__module__title')
    def module_title(self, obj): return obj.course.module.title if obj.course and obj.course.module else "-"
    @admin.display(description=_('Yozilgan sana'), ordering='enrolled_at')
    def enrolled_at_formatted(self, obj): return obj.enrolled_at.strftime('%d-%m-%Y %H:%M') if obj.enrolled_at else '-'
    @admin.display(description=_('Yangilangan sana'), ordering='updated_at')
    def updated_at_formatted(self, obj): return obj.updated_at.strftime('%d-%m-%Y %H:%M') if obj.updated_at else '-'
    def has_add_permission(self, request, obj=None): return False

@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'course_link', 'module_title', 'created_at_formatted')
    list_filter = ('created_at', 'course__module__title', 'user__username')
    search_fields = ('user__username', 'course__title', 'course__module__title')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'course', 'created_at', 'updated_at')
    list_select_related = ('user', 'course', 'course__module')
    user_link = EnrollmentAdmin.user_link # Reuse
    course_link = EnrollmentAdmin.course_link # Reuse
    module_title = EnrollmentAdmin.module_title # Reuse
    @admin.display(description=_('Tugatilgan sana'), ordering='created_at')
    def created_at_formatted(self, obj): return obj.created_at.strftime('%d-%m-%Y %H:%M') if obj.created_at else '-'
    def has_add_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False
    # O'chirishga ruxsat berish (Variant 1 bo'yicha)
    def has_delete_permission(self, request, obj=None): return True

@admin.register(UserTestResult)
class UserTestResultAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'test_link', 'module_title', 'score', 'passed_status', 'created_at_formatted')
    list_filter = ('passed', 'test__module__title', 'created_at', 'user__username')
    search_fields = ('user__username', 'test__title', 'test__module__title')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'test', 'score', 'passed', 'created_at', 'updated_at')
    list_select_related = ('user', 'test', 'test__module')
    user_link = EnrollmentAdmin.user_link # Reuse

    @admin.display(description=_('Test'), ordering='test__title')
    def test_link(self, obj):
         if obj.test: link = reverse("admin:core_test_change", args=[obj.test.id]); return format_html('<a href="{}">{}</a>', link, obj.test.title)
         return "-"
    @admin.display(description=_('Modul'), ordering='test__module__title')
    def module_title(self, obj: UserTestResult):
        return obj.test.module.title if obj.test and obj.test.module else "-"
    @admin.display(description=_("O'tganligi"), boolean=True, ordering='passed')
    def passed_status(self, obj): return obj.passed
    @admin.display(description=_('Urinish vaqti'), ordering='created_at')
    def created_at_formatted(self, obj): return obj.created_at.strftime('%d-%m-%Y %H:%M') if obj.created_at else '-'
    def has_add_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_link', 'user_link', 'module_link', 'created_at_formatted')
    list_filter = ('created_at', 'module__title', 'user__username')
    search_fields = ('user__username', 'module__title', 'certificate_id')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'module', 'certificate_id', 'created_at', 'updated_at')
    list_select_related = ('user', 'module')
    user_link = EnrollmentAdmin.user_link # Reuse

    @admin.display(description=_('Modul'), ordering='module__title')
    def module_link(self, obj: Certificate):
        if obj.module: link = reverse("admin:core_module_change", args=[obj.module.id]); return format_html('<a href="{}">{}</a>', link, obj.module.title)
        return "-"
    @admin.display(description=_('Sertifikat ID'), ordering='certificate_id')
    def certificate_link(self, obj):
        link = reverse("admin:core_certificate_change", args=[obj.id]); return format_html('<a href="{}">{}...</a>', link, str(obj.certificate_id)[:13])
    @admin.display(description=_('Berilgan sana'), ordering='created_at')
    def created_at_formatted(self, obj): return obj.created_at.strftime('%d-%m-%Y %H:%M') if obj.created_at else '-'
    def has_add_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False

# --- Admin sayt sozlamalari ---
admin.site.site_header = _("AnorEdu Admin Paneli") # Nom o'zgartirildi
admin.site.site_title = _("AnorEdu Admin")
admin.site.index_title = _("Boshqaruv Paneli")

# --- END OF FILE admin.py ---