# 🚀 Startanleitung: PersoFinanz v8.0 (Ultimate Complete Edition)

Willkommen zur **Version 8.0** deines persönlichen Finanzplaners! In dieser Version wurden **ausnahmslos alle Funktionen aus v1 bis v7** zusammengeführt und in das elegante **Apple Glassmorphism Design** integriert.

---

### 📦 Enthaltene Dateien (im Studio-Bereich):

1. **`finanzplaner_app_v8.py`** – Das Hauptprogramm (Streamlit Web-App).
2. **`finanzplaner_core_v8.py`** – Das komplette Rechenwerk & Logik-Modul.
3. **`STARTANLEITUNG_v8.md`** – Diese Anleitung.
4. **`requirements.txt`** – Paketliste für Streamlit Cloud & iPad-Nutzung (inkl. `fpdf2` & `openpyxl`).

---

### 🌟 Alle Funktionen im Überblick (100 % Vollständig):

* **⚙️ Startwerte & Parameter anpassen (Kategorie 11)**:
  * Passe deinen **Girokonto-Startbestand (€)**, **Bargeld-Startbestand (€)** und den **Stichtag (Cutoff-Datum)** jederzeit in den Einstellungen an.

* **🎉 Event-Monate & individuelle Boni (Kategorie 8)**:
  * Aktiviere jeden Monat einzeln, gib einen Freitext-Grund an und lege für jeden Monat einen **individuellen Euro-Bonus-Betrag** fest.

* **📈 6–60 Monats-Prognose & Interaktive Szenarien (Kategorie 9)**:
  * Schieberegler/Auswahl für 6, 12, 24, 36, 48 oder 60 Monate Prognosezeitraum.
  * Interaktives **Szenario-Liniendiagramm** (Best Case, Normal Case, Worst Case) und automatische Systemwarnungen bei negativen Salden.

* **📅 Interaktiver Kalender & Tages-Kontostand-Prognose (Kategorie 8)**:
  * Klicke auf jeden beliebigen Tag im Kalender, um den **exakt prognostizierten Kontostand** für diesen Tag zu sehen.
  * Verschiebe den Abbuchungstag von Fixkosten/Abos direkt per Klick auf einen Kalendertag.

* **➕ Alle Formulare zum Hinzufügen & Bearbeiten**:
  * **Buchungen:** Neue Buchungen (mit `#Hashtags`), Umbuchungen zwischen Konto und Bargeld, Duplizieren & Löschen.
  * **Sparziele:** Neue Sparziele anlegen, Sparrate anpassen, Einzahlungen vornehmen, Löschen.
  * **Schulden & Forderungen:** Neue Einträge erfassen, Teilzahlungen buchen (mit automatischer Gegenbuchung), Historie.
  * **Wunschlisten:** Neue Wunschlisten (Oberkategorien) anlegen, neue Wünsche hinzufügen, Kaufen-Button (bucht Ausgabe), Löschen.
  * **Monatsbudget:** Neue Kategorien anlegen, Limits in Euro anpassen, Kategorien löschen.
  * **Einnahmen & Abos:** Neue Fixkosten / Abos hinzufügen, Rhythmus & Abbuchungstag wählen, Taschengeld-Rückstandsrechner.

* **🎯 Individueller Spar-Challenge Generator (Kategorie 4)**:
  * Beliebigen Zielbetrag in Euro, Wochenanzahl und Challenge-Typ (*Progressiv* oder *Gleichmäßig*) wählen.

* **📄 PDF-, Excel- & CSV-Export (Kategorie 9)**:
  * Generiere saubere **PDF-Monatsberichte**, lade eine **Excel-Arbeitsmappe (`.xlsx`)** mit mehreren Tabellenblättern herunter oder exportiere eine **CSV-Datei**.

* **👁️ Diskreter Privacy Mode & PIN-Schutz (Sidebar & Einstellungen)**:
  * Beträge auf Knopfdruck mit `••• €` verbergen und 4-stelligen PIN-Code festlegen.

* **💱 Live-Währungsrechner & Urlaubsmodus (Kategorie 10)**:
  * Fremdwährungen umrechnen und direkt verbuchen.

---

### 💻 Befehl zum Starten am PC (Terminal):

```cmd
py -3.12 -m streamlit run finanzplaner_app_v8
```
*(Tipp: Tippe `py -3.12 -m streamlit run fin` ein und drücke die **Tab-Taste**)*.

---

### 🌐 Für deine Online-App auf dem iPad (GitHub / Streamlit Cloud):

1. Lade `finanzplaner_app_v8.py`, `finanzplaner_core_v8.py` und `requirements.txt` in dein GitHub-Repository hoch.
2. Wähle auf Streamlit Cloud als Hauptdatei **`finanzplaner_app_v8.py`** aus.
3. Nach ca. 1 Minute ist deine Online-App auf dem iPad voll einsatzbereit!
