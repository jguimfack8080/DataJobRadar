# ADR 0004: Datengetriebene Skill-Taxonomie mit Wortgrenzenpruefung

## Status
Akzeptiert.

## Kontext
Skills sollen aus Jobbeschreibungen extrahiert werden. Naive Substring-Suche
fuehrt zu Fehltreffern (z.B. `R` in `Bachelor`, `Go` in `Google`).

## Entscheidung
Die Taxonomie ist eine Liste kanonischer Bezeichnungen mit expliziten
Synonymen. Die Erkennung erfolgt ueber vorab kompilierte regulaere Ausdruecke
mit Wortgrenzenpruefung (`(?<![A-Za-z0-9_+#])` und `(?![A-Za-z0-9_+#])`). Die
Taxonomie ist optional aus YAML erweiterbar, ohne Code anzupassen.

## Konsequenzen
- Hohe Treffergenauigkeit, niedrige Falsch-Positiv-Rate.
- Erweiterbarkeit ueber Konfiguration; neue Skills sind in einer YAML-Datei
  hinzufuegbar.
- Performance ausreichend hoch, da die Regexes pro Skill nur einmal kompiliert
  werden.
