"""
Django-Formulare für die CRM-Webanwendung.

SICHERHEIT (A05 Injection):
- Alle Formulare nutzen Django-Validierung und -Escaping.
- Keine Rohdaten direkt in die Datenbank.
"""

from django import forms
from .models import Kunde, Artikel, Auftrag, Auftragsposition


class KundeForm(forms.ModelForm):
    class Meta:
        model = Kunde
        fields = ["name", "email", "telefon", "adresse"]
        labels = {
            "name": "Name",
            "email": "E-Mail-Adresse",
            "telefon": "Telefon",
            "adresse": "Adresse",
        }
        widgets = {
            "adresse": forms.Textarea(attrs={"rows": 3}),
        }


class ArtikelForm(forms.ModelForm):
    class Meta:
        model = Artikel
        fields = ["artikelnummer", "bezeichnung", "beschreibung", "preis", "bestand"]
        labels = {
            "artikelnummer": "Artikelnummer",
            "bezeichnung": "Bezeichnung",
            "beschreibung": "Beschreibung",
            "preis": "Preis (€)",
            "bestand": "Bestand",
        }
        widgets = {
            "beschreibung": forms.Textarea(attrs={"rows": 3}),
        }


class AuftragForm(forms.ModelForm):
    class Meta:
        model = Auftrag
        fields = ["kunde", "status", "notizen"]
        labels = {
            "kunde": "Kunde",
            "status": "Status",
            "notizen": "Notizen",
        }
        widgets = {
            "notizen": forms.Textarea(attrs={"rows": 3}),
        }


class AuftragspositionForm(forms.ModelForm):
    class Meta:
        model = Auftragsposition
        fields = ["artikel", "menge"]
        labels = {
            "artikel": "Artikel",
            "menge": "Menge",
        }
