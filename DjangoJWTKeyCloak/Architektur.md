# Architektur – Django CRM-Demo mit Keycloak & JWT

## Überblick

Die Anwendung besteht aus drei Schichten:

1. **Keycloak** – externer Identity-Provider (läuft in Docker)
2. **Django-Backend** – Webanwendung + REST-API
3. **Browser / API-Client** – Endbenutzer oder Tools (curl, Postman)

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser / curl                        │
└──────┬──────────────────────────────────┬───────────────────┘
       │ OIDC (Authorization Code + PKCE) │ REST (Bearer JWT)
       ▼                                  ▼
┌──────────────────┐            ┌──────────────────────────────┐
│  Keycloak :8080  │            │       Django :8125           │
│  Realm: demo     │            │                              │
│  Client: django- │◄──JWKS────►│  auth_kc/jwt_bearer.py       │
│  app             │            │  (RS256-Signaturprüfung)     │
│                  │            │                              │
│  Benutzer:       │            │  config/settings.py          │
│  reader / writer │            │  config/urls.py              │
└──────────────────┘            │                              │
                                │  crm/ (Modelle, Views, API)  │
                                │                              │
                                │  db.sqlite3                  │
                                └──────────────────────────────┘
```

---

## Verzeichnisstruktur

```
DjangoJWTKeyCloak/
├── manage.py                    # Django-CLI-Einstiegspunkt
├── requirements.txt             # Gepinnte Abhängigkeiten
├── .env                         # Lokale Secrets (nicht eingecheckt)
├── .env.example                 # Vorlage für .env
├── .gitignore
├── docker-compose.yml           # Keycloak-Container
├── keycloak/
│   └── realm-export.json        # Realm-Konfiguration (auto-import)
│
├── config/                      # Django-Projektkonfiguration
│   ├── settings.py              # Alle Einstellungen, .env-getrieben
│   ├── urls.py                  # Root-URL-Routing
│   ├── wsgi.py
│   └── asgi.py
│
├── auth_kc/                     # Keycloak/JWT-Integrationsschicht
│   ├── oidc_backend.py          # OIDC-Backend: Rollen aus JWT → Django-Gruppen
│   └── jwt_bearer.py            # DRF-Auth: Bearer-JWT gegen JWKS validieren
│
├── crm/                         # Fachanwendung
│   ├── models.py                # Kunde, Artikel, Auftrag, Auftragsposition
│   ├── admin.py                 # Django-Admin-Konfiguration
│   ├── forms.py                 # Formularklassen
│   ├── views.py                 # Template-basierte Web-Views
│   ├── urls.py                  # Web-URL-Muster
│   ├── permissions.py           # Rollen-Checks für Web + API
│   ├── serializers.py           # DRF-Serialisierer
│   ├── api.py                   # DRF-ViewSets
│   ├── api_urls.py              # API-URL-Muster (Router)
│   ├── migrations/              # Datenbankmigrationen
│   ├── management/commands/
│   │   └── seed_demo.py         # Demodaten-Command (idempotent)
│   └── templates/crm/           # HTML-Templates
│       ├── startseite.html
│       ├── kunde_liste.html / kunde_detail.html / kunde_formular.html
│       ├── artikel_liste.html / artikel_detail.html / artikel_formular.html
│       ├── auftrag_liste.html / auftrag_detail.html / auftrag_formular.html
│       └── bestaetigung_loeschen.html
│
└── templates/
    └── base.html                # Gemeinsames Layout aller Seiten
```

---

## Datenmodell

```
Kunde (1) ──────── (N) Auftrag (1) ──────── (N) Auftragsposition (N) ──── (1) Artikel
  name                  kunde (FK)                auftrag (FK)                artikelnummer
  email                 auftragsdatum             artikel (FK)                bezeichnung
  telefon               status                    menge                       preis
  adresse               notizen                   einzelpreis                 bestand
  erstellt_am         → gesamtbetrag (property) → zwischensumme (property)
