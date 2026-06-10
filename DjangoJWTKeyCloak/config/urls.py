"""URL-Konfiguration für das Django-Keycloak-JWT-Demo-Projekt."""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # OIDC-Endpunkte (Login, Callback, Logout)
    path("oidc/", include("mozilla_django_oidc.urls")),
    # Fachanwendung Web-Oberfläche
    path("", include("crm.urls")),
    # REST-API
    path("api/", include("crm.api_urls")),
]
