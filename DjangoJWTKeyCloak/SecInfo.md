# Sicherheitsdokumentation – OWASP Top 10:2025 & JWT Best Practices

Dieses Dokument beschreibt die Sicherheitsmaßnahmen der Anwendung, gegliedert nach
**OWASP Top 10:2025** und ergänzt um einen ausführlichen Abschnitt zu **JWT-Best-Practices**.

---

## OWASP Top 10:2025 – Mapping

### A01:2025 – Broken Access Control (inkl. SSRF)

**Risiko:** Benutzer können auf Ressourcen oder Aktionen zugreifen, für die sie keine Berechtigung haben.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| Fail-closed als Standard | `DEFAULT_PERMISSION_CLASSES: [IsAuthenticated]` in `settings.py`; alle Views erfordern explizit eine Rolle |
| Server-seitige Rollenprüfung | Rollen aus JWT, nie aus Client-Parametern; `crm/permissions.py` |
| Trennung Lesen/Schreiben | `IstLeser` für GET-Methoden, `IstSchreiber` für POST/PUT/PATCH/DELETE |
| Keine direkte Objekt-Referenz ohne Auth | Alle ViewSets/Views hinter Auth-Middleware |
| JWT `aud`/`azp`-Prüfung | `jwt_bearer.py`: Audience `account` wird explizit geprüft |
| SSRF-Prävention | Keine Server-seitige URL-Anfragen aus Benutzereingaben; OIDC-Endpunkte sind fest in `settings.py` konfiguriert |

---

### A02:2025 – Security Misconfiguration

**Risiko:** Unsichere Standardeinstellungen, unnötige Features, fehlerhafte Konfiguration.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| `DEBUG=False` als Standard | `config/settings.py`: `config("DEBUG", default=False)` |
| Keine Secrets im Code | Alle Secrets aus `.env` via `python-decouple` |
| `ALLOWED_HOSTS` gesetzt | Explizite Whitelist, kein `*` |
| Security-Header gesetzt | `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS=DENY`, `SECURE_BROWSER_XSS_FILTER` |
| HSTS vorkonfiguriert | `SECURE_HSTS_SECONDS` (in Produktion: `31536000`) |
| Django-Admin auf separater URL | Nicht auf `/admin/` mit Default-Zugangsdaten |
| `.env` in `.gitignore` | Secrets verlassen nie das Dateisystem |

**Produktions-Checkliste:**
```bash
python manage.py check --deploy
# Setzt SECURE_SSL_REDIRECT=True, SESSION_COOKIE_SECURE=True,
# CSRF_COOKIE_SECURE=True, SECURE_HSTS_SECONDS=31536000 voraus.
```

---

### A03:2025 – Software Supply Chain Failures

**Risiko:** Kompromittierte Abhängigkeiten, nicht geprüfte Pakete, unsichere Build-Prozesse.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| Gepinnte Versionen | `requirements.txt` mit exakten Versionen (z. B. `Django==5.0.9`) |
| Gepinntes Container-Image | `quay.io/keycloak/keycloak:26.0.7` (kein `:latest`) |
| Vertrauenswürdige Quellen | Nur offizielle PyPI-Pakete und Keycloak-Quay-Image |

**Empfehlungen für Produktion:**
```bash
# Sicherheitslücken in Abhängigkeiten prüfen:
pip install pip-audit
pip-audit -r requirements.txt

# Hash-Pinning (pip-compile):
pip-compile --generate-hashes requirements.in
```

---

### A04:2025 – Cryptographic Failures

