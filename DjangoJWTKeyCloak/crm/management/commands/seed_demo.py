"""
Management-Command: Demodaten anlegen.

Idempotent – kann beliebig oft ausgeführt werden ohne Duplikate zu erzeugen.
Legt Kunden, Artikel, Aufträge und Auftragspositionen an.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from crm.models import Kunde, Artikel, Auftrag, Auftragsposition


KUNDEN_DATEN = [
    {
        "name": "Müller & Söhne GmbH",
        "email": "info@mueller-soehne.de",
        "telefon": "+49 89 12345-0",
        "adresse": "Hauptstraße 10\n80331 München",
    },
    {
        "name": "Schmidt Handel AG",
        "email": "kontakt@schmidt-handel.de",
        "telefon": "+49 40 98765-0",
        "adresse": "Hamburger Allee 55\n20095 Hamburg",
    },
    {
        "name": "Technik Innovation GmbH",
        "email": "service@technik-innovation.de",
        "telefon": "+49 30 55500-0",
        "adresse": "Berliner Str. 200\n10115 Berlin",
    },
    {
        "name": "Bauer Elektrotechnik e.K.",
        "email": "bauer@elektrotechnik-bauer.de",
        "telefon": "+49 711 33300-0",
        "adresse": "Stuttgarter Ring 5\n70173 Stuttgart",
    },
    {
        "name": "Riedel Software Solutions",
        "email": "hello@riedel-software.de",
        "telefon": "+49 221 44400-0",
        "adresse": "Kölner Dom-Platz 1\n50667 Köln",
    },
]

ARTIKEL_DATEN = [
    {
        "artikelnummer": "ART-001",
        "bezeichnung": "Notebook Pro 15",
        "beschreibung": "Leistungsstarkes Business-Notebook, 15 Zoll, 16 GB RAM, 512 GB SSD",
        "preis": Decimal("1299.00"),
        "bestand": 25,
    },
    {
        "artikelnummer": "ART-002",
        "bezeichnung": "Bürostuhl Ergonomic Plus",
        "beschreibung": "Ergonomischer Bürostuhl mit Lendenwirbelstütze, höhenverstellbar",
        "preis": Decimal("349.00"),
        "bestand": 40,
    },
    {
        "artikelnummer": "ART-003",
        "bezeichnung": "USB-C Hub 7-Port",
        "beschreibung": "Hub mit HDMI, 3× USB-A, 2× USB-C, SD-Kartenleser, Ethernet",
        "preis": Decimal("59.99"),
        "bestand": 150,
    },
    {
        "artikelnummer": "ART-004",
        "bezeichnung": "Wireless Maus",
        "beschreibung": "Kabellose Maus, 2.4 GHz, ergonomisches Design",
        "preis": Decimal("39.99"),
        "bestand": 200,
    },
    {
        "artikelnummer": "ART-005",
        "bezeichnung": "Monitor 27 Zoll 4K",
        "beschreibung": "4K-Monitor, IPS-Panel, USB-C-Ladung, höhenverstellbar",
        "preis": Decimal("599.00"),
        "bestand": 30,
    },
    {
        "artikelnummer": "ART-006",
        "bezeichnung": "Netzwerk-Switch 24-Port",
        "beschreibung": "Managed Switch, 24× Gigabit-Ethernet, PoE+",
        "preis": Decimal("289.00"),
        "bestand": 15,
    },
    {
        "artikelnummer": "ART-007",
        "bezeichnung": "Tastatur Wireless DE",
        "beschreibung": "Kabellose Tastatur, deutsches Layout, Bluetooth 5.0",
        "preis": Decimal("69.99"),
        "bestand": 180,
    },
]


class Command(BaseCommand):
    help = "Legt Demo-Daten in der Datenbank an (idempotent)."

    def handle(self, *args, **options):
        self.stdout.write("Lege Demodaten an …")
        kunden = self._kunden_anlegen()
        artikel = self._artikel_anlegen()
        self._auftraege_anlegen(kunden, artikel)
        self.stdout.write(self.style.SUCCESS("Demodaten erfolgreich angelegt."))

    def _kunden_anlegen(self):
        kunden = []
        for daten in KUNDEN_DATEN:
            obj, erstellt = Kunde.objects.get_or_create(
                email=daten["email"], defaults=daten
            )
            kunden.append(obj)
            status = "angelegt" if erstellt else "bereits vorhanden"
            self.stdout.write(f"  Kunde '{obj.name}': {status}")
        return kunden

    def _artikel_anlegen(self):
        artikel = []
        for daten in ARTIKEL_DATEN:
            obj, erstellt = Artikel.objects.get_or_create(
                artikelnummer=daten["artikelnummer"], defaults=daten
            )
            artikel.append(obj)
            status = "angelegt" if erstellt else "bereits vorhanden"
            self.stdout.write(f"  Artikel '{obj.bezeichnung}': {status}")
        return artikel

    def _auftraege_anlegen(self, kunden, artikel):
        auftraege_config = [
            {
                "kunde": kunden[0],
                "status": Auftrag.Status.ABGESCHLOSSEN,
                "positionen": [
                    (artikel[0], 2),   # 2× Notebook Pro
                    (artikel[4], 2),   # 2× Monitor
                    (artikel[2], 3),   # 3× USB-C Hub
                ],
            },
            {
                "kunde": kunden[1],
                "status": Auftrag.Status.BEARBEITUNG,
                "positionen": [
                    (artikel[1], 10),  # 10× Bürostuhl
                    (artikel[6], 10),  # 10× Tastatur
                    (artikel[3], 10),  # 10× Maus
                ],
            },
            {
                "kunde": kunden[2],
                "status": Auftrag.Status.OFFEN,
                "positionen": [
                    (artikel[5], 2),   # 2× Switch
                    (artikel[0], 5),   # 5× Notebook
                ],
            },
            {
                "kunde": kunden[3],
                "status": Auftrag.Status.STORNIERT,
                "positionen": [
                    (artikel[4], 1),   # 1× Monitor
                ],
            },
            {
                "kunde": kunden[4],
                "status": Auftrag.Status.OFFEN,
                "positionen": [
                    (artikel[0], 3),   # 3× Notebook
                    (artikel[2], 5),   # 5× Hub
                    (artikel[6], 3),   # 3× Tastatur
                    (artikel[3], 3),   # 3× Maus
                ],
            },
        ]

        for cfg in auftraege_config:
            # Prüfe ob Auftrag für diesen Kunden mit diesem Status schon existiert
            auftrag, erstellt = Auftrag.objects.get_or_create(
                kunde=cfg["kunde"],
                status=cfg["status"],
                defaults={"notizen": "Automatisch generierter Demo-Auftrag"},
            )
            if erstellt:
                for art, menge in cfg["positionen"]:
                    Auftragsposition.objects.create(
                        auftrag=auftrag,
                        artikel=art,
                        menge=menge,
                        einzelpreis=art.preis,
                    )
                self.stdout.write(
                    f"  Auftrag #{auftrag.pk} für '{auftrag.kunde.name}' angelegt "
                    f"(Gesamt: {auftrag.gesamtbetrag:.2f} €)"
                )
            else:
                self.stdout.write(f"  Auftrag für '{auftrag.kunde.name}' bereits vorhanden")
