"""
DRF-Serialisierer für die CRM-REST-API.

SICHERHEIT (A01/A05):
- Explizite Feldlisten (whitelist) – keine ModelSerializer-Wildcard-Felder.
- Eingaben werden durch DRF-Validierung geprüft.
"""

from rest_framework import serializers
from .models import Kunde, Artikel, Auftrag, Auftragsposition


class KundeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kunde
        fields = ["id", "name", "email", "telefon", "adresse", "erstellt_am"]
        read_only_fields = ["id", "erstellt_am"]


class ArtikelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artikel
        fields = ["id", "artikelnummer", "bezeichnung", "beschreibung", "preis", "bestand"]
        read_only_fields = ["id"]


class AuftragspositionSerializer(serializers.ModelSerializer):
    zwischensumme = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    artikel_bezeichnung = serializers.CharField(
        source="artikel.bezeichnung", read_only=True
    )

    class Meta:
        model = Auftragsposition
        fields = [
            "id",
            "artikel",
            "artikel_bezeichnung",
            "menge",
            "einzelpreis",
            "zwischensumme",
        ]
        read_only_fields = ["id", "einzelpreis", "zwischensumme", "artikel_bezeichnung"]


class AuftragSerializer(serializers.ModelSerializer):
    positionen = AuftragspositionSerializer(many=True, read_only=True)
    gesamtbetrag = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    kunde_name = serializers.CharField(source="kunde.name", read_only=True)
    status_anzeige = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Auftrag
        fields = [
            "id",
            "kunde",
            "kunde_name",
            "auftragsdatum",
            "status",
            "status_anzeige",
            "notizen",
            "positionen",
            "gesamtbetrag",
        ]
        read_only_fields = ["id", "auftragsdatum", "kunde_name", "status_anzeige", "gesamtbetrag"]
