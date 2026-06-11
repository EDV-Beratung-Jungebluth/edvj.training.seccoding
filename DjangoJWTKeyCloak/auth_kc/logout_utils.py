"""
Hilfsfunktion für den RP-Initiated Logout gegen Keycloak.

Wird über OIDC_OP_LOGOUT_URL_METHOD eingebunden. mozilla-django-oidc ruft
diese Funktion beim Logout auf und leitet den Browser anschließend zur
zurückgegebenen URL weiter. Keycloak beendet dort die SSO-Sitzung und
leitet zurück zur Anwendung.

SICHERHEIT (A07): Nur mit id_token_hint und bekannter redirect_uri;
das Token wird nie geloggt (A09).
"""
import logging
from urllib.parse import urlencode

from django.conf import settings

logger = logging.getLogger("auth_kc")


def keycloak_logout_url(request) -> str:
    """
    Baut die Keycloak-End-Session-URL für RP-Initiated Logout.

    Keycloak benötigt:
    - id_token_hint: das ID-Token der aktuellen Sitzung
    - post_logout_redirect_uri: absoluter Rücksprung-URL (muss in Keycloak registriert sein)
    - client_id: Fallback, falls id_token_hint fehlt (Keycloak zeigt dann Bestätigungsseite)
    """
    id_token = request.session.get("oidc_id_token")
    redirect_uri = request.build_absolute_uri("/")

    params = {
        "post_logout_redirect_uri": redirect_uri,
        "client_id": settings.OIDC_RP_CLIENT_ID,
    }
    if id_token:
        params["id_token_hint"] = id_token
        logger.info("Keycloak-Logout mit id_token_hint wird eingeleitet.")
    else:
        logger.warning(
            "Kein oidc_id_token in Session – Logout ohne id_token_hint. "
            "Keycloak könnte eine Bestätigungsseite anzeigen."
        )

    return "{endpoint}?{params}".format(
        endpoint=settings.OIDC_OP_LOGOUT_ENDPOINT,
        params=urlencode(params),
    )
