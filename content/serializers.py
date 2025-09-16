from rest_framework import serializers
from .models import Video, Course
from users.serializers import UserSerializer


class CourseListSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    video_count = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()  # NEW
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'description', 'thumbnail', 'thumbnail_url', 
                  'created_by', 'created_at', 'is_active', 'video_count','duration']
        read_only_fields = ['created_at', 'created_by', 'slug']
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.thumbnail.url)
        return None
    
    def get_video_count(self, obj):
        return obj.videos.filter(is_active=True).count()
    def get_duration(self, obj):
        return sum(obj.videos.filter(is_active=True).values_list('duration', flat=True))


class CourseDetailSerializer(CourseListSerializer):
    videos = serializers.SerializerMethodField()
    
    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['videos']
    
    def get_videos(self, obj):
        videos = obj.videos.filter(is_active=True).order_by('order_in_course')
        return VideoSerializer(videos, many=True, context=self.context).data


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['title', 'description', 'thumbnail', 'is_active']
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Only allow admins to create courses
        if user.role != 'admin':
            raise serializers.ValidationError("Only admin users can create courses.")
        
        course = Course.objects.create(
            created_by=user,
            **validated_data
        )
        
        return course


class VideoSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    video_file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'video_file', 'video_file_url', 
                  'thumbnail', 'thumbnail_url', 'course', 'course_title', 'order_in_course',
                  'uploaded_by', 'upload_date', 'is_active','duration']
        read_only_fields = ['upload_date', 'uploaded_by']
    
    def get_video_file_url(self, obj):
        if obj.video_file:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.video_file.url)
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.thumbnail.url)
        return None
    
    def get_course_title(self, obj):
        if obj.course:
            return obj.course.title
        return None


class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['title', 'description', 'video_file', 'thumbnail', 'course', 'order_in_course']
    
    def create(self, validated_data):
        # Get the current user from the context
        user = self.context['request'].user
        
        # Only allow admins to upload videos
        if user.role != 'admin':
            raise serializers.ValidationError("Only admin users can upload videos.")
        
        # Create the video with the current user as uploader
        video = Video.objects.create(
            uploaded_by=user,
            **validated_data
        )
        
        return video