**Risiko:** Schwache Kryptographie, ungesicherte Datenübertragung, Schlüssel im Code.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| RS256 JWT-Signatur | Asymmetrisches Verfahren; Private Key bleibt bei Keycloak |
| JWKS-Endpunkt für Key-Rotation | Public Keys werden dynamisch vom JWKS-Endpoint geladen |
| `alg=none` abgelehnt | `ERLAUBTE_ALGORITHMEN = ["RS256"]` in `jwt_bearer.py` |
| HTTPS-Cookies | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` (in Produktion) |
| HTTPOnly-Cookies | `SESSION_COOKIE_HTTPONLY = True` – JS kann nicht auf Session zugreifen |
| SameSite-Cookies | `SESSION_COOKIE_SAMESITE = "Lax"` – CSRF-Schutz |
| Keine Secrets im Code | `SECRET_KEY` aus `.env` |

---

### A05:2025 – Injection

**Risiko:** SQL-Injection, XSS, Command-Injection durch unsanitisierte Eingaben.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| Kein Raw-SQL | Ausschließlich Django-ORM in `crm/models.py` |
| Template-Autoescaping | Django-Templates escapen HTML automatisch (XSS-Schutz) |
| Content Security Policy | `<meta http-equiv="Content-Security-Policy" ...>` in `base.html` |
| Formular-Validierung | Django-Forms und DRF-Serializer validieren alle Eingaben |
| CSRF-Schutz | `{% csrf_token %}` in jedem Formular; `CsrfViewMiddleware` aktiv |

#### CSRF-Token – Erläuterung

**CSRF** (Cross-Site Request Forgery) ist ein Angriff, bei dem eine fremde Website im Browser des eingeloggten Benutzers unbemerkt Aktionen in der eigenen Anwendung auslöst.

**Das Angriffsszenario ohne CSRF-Schutz:**

```
1. Benutzer loggt sich in crm-demo.de ein → Browser speichert Session-Cookie
2. Benutzer öffnet böse-seite.de in einem anderen Tab
3. Böse Seite enthält ein verstecktes Formular:
      <form action="http://crm-demo.de/kunden/42/loeschen/" method="POST">
   → Das Formular wird automatisch per JavaScript abgeschickt
4. Der Browser hängt das Session-Cookie automatisch an → Kunde wird gelöscht!
```

Der Browser schickt das Session-Cookie automatisch mit — er kann nicht unterscheiden, ob die Anfrage von der *eigenen* Seite oder einer *fremden* kommt.

**Wie das CSRF-Token schützt:**

Django erzeugt beim ersten Seitenaufruf einen zufälligen Geheimwert (das CSRF-Token) und speichert ihn in einem Cookie. Jedes HTML-Formular muss diesen Wert als verstecktes Feld mitsenden:

```html
<form method="post">
    {% csrf_token %}
    <!-- Wird gerendert als: -->
    <input type="hidden" name="csrfmiddlewaretoken" value="abc123xyz...">
