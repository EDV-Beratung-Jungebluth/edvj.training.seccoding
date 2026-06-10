"""
Datenmodell für die CRM-Demo-Anwendung.

Entitäten: Kunde, Artikel, Auftrag, Auftragsposition.

SICHERHEIT (A05 Injection):
- Ausschließlich Django-ORM – kein Raw-SQL.
- Dezimalfelder für Geldbeträge (keine Floats wegen Rundungsfehlern).
"""

from django.db import models


class Kunde(models.Model):
    """Repräsentiert einen Kunden im System."""

    name = models.CharField("Name", max_length=200)
    email = models.EmailField("E-Mail", unique=True)
    telefon = models.CharField("Telefon", max_length=50, blank=True)
    adresse = models.TextField("Adresse", blank=True)
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)

    class Meta:
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Artikel(models.Model):
    """Repräsentiert einen Artikel im Produktkatalog."""

    artikelnummer = models.CharField("Artikelnummer", max_length=50, unique=True)
    bezeichnung = models.CharField("Bezeichnung", max_length=200)
    beschreibung = models.TextField("Beschreibung", blank=True)
    # SICHERHEIT: Decimal statt Float für Geldbeträge
    preis = models.DecimalField("Preis (€)", max_digits=10, decimal_places=2)
    bestand = models.PositiveIntegerField("Bestand", default=0)

    class Meta:
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"
        ordering = ["artikelnummer"]

    def __str__(self):
        return f"{self.artikelnummer} – {self.bezeichnung}"


class Auftrag(models.Model):
    """Repräsentiert einen Kundenauftrag."""

    class Status(models.TextChoices):
        OFFEN = "offen", "Offen"
        BEARBEITUNG = "bearbeitung", "In Bearbeitung"
        ABGESCHLOSSEN = "abgeschlossen", "Abgeschlossen"
        STORNIERT = "storniert", "Storniert"

    kunde = models.ForeignKey(
        Kunde,
        on_delete=models.PROTECT,
        related_name="auftraege",
        verbose_name="Kunde",
    )
    auftragsdatum = models.DateField("Auftragsdatum", auto_now_add=True)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.OFFEN,
    )
    notizen = models.TextField("Notizen", blank=True)

    class Meta:
        verbose_name = "Auftrag"
        verbose_name_plural = "Aufträge"
        ordering = ["-auftragsdatum"]

    def __str__(self):
        return f"Auftrag #{self.pk} – {self.kunde.name} ({self.get_status_display()})"

    @property
    def gesamtbetrag(self):
        """Berechnet die Gesamtsumme aller Positionen."""
        return sum(p.zwischensumme for p in self.positionen.all())


class Auftragsposition(models.Model):
    """Eine einzelne Position in einem Auftrag."""

    auftrag = models.ForeignKey(
        Auftrag,
        on_delete=models.CASCADE,
        related_name="positionen",
        verbose_name="Auftrag",
    )
    artikel = models.ForeignKey(
        Artikel,
        on_delete=models.PROTECT,
        related_name="positionen",
        verbose_name="Artikel",
    )
    menge = models.PositiveIntegerField("Menge", default=1)
    # Preis wird beim Anlegen aus dem Artikel übernommen (Preishistorie)
    einzelpreis = models.DecimalField(
        "Einzelpreis (€)", max_digits=10, decimal_places=2
    )

    class Meta:
        verbose_name = "Auftragsposition"
        verbose_name_plural = "Auftragspositionen"

    def __str__(self):
        return f"{self.menge}× {self.artikel.bezeichnung}"

    @property
    def zwischensumme(self):
        """Berechnet den Gesamtbetrag dieser Position."""
        return self.menge * self.einzelpreis

    def save(self, *args, **kwargs):
        """Übernimmt den aktuellen Artikelpreis beim erstmaligen Anlegen."""
        if not self.pk and not self.einzelpreis:
            self.einzelpreis = self.artikel.preis
        super().save(*args, **kwargs)
