"""GUI-Klasse Dashboard: baut die Tkinter-Oberflaeche des Studiendashboards auf
(Kopfbereich, drei Kennzahlen-Kacheln, scrollbare Modulübersicht)."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

from kennzahlenrechner import Kennzahlenrechner
from modelle import ModulStatus, MuendlichePruefung, Studiengang

FONT_FAMILY = "Segoe UI"
SEITEN_HINTERGRUND = "#f8fafc"
KARTEN_RADIUS = 14

# Farben und Beschriftung je Modul-Status, fuer die Status-Badges in der Modulübersicht.
STATUS_FARBEN = {
    ModulStatus.BESTANDEN: {"bg": "#dcfce7", "fg": "#15803d", "text": "BESTANDEN"},
    ModulStatus.IN_BEARBEITUNG: {"bg": "#fef3c7", "fg": "#b45309", "text": "IN BEARBEITUNG"},
    ModulStatus.OFFEN: {"bg": "#f1f5f9", "fg": "#475569", "text": "OFFEN"},
}


def _create_progress_ring(canvas, x, y, radius, thickness, percent, color) -> None:
    """Zeichnet einen Fortschrittsring (grauer Hintergrundkreis + farbiger Bogen) mit Prozentzahl."""
    canvas.create_oval(
        x - radius, y - radius, x + radius, y + radius,
        outline="#e2e8f0", width=thickness,
    )
    start_angle = 90
    extent = -360 * (percent / 100)
    canvas.create_arc(
        x - radius, y - radius, x + radius, y + radius,
        start=start_angle, extent=extent,
        outline=color, width=thickness, style="arc",
    )
    canvas.create_text(x, y, text=f"{percent}%", font=(FONT_FAMILY, 17, "bold"))


def _create_badge(parent, text, bg_color, fg_color):
    """Erzeugt ein kleines, farbiges Status-Label (z. B. "BESTANDEN")."""
    return tk.Label(
        parent, text=text, bg=bg_color, fg=fg_color,
        font=(FONT_FAMILY, 9, "bold"), padx=8, pady=2,
    )


def _create_divider(parent, color, card_width):
    """Erzeugt eine duenne, farbige Trennlinie innerhalb einer Kachel."""
    line = tk.Frame(parent, bg=color, height=1, width=card_width)
    line.pack(fill="x", pady=10)
    return line


def _rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Zeichnet ein Rechteck mit abgerundeten Ecken als Polygon (fuer die Kachel-Karten)."""
    punkte = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(punkte, smooth=True, **kwargs)


