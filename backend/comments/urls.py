from django.urls import path
from . import views

urlpatterns = [
    path("comments", views.comments_list_create),
    path("comments/<int:id>", views.comment_detail),
]
