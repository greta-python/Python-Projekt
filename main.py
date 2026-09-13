"""
Application: definiert den Programmeinstieg und legt die benoetigten
Objekte an (siehe Gesamtarchitektur, Klasse Application).

Ausfuehren mit:
    python main.py
(siehe Installationsanleitung fuer Details zur Einrichtung.)
"""

from __future__ import annotations

from pathlib import Path

from controller import Controller
from dashboard import Dashboard
from datenmanager import Datenmanager
from kennzahlenrechner import Kennzahlenrechner

#: Demo-Datendatei liegt neben diesem Skript, damit das Programm
#: unabhaengig vom aktuellen Arbeitsverzeichnis gestartet werden kann.
STANDARD_DATENPFAD = Path(__file__).resolve().parent / "studiengang_demo.json"


class Application:
    """Programmeinstieg: erzeugt Datenmanager, Kennzahlenrechner,
    Dashboard und Controller und startet den Ablauf."""

    def starten(self) -> None:
        datenmanager = Datenmanager(str(STANDARD_DATENPFAD))
        kennzahlenrechner = Kennzahlenrechner()
        dashboard = Dashboard(kennzahlenrechner)
        controller = Controller(datenmanager, dashboard)
        controller.programm_starten()


if __name__ == "__main__":
    Application().starten()
