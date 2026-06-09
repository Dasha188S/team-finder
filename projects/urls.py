"""URL-маршруты приложения projects."""
from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list, name="list"),
    path("list", views.project_list),
    path("create-project/", views.project_create, name="create"),
    path("create-project", views.project_create),
    path("<int:project_id>/", views.project_detail, name="detail"),
    path("<int:project_id>", views.project_detail),
    path("<int:project_id>/edit/", views.project_edit, name="edit"),
    path("<int:project_id>/edit", views.project_edit),
    path("<int:project_id>/complete/", views.project_complete, name="complete"),
    path(
        "<int:project_id>/toggle-participate/",
        views.project_toggle_participate,
        name="toggle_participate",
    ),
    path(
        "<int:project_id>/toggle-participate",
        views.project_toggle_participate,
    ),
]
