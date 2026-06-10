"""Django-Admin-Konfiguration für die CRM-Entitäten."""

from django.contrib import admin
from .models import Kunde, Artikel, Auftrag, Auftragsposition


class AuftragspositionInline(admin.TabularInline):
    model = Auftragsposition
    extra = 1
    fields = ("artikel", "menge", "einzelpreis")
    readonly_fields = ("einzelpreis",)


@admin.register(Kunde)
class KundeAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "telefon", "erstellt_am")
    search_fields = ("name", "email")


@admin.register(Artikel)
class ArtikelAdmin(admin.ModelAdmin):
    list_display = ("artikelnummer", "bezeichnung", "preis", "bestand")
    search_fields = ("artikelnummer", "bezeichnung")


@admin.register(Auftrag)
class AuftragAdmin(admin.ModelAdmin):
    list_display = ("pk", "kunde", "auftragsdatum", "status", "gesamtbetrag")
    list_filter = ("status",)
    search_fields = ("kunde__name",)
    inlines = [AuftragspositionInline]


@admin.register(Auftragsposition)
class AuftragspositionAdmin(admin.ModelAdmin):
    list_display = ("auftrag", "artikel", "menge", "einzelpreis", "zwischensumme")