class Dashboard:
    """Baut das Dashboard-Fenster auf und aktualisiert es bei Bedarf neu."""

    def __init__(self, kennzahlenrechner: Kennzahlenrechner) -> None:
        self._kennzahlenrechner = kennzahlenrechner
        self._root: Optional[tk.Tk] = None
        self._kacheln_bereich: Optional[tk.Frame] = None
        self._inhalt: Optional[tk.Frame] = None
        self._canvas: Optional[tk.Canvas] = None
        self._scrollbar: Optional[tk.Scrollbar] = None
        self._studiengang: Optional[Studiengang] = None
        self._aufgeklappte_module: set = set()

    def anzeigen(self, studiengang: Studiengang, on_neu_laden: Optional[Callable[[], None]] = None) -> None:
        """Baut das Fenster erstmalig auf und startet die Tkinter-Ereignisschleife."""
        self._root = tk.Tk()
        self._root.title(f"Dashboard - {studiengang.name}")
        self._root.configure(bg=SEITEN_HINTERGRUND)

        kopf = tk.Frame(self._root, bg=SEITEN_HINTERGRUND)
        kopf.pack(fill="x", padx=16, pady=(16, 0))

        titel = tk.Frame(kopf, bg=SEITEN_HINTERGRUND)
        titel.pack(side="left", anchor="w")
        tk.Label(
            titel, text="Schön, dass du da bist!", bg=SEITEN_HINTERGRUND,
            font=(FONT_FAMILY, 19, "bold"),
        ).pack(anchor="w")
        tk.Label(
            titel, text=studiengang.name, bg=SEITEN_HINTERGRUND, fg="#64748b",
            font=(FONT_FAMILY, 11),
        ).pack(anchor="w")

        if on_neu_laden is not None:
            tk.Button(
                kopf, text="Neu laden", command=on_neu_laden,
                font=(FONT_FAMILY, 9),
            ).pack(side="right", anchor="n", pady=(4, 0))

        self._kacheln_bereich = tk.Frame(self._root, bg=SEITEN_HINTERGRUND)
        self._kacheln_bereich.pack(fill="x", padx=16, pady=(16, 8))

        # Scrollbarer Bereich fuer die Modulübersicht: Canvas + Scrollbar + innerer Frame.
        scroll_bereich = tk.Frame(self._root, bg=SEITEN_HINTERGRUND)
        scroll_bereich.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        canvas = tk.Canvas(scroll_bereich, bg=SEITEN_HINTERGRUND, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_bereich, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        self._canvas = canvas
        self._scrollbar = scrollbar

        self._inhalt = tk.Frame(canvas, bg=SEITEN_HINTERGRUND)
        self._inhalt.pack_propagate(True)
        inhalt_fenster = canvas.create_window((0, 0), window=self._inhalt, anchor="n")

        def _inhalt_groesse_geaendert(_event=None) -> None:
            # Scrollbereich an die tatsaechliche Inhaltsgroesse anpassen.
            canvas.configure(scrollregion=canvas.bbox("all"))
            self._scrollzustand_aktualisieren()

        def _canvas_breite_geaendert(event) -> None:
            # Inhaltsbreite an die Canvas-Breite koppeln (aber nicht schmaler als die Kacheln).
            kacheln_breite = (
                self._kacheln_bereich.winfo_reqwidth() if self._kacheln_bereich is not None else event.width
            )
            ziel_breite = min(kacheln_breite, event.width)
            canvas.itemconfig(inhalt_fenster, width=ziel_breite)
            canvas.coords(inhalt_fenster, event.width / 2, 0)

        self._inhalt.bind("<Configure>", _inhalt_groesse_geaendert)
        canvas.bind("<Configure>", _canvas_breite_geaendert)

        def _mit_mausrad_scrollen(event) -> None:
            # Plattformuebergreifendes Mausrad-Scrollen (Windows/Mac: delta, Linux: Button-4/5).
            if getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
                canvas.yview_scroll(1, "units")
            elif getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
                canvas.yview_scroll(-1, "units")

        canvas.bind_all("<MouseWheel>", _mit_mausrad_scrollen)
        canvas.bind_all("<Button-4>", _mit_mausrad_scrollen)
        canvas.bind_all("<Button-5>", _mit_mausrad_scrollen)

        self._inhalt_befuellen(studiengang)

        # Fenstergroesse anhand des benoetigten Platzes berechnen, aber auf die Bildschirmhoehe begrenzen.
        self._root.update_idletasks()
        kacheln_breite = self._kacheln_bereich.winfo_reqwidth()
        inhalt_breite = self._inhalt.winfo_reqwidth() + scrollbar.winfo_reqwidth() + 4
        fenster_breite = max(kacheln_breite, inhalt_breite) + 32

        gewuenschte_hoehe = (
            kopf.winfo_reqheight()
            + self._kacheln_bereich.winfo_reqheight()
            + self._inhalt.winfo_reqheight()
            + 64
        )
        bildschirm_hoehe = self._root.winfo_screenheight()
        fenster_hoehe = min(gewuenschte_hoehe, bildschirm_hoehe - 80)
        self._root.geometry(f"{fenster_breite}x{fenster_hoehe}")
        self._root.minsize(fenster_breite, 300)

        self._root.update_idletasks()
        self._scrollzustand_aktualisieren()

        self._root.mainloop()

    def aktualisieren(self, studiengang: Studiengang) -> None:
        """Baut Kacheln und Modulübersicht neu auf (z. B. nach Aufklappen eines Moduls)."""
        if self._root is None or self._inhalt is None or self._kacheln_bereich is None:
            raise RuntimeError("aktualisieren() setzt ein zuvor mit anzeigen() geoeffnetes Fenster voraus.")
        self._root.title(f"Dashboard - {studiengang.name}")

        # Scrollposition merken, damit sie nach dem Neuaufbau erhalten bleibt.
        scroll_position = self._canvas.yview()[0] if self._canvas is not None else 0.0

        for kind in self._kacheln_bereich.winfo_children():
            kind.destroy()
        for kind in self._inhalt.winfo_children():
            kind.destroy()
        self._inhalt_befuellen(studiengang)

        if self._canvas is not None:
            self._canvas.update_idletasks()
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            self._canvas.yview_moveto(scroll_position)
            self._scrollzustand_aktualisieren()


    def _scrollzustand_aktualisieren(self) -> None:
        """Blendet die Scrollbar nur ein, wenn der Inhalt tatsaechlich hoeher als der sichtbare Bereich ist."""
        if self._canvas is None or self._scrollbar is None or self._inhalt is None:
            return
        self._canvas.update_idletasks()
        sichtbare_hoehe = self._canvas.winfo_height()
        benoetigte_hoehe = self._inhalt.winfo_reqheight()

        if benoetigte_hoehe > sichtbare_hoehe:
            if not self._scrollbar.winfo_ismapped():
                self._scrollbar.pack(side="right", fill="y")
        else:
            if self._scrollbar.winfo_ismapped():
                self._scrollbar.pack_forget()
            self._canvas.yview_moveto(0)

    def _build_rounded_card(self, parent, card_width, card_height, bg, rahmen, inhalt_aufbauen):
        """Erzeugt eine Kachel mit abgerundeten Ecken und fuellt sie ueber die uebergebene Funktion."""
        canvas = tk.Canvas(parent, width=card_width, height=card_height,
                            bg=SEITEN_HINTERGRUND, highlightthickness=0)
        _rounded_rect(canvas, 1, 1, card_width - 1, card_height - 1,
                      radius=KARTEN_RADIUS, fill=bg, outline=rahmen, width=1)

        inner = tk.Frame(canvas, bg=bg, width=card_width - 4, height=card_height - 4,
                          padx=16, pady=16)
        inner.pack_propagate(False)
        rueckgabe = inhalt_aufbauen(inner)
        canvas.create_window(card_width / 2, card_height / 2, window=inner)
        return canvas, rueckgabe

    def _inhalt_befuellen(self, studiengang: Studiengang) -> None:
        """Baut sowohl die Kennzahlen-Kacheln als auch die Modulübersicht auf."""
        self._studiengang = studiengang
        self._kacheln_befuellen(studiengang)
        self._build_moduluebersicht(self._inhalt, studiengang)

    def _kacheln_befuellen(self, studiengang: Studiengang) -> None:
        """Baut die drei Kennzahlen-Kacheln (Fortschritt, Semester, Note) nebeneinander auf."""
        kr = self._kennzahlenrechner
        module = studiengang.module()
        bestandene_module = [m for m in module if m.status == ModulStatus.BESTANDEN]

        ects_fortschritt = kr.ects_fortschritt(studiengang)
        geschwindigkeit = kr.geschwindigkeit(studiengang)
        notendurchschnitt = kr.notendurchschnitt(studiengang)

        zeile = tk.Frame(self._kacheln_bereich, bg=SEITEN_HINTERGRUND)
        zeile.pack()

        card_width = 260

        # Jede Kachel wird zunaechst "unsichtbar" probehalber gefuellt, nur um ihre benoetigte
        # Hoehe zu ermitteln. So koennen alle drei Kacheln anschliessend auf dieselbe Hoehe gebracht werden.
        probe1 = tk.Frame(zeile, bg="white", width=card_width, padx=16, pady=16)
        self._fill_progress_card(probe1, ects_fortschritt, module, bestandene_module)
        probe1.pack_propagate(True)
        probe1.update_idletasks()
        progress_height = probe1.winfo_reqheight()
        probe1.destroy()

        probe2 = tk.Frame(zeile, bg="white", width=card_width, padx=16, pady=16)
        h2_vor_trennstrich = self._fill_semester_card(probe2, studiengang, geschwindigkeit)
        probe2.pack_propagate(True)
        probe2.update_idletasks()
        semester_height = probe2.winfo_reqheight()
        probe2.destroy()

        probe3 = tk.Frame(zeile, bg="white", width=card_width, padx=16, pady=16)
        h3_vor_trennstrich = self._fill_grade_card(probe3, studiengang, notendurchschnitt)
        probe3.pack_propagate(True)
        probe3.update_idletasks()
        grade_height = probe3.winfo_reqheight()
        probe3.destroy()

        # Ausgleichsabstand, damit die Trennstriche in Kachel 2 und 3 auf gleicher Hoehe liegen.
        ausgleich2 = max(0, h3_vor_trennstrich - h2_vor_trennstrich)
        ausgleich3 = max(0, h2_vor_trennstrich - h3_vor_trennstrich)

        target_height = max(
            progress_height, semester_height + ausgleich2, grade_height + ausgleich3
        ) + 8

        card1, _ = self._build_rounded_card(
            zeile, card_width, target_height, "white", "#e2e8f0",
            lambda inner: self._fill_progress_card(inner, ects_fortschritt, module, bestandene_module),
        )

        # Kachel 2 (Semester): Farbe richtet sich danach, ob die Regelstudienzeit ueberschritten ist,
        # ob man trotz laufender Regelstudienzeit im Verzug ist, oder ob alles im Plan ist.
        aktuelles_semester = len(studiengang.semester())
        gesamt_ects_alle = sum(m.ects for m in studiengang.module())
        soll_tempo_alle = gesamt_ects_alle / studiengang.regelstudienzeit_semester
        im_plan = aktuelles_semester <= studiengang.regelstudienzeit_semester
        im_verzug = im_plan and geschwindigkeit < soll_tempo_alle
        if not im_plan:
            semester_bg, semester_rahmen = "#fef2f2", "#fecaca"
        elif im_verzug:
            semester_bg, semester_rahmen = "#fffbeb", "#fde68a"
        else:
            semester_bg, semester_rahmen = "#f0fdf4", "#bbf7d0"
        card2, _ = self._build_rounded_card(
            zeile, card_width, target_height, semester_bg, semester_rahmen,
            lambda inner: self._fill_semester_card(inner, studiengang, geschwindigkeit, ausgleich2),
        )

        # Kachel 3 (Note): Farbe richtet sich danach, ob die Zielnote erreicht, knapp verfehlt
        # (Abweichung < 1,0) oder deutlich verfehlt ist (Abweichung >= 1,0).
        ziel = studiengang.ziel_notendurchschnitt
        if notendurchschnitt is None:
            note_bg, note_rahmen = "#f1f5f9", "#e2e8f0"
        elif notendurchschnitt <= ziel:
            note_bg, note_rahmen = "#f0fdf4", "#bbf7d0"
        elif notendurchschnitt - ziel >= 1.0:
            note_bg, note_rahmen = "#fef2f2", "#fecaca"
        else:
            note_bg, note_rahmen = "#fffbeb", "#fde68a"
        card3, _ = self._build_rounded_card(
            zeile, card_width, target_height, note_bg, note_rahmen,
            lambda inner: self._fill_grade_card(inner, studiengang, notendurchschnitt, ausgleich3),
        )

        card1.grid(row=0, column=0, padx=8, sticky="n")
        card2.grid(row=0, column=1, padx=8, sticky="n")
        card3.grid(row=0, column=2, padx=8, sticky="n")

    def _fill_progress_card(self, card, ects_fortschritt, module, bestandene_module):
        """Fuellt Kachel 1: Fortschrittsring mit ECTS-Gesamtfortschritt."""
        bg = card.cget("bg")
        tk.Label(card, text="Gesamtfortschritt", bg=bg,
                 font=(FONT_FAMILY, 12, "bold")).pack(anchor="w")

        canvas = tk.Canvas(card, width=110, height=110, bg=bg, highlightthickness=0)
        canvas.pack(pady=10)
        percent = round(ects_fortschritt * 100)
        _create_progress_ring(canvas, x=55, y=55, radius=38, thickness=10, percent=percent, color="#2563eb")

        tk.Label(
            card, text=f"{len(bestandene_module)} von {len(module)} Modulen bestanden", bg=bg,
            font=(FONT_FAMILY, 10),
        ).pack(pady=(4, 0))

    def _fill_semester_card(self, card, studiengang, geschwindigkeit, ausgleich_vor_trennstrich=0):
        """Fuellt Kachel 2: aktuelles Semester, Status-Badge und ECTS-Tempo-Prognose."""
        bg = card.cget("bg")
        aktuelles_semester = len(studiengang.semester())
        gesamt_ects = sum(m.ects for m in studiengang.module())
        soll_tempo = gesamt_ects / studiengang.regelstudienzeit_semester
        im_plan = aktuelles_semester <= studiengang.regelstudienzeit_semester
        im_verzug = im_plan and geschwindigkeit < soll_tempo

        tk.Label(card, text="Semesteranzahl", bg=bg, font=(FONT_FAMILY, 12, "bold")).pack(anchor="w")
        if not im_plan:
            _create_badge(card, "REGELSTUDIENZEIT UEBERSCHRITTEN", "#fee2e2", "#b91c1c").pack(anchor="w", pady=(4, 10))
        elif im_verzug:
            _create_badge(card, "IM VERZUG", "#fef3c7", "#b45309").pack(anchor="w", pady=(4, 10))
        else:
            _create_badge(card, "IM PLAN", "#dcfce7", "#15803d").pack(anchor="w", pady=(4, 10))

        tk.Label(card, text=f"{aktuelles_semester}. Semester", bg=bg, font=(FONT_FAMILY, 18, "bold")).pack()

        bestandene_ects = sum(m.ects for m in studiengang.module() if m.status == ModulStatus.BESTANDEN)
        geschwindigkeit_text = f"{geschwindigkeit:.1f}".replace(".", ",")
        ects_label = tk.Label(
            card, text=f"{bestandene_ects} von {gesamt_ects} ECTS · Ø {geschwindigkeit_text} ECTS / Semester",
            bg=bg, font=(FONT_FAMILY, 10), wraplength=260 - 32, justify="center",
        )
        ects_label.pack(pady=(4, 0))

        # Fuellt bei Bedarf die Differenz zur laengeren Nachbarkachel auf, damit die Trennstriche fluchten.
        if ausgleich_vor_trennstrich:
            tk.Frame(card, bg=bg, height=ausgleich_vor_trennstrich, width=1).pack()

        card.update_idletasks()
        hoehe_vor_trennstrich = card.winfo_reqheight()

        if not im_plan:
            rahmen = "#fecaca"
        elif im_verzug:
            rahmen = "#fde68a"
        else:
            rahmen = "#bbf7d0"
        _create_divider(card, rahmen, 260 - 32)

        if geschwindigkeit >= soll_tempo:
            note = (
                f"Auf Grundlage der pro Semester durchschnittlich erreichten ECTS ist das "
                f"Abschlussziel nach {studiengang.regelstudienzeit_semester} Semestern erreichbar."
            )
        else:
            prognose_ects = geschwindigkeit * studiengang.regelstudienzeit_semester
            note = (
                f"Bei gleichbleibender Geschwindigkeit werden bis zum "
                f"{studiengang.regelstudienzeit_semester}. Semester voraussichtlich {prognose_ects:.0f} ECTS erreicht."
            )
        tk.Label(card, text=note, bg=bg, font=(FONT_FAMILY, 9),
                 fg="#475569", wraplength=260 - 32, justify="center").pack()

        return hoehe_vor_trennstrich

    def _fill_grade_card(self, card, studiengang, notendurchschnitt, ausgleich_vor_trennstrich=0):
        """Fuellt Kachel 3: aktuelle Durchschnittsnote, Status-Badge und Einordnung zur Zielnote."""
        bg = card.cget("bg")
        ziel = studiengang.ziel_notendurchschnitt

        tk.Label(card, text="Aktuelle Durchschnittsnote", bg=bg,
                 font=(FONT_FAMILY, 12, "bold"), anchor="w", justify="left",
                 wraplength=260 - 32).pack(fill="x")

        if notendurchschnitt is None:
            _create_badge(card, "NOCH KEINE NOTE", "#e2e8f0", "#475569").pack(anchor="w", pady=(4, 10))
        elif notendurchschnitt <= ziel:
            _create_badge(card, "IM ZIEL", "#dcfce7", "#15803d").pack(anchor="w", pady=(4, 10))
        elif notendurchschnitt - ziel >= 1.0:
            _create_badge(card, "ZIEL GEFÄHRDET", "#fee2e2", "#b91c1c").pack(anchor="w", pady=(4, 10))
        else:
            _create_badge(card, "ZU BEOBACHTEN", "#fef3c7", "#b45309").pack(anchor="w", pady=(4, 10))

        notentext = f"Ø {notendurchschnitt:.1f}".replace(".", ",") if notendurchschnitt is not None else "–"
        tk.Label(card, text=notentext, bg=bg, font=(FONT_FAMILY, 18, "bold")).pack()

        # Fuellt bei Bedarf die Differenz zur laengeren Nachbarkachel auf.
        if ausgleich_vor_trennstrich:
            tk.Frame(card, bg=bg, height=ausgleich_vor_trennstrich, width=1).pack()

        card.update_idletasks()
        hoehe_vor_trennstrich = card.winfo_reqheight()

        if notendurchschnitt is None:
            rahmen = "#e2e8f0"
        elif notendurchschnitt <= ziel:
            rahmen = "#bbf7d0"
        elif notendurchschnitt - ziel >= 1.0:
            rahmen = "#fecaca"
        else:
            rahmen = "#fde68a"
        _create_divider(card, rahmen, 260 - 32)

        zielnote_text = f"{ziel:.1f}".replace(".", ",")
        if notendurchschnitt is None:
            note = "Sobald die erste Pruefungsleistung bewertet ist, erscheint hier die Durchschnittsnote."
        elif notendurchschnitt <= ziel:
            note = f"Die aktuelle Durchschnittsnote liegt im Rahmen der Zielnote von ≤ {zielnote_text}."
        elif notendurchschnitt - ziel >= 1.0:
            note = f"Die aktuelle Durchschnittsnote liegt deutlich oberhalb der Zielnote von ≤ {zielnote_text}."
        else:
            note = f"Die aktuelle Durchschnittsnote liegt oberhalb der Zielnote von ≤ {zielnote_text}."
        tk.Label(card, text=note, bg=bg, font=(FONT_FAMILY, 9),
                 fg="#475569", wraplength=260 - 32, justify="center").pack()

        return hoehe_vor_trennstrich

    def _build_moduluebersicht(self, parent, studiengang: Studiengang) -> None:
        """Baut die Tabelle mit allen Modulen auf; per Klick auf den Namen lassen sich Details aufklappen."""
        bereich = tk.Frame(parent, bg=SEITEN_HINTERGRUND)
        bereich.pack(fill="x")

        tk.Label(bereich, text="Modulübersicht", bg=SEITEN_HINTERGRUND,
                 font=(FONT_FAMILY, 13, "bold")).pack(anchor="w", pady=(0, 8))

        tabelle = tk.Frame(bereich, bg="white", highlightbackground="#e2e8f0", highlightthickness=1)
        tabelle.pack(fill="x")
        tabelle.grid_columnconfigure(0, weight=1, minsize=260)
        for spalte in (1, 2, 3):
            tabelle.grid_columnconfigure(spalte, weight=0, minsize=90)

        kopf_modul = tk.Frame(tabelle, bg="white")
        kopf_modul.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        tk.Label(kopf_modul, text="MODUL", bg="white", fg="#94a3b8",
                 font=(FONT_FAMILY, 9, "bold")).pack(anchor="w")
        tk.Label(
            kopf_modul, text="(für weitere Informationen auf den Titel des Moduls klicken)",
            bg="white", fg="#94a3b8", font=(FONT_FAMILY, 8),
        ).pack(anchor="w")

        for spalte, text in ((1, "SEMESTER"), (2, "ECTS"), (3, "STATUS")):
            tk.Label(
                tabelle, text=text, bg="white", fg="#94a3b8", font=(FONT_FAMILY, 9, "bold"),
            ).grid(row=0, column=spalte, padx=16)

        # Alle Module aller Semester in eine flache Liste bringen, damit sie zeilenweise
        # in der Tabelle dargestellt werden koennen.
        alle_zeilen = [
            (semester, modul) for semester in studiengang.semester() for modul in semester.module()
        ]

        zeilennummer = 1
        for index, (semester, modul) in enumerate(alle_zeilen):
            if index > 0:
                tk.Frame(tabelle, bg="#f1f5f9", height=1).grid(
                    row=zeilennummer, column=0, columnspan=4, sticky="ew"
                )
                zeilennummer += 1

            aufgeklappt = modul in self._aufgeklappte_module
            pfeil = "▾" if aufgeklappt else "▸"
            name_label = tk.Label(
                tabelle, text=f"{pfeil} {modul.name}", bg="white", font=(FONT_FAMILY, 10),
                anchor="w", cursor="hand2",
            )
            name_label.grid(row=zeilennummer, column=0, sticky="ew", padx=16, pady=10)
            name_label.bind("<Button-1>", lambda _e, m=modul: self._modul_umschalten(m))

            tk.Label(tabelle, text=str(modul.empfohlenes_semester), bg="white", fg="#334155", font=(FONT_FAMILY, 10)).grid(
                row=zeilennummer, column=1, pady=10
            )
            tk.Label(tabelle, text=str(modul.ects), bg="white", fg="#334155", font=(FONT_FAMILY, 10)).grid(
                row=zeilennummer, column=2, pady=10
            )
            farben = STATUS_FARBEN[modul.status]
            _create_badge(tabelle, farben["text"], farben["bg"], farben["fg"]).grid(
                row=zeilennummer, column=3, pady=8
            )
            zeilennummer += 1

            if aufgeklappt:
                # Detailzeile mit allen Pruefungsleistungen des Moduls (nur sichtbar, wenn aufgeklappt).
                details = tk.Frame(tabelle, bg="#f8fafc")
                details.grid(row=zeilennummer, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 10))

                pruefungsleistungen = modul.pruefungsleistungen()
                if not pruefungsleistungen:
                    tk.Label(
                        details, text="Noch keine Prüfungsleistung angemeldet.", bg="#f8fafc",
                        fg="#64748b", font=(FONT_FAMILY, 9, "italic"),
                    ).pack(anchor="w")
                else:
                    for pruefung in pruefungsleistungen:
                        if pruefung.note is not None:
                            note_text = f"Note {pruefung.note:.1f}".replace(".", ",")
                        else:
                            note_text = "noch keine Note"
                        zeile_text = f"→ {pruefung.beschreibung()}: {note_text}"
                        if isinstance(pruefung, MuendlichePruefung):
                            zeile_text += f" · Prüfer/-in: {pruefung.pruefer}"
                        tk.Label(
                            details, text=zeile_text, bg="#f8fafc",
                            fg="#334155", font=(FONT_FAMILY, 9),
                        ).pack(anchor="w", pady=1)
                zeilennummer += 1

    def _modul_umschalten(self, modul) -> None:
        """Klappt die Detailansicht eines Moduls auf/zu und baut das Dashboard neu auf."""
        if modul in self._aufgeklappte_module:
            self._aufgeklappte_module.discard(modul)
        else:
            self._aufgeklappte_module.add(modul)
        if self._studiengang is not None:
            self.aktualisieren(self._studiengang)
