from django.urls import path
from . import views

urlpatterns = [
    path("history/", views.get_watch_history, name="get_watch_history"),
    path("history/<int:movie_id>/", views.mark_as_watched, name="mark_as_watched"),
]
