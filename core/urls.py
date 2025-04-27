# --- START OF FILE core/urls.py ---

from django.urls import path
from . import views # Shu papkadagi views.py ni import qilish

app_name = 'core' # Ilova uchun nom maydoni (namespace)

urlpatterns = [
    # Authentication URLs (core ilovasiga tegishli)
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Module and Course URLs
    # Bosh sahifa (ilovaning ildizi) modullar ro'yxatini ko'rsatadi
    path('', views.module_list_view, name='module_list'),
    path('modules/<int:pk>/', views.module_detail_view, name='module_detail'),
    path('courses/<int:pk>/', views.course_detail_view, name='course_detail'),
    # Kursni 'Tugatildi' deb belgilash uchun POST endpoint
    path('courses/<int:pk>/complete/', views.mark_course_complete_view, name='mark_course_complete'),

    # Test URLs
    path('modules/<int:module_pk>/test/', views.take_test_view, name='take_test'), # GET/POST
    # Test natijasini ko'rsatish (UserTestResult PKsi)
    path('results/<int:pk>/', views.test_result_view, name='test_result'),

    # Certificate URLs
    path('certificates/', views.my_certificates_view, name='my_certificates'), # Mening sertifikatlarim
    # Bitta sertifikatni UUID bo'yicha ko'rsatish
    path('certificates/<uuid:certificate_id>/', views.certificate_view, name='certificate_detail'),

    # Foydalanuvchi uchun maxsus sahifalar
    path('my-courses/', views.my_courses_view, name='my_courses'), # Mening kurslarim
    path('my-results/', views.my_results_view, name='my_results'), # Mening natijalarim

]

# Eslatma: Media fayllarni (settings.MEDIA_URL) sozlash loyihaning asosiy
# urls.py faylida amalga oshirilishi kerak (DEBUG=True bo'lganda).

# --- END OF FILE core/urls.py ---