```

Bei jedem POST prüft Django: **Stimmt der Wert im Formular mit dem Cookie überein?**

- **Eigene Seite:** Ja — JavaScript konnte das Token aus dem Cookie lesen und ins Formular schreiben.
- **Fremde Seite:** Nein — fremde Domains können das Cookie nicht lesen (Same-Origin-Policy des Browsers). Die Anfrage wird mit **HTTP 403 Forbidden** abgelehnt.

**Umsetzung in dieser Anwendung:**

| Wo | Was |
|----|-----|
| `config/settings.py` | `CsrfViewMiddleware` aktiv — prüft jeden POST automatisch |
| `config/settings.py` | `CSRF_COOKIE_HTTPONLY = True`, `CSRF_COOKIE_SAMESITE = "Lax"` |
| Alle Formular-Templates | `{% csrf_token %}` in jedem `<form method="post">` |
| REST-API | Kein CSRF-Token erforderlich — das `Authorization: Bearer`-Header-Schema schützt bereits, da fremde Seiten keine HTTP-Request-Header setzen können (CORS-Schutz des Browsers) |

---

### A06:2025 – Insecure Design

**Risiko:** Fehlende Sicherheitskontrollen durch schlechtes Design.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| Trennung Authn/Authz | Authentifizierung: Keycloak; Autorisierung: App-Rollen-Checks |
| Least-Privilege-Prinzip | Benutzer erhalten nur die minimal nötige Rolle |
| Whitelist statt Blacklist | Nur explizit bekannte Rollen werden in `ROLE_MAP` übernommen |
| Preishistorie gesichert | `einzelpreis` bei Auftragsposition wird beim Anlegen fixiert |

---

### A07:2025 – Authentication Failures

**Risiko:** Unsichere Authentifizierung, Session-Management, Credential-Diebstahl.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| Authentifizierung ausgelagert | Keycloak als vertrauenswürdiger IdP – keine Passwörter in der App |
| PKCE (Authorization Code) | `pkce.code.challenge.method: S256` im Realm-Export |
| Kurzlebige Access-Tokens | `accessTokenLifespan: 900` (15 min) im Realm |
| Session-Timeout | `ssoSessionIdleTimeout: 1800` (30 min) |
| Token-Ablauf geprüft | `OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = 900` in `settings.py` |
| Brute-Force-Schutz | `bruteForceProtected: true` in `realm-export.json` |
| Logout-Weiterleitung | `LOGOUT_REDIRECT_URL` und `post.logout.redirect.uris` konfiguriert |

---

### A08:2025 – Data Integrity & Confidentiality Failures

**Risiko:** Manipulierbare Daten, fehlende Integritätsprüfung, Datenlecks.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| JWT-Signaturprüfung | RS256 gegen JWKS – gefälschte Token werden abgelehnt |
| Kein Client-seitiges Vertrauen | Rollen kommen aus dem signierten JWT, nicht aus dem Request-Body |
| Explizite Serializer-Felder | Keine Wildcard-Felder in `serializers.py` – kein Mass-Assignment |
| Datenbankintegrität | Fremdschlüssel mit `PROTECT` (Auftrag/Artikel nicht löschbar wenn referenziert) |

---

### A09:2025 – Security Logging & Alerting Failures

**Risiko:** Angriffe werden nicht erkannt, keine Audit-Spur.

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| Auth-Ereignisse geloggt | Login, Rollen-Zuweisung, Logout in `auth_kc/oidc_backend.py` |
| Fehlgeschlagene Authentifizierungen | `jwt_bearer.py`: Warning-Log bei abgelaufenem/ungültigem Token |
| Zugriffsverweigert-Ereignisse | `permissions.py`: Warning-Log mit Benutzername und Pfad |
| **Keine** Tokens/Passwörter in Logs | Explizit kommentiert in `jwt_bearer.py` und `oidc_backend.py` |
| Log-Konfiguration in settings | `LOGGING`-Dict mit dedizierten Loggern für `auth_kc`, `crm`, `django.security` |

---

### A10:2025 – Mishandling of Exceptional Conditions

**Risiko:** Fehler-Handling öffnet Sicherheitslücken (fail-open, Stack-Trace-Leak).

**Umgesetzte Maßnahmen:**

| Maßnahme | Implementierung |
|----------|----------------|
| Fail-closed bei JWT-Fehler | Alle Exceptions in `jwt_bearer.py` → HTTP 401, nie HTTP 200 |
| Kein Stack-Trace an Client | `DEBUG=False`; unerwartete Fehler → generische 401/403/500-Antwort |
| Exception-Typen differenziert | `ExpiredSignatureError` separat behandelt, Rest als generischer `InvalidTokenError` |
| Unerwartete Exceptions abgefangen | `except Exception` als letzter Fallback → 401 (nicht 500) |
| Django-Fehlerseiten | Standardmäßig keine Debug-Seiten in Produktion |

---

## JWT-Best-Practices

### Was ist ein JWT?

Ein **JSON Web Token (JWT)** besteht aus drei Base64url-codierten Teilen:

```
Header.Payload.Signatur
```

- **Header**: `{"alg": "RS256", "typ": "JWT", "kid": "..."}` – Algorithmus und Key-ID
- **Payload**: Claims wie `sub`, `iss`, `aud`, `exp`, `realm_access.roles`
- **Signatur**: Kryptographischer Hash über Header+Payload mit dem Private Key

> **Wichtig:** Der Payload ist **nicht verschlüsselt** – nur signiert. Jeder kann ihn Base64-dekodieren und lesen. Niemals sensible Daten (Passwörter, Kreditkartennummern) im JWT-Payload speichern.

### 1. Signatur immer prüfen

```python
# auth_kc/jwt_bearer.py
jwks_client = PyJWKClient(settings.KEYCLOAK_JWKS_URL)
signing_key = jwks_client.get_signing_key_from_jwt(token)
payload = jwt.decode(token, signing_key.key, algorithms=["RS256"])
```

- **Asymmetrisches Verfahren (RS256)**: Keycloak signiert mit Private Key; die App prüft mit Public Key (JWKS). Der Private Key verlässt Keycloak nie.
- **Symmetrische Algorithmen (HS256) vermeiden** bei mehreren Diensten: Das Shared Secret müsste allen Diensten bekannt sein → größere Angriffsfläche.

### 2. `alg=none` explizit ablehnen

```python
# ERLAUBTE_ALGORITHMEN = ["RS256"] – niemals "none" oder "*"
ERLAUBTE_ALGORITHMEN = ["RS256"]
```

Tokens mit `"alg": "none"` haben keine Signatur. Historische JWT-Bibliotheken haben sie akzeptiert → kritische Schwachstelle. Durch explizite Whitelist wird diese Klasse von Angriffen ausgeschlossen.

### 3. Claims vollständig validieren

| Claim | Bedeutung | Prüfung |
|-------|-----------|---------|
| `exp` | Ablaufzeit | Token nach diesem Zeitpunkt ungültig |
| `nbf` | Not-Before | Token vor diesem Zeitpunkt ungültig |
| `iat` | Ausgestellt am | Plausibilitätsprüfung |
| `iss` | Aussteller | Muss exakt `http://localhost:8080/realms/demo` sein |
| `aud` | Zielgruppe | Muss `account` enthalten (Keycloak-Standard) |
| `sub` | Subjekt | Eindeutige Benutzer-ID (UUID bei Keycloak) |

