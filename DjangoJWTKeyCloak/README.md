# Django CRM-Demo mit Keycloak & JWT

Eine vollständige Demo-Webanwendung, die zeigt wie Django mit **Keycloak** als
Identity-Provider (OIDC) und **JWT** als Bearer-Token für eine REST-API zusammenarbeitet.

## Was die Anwendung macht

- Server-gerenderte **Webanwendung** (Browser-Login via Keycloak OIDC) für Kunden, Artikel und Aufträge
- **REST-API** (Django REST Framework) die Keycloak-JWTs als Bearer-Token validiert
- **Rollenbasierte Zugriffskontrolle**: `reader` darf nur lesen, `writer` darf lesen und schreiben
- SQLite-Datenbank mit Demodaten (5 Kunden, 7 Artikel, 5 Aufträge)
- Sicherheitsmaßnahmen nach OWASP Top 10:2025 (siehe [SecInfo.md](SecInfo.md))

## Demo-Benutzer

| Benutzername | Passwort    | Keycloak-Rolle | Rechte in der App          |
|-------------|-------------|----------------|----------------------------|
| `reader`    | `reader123` | `app-reader`   | Nur Lesen (Listen, Details) |
| `writer`    | `writer123` | `app-writer`   | Lesen und Schreiben        |

## Voraussetzungen

- **Python 3.10+** (getestet mit 3.12)
- **Docker Desktop** (für Keycloak)
- Docker Compose v2 (`docker compose`, nicht `docker-compose`)

## Schritt-für-Schritt-Anleitung

### 1. Repository klonen / Verzeichnis wechseln

```bash
cd DjangoJWTKeyCloak
```

### 2. `.env`-Datei anlegen

```bash
cp .env.example .env
```

Für die lokale Demo passen die voreingestellten Werte. In Produktion unbedingt
`SECRET_KEY` und `OIDC_RP_CLIENT_SECRET` mit sicheren Zufallswerten belegen.

### 3. Keycloak starten (Docker Desktop)

```bash
docker compose up -d
```

Keycloak startet auf **http://localhost:8080** und importiert beim ersten Start
automatisch den Realm `demo` mit Client, Rollen und den beiden Demo-Benutzern.

**Admin-Konsole**: http://localhost:8080/admin (Benutzer: `admin`, Passwort: `admin`)

Warten bis Keycloak bereit ist (ca. 30 Sekunden):

```bash
docker compose logs -f keycloak
# Bereit wenn: "Keycloak 26.x.x ... started"
```

### 4. Virtuelle Python-Umgebung anlegen und Pakete installieren

```bash
python -m venv .venv

# Windows:
.\.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 5. Datenbank migrieren und Demodaten laden

```bash
python manage.py migrate
python manage.py seed_demo
```

### 6. Django-Server starten

```bash
python manage.py runserver
```

Anwendung ist erreichbar unter: **http://localhost:8125**

### 7. Anmelden

Klick auf **Anmelden** → Weiterleitung zu Keycloak → Login mit `reader` oder `writer`.

---

## REST-API verwenden

Die API ist unter `/api/` erreichbar. Sie erfordert ein JWT Bearer-Token von Keycloak.

### Token holen (Password Grant – nur für Demo/Tests)

```bash
curl -s -X POST "http://localhost:8080/realms/demo/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=django-app" \
  -d "client_secret=django-demo-secret-aendern-in-produktion" \
  -d "username=writer" \
  -d "password=writer123" \
  -d "grant_type=password" \
  | python -m json.tool
```

Den `access_token` aus der Antwort in eine Variable speichern:

```bash
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/demo/protocol/openid-connect/token" \
  -d "client_id=django-app&client_secret=django-demo-secret-aendern-in-produktion&username=writer&password=writer123&grant_type=password" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### API-Aufrufe

**Kunden auflisten** (Leser und Schreiber):
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8125/api/kunden/
```

**Neuen Kunden anlegen** (nur Schreiber):
```bash
curl -X POST http://localhost:8125/api/kunden/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test GmbH","email":"test@beispiel.de","telefon":"","adresse":""}'
```

**Mit reader-Token schreiben → 403 Forbidden**:
```bash
READER_TOKEN=$(curl -s -X POST "http://localhost:8080/realms/demo/protocol/openid-connect/token" \
  -d "client_id=django-app&client_secret=django-demo-secret-aendern-in-produktion&username=reader&password=reader123&grant_type=password" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8125/api/kunden/ \
  -H "Authorization: Bearer $READER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Darf nicht","email":"nicht@erlaubt.de"}' \
  -v
