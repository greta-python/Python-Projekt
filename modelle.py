"""
Entity-Klassen des Dashboard-Prototypen.

Bildet das in der Konzeptions- und Reflexionsphase entworfene
Klassendiagramm 1:1 in Python ab: Studiengang, Semester, Modul und
Pruefungsleistung (mit den Unterklassen SchriftlichePruefung und
MuendlichePruefung), sowie die Enumeration ModulStatus.

Komposition und Aggregation werden ueber die fachliche
Zugehoerigkeit und den Lebenszyklus umgesetzt: Bei einer Komposition
erzeugt die "Ganzes"-Klasse ihre Teile ausschliesslich selbst
(Studiengang -> Semester, Modul -> Pruefungsleistung). Bei der
Aggregation Semester -> Modul werden dagegen bereits vorhandene
Modul-Objekte nur zugeordnet.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class ModulStatus(Enum):
    """Enumeration der moeglichen Modul-Zustaende (siehe Gesamtarchitektur)."""

    OFFEN = "offen"
    IN_BEARBEITUNG = "in_bearbeitung"
    BESTANDEN = "bestanden"


class Pruefungsleistung(ABC):
    """Abstrakte Oberklasse fuer eine einzelne Teilleistung eines Moduls.

    datum und note sind optional ([0..1]), da eine angemeldete, aber noch
    nicht abgelegte oder noch nicht bewertete Pruefungsleistung anfangs
    keinen Termin bzw. keine Note besitzt. bestanden ist bewusst kein
    gespeichertes Attribut, sondern wird als Property aus note abgeleitet
    (/bestanden), um keinen redundanten, potenziell widerspruechlichen
    Zustand zu fuehren.
    """

    #: Note, ab der eine Pruefungsleistung als bestanden gilt (deutsche Notenskala).
    BESTEHENSGRENZE = 4.0

    def __init__(
        self,
        gewichtung: float,
        datum: Optional[str] = None,
        note: Optional[float] = None,
    ) -> None:
        self.datum = datum
        self.note = note
        self.gewichtung = gewichtung

    @abstractmethod
    def beschreibung(self) -> str:
        """Liefert eine menschenlesbare Kurzbeschreibung (Polymorphie,
        siehe test_vererbung.py: jede Unterklasse implementiert dies anders)."""
        raise NotImplementedError

    @property
    def bestanden(self) -> Optional[bool]:
        """Abgeleitetes Attribut /bestanden: bool [0..1].

        None, solange keine Note vorliegt - der Zustand ist dann schlicht
        noch nicht bekannt, nicht "nicht bestanden".
        """
        if self.note is None:
            return None
        return self.note <= self.BESTEHENSGRENZE


class SchriftlichePruefung(Pruefungsleistung):
    """Schriftliche Pruefungsleistung, z. B. Klausur, Hausarbeit oder Essay.

    bezeichnung unterscheidet die konkrete Form (nur ein zusaetzliches
    Attribut, keine eigene Unterklasse je Form). bearbeitungszeit_minuten
    ist nur bei einer klassischen Klausur unter Zeitdruck sinnvoll und
    daher optional - bei einer Hausarbeit oder einem Essay mit freier
    Bearbeitungszeit bleibt es leer.
    """

    def __init__(
        self,
        bezeichnung: str,
        gewichtung: float,
        datum: Optional[str] = None,
        note: Optional[float] = None,
        bearbeitungszeit_minuten: Optional[int] = None,
    ) -> None:
        super().__init__(gewichtung, datum, note)
        self.bezeichnung = bezeichnung
        self.bearbeitungszeit_minuten = bearbeitungszeit_minuten

    def beschreibung(self) -> str:
        if self.bearbeitungszeit_minuten is not None:
            return f"{self.bezeichnung} ({self.bearbeitungszeit_minuten} Minuten)"
        return self.bezeichnung


class MuendlichePruefung(Pruefungsleistung):
    """Muendliche Pruefung mit Pruefungsdauer und pruefender Person."""

    def __init__(
        self,
        pruefungsdauer_minuten: int,
        pruefer: str,
        gewichtung: float,
        datum: Optional[str] = None,
        note: Optional[float] = None,
    ) -> None:
        super().__init__(gewichtung, datum, note)
        self.pruefungsdauer_minuten = pruefungsdauer_minuten
        self.pruefer = pruefer

    def beschreibung(self) -> str:
        return f"Muendliche Pruefung ({self.pruefungsdauer_minuten} Minuten)"


class Modul:
    """Ein Modul mit seinen Pruefungsleistungen (Komposition).

    /status und /note sind abgeleitete Properties.
    """

    def __init__(self, name: str, ects: int, empfohlenes_semester: int) -> None:
        self.name = name
        self.ects = ects
        self.empfohlenes_semester = empfohlenes_semester
        self._pruefungsleistungen: list[Pruefungsleistung] = []

    def pruefungsleistung_anmelden(
        self,
        art: str,
        gewichtung: float,
        datum: Optional[str] = None,
        note: Optional[float] = None,
        **weitere_attribute,
    ) -> Pruefungsleistung:
        """Meldet eine neue Pruefungsleistung fuer dieses Modul an.

        Einzige Moeglichkeit, dem Modul eine Pruefungsleistung
        hinzuzufuegen: Das Modul erzeugt das Objekt selbst (Komposition,
        siehe test_komposition.py). art bestimmt die konkrete Unterklasse;
        weitere_attribute nimmt die dafuer jeweils benoetigten
        Zusatzangaben entgegen (bezeichnung und optional
        bearbeitungszeit_minuten bzw. pruefungsdauer_minuten und pruefer).
        """
        if art == "schriftlich":
            neue_pruefung: Pruefungsleistung = SchriftlichePruefung(
                bezeichnung=weitere_attribute["bezeichnung"],
                bearbeitungszeit_minuten=weitere_attribute.get("bearbeitungszeit_minuten"),
                gewichtung=gewichtung,
                datum=datum,
                note=note,
            )
        elif art == "muendlich":
            neue_pruefung = MuendlichePruefung(
                pruefungsdauer_minuten=weitere_attribute["pruefungsdauer_minuten"],
                pruefer=weitere_attribute["pruefer"],
                gewichtung=gewichtung,
                datum=datum,
                note=note,
            )
        else:
            raise ValueError(f"Unbekannte Pruefungsart: {art!r}")

        self._pruefungsleistungen.append(neue_pruefung)
        return neue_pruefung

    def pruefungsleistungen(self) -> list[Pruefungsleistung]:
        """Nur lesender Zugriff auf die Pruefungsleistungen von aussen."""
        return list(self._pruefungsleistungen)

    @property
    def status(self) -> ModulStatus:
        """Abgeleitetes Attribut /status: ModulStatus."""
        if not self._pruefungsleistungen:
            return ModulStatus.OFFEN
        if all(p.bestanden for p in self._pruefungsleistungen):
            return ModulStatus.BESTANDEN
        return ModulStatus.IN_BEARBEITUNG

    @property
    def note(self) -> Optional[float]:
        """Abgeleitetes Attribut /note: float [0..1] - gewichteter
        Durchschnitt der bereits bewerteten Pruefungsleistungen."""
        bewertete = [p for p in self._pruefungsleistungen if p.note is not None]
        if not bewertete:
            return None
        gesamtgewicht = sum(p.gewichtung for p in bewertete)
        return sum(p.note * p.gewichtung for p in bewertete) / gesamtgewicht


class Semester:
    """Ein Semester mit den ihm zugeordneten Modulen (Aggregation)."""

    def __init__(self, nummer: int, startdatum: Optional[str] = None) -> None:
        self.nummer = nummer
        self.startdatum = startdatum
        self._module: list[Modul] = []

    def modul_zuordnen(self, modul: Modul) -> None:
        """Ordnet ein bereits existierendes Modul diesem Semester zu.
        """
        self._module.append(modul)

    def module(self) -> list[Modul]:
        return list(self._module)


class Studiengang:
    """Wurzel des Objektgraphen: ein Studiengang mit seinen Semestern
    (Komposition)."""

    def __init__(
        self,
        name: str,
        regelstudienzeit_semester: int,
        ziel_notendurchschnitt: float,
    ) -> None:
        if ziel_notendurchschnitt < 1.0:
            raise ValueError(
                "ziel_notendurchschnitt darf nicht kleiner als 1.0 sein "
                "(bestmoegliche Note im deutschen Notensystem)."
            )
        self.name = name
        self.regelstudienzeit_semester = regelstudienzeit_semester
        self.ziel_notendurchschnitt = ziel_notendurchschnitt
        self._semester: list[Semester] = []

    def semester_anlegen(self, nummer: int, startdatum: Optional[str] = None) -> Semester:
        """Legt ein neues Semester fuer diesen Studiengang an.

        Wie bei Modul.pruefungsleistung_anmelden() erzeugt die
        "Ganzes"-Klasse das Teil hier selbst (Komposition
        Studiengang -> Semester, Multiplizitaet 1..*).
        """
        neues_semester = Semester(nummer=nummer, startdatum=startdatum)
        self._semester.append(neues_semester)
        return neues_semester

    def semester(self) -> list[Semester]:
        return list(self._semester)

    def module(self) -> list[Modul]:
        """Bequemlichkeitsmethode: alle Module ueber alle Semester hinweg,
        z. B. fuer den Kennzahlenrechner."""
        return [modul for sem in self._semester for modul in sem.module()]
