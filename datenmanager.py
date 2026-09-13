"""
Datenmanager: kapselt das Lesen und Schreiben der JSON-Datei
"""

from __future__ import annotations

import json
from pathlib import Path

from modelle import Studiengang


class Datenmanager:
    """Laedt und speichert einen Studiengang als JSON-Datei."""

    def __init__(self, dateipfad: str) -> None:
        self.dateipfad = dateipfad

    def laden(self) -> Studiengang:
        """Liest die JSON-Datei ein und baut den vollstaendigen
        Objektgraphen (Studiengang -> Semester -> Modul ->
        Pruefungsleistung) wieder auf."""
        with open(self.dateipfad, "r", encoding="utf-8") as datei:
            daten = json.load(datei)

        studiengang = Studiengang(
            name=daten["name"],
            regelstudienzeit_semester=daten["regelstudienzeitSemester"],
            ziel_notendurchschnitt=daten["zielNotendurchschnitt"],
        )

        for semester_daten in daten.get("semester", []):
            semester = studiengang.semester_anlegen(
                nummer=semester_daten["nummer"],
                startdatum=semester_daten.get("startdatum"),
            )
            for modul_daten in semester_daten.get("module", []):
                modul = self._modul_aus_daten(modul_daten)
                semester.modul_zuordnen(modul)

        return studiengang

    def _modul_aus_daten(self, modul_daten: dict) -> "Modul":
        from modelle import Modul  # lokaler Import: vermeidet Zirkelbezug in Typannotationen

        modul = Modul(
            name=modul_daten["name"],
            ects=modul_daten["ects"],
            empfohlenes_semester=modul_daten["empfohlenesSemester"],
        )
        for pruefung_daten in modul_daten.get("pruefungsleistungen", []):
            art = pruefung_daten["art"]
            weitere_attribute = {}
            if art == "schriftlich":
                weitere_attribute["bezeichnung"] = pruefung_daten["bezeichnung"]
                if "bearbeitungszeitMinuten" in pruefung_daten:
                    weitere_attribute["bearbeitungszeit_minuten"] = pruefung_daten["bearbeitungszeitMinuten"]
            elif art == "muendlich":
                weitere_attribute["pruefungsdauer_minuten"] = pruefung_daten["pruefungsdauerMinuten"]
                weitere_attribute["pruefer"] = pruefung_daten["pruefer"]

            modul.pruefungsleistung_anmelden(
                art=art,
                gewichtung=pruefung_daten["gewichtung"],
                datum=pruefung_daten.get("datum"),
                note=pruefung_daten.get("note"),
                **weitere_attribute,
            )
        return modul

    def speichern(self, studiengang: Studiengang) -> None:
        """Schreibt den uebergebenen Studiengang als JSON-Datei."""
        daten = {
            "name": studiengang.name,
            "regelstudienzeitSemester": studiengang.regelstudienzeit_semester,
            "zielNotendurchschnitt": studiengang.ziel_notendurchschnitt,
            "semester": [
                {
                    "nummer": semester.nummer,
                    "startdatum": semester.startdatum,
                    "module": [self._modul_zu_daten(modul) for modul in semester.module()],
                }
                for semester in studiengang.semester()
            ],
        }
        Path(self.dateipfad).parent.mkdir(parents=True, exist_ok=True)
        with open(self.dateipfad, "w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=2)

    def _modul_zu_daten(self, modul) -> dict:
        from modelle import SchriftlichePruefung, MuendlichePruefung

        pruefungen_daten = []
        for pruefung in modul.pruefungsleistungen():
            eintrag = {
                "datum": pruefung.datum,
                "note": pruefung.note,
                "gewichtung": pruefung.gewichtung,
            }
            if isinstance(pruefung, SchriftlichePruefung):
                eintrag["art"] = "schriftlich"
                eintrag["bezeichnung"] = pruefung.bezeichnung
                if pruefung.bearbeitungszeit_minuten is not None:
                    eintrag["bearbeitungszeitMinuten"] = pruefung.bearbeitungszeit_minuten
            elif isinstance(pruefung, MuendlichePruefung):
                eintrag["art"] = "muendlich"
                eintrag["pruefungsdauerMinuten"] = pruefung.pruefungsdauer_minuten
                eintrag["pruefer"] = pruefung.pruefer
            pruefungen_daten.append(eintrag)

        return {
            "name": modul.name,
            "ects": modul.ects,
            "empfohlenesSemester": modul.empfohlenes_semester,
            "pruefungsleistungen": pruefungen_daten,
        }