# → HTTP 403 Forbidden
```

### Verfügbare API-Endpunkte

| Methode | URL | Berechtigung |
|---------|-----|--------------|
| GET | `/api/kunden/` | app-reader, app-writer |
| POST | `/api/kunden/` | app-writer |
| GET | `/api/kunden/{id}/` | app-reader, app-writer |
| PUT/PATCH | `/api/kunden/{id}/` | app-writer |
| DELETE | `/api/kunden/{id}/` | app-writer |
| GET | `/api/artikel/` | app-reader, app-writer |
| POST | `/api/artikel/` | app-writer |
| GET | `/api/auftraege/` | app-reader, app-writer |
| POST | `/api/auftraege/` | app-writer |
| GET | `/api/positionen/` | app-reader, app-writer |

---

## Keycloak manuell einrichten (Alternative zum automatischen Import)

Falls der automatische Import nicht funktioniert, kann der Realm manuell eingerichtet werden:

### 1. Admin-Konsole öffnen

http://localhost:8080/admin → Login mit `admin`/`admin`

### 2. Neuen Realm anlegen

- Linke Seitenleiste: Dropdown oben → **Create Realm**
- Realm Name: `demo`
- **Create** klicken

### 3. Rollen anlegen

- **Realm roles** → **Create role**
- Rolle `app-reader` anlegen (Beschreibung: "Lesezugriff")
- Nochmals: Rolle `app-writer` anlegen (Beschreibung: "Schreibzugriff")

### 4. Client anlegen

- **Clients** → **Create client**
- Client ID: `django-app`
- Client type: `OpenID Connect` → **Next**
- **Client authentication**: Ein → **Next**
- Valid redirect URIs: `http://localhost:8125/*`
- Web origins: `http://localhost:8125`
- **Save**

Client-Secret notieren: **Clients** → `django-app` → **Credentials** → Secret kopieren

### 5. Realm-Rollen im Access-Token veröffentlichen

- **Clients** → `django-app` → **Client scopes** → `django-app-dedicated` → **Add mapper by configuration**
- Typ: **User Realm Role** wählen
- Token Claim Name: `realm_access.roles` (wichtig: genau so)
- Add to access token: Ein → **Save**

### 6. Benutzer anlegen

- **Users** → **Add user**
- Username: `reader`, E-Mail: `reader@demo.local`
- **Create** → Tab **Credentials** → Passwort `reader123` setzen (Temporary: Aus)
- Tab **Role mapping** → **Assign role** → `app-reader` zuweisen
- Gleich für `writer` mit Passwort `writer123` und Rolle `app-writer`

### 7. `.env` aktualisieren

```
OIDC_RP_CLIENT_SECRET=<kopiiertes-client-secret>
```

---

## Sicherheitsprüfung (Deployment-Check)

```bash
python manage.py check --deploy
```

Für lokale Entwicklung werden Warnungen wegen HTTP angezeigt — das ist erwartet.
In Produktion alle Punkte aus `SecInfo.md` umsetzen.

---

## Troubleshooting

**Keycloak startet nicht / Realm nicht importiert**
- `docker compose logs keycloak` prüfen
- Port 8080 frei? `netstat -an | findstr 8080`
- Docker Desktop läuft?

**`OIDC callback returned an error`**
- Client-Secret in `.env` prüft → muss mit Keycloak-Client übereinstimmen
- Redirect-URI in Keycloak: `http://localhost:8125/*`

**JWT-Validierung schlägt fehl (API)**
- Token abgelaufen? Neuen Token holen (Lebensdauer: 15 min)
- `iss`-Claim: muss `http://localhost:8080/realms/demo` sein
- Audience: `account` muss im `aud`-Claim enthalten sein

**`PermissionDenied` im Browser**
- Benutzer hat keine `app-reader`- oder `app-writer`-Rolle
- Keycloak-Realm-Rollen prüfen und Benutzer zuweisen
- Neu anmelden (Session invalidieren: Abmelden → erneut anmelden)
