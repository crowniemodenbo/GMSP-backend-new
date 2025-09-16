from django.db import models
from django.utils import timezone
from users.models import User


def video_upload_path(instance, filename):
    # Generate a path like: videos/YYYY-MM-DD/filename
    today = timezone.now().strftime('%Y-%m-%d')
    return f'videos/{today}/{filename}'


class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['title']


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_file = models.FileField(upload_to=video_upload_path)
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_videos')
    upload_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    order_in_course = models.PositiveIntegerField(default=0, help_text="Order of video within the course")
    duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['course', 'order_in_course', '-upload_date']
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'
