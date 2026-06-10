"""
JWT-Bearer-Authentifizierung für die REST-API.

SICHERHEIT – JWT Best Practices (A04/A07):

1. Signaturprüfung:  RS256-Signatur wird gegen die JWKS-Public-Keys von
   Keycloak geprüft. Asymmetrisches Verfahren – der Private Key verlässt
   Keycloak nie. 'alg=none' wird abgelehnt.

2. Claims-Validierung: 'exp', 'nbf', 'iat', 'iss', 'aud' werden geprüft.
   Ein ungültiger Claim führt zu HTTP 401 – kein Fallback, kein fail-open.

3. Clock-Skew: Kleiner 'leeway' (10 s) für Zeitunterschiede zwischen
   App-Server und Keycloak.

4. Kurzlebige Tokens: Keycloak stellt Access-Tokens mit kurzer Laufzeit
   aus (konfigurierbar im Realm, empfohlen: 5–15 min). Refresh-Tokens
   verbleiben beim Client – die API akzeptiert nur Access-Tokens.

5. Transport: Tokens werden ausschließlich über TLS übertragen.
   In Produktion SECURE_SSL_REDIRECT=True setzen.

6. Key-Rotation: JWKS-Endpoint wird automatisch nach Ablauf des
   Caches neu abgefragt (PyJWKClient-Cache-Mechanismus).

7. Kein Logging von Token-Inhalten: Im Fehlerfall werden nur
   anonymisierte Fehlermeldungen protokolliert (A09).
"""

import logging
import jwt
from jwt import PyJWKClient, ExpiredSignatureError, InvalidTokenError
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)
User = get_user_model()

# SICHERHEIT: Nur RS256 ist erlaubt. Symmetrische Algorithmen (HS256)
# und 'alg=none' werden hier explizit ausgeschlossen (A04).
ERLAUBTE_ALGORITHMEN = ["RS256"]

# Kleiner Puffer für Zeitunterschiede zwischen Servern
LEEWAY_SEKUNDEN = 10


class JWTBearerAuthentication(BaseAuthentication):
    """
    DRF-Authentifizierungsklasse für Keycloak JWT Bearer Tokens.

    Erwartet den Header: Authorization: Bearer <JWT>

    Prüft:
    - RS256-Signatur gegen JWKS von Keycloak
    - iss (Issuer) entspricht dem konfigurierten Keycloak-Realm
    - aud (Audience) enthält 'account' (Keycloak-Standard) oder Client-ID
    - exp, nbf, iat (Zeitclaims) mit Leeway
    - Rollen aus realm_access.roles
    """

    def authenticate(self, request):
        """Extrahiert und validiert das Bearer-Token aus dem Authorization-Header."""
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            # Kein Bearer-Token → andere Authentifizierungsklasse versuchen
            return None

        token = auth_header.split(" ", 1)[1]

        if not token:
            raise AuthenticationFailed("Leeres Bearer-Token.")

        return self._token_validieren(token)

    def _token_validieren(self, token):
        """
        Vollständige JWT-Validierung gegen Keycloak JWKS.

        SICHERHEIT: Alle relevanten Claims werden geprüft.
        Bei jedem Fehler wird HTTP 401 zurückgegeben – nie HTTP 200
        mit eingeschränkten Rechten (A01: fail-closed).
        """
        try:
            # Public Key vom JWKS-Endpoint holen (mit Caching)
            jwks_client = PyJWKClient(settings.KEYCLOAK_JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # SICHERHEIT: Token dekodieren und alle Claims prüfen (A07)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=ERLAUBTE_ALGORITHMEN,
                # iss muss exakt dem Keycloak-Realm-Issuer entsprechen
                issuer=settings.KEYCLOAK_ISSUER_URL,
                # aud muss 'account' enthalten (Keycloak-Standard)
                audience="account",
                options={
                    "verify_exp": True,      # Ablaufzeit prüfen
                    "verify_nbf": True,      # Not-Before prüfen
                    "verify_iat": True,      # Ausstellungszeit prüfen
                    "verify_iss": True,      # Aussteller prüfen
                    "verify_aud": True,      # Zielgruppe prüfen
                    "require": ["exp", "iss", "sub", "iat"],
                },
                leeway=LEEWAY_SEKUNDEN,
            )

        except ExpiredSignatureError:
            # SICHERHEIT: Kein Detail über Token-Inhalt nach außen (A09)
            logger.warning("JWT-Authentifizierung fehlgeschlagen: Token abgelaufen.")
            raise AuthenticationFailed("Token ist abgelaufen.")

        except InvalidTokenError as fehler:
            logger.warning(
                "JWT-Authentifizierung fehlgeschlagen: Ungültiges Token. Ursache: %s",
                type(fehler).__name__,  # Nur Fehlertyp, nicht Token-Inhalt (A09)
            )
            raise AuthenticationFailed("Ungültiges Token.")

        except Exception as fehler:
            # SICHERHEIT: Unerwartete Fehler führen zu 401, nicht zu 500 (A10)
            logger.error(
                "Unerwarteter Fehler bei JWT-Validierung: %s",
                type(fehler).__name__,
            )
            raise AuthenticationFailed("Token konnte nicht geprüft werden.")

        # Django-Benutzer aus Token-Subject (sub) ermitteln oder anlegen
        benutzer = self._benutzer_aus_payload(payload)
        return (benutzer, payload)

    def _benutzer_aus_payload(self, payload):
        """
        Erstellt oder aktualisiert den Django-Benutzer aus den JWT-Claims.

        SICHERHEIT: Nur Felder aus dem verifizierten Payload werden
        übernommen – niemals aus dem Request-Body (A01).
        """
        sub = payload.get("sub")
        if not sub:
            raise AuthenticationFailed("Token enthält kein 'sub'-Claim.")

        email = payload.get("email", "")
        preferred_username = payload.get("preferred_username", sub)

        benutzer, erstellt = User.objects.get_or_create(
            username=sub,
            defaults={
                "email": email,
                "first_name": payload.get("given_name", ""),
                "last_name": payload.get("family_name", ""),
            },
        )

        if erstellt:
            logger.info("Neuer API-Benutzer angelegt: %s", preferred_username)

        # Rollen synchronisieren
        self._rollen_aus_payload_setzen(benutzer, payload)
        return benutzer

    def _rollen_aus_payload_setzen(self, benutzer, payload):
        """
        Liest Rollen aus realm_access.roles und setzt Django-Gruppen.

        SICHERHEIT: Whitelist-Prinzip – nur bekannte Rollen werden
        übernommen (A01). Wird bei jedem API-Request synchronisiert.
        """
        from django.contrib.auth.models import Group
        from auth_kc.oidc_backend import ROLE_MAP

        realm_rollen = payload.get("realm_access", {}).get("roles", [])
        app_gruppen = set(ROLE_MAP.values())
        benutzer.groups.remove(*benutzer.groups.filter(name__in=app_gruppen))

        neue_gruppen = []
        for kc_rolle, django_gruppe in ROLE_MAP.items():
            if kc_rolle in realm_rollen:
                gruppe, _ = Group.objects.get_or_create(name=django_gruppe)
                neue_gruppen.append(gruppe)

        if neue_gruppen:
            benutzer.groups.add(*neue_gruppen)


def hat_rolle(payload, rolle):
    """
    Hilfsfunktion: Prüft ob ein JWT-Payload eine bestimmte Realm-Rolle enthält.
    Wird in API-Permissions verwendet.
    """
    return rolle in payload.get("realm_access", {}).get("roles", [])
