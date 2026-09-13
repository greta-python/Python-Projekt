"""
Controller: koordiniert Datenmanager und Dashboard.

Haelt je eine Referenz auf Datenmanager und Dashboard (Assoziation,
siehe Gesamtarchitektur), aber bewusst keine eigene, dauerhaft
gespeicherte Referenz auf ein Studiengang-Objekt.
"""

from __future__ import annotations

from dashboard import Dashboard
from datenmanager import Datenmanager
from modelle import Studiengang


class Controller:
    """Koordiniert den Ablauf zwischen Datenmanager und Dashboard."""

    def __init__(self, datenmanager: Datenmanager, dashboard: Dashboard) -> None:
        self.datenmanager = datenmanager
        self.dashboard = dashboard

    def programm_starten(self) -> None:
        """Laedt den Studiengang ueber Datenmanager und uebergibt ihn an
        Dashboard.anzeigen(). Blockiert, bis das Dashboard-Fenster
        geschlossen wird (tkinter-Ereignisschleife)."""
        studiengang = self.datenmanager.laden()
        self.dashboard.anzeigen(studiengang, on_neu_laden=self._neu_laden)

    def studiengang_speichern(self, studiengang: Studiengang) -> None:
        """Leitet eine Aenderung an Datenmanager.speichern() weiter.

        Der aktuelle Prototyp ist auf reine Anzeige ausgelegt (siehe
        Installationsanleitung/Abstract) und bietet daher noch keine
        Eingabemaske, die diese Methode auslöst - sie steht aber bereit,
        sobald eine solche Eingabemoeglichkeit ergaenzt wird.
        """
        self.datenmanager.speichern(studiengang)

    def _neu_laden(self) -> None:
        """Callback fuer den 'Neu laden'-Button im Dashboard: liest die
        JSON-Datei erneut ein und aktualisiert das bereits offene
        Fenster, ohne es neu zu erzeugen."""
        studiengang = self.datenmanager.laden()
        self.dashboard.aktualisieren(studiengang)
