# wem-python

## Beschreibung
Python Scripte zur Analyse und Auswertung für den Weishaupt WEM CAN Bus
Verwendete Systemhardware:
- WTC-GW 25 B Ausf. H
- WEM-FA-G Bediengerät
- WEM-EM-HK Heizkreismodul
- WEM-EM-Sol Solarmodul

## Hardware/Interface
Der CAN Bus ist abgreifbar bei den Modulen oder in der WTC, entweder über die RJ11 Buchse oder über die Schraubklemmenstecker (gekennzeichnet mit +, -, H und L) und wird mit dem ADM3052 und MCP2515 an einen Raspberry Pi angeschlossen. Der ADM3052 verwendet dabei die 24 Volt des CAN Bus.

<img  src="https://raw.githubusercontent.com/geronet1/wem-python/main/images/can%20interface.png">


## Dateien
* init_can: Initialiserungskommando für den CAN Bus
* can_analyze.py: curses Analysetool für alle Nachrichten
* viewer: bash Kommandozeilenbeispiel für python-can inkl. filter
* filter.txt: python-can Filterdatei
* sniff: bash Kommandozeilenbeispiel für cansniffer
* generate_wem_table.sh: Bash Script zum erstellen einer html-Übersichtsdatei aller Werte
* wem_codes.py: Tabellenliste mit erkannten Nachrichtencodes
* wem.py: Interpreter

## Funktionsbeschreibung wem.py
Jede Nachricht vom Bus wird überprüft ob sie in der Liste der codes vorhanden ist und falls zutreffend entsprechend ausgewertet, über einen websocket an die Clients (http Seite) verteilt, über mqtt gesendet oder in InfluxDB geschrieben.

Alle 10 Sekunden werden DISPLAY (DISP) - Werte über den Bus abgefragt

Störungsnachrichten werden über Telegram versendet (telegram.py hier nicht enthalten)
