"""URL-Muster für die CRM-Webanwendung."""

from django.urls import path
from . import views

urlpatterns = [
    # Startseite
    path("", views.StartseiteView.as_view(), name="startseite"),

    # Kunden
    path("kunden/", views.KundeListeView.as_view(), name="kunde-liste"),
    path("kunden/neu/", views.KundeErstellenView.as_view(), name="kunde-erstellen"),
    path("kunden/<int:pk>/", views.KundeDetailView.as_view(), name="kunde-detail"),
    path("kunden/<int:pk>/bearbeiten/", views.KundeBearbeitenView.as_view(), name="kunde-bearbeiten"),
    path("kunden/<int:pk>/loeschen/", views.KundeLoeschenView.as_view(), name="kunde-loeschen"),

    # Artikel
    path("artikel/", views.ArtikelListeView.as_view(), name="artikel-liste"),
    path("artikel/neu/", views.ArtikelErstellenView.as_view(), name="artikel-erstellen"),
    path("artikel/<int:pk>/", views.ArtikelDetailView.as_view(), name="artikel-detail"),
    path("artikel/<int:pk>/bearbeiten/", views.ArtikelBearbeitenView.as_view(), name="artikel-bearbeiten"),
    path("artikel/<int:pk>/loeschen/", views.ArtikelLoeschenView.as_view(), name="artikel-loeschen"),

    # Aufträge
    path("auftraege/", views.AuftragListeView.as_view(), name="auftrag-liste"),
    path("auftraege/neu/", views.AuftragErstellenView.as_view(), name="auftrag-erstellen"),
    path("auftraege/<int:pk>/", views.AuftragDetailView.as_view(), name="auftrag-detail"),
    path("auftraege/<int:pk>/bearbeiten/", views.AuftragBearbeitenView.as_view(), name="auftrag-bearbeiten"),
    path("auftraege/<int:pk>/loeschen/", views.AuftragLoeschenView.as_view(), name="auftrag-loeschen"),
]
