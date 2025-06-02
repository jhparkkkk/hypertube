from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubtitleViewSet

router = DefaultRouter()
router.register('', SubtitleViewSet, basename='subtitles')

urlpatterns = [
    path('', include(router.urls)),
] 