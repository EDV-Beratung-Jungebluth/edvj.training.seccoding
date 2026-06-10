"""
Django-Einstellungen für das Django-Keycloak-JWT-Demo-Projekt.

Sicherheitshinweise (OWASP Top 10:2025):
- A02 Security Misconfiguration: DEBUG ist standardmäßig False, Secrets
  kommen aus der Umgebung, nie aus dem Code.
- A04 Cryptographic Failures: Sichere Cookie-Einstellungen und HTTPS-Header
  sind vorkonfiguriert.
- Alle sicherheitsrelevanten Einstellungen sind mit SICHERHEIT-Kommentaren
  markiert.
"""

from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# SICHERHEIT: SECRET_KEY niemals hartkodieren – aus .env lesen (A02/A04)
# ---------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY")

# SICHERHEIT: DEBUG in Produktion immer False (A02)
DEBUG = config("DEBUG", default=False, cast=bool)

# SICHERHEIT: Nur explizit erlaubte Hosts (A02)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ---------------------------------------------------------------------------
# Installierte Apps
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Keycloak-OIDC-Integration
    "mozilla_django_oidc",
    # Django REST Framework
    "rest_framework",
    # Fachanwendung
    "crm",
]

# ---------------------------------------------------------------------------
# Middleware – Reihenfolge ist sicherheitsrelevant
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # SICHERHEIT: CSRF-Schutz für alle Formular-Endpunkte (A05)
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # SICHERHEIT: Verhindert Clickjacking (A01)
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # OIDC-Ablaufprüfung (Token-Refresh)
    "mozilla_django_oidc.middleware.SessionRefresh",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Datenbank – SQLite für Demo
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# Passwort-Validierung
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Lokalisierung
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Statische Dateien
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Authentifizierungs-Backends
# SICHERHEIT: OIDC-Backend + Standard-Backend (für Django-Admin) (A07)
# ---------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "auth_kc.oidc_backend.KeycloakOIDCBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# ---------------------------------------------------------------------------
# Keycloak / OIDC-Konfiguration
# ---------------------------------------------------------------------------
_kc_base = config("KEYCLOAK_BASE_URL", default="http://localhost:8080")
_kc_realm = config("KEYCLOAK_REALM", default="demo")
_kc_base_url = f"{_kc_base}/realms/{_kc_realm}/protocol/openid-connect"

OIDC_RP_CLIENT_ID = config("OIDC_RP_CLIENT_ID", default="django-app")
OIDC_RP_CLIENT_SECRET = config("OIDC_RP_CLIENT_SECRET")

# SICHERHEIT: Nur RS256 erlauben – alg=none und symmetrische Algorithmen
# werden abgelehnt (JWT Best Practice, A04/A07)
OIDC_RP_SIGN_ALGO = "RS256"

# SICHERHEIT: PKCE (Proof Key for Code Exchange) aktivieren – verhindert
# Authorization-Code-Interception-Angriffe (A07). Keycloak verlangt S256.
OIDC_USE_PKCE = True

# JWKS-Endpoint – Public Keys von Keycloak für Signaturprüfung
OIDC_OP_JWKS_ENDPOINT = f"{_kc_base_url}/certs"
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{_kc_base_url}/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{_kc_base_url}/token"
OIDC_OP_USER_ENDPOINT = f"{_kc_base_url}/userinfo"
OIDC_OP_LOGOUT_ENDPOINT = f"{_kc_base_url}/logout"

# SICHERHEIT: Nach Logout zur Startseite umleiten
OIDC_REDIRECT_REQUIRE_HTTPS = False  # In Produktion auf True setzen
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/oidc/authenticate/"

# SICHERHEIT: Access-Token-Ablaufprüfung aktivieren (A07)
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = 900  # 15 Minuten

# Issuer-URL für JWT-Validierung in der REST-API
KEYCLOAK_ISSUER_URL = f"{_kc_base}/realms/{_kc_realm}"
KEYCLOAK_JWKS_URL = OIDC_OP_JWKS_ENDPOINT

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    # SICHERHEIT: Standard ist verweigern – explizit erlauben (A01, fail-closed)
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # JWT-Bearer-Authentifizierung für die API
        "auth_kc.jwt_bearer.JWTBearerAuthentication",
    ],
}

# ---------------------------------------------------------------------------
# SICHERHEIT: HTTP-Sicherheits-Header (A02)
# ---------------------------------------------------------------------------
# In Produktion (HTTPS) auf True setzen:
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)

# SICHERHEIT: HSTS – Browser erzwingen HTTPS für 1 Jahr (A04)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SICHERHEIT: Verhindert MIME-Typ-Sniffing (A02)
SECURE_CONTENT_TYPE_NOSNIFF = True

# SICHERHEIT: XSS-Filter in älteren Browsern (A05)
SECURE_BROWSER_XSS_FILTER = True

# SICHERHEIT: Clickjacking-Schutz (A01)
X_FRAME_OPTIONS = "DENY"

# SICHERHEIT: Session-Cookie nur über HTTPS (A04) – lokal False
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True   # JavaScript kann nicht auf Cookie zugreifen
SESSION_COOKIE_SAMESITE = "Lax"  # CSRF-Schutz

# SICHERHEIT: CSRF-Cookie absichern (A05)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# ---------------------------------------------------------------------------
# Logging – Sicherheitsereignisse protokollieren (A09)
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        # SICHERHEIT: Auth-Ereignisse protokollieren (A09)
        # Tokens und Passwörter werden NIEMALS geloggt.
        "auth_kc": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "mozilla_django_oidc": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "crm": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
