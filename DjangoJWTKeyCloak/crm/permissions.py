"""
Berechtigungsklassen für Web-Views und REST-API.

SICHERHEIT (A01 Broken Access Control):
- Standard ist immer "verweigern" (fail-closed).
- Rollen werden server-seitig aus der Django-Gruppe geprüft,
  die beim Login aus dem JWT synchronisiert wurde.
- Für die API werden Rollen zusätzlich direkt aus dem JWT-Payload geprüft.
"""

import logging
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from auth_kc.jwt_bearer import hat_rolle

logger = logging.getLogger(__name__)

# Gruppen-Namen müssen mit ROLE_MAP in oidc_backend.py übereinstimmen
GRUPPE_LESER = "Leser"
GRUPPE_SCHREIBER = "Schreiber"


# ---------------------------------------------------------------------------
# Web-View-Mixins (für Template-basierte Views)
# ---------------------------------------------------------------------------

class LeserOderSchreiberMixin(AccessMixin):
    """
    Erlaubt den Zugriff für eingeloggte Benutzer mit Leser- oder Schreiber-Rolle.
    SICHERHEIT: Nicht eingeloggte Benutzer werden zur Login-Seite weitergeleitet.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not _ist_leser_oder_schreiber(request.user):
            logger.warning(
                "Zugriff verweigert für Benutzer '%s' auf %s (keine App-Rolle).",
                request.user.username,
                request.path,
            )
            raise PermissionDenied("Sie haben keine Berechtigung für diese Seite.")
        return super().dispatch(request, *args, **kwargs)


class SchreiberMixin(AccessMixin):
    """
    Erlaubt den Zugriff nur für Benutzer mit Schreiber-Rolle.
    Lesende Benutzer erhalten HTTP 403.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not _ist_schreiber(request.user):
            logger.warning(
                "Schreibzugriff verweigert für Benutzer '%s' auf %s.",
                request.user.username,
                request.path,
            )
            raise PermissionDenied("Sie benötigen die Schreiber-Rolle für diese Aktion.")
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# DRF-Permissions (für die REST-API)
# ---------------------------------------------------------------------------

class IstLeser(BasePermission):
    """
    API-Permission: Erlaubt Lesezugriff für Benutzer mit app-reader oder app-writer Rolle.
    SICHERHEIT: Rollen werden aus dem verifizierten JWT-Payload geprüft (A01).
    """

    message = "Sie benötigen mindestens die app-reader Rolle."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # JWT-Payload ist in request.auth verfügbar (aus JWTBearerAuthentication)
        payload = request.auth or {}
        hat_leser = hat_rolle(payload, "app-reader") or hat_rolle(payload, "app-writer")
        if not hat_leser:
            logger.warning(
                "API-Lesezugriff verweigert für Benutzer '%s'.",
                getattr(request.user, "username", "unbekannt"),
            )
        return hat_leser


class IstSchreiber(BasePermission):
    """
    API-Permission: Erlaubt Schreibzugriff nur für Benutzer mit app-writer Rolle.
    SICHERHEIT: Rollen werden aus dem verifizierten JWT-Payload geprüft (A01).
    """

    message = "Sie benötigen die app-writer Rolle."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        payload = request.auth or {}
        hat_schreiber = hat_rolle(payload, "app-writer")
        if not hat_schreiber:
            logger.warning(
                "API-Schreibzugriff verweigert für Benutzer '%s'.",
                getattr(request.user, "username", "unbekannt"),
            )
        return hat_schreiber


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _ist_leser_oder_schreiber(benutzer):
    """Prüft ob der Benutzer Leser- oder Schreiber-Gruppe hat."""
    return benutzer.groups.filter(
        name__in=[GRUPPE_LESER, GRUPPE_SCHREIBER]
    ).exists()


def _ist_schreiber(benutzer):
    """Prüft ob der Benutzer die Schreiber-Gruppe hat."""
    return benutzer.groups.filter(name=GRUPPE_SCHREIBER).exists()
