from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StreamingViewSet

router = DefaultRouter()
router.register(r"streaming", StreamingViewSet, basename="streaming")

urlpatterns = [
    path("", include(router.urls)),
]