```python
payload = jwt.decode(
    token,
    signing_key.key,
    algorithms=["RS256"],
    issuer=settings.KEYCLOAK_ISSUER_URL,  # iss prüfen
    audience="account",                    # aud prüfen
    options={
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iss": True,
        "verify_aud": True,
        "require": ["exp", "iss", "sub", "iat"],
    },
    leeway=10,  # 10 Sekunden Clock-Skew
)
```

### 4. Kurzlebige Access-Tokens

- Access-Tokens: **5–15 Minuten** (hier: 15 min via `accessTokenLifespan: 900`)
- Refresh-Tokens: **30 min bis Stunden** (session-gebunden)
- Kurzlebige Tokens begrenzen das Missbrauchsfenster bei Token-Diebstahl

### 5. Tokens sicher speichern (Client-Seite)

| Speicherort | XSS-anfällig | CSRF-anfällig | Empfehlung |
|-------------|-------------|---------------|------------|
| `localStorage` | **Ja** | Nein | Nicht verwenden für sensible Tokens |
| `sessionStorage` | **Ja** | Nein | Nur für kurzlebige, unkritische Tokens |
| `HttpOnly`-Cookie | **Nein** | Ja (mit SameSite mitigiert) | Empfohlen für Browser-Apps |
| Serverseitige Session | Nein | Mit CSRF-Token mitigiert | **Empfohlen** (wie in dieser App) |

In dieser App: Django-Session nach OIDC-Login → Token bleibt serverseitig, kein `localStorage`.

### 6. Key-Rotation via JWKS

```
GET http://localhost:8080/realms/demo/protocol/openid-connect/certs
→ {"keys": [{"kid": "abc123", "kty": "RSA", "n": "...", "e": "AQAB"}]}
```

