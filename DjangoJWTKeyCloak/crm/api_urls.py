"""URL-Muster für die REST-API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api

router = DefaultRouter()
router.register("kunden", api.KundeViewSet, basename="api-kunde")
router.register("artikel", api.ArtikelViewSet, basename="api-artikel")
router.register("auftraege", api.AuftragViewSet, basename="api-auftrag")
router.register("positionen", api.AuftragspositionViewSet, basename="api-position")

urlpatterns = [
    path("", include(router.urls)),
]
