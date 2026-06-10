"""
REST-API-Views für die CRM-Anwendung.

SICHERHEIT (A01 Broken Access Control):
- Alle Lese-Endpunkte erfordern IstLeser-Permission.
- Alle Schreib-Endpunkte erfordern IstSchreiber-Permission.
- Authentifizierung erfolgt über JWTBearerAuthentication (auth_kc/jwt_bearer.py).
- HTTP-Methoden werden explizit auf Lesen/Schreiben aufgeteilt.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Kunde, Artikel, Auftrag, Auftragsposition
from .serializers import (
    KundeSerializer,
    ArtikelSerializer,
    AuftragSerializer,
    AuftragspositionSerializer,
)
from .permissions import IstLeser, IstSchreiber

logger = logging.getLogger(__name__)

# SICHERHEIT: Schreibmethoden sind explizit definiert (A01)
LESE_METHODEN = ("GET", "HEAD", "OPTIONS")
SCHREIB_METHODEN = ("POST", "PUT", "PATCH", "DELETE")


class RollenBasierterViewSet(viewsets.ModelViewSet):
    """
    Basisklasse mit rollen-basierter Berechtigungsprüfung.

    Lesen: app-reader oder app-writer Rolle
    Schreiben: nur app-writer Rolle
    """

    def get_permissions(self):
        """
        SICHERHEIT: Berechtigungen werden pro HTTP-Methode vergeben.
        Standard ist immer verweigern (fail-closed, A01).
        """
        if self.request.method in LESE_METHODEN:
            return [IstLeser()]
        return [IstSchreiber()]

    def perform_create(self, serializer):
        logger.info(
            "API: Neuer Eintrag '%s' angelegt von Benutzer '%s'.",
            self.get_queryset().model.__name__,
            getattr(self.request.user, "username", "unbekannt"),
        )
        serializer.save()

    def perform_destroy(self, instance):
        logger.info(
            "API: Eintrag '%s' #%s gelöscht von Benutzer '%s'.",
            instance.__class__.__name__,
            instance.pk,
            getattr(self.request.user, "username", "unbekannt"),
        )
        instance.delete()


class KundeViewSet(RollenBasierterViewSet):
    queryset = Kunde.objects.all().order_by("name")
    serializer_class = KundeSerializer


class ArtikelViewSet(RollenBasierterViewSet):
    queryset = Artikel.objects.all().order_by("artikelnummer")
    serializer_class = ArtikelSerializer


class AuftragViewSet(RollenBasierterViewSet):
    serializer_class = AuftragSerializer

    def get_queryset(self):
        return Auftrag.objects.select_related("kunde").prefetch_related(
            "positionen__artikel"
        ).order_by("-auftragsdatum")


class AuftragspositionViewSet(RollenBasierterViewSet):
    queryset = Auftragsposition.objects.select_related("auftrag", "artikel")
    serializer_class = AuftragspositionSerializer