- Keycloak kann Keys rotieren ohne App-Neustart
- `PyJWKClient` wählt anhand der `kid`-Header-Eigenschaft des Tokens den richtigen Key aus
- **Caching**: JWKS wird gecacht; bei unbekannter `kid` wird der JWKS-Endpoint neu abgefragt

### 7. Clock-Skew / Leeway

```python
leeway=10  # 10 Sekunden Toleranz für Zeitunterschiede
```

App-Server und Keycloak-Server können kleine Zeitabweichungen haben. Ohne Leeway werden Tokens sofort nach `exp` abgelehnt, auch wenn der App-Server 2 Sekunden nachgeht. Empfohlen: 10–30 Sekunden.

### 8. Transport nur über TLS

- Tokens dürfen **ausschließlich über HTTPS** übertragen werden
- In Produktion: `SECURE_SSL_REDIRECT=True` und Reverse-Proxy (Nginx/Caddy) mit TLS
- Lokal: HTTP akzeptabel für Entwicklung; `SECURE_*`-Settings deaktiviert via `.env`

### 9. Keine sensiblen Daten im Payload

```json
// Keycloak JWT-Payload (Beispiel)
{
  "sub": "a1b2c3d4-...",
  "preferred_username": "writer",
  "email": "writer@demo.local",
  "realm_access": {
    "roles": ["app-writer", "default-roles-demo"]
  },
  "exp": 1234567890,
  "iss": "http://localhost:8080/realms/demo"
}
```

Der Payload ist **base64-dekodierbar** – kein Passwort, kein Geheimnis hier ablegen.

### 10. Logout und Token-Invalidierung

- **Browser-Session**: OIDC-Logout-Endpunkt (`/oidc/logout/`) leitet zu Keycloak-Logout weiter → Session auf beiden Seiten beendet
- **API-Tokens**: JWTs sind zustandslos – ein ausgestelltes Token kann nicht "zurückgerufen" werden
- **Mitigierungsstrategien** für API-Token-Invalidierung:
  - **Kurzlebige Tokens** (15 min): Fenster für Missbrauch begrenzt
  - **Token-Blacklist** in Redis: Bei Logout wird Token-ID (`jti`) als ungültig markiert (nicht in dieser Demo)
  - **Introspection**: App fragt Keycloak bei jeder Anfrage ob Token noch gültig ist (netzwerkintensiv)

### 11. Keine Tokens in Logs

```python
# SCHLECHT:
logger.info("Token empfangen: %s", token)

# GUT (in dieser App so umgesetzt):
logger.warning(
    "JWT-Authentifizierung fehlgeschlagen: %s",
    type(fehler).__name__,  # Nur Fehlertyp, nicht Token-Inhalt
)
```

Tokens in Logs sind ein Sicherheitsrisiko: Log-Aggregatoren, Monitoring-Tools oder Log-Dateien sind oft weniger gesichert als die Anwendung selbst.

---

## Produktions-Härtungscheckliste

Vor dem Go-live folgende Punkte umsetzen:

- [ ] `SECRET_KEY` mit kryptographisch sicherem Zufallswert ersetzen (`python -c "import secrets; print(secrets.token_hex(50))"`)
- [ ] `OIDC_RP_CLIENT_SECRET` ändern (in Keycloak Client-Secret regenerieren)
- [ ] `DEBUG=False` setzen
- [ ] `SECURE_SSL_REDIRECT=True` setzen
- [ ] TLS-Zertifikat einrichten (Let's Encrypt / internes CA)
- [ ] `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True` setzen
- [ ] `SECURE_HSTS_SECONDS=31536000` setzen
- [ ] Keycloak: `start` statt `start-dev`, PostgreSQL statt H2
- [ ] Keycloak-Admin-Passwort ändern
- [ ] `bruteForceProtected: true` im Realm bestätigen
- [ ] `pip-audit -r requirements.txt` regelmäßig ausführen
- [ ] Log-Aggregation einrichten (ELK, Grafana Loki o. ä.) für A09
- [ ] `python manage.py check --deploy` ohne Fehler
