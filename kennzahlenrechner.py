"""
Kennzahlenrechner: berechnet abgeleitete Fortschrittskennzahlen fuer
einen Studiengang, ausserhalb der Entity-Klassen und ausserhalb von
Dashboard. Dashboard nutzt diese Klasse nur, um die fuer die Anzeige
benoetigten Werte zu ermitteln, uebernimmt die Berechnungslogik aber
nicht selbst.
"""

from __future__ import annotations

from typing import Optional

from modelle import ModulStatus, Studiengang


class Kennzahlenrechner:
    """Berechnet ECTS-Fortschritt, Studiengeschwindigkeit und
    gewichteten Notendurchschnitt eines Studiengangs."""

    def ects_fortschritt(self, studiengang: Studiengang) -> float:
        """Anteil der bereits bestandenen ECTS an allen im Studiengang
        bislang angelegten ECTS, als Wert zwischen 0.0 und 1.0.
        """
        module = studiengang.module()
        gesamt_ects = sum(modul.ects for modul in module)
        if gesamt_ects == 0:
            return 0.0
        bestandene_ects = sum(
            modul.ects for modul in module if modul.status == ModulStatus.BESTANDEN
        )
        return bestandene_ects / gesamt_ects

    def geschwindigkeit(self, studiengang: Studiengang) -> float:
        """Durchschnittlich erreichte ECTS pro bisherigem Semester.
        """
        semester_liste = studiengang.semester()
        if not semester_liste:
            return 0.0
        bestandene_ects = sum(
            modul.ects for modul in studiengang.module() if modul.status == ModulStatus.BESTANDEN
        )
        return bestandene_ects / len(semester_liste)

    def notendurchschnitt(self, studiengang: Studiengang) -> Optional[float]:
        """ECTS-gewichteter Durchschnitt ueber alle Module, fuer die
        bereits eine Note vorliegt. None, solange noch kein Modul
        bewertet ist.
        """
        bewertete_module = [
            modul for modul in studiengang.module() if modul.note is not None
        ]
        if not bewertete_module:
            return None
        gesamt_ects = sum(modul.ects for modul in bewertete_module)
        return sum(modul.note * modul.ects for modul in bewertete_module) / gesamt_ects
