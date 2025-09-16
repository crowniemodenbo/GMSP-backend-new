from django.contrib import admin
from .models import Video, Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_active', 'video_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'created_by__email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}
    
    def video_count(self, obj):
        return obj.videos.count()
    video_count.short_description = 'Videos'


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'uploaded_by', 'upload_date', 'is_active')
    list_filter = ('is_active', 'upload_date', 'course')
    search_fields = ('title', 'description', 'uploaded_by__email', 'course__title')
    readonly_fields = ('upload_date',)
    date_hierarchy = 'upload_date'
    autocomplete_fields = ['course']
    list_select_related = ('course', 'uploaded_by')
