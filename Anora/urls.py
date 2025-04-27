# Anora/urls.py (yoki loyihangizning asosiy urls.py fayli)

from django.contrib import admin
from django.urls import path, include, reverse_lazy # reverse_lazy import qilinganligini tekshiring
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')), # Core ilovasi
    path('accounts/', include('django.contrib.auth.urls')), # Django autentifikatsiya URLlarini qo'shish
    # --- Autentifikatsiya URL manzillari ---
    # Eslatma: Bu URLlar odatda '/accounts/' prefiksi ostida joylanadi
    # yoki `django.contrib.auth.urls` orqali qo'shiladi.
    # Agar alohida yozsangiz, template_name va success_url to'g'ri bo'lishi kerak.

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html', # templates/registration/ papkasidan qidiriladi
        email_template_name='registration/password_reset_email.html', # Email uchun shablon
        subject_template_name='registration/password_reset_subject.txt', # Email mavzusi uchun (ixtiyoriy)
        success_url=reverse_lazy('password_reset_done')), # Nomlangan URLga yo'naltirish
        name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'),
        name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')),
        name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'),
        name='password_reset_complete'),

    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html',
        success_url=reverse_lazy('password_change_done')),
        name='password_change'),

    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'),
        name='password_change_done'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)