from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Video, Course
from .serializers import (
    VideoSerializer, VideoUploadSerializer,
    CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer
)


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users to upload videos."""
    
    def has_permission(self, request, view):
        # Allow GET requests for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin users
        return request.user and request.user.role == 'admin'


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseListSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of a course."""
        course = self.get_object()
        course.is_active = not course.is_active
        course.save()
        serializer = CourseListSerializer(course, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def videos(self, request, pk=None):
        """Get all videos for a specific course."""
        course = self.get_object()
        videos = course.videos.filter(is_active=True).order_by('order_in_course')
        serializer = VideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return VideoUploadSerializer
        return VideoSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_videos(self, request):
        """Get videos uploaded by the current user."""
        videos = Video.objects.filter(uploaded_by=request.user)
        serializer = VideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of a video."""
        video = self.get_object()
        video.is_active = not video.is_active
        video.save()
        serializer = VideoSerializer(video, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get videos filtered by course."""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({"error": "course_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        course = get_object_or_404(Course, id=course_id)
        videos = Video.objects.filter(course=course, is_active=True).order_by('order_in_course')
        serializer = VideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)
