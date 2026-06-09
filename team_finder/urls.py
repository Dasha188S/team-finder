"""URL-маршруты проекта Team Finder."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda request: redirect("/projects/list/", permanent=False)),
    path("admin/", admin.site.urls),
    path("projects/", include("projects.urls", namespace="projects")),
    path("users/", include("users.urls", namespace="users")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
