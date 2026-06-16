"""URL-маршруты проекта Team Finder."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

HOME_REDIRECT_ROUTE = "projects:list"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name=HOME_REDIRECT_ROUTE, permanent=False)),
    path("admin/", admin.site.urls),
    path("projects/", include("projects.urls", namespace="projects")),
    path("users/", include("users.urls", namespace="users")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
