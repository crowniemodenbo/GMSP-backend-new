from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, CourseViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'videos', VideoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

