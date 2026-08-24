# Terminal Copy

Terminal Copy ist eine NVDA-Erweiterung zum Kopieren von Bereichen aus Windows Terminal mit dem
NVDA-Cursor.

Die Bedienung mit zwei Marken wurde aus
[Terminal Access for NVDA](https://github.com/PratikP1/Terminal-Access-for-NVDA) von Pratik Patel
übernommen. Terminal Access nennt seinerseits [TDSR](https://github.com/tspivey/tdsr) von Tyler Spivey
und [Speakup](https://github.com/linux-speakup/speakup), den Linux-Kernel-Screenreader, als
Inspirationen.

## Voraussetzungen

Terminal Copy Entwicklungsversion 0.1.1 benötigt NVDA 2026.1 oder neuer sowie die Anwendung Windows
Terminal.

Die Oberfläche und die installierte Hilfe der Erweiterung sind auf Deutsch und Englisch verfügbar.

## Installation

Öffnen Sie die Datei mit der Endung `.nvda-addon`, bestätigen Sie die Installation in NVDA und
starten Sie NVDA nach Aufforderung neu.

## Einen Bereich kopieren

1. Bewegen Sie den NVDA-Cursor in Windows Terminal auf das erste Zeichen und drücken Sie `NVDA+R`.
2. Bewegen Sie ihn auf das letzte Zeichen und drücken Sie erneut `NVDA+R`.
3. Drücken Sie `NVDA+C`, um den Bereich einschließlich der beiden markierten Zeichen zu kopieren.

Drücken Sie `NVDA+R` ein drittes Mal, um beide Marken zu löschen. Sie können die Marken in beliebiger
Reihenfolge setzen, sie müssen sich jedoch im selben Windows-Terminal-Puffer befinden. NVDA meldet
jede Marke und ob das Kopieren erfolgreich war.

Die Befehle finden Sie im NVDA-Dialog „Tastenbefehle“ in der Kategorie `Terminal Copy` und können
dort neu zugewiesen werden.

## Kompatibilität mit anderen Erweiterungen

Terminal Copy funktioniert ohne eine weitere Erweiterung für Windows Terminal. Die Erweiterung
erhält außerdem ein direktes `windowsterminal`-AppModule einer anderen Erweiterung einschließlich
dessen Befehlen und Ereignisbehandlung. NVDA unterstützt jeweils nur eine durch eine Erweiterung
registrierte Programmzuordnung. Eine Erweiterung, die `windowsterminal` ebenfalls neu zuordnet, kann
daher weiterhin mit Terminal Copy in Konflikt geraten.

## Bildlaufpuffer und Einschränkungen

Terminal Copy verwendet die über NVDA bereitgestellten UI-Automation-Textbereiche von Windows
Terminal. Dadurch kann die Erweiterung verfügbare Inhalte des Bildlaufpuffers außerhalb des
sichtbaren Bereichs kopieren, wenn der NVDA-Cursor sie erreichen kann. Bereits von Windows Terminal
aus dem Puffer entfernte Inhalte können nicht kopiert werden.

Zeilen innerhalb des ausgewählten Texts, die nur Leerzeichen oder anderen Leerraum enthalten, werden
als leere Zeilen kopiert. Solche Zeilen am Anfang oder Ende werden entfernt. Nachgestellter Leerraum
wird aus jeder Zeile entfernt; führende Einrückung vor sichtbarem Text bleibt erhalten.

## Lizenz

Terminal Copy steht ausschließlich unter Version 2 der GNU General Public License (`GPL-2.0-only`).
