"""
Keycloak-OIDC-Authentifizierungs-Backend für den Browser-Login.

SICHERHEIT (A07 Authentication Failures):
- Erbt von OIDCAuthenticationBackend, das die Signatur des ID-Tokens
  automatisch gegen die JWKS-Public-Keys von Keycloak prüft.
- Rollen werden aus dem Access-Token-Claim 'realm_access.roles' gelesen
  und als Django-Gruppen gespeichert – nur Rollen in ROLE_MAP werden
  übernommen (whitelist-Prinzip, A01).
- Keine Passwörter werden gespeichert – die Authentifizierung erfolgt
  ausschließlich über Keycloak (A07).
"""

import logging
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

logger = logging.getLogger(__name__)

# Whitelist: Keycloak-Realm-Rollen → Django-Gruppen-Namen (A01: fail-closed)
ROLE_MAP = {
    "app-reader": "Leser",
    "app-writer": "Schreiber",
}


class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    """
    Erweitertes OIDC-Backend mit Rollen-Mapping aus dem Keycloak-JWT.

    Beim Login werden die Realm-Rollen aus dem Access-Token gelesen und
    dem Django-Benutzer als Gruppen zugewiesen. Rollen die nicht in
    ROLE_MAP stehen, werden ignoriert (whitelist).
    """

    def create_user(self, claims):
        """Legt einen neuen Django-Benutzer beim ersten Login an."""
        benutzer = super().create_user(claims)
        self._rollen_zuweisen(benutzer, claims)
        return benutzer

    def update_user(self, benutzer, claims):
        """Aktualisiert den Benutzer und synchronisiert Rollen bei jedem Login."""
        benutzer = super().update_user(benutzer, claims)
        self._rollen_zuweisen(benutzer, claims)
        return benutzer

    def _rollen_zuweisen(self, benutzer, claims):
        """
        Liest Realm-Rollen aus dem JWT-Claim 'realm_access.roles' und
        weist dem Benutzer die entsprechenden Django-Gruppen zu.

        SICHERHEIT: Nur bekannte Rollen aus ROLE_MAP werden übernommen.
        Veraltete App-Rollen werden beim Login entzogen (A01).
        """
        from django.contrib.auth.models import Group

        realm_rollen = claims.get("realm_access", {}).get("roles", [])
        logger.info(
            "Benutzer '%s' meldet sich an. Realm-Rollen im Token: %s",
            benutzer.username,
            [r for r in realm_rollen if r in ROLE_MAP],
            # SICHERHEIT: Keine vollständige Token-Dump-Ausgabe im Log (A09)
        )

        # Alle App-Gruppen entfernen, dann neu zuweisen (saubere Synchronisation)
        app_gruppen = set(ROLE_MAP.values())
        benutzer.groups.remove(
            *benutzer.groups.filter(name__in=app_gruppen)
        )

        neue_gruppen = []
        for kc_rolle, django_gruppe in ROLE_MAP.items():
            if kc_rolle in realm_rollen:
                gruppe, _ = Group.objects.get_or_create(name=django_gruppe)
                neue_gruppen.append(gruppe)

        if neue_gruppen:
            benutzer.groups.add(*neue_gruppen)
            logger.info(
                "Benutzer '%s' erhält Gruppen: %s",
                benutzer.username,
                [g.name for g in neue_gruppen],
            )
        else:
            logger.warning(
                "Benutzer '%s' hat keine bekannten App-Rollen im Token.",
                benutzer.username,
            )

    def get_userinfo(self, access_token, id_token, payload):
        """
        Überschrieben, um Realm-Rollen aus dem Access-Token in die Claims
        zu übertragen, die an create_user/update_user weitergegeben werden.

        SICHERHEIT: Das Access-Token wird hier NICHT im Klartext geloggt (A09).
        """
        userinfo = super().get_userinfo(access_token, id_token, payload)
        # Realm-Rollen aus dem dekodieren Access-Token-Payload übernehmen
        # (UserInfo-Endpoint liefert sie evtl. nicht)
        if "realm_access" not in userinfo and "realm_access" in payload:
            userinfo["realm_access"] = payload["realm_access"]
        return userinfo
