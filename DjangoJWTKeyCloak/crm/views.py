"""
Web-Views für die CRM-Anwendung.

SICHERHEIT:
- Alle Views erfordern Authentifizierung via Mixin (A01, A07).
- Schreibende Operationen erfordern Schreiber-Rolle (A01).
- Django-Templates escapen Ausgaben automatisch (A05 XSS-Schutz).
- CSRF-Token wird in allen Formularen eingebunden (A05).
"""

import logging
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Kunde, Artikel, Auftrag, Auftragsposition
from .forms import KundeForm, ArtikelForm, AuftragForm, AuftragspositionForm
from .permissions import LeserOderSchreiberMixin, SchreiberMixin

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Startseite
# ---------------------------------------------------------------------------

class StartseiteView(LeserOderSchreiberMixin, TemplateView):
    template_name = "crm/startseite.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kunden_anzahl"] = Kunde.objects.count()
        ctx["artikel_anzahl"] = Artikel.objects.count()
        ctx["auftraege_anzahl"] = Auftrag.objects.count()
        return ctx


# ---------------------------------------------------------------------------
# Kunden
# ---------------------------------------------------------------------------

class KundeListeView(LeserOderSchreiberMixin, ListView):
    model = Kunde
    template_name = "crm/kunde_liste.html"
    context_object_name = "kunden"


class KundeDetailView(LeserOderSchreiberMixin, DetailView):
    model = Kunde
    template_name = "crm/kunde_detail.html"
    context_object_name = "kunde"


class KundeErstellenView(SchreiberMixin, CreateView):
    model = Kunde
    form_class = KundeForm
    template_name = "crm/kunde_formular.html"
    success_url = reverse_lazy("kunde-liste")

    def form_valid(self, form):
        messages.success(self.request, f"Kunde '{form.instance.name}' wurde angelegt.")
        logger.info("Kunde angelegt von Benutzer '%s'.", self.request.user.username)
        return super().form_valid(form)


class KundeBearbeitenView(SchreiberMixin, UpdateView):
    model = Kunde
    form_class = KundeForm
    template_name = "crm/kunde_formular.html"
    success_url = reverse_lazy("kunde-liste")

    def form_valid(self, form):
        messages.success(self.request, f"Kunde '{form.instance.name}' wurde aktualisiert.")
        return super().form_valid(form)


class KundeLoeschenView(SchreiberMixin, DeleteView):
    model = Kunde
    template_name = "crm/bestaetigung_loeschen.html"
    success_url = reverse_lazy("kunde-liste")

    def form_valid(self, form):
        messages.success(self.request, "Kunde wurde gelöscht.")
        logger.info("Kunde #%s gelöscht von Benutzer '%s'.", self.object.pk, self.request.user.username)
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Artikel
# ---------------------------------------------------------------------------

class ArtikelListeView(LeserOderSchreiberMixin, ListView):
    model = Artikel
    template_name = "crm/artikel_liste.html"
    context_object_name = "artikel_liste"


class ArtikelDetailView(LeserOderSchreiberMixin, DetailView):
    model = Artikel
    template_name = "crm/artikel_detail.html"
    context_object_name = "artikel"


class ArtikelErstellenView(SchreiberMixin, CreateView):
    model = Artikel
    form_class = ArtikelForm
    template_name = "crm/artikel_formular.html"
    success_url = reverse_lazy("artikel-liste")

    def form_valid(self, form):
        messages.success(self.request, f"Artikel '{form.instance.bezeichnung}' wurde angelegt.")
        return super().form_valid(form)


class ArtikelBearbeitenView(SchreiberMixin, UpdateView):
    model = Artikel
    form_class = ArtikelForm
    template_name = "crm/artikel_formular.html"
    success_url = reverse_lazy("artikel-liste")

    def form_valid(self, form):
        messages.success(self.request, f"Artikel '{form.instance.bezeichnung}' wurde aktualisiert.")
        return super().form_valid(form)


class ArtikelLoeschenView(SchreiberMixin, DeleteView):
    model = Artikel
    template_name = "crm/bestaetigung_loeschen.html"
    success_url = reverse_lazy("artikel-liste")

    def form_valid(self, form):
        messages.success(self.request, "Artikel wurde gelöscht.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Aufträge
# ---------------------------------------------------------------------------

class AuftragListeView(LeserOderSchreiberMixin, ListView):
    model = Auftrag
    template_name = "crm/auftrag_liste.html"
    context_object_name = "auftraege"

    def get_queryset(self):
        return Auftrag.objects.select_related("kunde").prefetch_related("positionen")


class AuftragDetailView(LeserOderSchreiberMixin, DetailView):
    model = Auftrag
    template_name = "crm/auftrag_detail.html"
    context_object_name = "auftrag"

    def get_queryset(self):
        return Auftrag.objects.select_related("kunde").prefetch_related(
            "positionen__artikel"
        )


class AuftragErstellenView(SchreiberMixin, CreateView):
    model = Auftrag
    form_class = AuftragForm
    template_name = "crm/auftrag_formular.html"
    success_url = reverse_lazy("auftrag-liste")

    def form_valid(self, form):
        messages.success(self.request, "Auftrag wurde angelegt.")
        logger.info("Auftrag angelegt von Benutzer '%s'.", self.request.user.username)
        return super().form_valid(form)


class AuftragBearbeitenView(SchreiberMixin, UpdateView):
    model = Auftrag
    form_class = AuftragForm
    template_name = "crm/auftrag_formular.html"
    success_url = reverse_lazy("auftrag-liste")

    def form_valid(self, form):
        messages.success(self.request, "Auftrag wurde aktualisiert.")
        return super().form_valid(form)


class AuftragLoeschenView(SchreiberMixin, DeleteView):
    model = Auftrag
    template_name = "crm/bestaetigung_loeschen.html"
    success_url = reverse_lazy("auftrag-liste")

    def form_valid(self, form):
        messages.success(self.request, "Auftrag wurde gelöscht.")
        return super().form_valid(form)
