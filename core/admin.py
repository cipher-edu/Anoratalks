from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'level', 'duration', 'price', 'created_at')
    list_filter = ('category', 'level')
    search_fields = ('name', 'category')
    ordering = ('name',)

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'section', 'section_order', 'duration', 'is_visible', 'uploaded_at')
    list_filter = ('course', 'section', 'is_visible')
    search_fields = ('title', 'course__name', 'section')
    ordering = ('course', 'section_order')