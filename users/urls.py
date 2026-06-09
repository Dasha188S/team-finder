"""URL-маршруты приложения users."""
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("list/", views.participants_view, name="list"),
    path("list", views.participants_view),
    path("edit-profile/", views.edit_profile_view, name="edit_profile"),
    path("edit-profile", views.edit_profile_view),
    path("change-password/", views.change_password_view, name="change_password"),
    path("change-password", views.change_password_view),
    path("skills/", views.skills_autocomplete, name="skills_autocomplete"),
    path("<int:user_id>/skills/add/", views.add_skill_view, name="skills_add"),
    path("<int:user_id>/skills/add", views.add_skill_view),
    path(
        "<int:user_id>/skills/<int:skill_id>/remove/",
        views.remove_skill_view,
        name="skills_remove",
    ),
    path("<int:user_id>/", views.user_detail_view, name="detail"),
    path("<int:user_id>", views.user_detail_view),
]