```

**Wichtige Designentscheidungen:**
- `einzelpreis` in `Auftragsposition`: Wird beim Anlegen aus `Artikel.preis` kopiert → Preishistorie bleibt erhalten, auch wenn der Artikelpreis später geändert wird.
- `gesamtbetrag` und `zwischensumme` sind berechnete Properties, kein gespeichertes Feld → immer konsistent.
- `Decimal` für alle Geldbeträge (keine Floats).

---

## OIDC-Login-Sequenz (Browser)

```
Browser           Django (:8125)           Keycloak (:8080)
   │                    │                        │
   │  GET /             │                        │
   │──────────────────► │                        │
   │                    │ (nicht eingeloggt)     │
   │  302 → /oidc/auth  │                        │
   │◄───────────────────│                        │
   │                    │                        │
   │  GET /oidc/auth/?redirect=...               │
   │─────────────────────────────────────────── ►│
   │  302 → Keycloak Login-Seite                 │
   │◄────────────────────────────────────────────│
   │                    │                        │
   │  [Benutzer gibt Anmeldedaten ein]           │
   │  POST Login-Formular                        │
   │─────────────────────────────────────────── ►│
   │  302 → /oidc/callback/?code=AUTH_CODE       │
   │◄────────────────────────────────────────────│
   │                    │                        │
   │  GET /oidc/callback/?code=...               │
   │──────────────────► │                        │
   │                    │  POST /token (code)    │
   │                    │───────────────────────►│
   │                    │  {id_token, access_token, refresh_token}
   │                    │◄───────────────────────│
   │                    │                        │
   │                    │  Signatur prüfen (JWKS)│
   │                    │  Rollen → Django-Gruppen
   │                    │  Session anlegen       │
   │  302 → /           │                        │
   │◄───────────────────│                        │
   │  GET /             │                        │
   │──────────────────► │                        │
   │  200 Startseite    │                        │
   │◄───────────────────│                        │
```

---

## Bearer-JWT-Sequenz (REST-API)

```
API-Client              Django API (:8000)      Keycloak (:8080)
    │                          │                       │
    │  [Token holen]           │                       │
    │  POST /realms/demo/protocol/openid-connect/token │
    │─────────────────────────────────────────────────►│
    │  {access_token: "eyJ..."}                        │
    │◄─────────────────────────────────────────────────│
    │                          │                       │
    │  GET /api/kunden/        │                       │
    │  Authorization: Bearer eyJ...                    │
    │─────────────────────────►│                       │
    │                          │  GET /certs (JWKS)    │
    │                          │  (gecacht)            │
    │                          │──────────────────────►│
    │                          │  {keys: [...]}        │
    │                          │◄──────────────────────│
    │                          │                       │
    │                          │ RS256 Signatur prüfen │
    │                          │ exp / iss / aud prüfen│
    │                          │ Rollen aus JWT lesen  │
    │                          │ IstLeser-Permission   │
    │  200 [{id:1, name:...}]  │                       │
    │◄─────────────────────────│                       │
```

---

## Rollen-Architektur

```
Keycloak Realm-Rollen          Django-Gruppen         Anwendungsrechte
─────────────────────          ──────────────         ─────────────────
app-reader          ────────►  Leser          ────────► GET-Views, API GET
app-writer          ────────►  Schreiber      ────────► alle Views, alle API-Methoden
```

**Synchronisation:**
- Browser-Login: `auth_kc/oidc_backend.py` → `_rollen_zuweisen()` bei jedem Login
- API-Anfrage: `auth_kc/jwt_bearer.py` → `_rollen_aus_payload_setzen()` bei jeder Anfrage

**Fail-closed:** Kein Benutzer mit unbekannter oder fehlender Rolle erhält Zugriff.

---

## Komponenten und ihre Verantwortlichkeiten

| Datei | Verantwortlichkeit |
|-------|-------------------|
| `config/settings.py` | Zentrales Sicherheits-Konfiguration, .env-getrieben |
| `auth_kc/oidc_backend.py` | OIDC-Login-Callback, Rollen-Mapping, Benutzer anlegen |
| `auth_kc/jwt_bearer.py` | Bearer-JWT validieren (JWKS, Claims), DRF-Auth-Klasse |
| `crm/permissions.py` | Zugriffsregeln für Web (Mixin) und API (BasePermission) |
| `crm/models.py` | Datenmodell (ORM, kein Raw-SQL) |
| `crm/views.py` | Template-Views, nutzt Mixins aus permissions.py |
| `crm/api.py` | DRF-ViewSets, nutzt IstLeser/IstSchreiber |
| `crm/serializers.py` | Serialisierung mit expliziten Feldlisten |
| `keycloak/realm-export.json` | Reproduzierbare Keycloak-Konfiguration |

---

## Erweiterungspunkte

- **HTTPS in Produktion**: `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `SECURE_HSTS_SECONDS=31536000` in `.env` setzen; Nginx/Caddy als Reverse-Proxy vorschalten.
- **PostgreSQL**: `DATABASES`-Einstellung in `settings.py` auf PostgreSQL umstellen; Keycloak-Compose auf `start` + Postgres-Service erweitern.
- **Weitere Rollen**: In `ROLE_MAP` (oidc_backend.py) und `crm/permissions.py` ergänzen.
- **Token-Introspection**: Statt JWKS-Validierung kann auch Keycloak-Introspection-Endpoint genutzt werden (netzwerkintensiver, aber bei Key-Rotation sofort aktuell).
- **Refresh-Token-Handling**: `mozilla-django-oidc` übernimmt Session-Refresh im Browser automatisch (SessionRefresh-Middleware).
