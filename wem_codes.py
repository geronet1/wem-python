'''
while [ 1 ]; do cat pipe2.log; done;

Nachrichtentypen:

OID	ID
000		Heartbeat? alle 10 sek.

08X		Fehlermeldung

181		Uhrzeit + Datum alle 60 sek.
182: 01 00 08 00 00|0F 00 28 00 00|0F 02 28 00 00|0F 01 28 00 00|0F 03 28 00 00|0F 03 28 01 00
1C1
1C2
201		Status / Außentemperatur alle 5 sek. / unknown: 3
241
60X 00
60X 14
60X 1B
60X 21
60X A4	Wertanforderung ->
60X 2F	Wert schreiben / Bestätigung

58X 20
58X 30
58X 60
58X 80

58X 4X	Aktueller Wert

68X 20
68X 30
68X 60
68X 80

6CX 00
6CX 19
6CX 21

70X	05	Heartbeat



582-43-31-25-00: 2048 |10240 |10241 |10243 |75779



181 AA BB CC DD EE FF GG HH
	AA = Stunden
	BB = Minuten
	CC = Jahr
	DD = Monat
	EE = Tag
	FF = Wochentag 1-7, 7=Sonntag

182 AA BB CC DD EE FF GG
	AA = 
	BB = 
	CC = 
	DD = 
	EE = 
	FF, GG = VPT Vorlauf

201 AA BB CC DD
	AA = Status 0=Aus, 1=Standby, 2=Sommer, 3=Automatik
	BB, CC = Außentemperatur signed float little endian Faktor=0.1
	DD = Bit 0: Frostschutz aktiv (AT < 5°)

241 AA BB CC DD EE FF GG HH
	AA, BB = Wärmeanforderung Heizkreis
	CC, DD = Puffer oben
	EE, FF = VPT Vorlauf
	GG, HH = Warmwassertemp.



	AA = 
	BB = 
	CC = 
	DD = 
	EE = 
	FF = 
	GG = 
	HH = 

Werte abrufen:

602 A4 4E 27 00 40 40 00 00		4E=Ausgangstest WE0 abrufen
602 A4 4F 27 YY 40 40 00 00		4F=MFA1 YY=00-> Wert 4 YY=02-> Wert 0


Werte setzen:

602 2F 4E 27 00 XX 00 00 00		Ausgangstest WTC, XX: 00=Aus, 01=Ein
602 2F 4F 27 02 XX 00 00 00		MFA1, 00=Aus, 01=Ein

603 2F 18 25 02 XX 00 00 00		Ausgangstest EM FBH, XX: 00=Aus, 01=Ein
Bestätigung?:
583 60 18 25 02 00 00 00 00
583 60 00 5E 01 00 00 00 00


603 2F 1A 25 02 XX 00 00 00		Ausgangstest EM FBH, XX=Pumpe/Mischer


604 2F 10 25 02 XX 00 00 00		Ausgangstest EM Solar, XX: 00=Aus, 01=Ein
Bestätigung?:
604 2F 21 26 00 00 00 00 00

604 11 25 02 XX 00 00 00 00		Pumpe, XX: 00=Aus, 01=Ein


Fehlermeldung:
ID	(WTC)			Störung			1B=F27					Störung Ende
082 (   6)      (  4) FF FF 01 02 00 1B 07 00   (  2) 00 00 00 00 00 00 00 01 

Vorlauffühler eSTB defekt:										1E=F30
082 (   3)      (  2) 00 00 00 00 00 00 00 01   (  1) FF FF 01 04 00 1E 07 00

Solar: 								02=F2 (Kollektorfühler)
084 (   7)      (  3) FF FF 01 01 00 02 09 03   (  4) 00 00 00 00 00 00 00 00 
Störung Ende:
00 00 01 00 00 00 09 03         000 000 001 000 000 000 009 003         1       0       50921472        0       777
00 00 00 00 00 00 00 00         000 000 000 000 000 000 000 000         0       0       0       0       0

Solar:								05=F5 (Pufferfühler)
084 (  10)      (  4) FF FF 01 01 00 05 09 03   (  6) 00 00 00 00 00 00 00 00 
00 00 01 00 00 00 09 03         000 000 001 000 000 000 009 003         1       0       50921472        0       777
00 00 00 00 00 00 00 00         000 000 000 000 000 000 000 000         0       0       0       0       0



'''

wem_system = '''<div class="value wem tag" id="wem_time" data-title="Zeit"></div>
<div class="value wem tag" id="wem_day" data-title="Tag"></div>
<div class="value wem tag" id="wem_date" data-title="Datum"></div>
<div class="value wem tag" id="wem_182" data-title="[182] Bytes 0-4:"></div>
<div class="value wem tag" id="wem_182_vpt_vorlauf" data-title="VPT Vorlauf"></div>
<div class="value wem tag" id="wem_201_status" data-title="System Status"></div>
<div class="value wem tag" id="wem_at" data-title="Außentemperatur"></div>
<div class="value wem tag" id="wem_unknown" data-title="wem_unknown"></div>
<div class="value wem tag" id="wem_241_waermeanforderung_heizkreis" data-title="Wärmeanforderung Heizkreis"></div>
<div class="value wem tag" id="wem_puffer_oben" data-title="Puffer oben"></div>
<div class="value wem tag" id="wem_241_vpt_vorlauf" data-title="VPT Vorlauf"></div>
<div class="value wem tag" id="wem_warmwasser" data-title="Warmwasser"></div>'''


'''
codes = 
[id, byte0, title] [ [byte1, byte2, byte3, precision, factor, unit, name, flags, (last value) ]

'''
OID = 0
BYTE0 = 1
OID_NAME = 2
BYTE1 = 3
BYTE2 = 4
BYTE3 = 5
PREC = 6
FACTOR = 7
UNIT = 8
NAME = 9
FLAGS = 10
VALUE = 11

# Flags:
SIGNED = 1 << 0	# signed or unsigned
PARAM = 1 << 1 # Parameter (changeable)
DISP = 1 << 2 # Display on Website
TABLE = 1 << 3 # Display on Website
DB = 1 << 4 # Store in Database

codes = [
[0x582, 0x4B, "WTC"],
[
[0x14, 0x27, 0x02, 2, 0.01, "bar", "Anlagendruck", DISP | DB],
[0x2C, 0x25, 0x00, 1, 0.1, "°C", "Wärmeanforderung Heizkreis Aktuell FBH", DISP],
[0x2D, 0x25, 0x00, 1, 0.1, "°C", "Wärmeanforderung Warmwasser Aktuell ? ", DISP],
[0x45, 0x25, 0x00, 1, 0.1, "°C", "Vorlaufsolltemperatur WE0", DISP | DB],
[0x42, 0x25, 0x00, 2, 0.01, "%", "Sollleistung WE0", DISP | DB],
[0x34, 0x25, 0x00, 1, 0.01, "%", "Leistung", DISP | DB],

[0x15, 0x27, 0x02, 1, 0.1, "°C", "Vorlauftemperatur VPT WE0", DISP | DB],
[0x32, 0x25, 0x00, 1, 0.1, "°C", "VPT Vorlauf", DISP | DB],
[0x33, 0x25, 0x02, 1, 0.1, "°C", "VPT Rücklauf", DISP | DB],
[0x13, 0x27, 0x02, 0, 1, "l/h", "Volumenstrom VPT Aktuell WE0", DISP | DB],
[0x31, 0x27, 0x02, 2, 0.01, "kW", "Wärmeleistung VPT Aktuell WE0", DISP | DB],

[0x36, 0x25, 0x00, 1, 0.1, "°C", "Vorlauf", DISP],
[0x37, 0x25, 0x00, 1, 0.1, "°C", "Abgas", DISP | DB],
[0x7E, 0x25, 0x00, 2, 0.01, "%", "Gebläse-Ansteuersignal Aktuell WE0", DISP | DB],
[0x40, 0x25, 0x00, 0, 1, "rpm", "Gebläsedrehzahl Aktuell WE0", DISP | DB],
[0x3F, 0x25, 0x00, 2, 0.01, "%", "Gasventil Ansteuersignal Aktuell WE0", DISP | DB],
[0x7D, 0x25, 0x00, 2, 0.01, "%", "Gas-Luft-Verhältnis Aktuell WE0", DISP],

[0x3D, 0x25, 0x00, 2, 0.01, "%", "Gasventil Offset WE0", 0],
[0x85, 0x25, 0x02, 1, 0.1, "%", "Gasventil Offset Speicher Aktuell WE0", 0],

[0x20, 0x2A, 0x00, 0, 1, "", "Zähler seit Rücksetzen Brennerstarts WE0", TABLE],
[0x21, 0x2A, 0x00, 0, 1, "h", "Zähler seit Rücksetzen Betriebsstunden WE0", TABLE],
[0x22, 0x2A, 0x00, 0, 1, "", "", 0],

[0x0D, 0x25, 0x02, 0, 0.1, "K", "Schaltdifferenz Regler Heizbetrieb WE0", PARAM],
[0x03, 0x25, 0x02, 0, 0.1, "K", "Schaltdifferenz Regler Warmwasser WE0", PARAM],
[0x13, 0x25, 0x00, 0, 0.1, "s", "Zeit Zwangsteillast Heizbetrieb WE0", PARAM], # Vielfache von 5
[0x23, 0x25, 0x02, 0, 0.01, "%", "Leistung maximal Heizbetrieb WE0", PARAM],
[0x28, 0x25, 0x02, 0, 0.01, "%", "Leistung maximal WW-Betrieb WE0", PARAM],
[0x29, 0x27, 0x02, 0, 1, "l/h", "Volumenstrom maximal WE0", PARAM],

[0x3B, 0x27, 0x02, 0, 1, "", "", 0],
[0x3D, 0x27, 0x01, 0, 1, "", "", 0],
[0x3F, 0x27, 0x02, 0, 1, "", "", 0],
[0x4B, 0x25, 0x00, 0, 1, "", "", 0],
[0x54, 0x27, 0x01, 0, 1, "", "", 0],
[0x03, 0x25, 0x01, 0, 1, "", "", 0],
[0x0D, 0x25, 0x01, 0, 1, "", "", 0],
[0x16, 0x25, 0x01, 0, 1, "", "", 0],
[0x16, 0x27, 0x01, 0, 1, "", "", 0],
[0x17, 0x27, 0x01, 0, 1, "", "", 0],
[0x23, 0x25, 0x01, 0, 1, "", "", 0],
[0x28, 0x25, 0x01, 0, 1, "", "", 0],
[0x29, 0x27, 0x01, 0, 1, "", "", 0],
[0x2A, 0x27, 0x01, 0, 1, "", "", 0],
[0x2B, 0x27, 0x01, 0, 1, "", "", 0],
[0x2E, 0x25, 0x00, 0, 1, "", "", 0],
[0x2F, 0x25, 0x00, 0, 1, "", "", 0],
[0x3B, 0x25, 0x01, 0, 1, "", "", 0],
[0x3F, 0x27, 0x01, 0, 1, "", "", 0],
[0x53, 0x27, 0x01, 0, 1, "", "", 0],
[0x65, 0x27, 0x01, 0, 1, "", "", 0],
[0x69, 0x25, 0x01, 0, 1, "", "", 0],
[0x69, 0x25, 0x02, 0, 1, "", "", 0],
[0x6A, 0x27, 0x01, 0, 1, "", "", 0],
[0x6B, 0x25, 0x01, 0, 1, "", "", 0],
[0x6C, 0x25, 0x01, 0, 1, "", "", 0],
[0x6E, 0x25, 0x01, 0, 1, "", "", 0],
[0x72, 0x27, 0x01, 0, 1, "", "", 0],
[0x74, 0x25, 0x01, 0, 1, "", "", 0],
[0x78, 0x27, 0x01, 0, 1, "", "", 0],
[0x81, 0x25, 0x01, 0, 1, "", "", 0],
[0x84, 0x25, 0x01, 0, 1, "", "", 0],
[0x85, 0x25, 0x01, 0, 1, "", "", 0],
[0x8A, 0x25, 0x01, 0, 1, "", "", 0],
[0x8B, 0x25, 0x01, 0, 1, "", "", 0],
[0x94, 0x25, 0x01, 0, 1, "", "", 0],
[0x9B, 0x25, 0x01, 0, 1, "", "", 0],

#4B 15 27 01 00 00 00 00         075 021 039 001 000 000 000 000         295     1       0       0       0
#4B 33 25 01 00 00 00 00         075 051 037 001 000 000 000 000         293     1       0       0       0
#4B 28 27 01 00 00 00 00         075 040 039 001 000 000 000 000         295     1       0       0       0
#4B 26 27 01 00 00 00 00         075 038 039 001 000 000 000 000         295     1       0       0       0
#4B 27 27 01 00 00 00 00         075 039 039 001 000 000 000 000         295     1       0       0       0
#4B 1A 27 01 10 00 00 00         075 026 039 001 016 000 000 000         295     4097    16      16      0
#4B 19 27 01 00 00 00 00         075 025 039 001 000 000 000 000         295     1       0       0       0
#4B 1B 27 01 00 00 00 00         075 027 039 001 000 000 000 000         295     1       0       0       0
#4B 2C 27 01 00 00 00 00         075 044 039 001 000 000 000 000         295     1       0       0       0
#4B 13 27 01 00 00 00 00         075 019 039 001 000 000 000 000         295     1       0       0       0
#4B 31 27 01 00 00 00 00         075 049 039 001 000 000 000 000         295     1       0       0       0
#4B 14 27 01 00 00 00 00         075 020 039 001 000 000 000 000         295     1       0       0       0
#4B 32 27 01 10 00 00 00         075 050 039 001 016 000 000 000         295     4097    16      16      0
#4B 63 27 01 00 00 00 00         075 099 039 001 000 000 000 000         295     1       0       0       0
#4B 64 27 01 11 00 00 00         075 100 039 001 017 000 000 000         295     4353    17      17      0
#4B 3B 27 01 11 00 00 00         075 059 039 001 017 000 000 000         295     4353    17      17      0


#[0x, 0x27, 0, 1, "", "Betriebsart Warmwasser", PARAM],

#[0x1A, 0x00, 0, 1, "°C", "", 0],
#[0x3B, 0x00, 0, 1, "°C", "", 0],
#[0x3F, 0x00, 0, 1, "°C", "", 0],
[0x53, 0x27, 0x02, 0, 1, "", "", 0],
#[0x54, 0x00, 0, 1, "°C", "", 0],
#[0x45, 0x00, 0, 1, "°C", "", 0],
#[0x45, 0x00, 0, 1, "°C", "", 0],
#[0x53, 0x27, 0, 1, "°C", "", 0],
],

[0x582, 0x43, "WTC Zähler"],
[
[0x00, 0x2A, 0x00, 0, 1, "h", "Gesamtzähler Betriebsstunden WE0", TABLE],
[0x01, 0x2A, 0x00, 0, 1, "", "Gesamtzähler Brennerstarts WE0", TABLE],
[0x26, 0x27, 0x02, 2, 0.01, "kWh", "Tageswärmemenge (Vortag) Heizbetrieb WE0", 0],
[0x27, 0x27, 0x02, 2, 0.01, "kWh", "Tageswärmemenge (Vortag) Warmwasserbetrieb WE0", 0],
[0x28, 0x27, 0x02, 2, 0.01, "kWh", "Tageswärmemenge (Vortag) Gesamt WE0", 0],

[0x31, 0x25, 0x00, 0, 1, "", "", 0], # ['2048', '08:08', '10240', '12:01', '2048', '12:01']		['10240', '12:01', '2048', '12:01', '10240', '12:01', '2048', '12:01', '10241', '05:01', '10243', '05:01', '75779', '05:01', '10241', '06:02', '10240', '06:02', '2048', '06:02']

[0x70, 0x27, 0x02, 0, 1, "", "", 0],
],

[0x582, 0x4F, "WTC Scot System"],
[
[0x30, 0x25, 0x00, 0, 1, "", "Betriebsphase WTC", DISP], #  0=Standby, 1=Brenner Aus, 10=Heizung, 15=Warmwasser, 104=Wartung, Betriebsphase Brenner WE0
[0x63, 0x27, 0x02, 0, 1, "", "Gasdruckwächter", DISP], # Gasdruck
[0x19, 0x27, 0x02, 0, 1, "%", "Pumpenleistung Pumpe intern Sollleistung WE0", DISP | DB],
[0x1B, 0x27, 0x02, 0, 1, "W", "Pumpenleistung Pumpe intern Elektrische Leistung WE0", DISP | DB],
[0x9B, 0x25, 0x02, 0, 1, "°C", "Abgastemperatur maximal WE0", 0],
[0x7A, 0x25, 0x00, 0, 1, "Pt", "Ionisationssignal Start WE0", 0],
[0x79, 0x25, 0x00, 0, 1, "Pt", "Ionisationssignal Sollwert WE0", 0],
[0x39, 0x25, 0x00, 0, 1, "Pt", "Ionisationssignal SCOT-Istwert WE0", DISP | DB],
[0x3A, 0x25, 0x00, 0, 1, "Pt", "Ionisationssignal SCOT-Basiswert WE0", 0],
[0x81, 0x25, 0x02, 0, 1, "%", "Korrektur Gasmenge beim Start WE0", 0],
[0x8B, 0x25, 0x02, 0, 1, "%", "Korrektur Leistung minimal WE0", 0],
[0x7B, 0x25, 0x00, 1, 0.1, "s", "Zeit bis Flammenbildung Aktuell WE0", DISP],

[0x0A, 0x25, 0x00, 0, 1, "min", "Brennertaktsperre Heizbetrieb WE0", PARAM],
[0x16, 0x27, 0x02, 1, 0.01, "bar", "Anlagendruck minimal Warnmeldung WE0", PARAM],
[0x17, 0x27, 0x02, 1, 0.01, "bar", "Anlagendruck minimal Brennersperre WE0", PARAM],
[0x6A, 0x27, 0x02, 0, 1, "", "Pumpe intern Betriebsart HZ WE0", PARAM], # 0=Leistungsproportional, 4=Volumenstromregelung, 5-6-7=Proportionaldruck Stufe 1-2-3, 8-9-10=Konstantdruck Stufe 1-2-3, 
[0x16, 0x25, 0x02, 0, 1, "", "Pumpe intern Betriebsart WW WE0", PARAM], # 0=Leistungsproportional, 4=Volumenstromregelung, 5=Konstante Pumpenleistung
[0x6B, 0x25, 0x02, 0, 1, "%", "Pumpenleistung minimal Heizbetrieb WE0", PARAM],
[0x6C, 0x25, 0x02, 0, 1, "%", "Pumpenleistung maximal Heizbetrieb WE0", PARAM],
[0x6E, 0x25, 0x02, 0, 1, "%", "Pumpenleistung minimal WW-Betrieb WE0", PARAM],
[0x3B, 0x25, 0x02, 0, 1, "%", "Pumpenleistung maximal WW-Betrieb WE0", PARAM],
[0x2A, 0x27, 0x02, 0, 1, "%", "Volumenstrom Faktor Heizbetrieb WE0", PARAM],
[0x2B, 0x27, 0x02, 0, 1, "%", "Volumenstrom Faktor Warmwasserladung WE0", PARAM],
[0x4E, 0x27, 0x00, 0, 1, "", "Ausgangstest WE0", PARAM], # 0=Aus, 1=Ein
[0x4F, 0x27, 0x02, 0, 1, "", "MFA1", PARAM], # 0=Aus, 1=Ein

[0x1A, 0x27, 0x02, 0, 1, "", "", 0],
[0x2C, 0x27, 0x02, 0, 1, "", "", 0],

[0x32, 0x27, 0x02, 0, 1, "", "", 0],
[0x39, 0x27, 0x00, 0, 1, "", "", 0], # 0 - 10 - 0
[0x3D, 0x27, 0x02, 0, 1, "", "", 0],
[0x41, 0x25, 0x00, 0, 1, "", "", 0], # Pumpe ? ['0', '06:56', '3', '05:52', '0', '06:02']  3 - 4 - 0
[0x54, 0x27, 0x02, 0, 1, "", "", 0],
[0x64, 0x27, 0x02, 0, 1, "", "", 0],
[0x66, 0x27, 0x02, 0, 1, "", "", 0],
[0x72, 0x27, 0x02, 0, 1, "", "", 0],
[0x74, 0x25, 0x02, 0, 1, "", "", 0],
[0x78, 0x27, 0x02, 0, 1, "", "", 0],
[0x8A, 0x25, 0x02, 0, 1, "", "", 0],
[0x8C, 0x25, 0x00, 0, 1, "", "", 0],
[0x84, 0x25, 0x02, 0, 1, "", "", 0],
[0x94, 0x25, 0x02, 0, 1, "", "", 0],
],

#[0x583, 0x43, "Heizkreis"],
#[
#[0x51, 0x26, None, 1, 0.1, "°C", "Zeitprogramm?", PARAM], # byte3=00-XX
#],

[0x583, 0x4B, "Heizkreis"],
[
[0x07, 0x26, 0x02, 1, 0.1, "°C", "Vorlauf FBH", DISP | DB],

[0xA2, 0x26, 0x01, 0, 1, "", "So/Wi Umschaltung Funktion", PARAM], # 0=Aus, 1=Ein
[0x7B, 0x26, 0x02, 0, 0.1, "°C", "So/Wi Umschaltung Umschalttemperatur", PARAM],
[0x39, 0x26, 0x02, 0, 0.1, "°C", "Raumsolltemperatur Absenk ", PARAM],
[0x3A, 0x26, 0x02, 0, 0.1, "°C", "Raumsolltemperatur Normal", PARAM],
[0x3B, 0x26, 0x02, 0, 0.1, "°C", "Raumsolltemperatur Komfort", PARAM],
[0x69, 0x26, 0x02, 1, 0.1, "°C", "Raumsolltemperatur Komfort FBH ?", 0],
[0x1B, 0x26, 0x02, 0, 0.1, "°C", "Vorlaufsolltemperatur minimal ", PARAM],
[0x1C, 0x26, 0x02, 0, 0.1, "°C", "Vorlaufsolltemperatur maximal", PARAM],
[0xC7, 0x26, 0x02, 0, 0.1, "°C", "Vorlaufsolltemperatur Heizgrenze", PARAM],
[0xAD, 0x26, 0x02, 0, 0.1, "K", "Heizkurve Parallel", PARAM],
[0x4B, 0x26, 0x02, 0, 0.1, "", "Heizkurve Steilheit", PARAM],
[0x54, 0x26, 0x02, 0, 0.1, "°C", "Frostschutz Außentemperatur", SIGNED|PARAM],
[0x34, 0x26, 0x02, 0, 0.1, "K", "Mischerüberhöhung", PARAM],
[0x05, 0x25, 0x02, 0, 1, "s", "Mischerlaufzeit", PARAM],
[0x07, 0x25, 0x02, 0, 1, "s", "Mischer Initialisierungslaufzeit", PARAM],
[0x5C, 0x26, 0x02, 0, 1, "", "Temperaturregler P-Anteil Kp", PARAM],
[0x4E, 0x26, 0x02, 0, 1, "", "Temperaturregler I-Anteil Tn", PARAM],
[0x81, 0x26, 0x02, 0, 0.1, "°C", "Niveauanhebung Außentemperatur", SIGNED|PARAM],
[0x7D, 0x26, 0x02, 0, 1/60, "min", "Verzögerungszeit Wärmeanforderung", PARAM],
[0x22, 0x26, 0x02, 0, 0.1, "°C", "Estrich Starttemperatur", PARAM],

[0x6C, 0x26, 0x02, 1, 0.1, "°C", "Außentemperatur lokal Gemittelt FBH", SIGNED|DISP],
[0x6D, 0x26, 0x02, 1, 0.1, "°C", "Außentemperatur lokal Gemischt FBH", SIGNED|DISP],
[0xD3, 0x26, 0x02, 1, 0.1, "°C", "Außentemperatur Aktuell FBH", SIGNED|DISP],

[0x58, 0x26, 0x02, 1, 0.1, "°C", "Raumsolltemperatur Aktuell FBH", 0],
[0x59, 0x26, 0x02, 1, 0.1, "°C", "Vorlaufsolltemperatur Aktuell FBH", DISP | DB],
[0x50, 0x26, 0x03, 1, 0.1, "°C", "Wärmeanforderung Heizkreis FBH", DISP],

[0xA1, 0x26, 0x02, 0, 1, "", "", 0],
[0xE6, 0x26, 0x02, 0, 1, "", "", 0],
[0xEF, 0x26, 0x01, 0, 1, "", "", 0],
[0xEF, 0x26, 0x02, 0, 1, "", "", 0],

[0x03, 0x26, 0x02, 0, 1, "", "", 0],
[0x80, 0x26, 0x01, 0, 1, "", "", 0],
[0x21, 0x26, 0x01, 0, 1, "", "", 0],
[0x26, 0x00, 0x00, 0, 1, "", "", 0],
[0xA1, 0x26, 0x01, 0, 1, "", "", 0],
[0xE6, 0x26, 0x01, 0, 1, "", "", 0],
[0xEB, 0x26, 0x01, 0, 1, "", "", 0],
[0xB8, 0x26, 0x01, 0, 1, "", "", 0],
[0x18, 0x25, 0x00, 0, 1, "", "", 0], # Pumpe ?
[0x6B, 0x26, 0x02, 0, 1, "", "", 0],
[0x6A, 0x26, 0x02, 0, 1, "", "", 0],
[0x2C, 0x26, 0x02, 0, 1, "", "", 0],

#4B 07 26 01 00 00 00 00         075 007 038 001 000 000 000 000         294     1       0       0       0
#4B D1 26 01 10 00 00 00         075 209 038 001 016 000 000 000         294     4097    16      16      0
#4B 03 26 01 10 00 00 00         075 003 038 001 016 000 000 000         294     4097    16      16      0
#4B 6C 26 01 00 00 00 00         075 108 038 001 000 000 000 000         294     1       0       0       0
#4B 6D 26 01 00 00 00 00         075 109 038 001 000 000 000 000         294     1       0       0       0
#4B D3 26 01 00 00 00 00         075 211 038 001 000 000 000 000         294     1       0       0       0
#4B 58 26 01 00 00 00 00         075 088 038 001 000 000 000 000         294     1       0       0       0
#4B 59 26 01 00 00 00 00         075 089 038 001 000 000 000 000         294     1       0       0       0
#4B 36 26 01 00 00 00 00         075 054 038 001 000 000 000 000         294     1       0       0       0
#4B 4F 26 01 00 00 00 00         075 079 038 001 000 000 000 000         294     1       0       0       0
#4B 46 26 01 00 00 00 00         075 070 038 001 000 000 000 000         294     1       0       0       0
#4B EF 26 01 10 00 00 00         075 239 038 001 016 000 000 000         294     4097    16      16      0

],

[0x583, 0x4F, "Heizkreis"],
[
[0x36, 0x26, 0x02, 0, 1, "%", "Mischerstellung Soll FBH", DISP],
[0x4F, 0x26, 0x02, 0, 1, "%", "Mischerstellung Ist FBH", DISP | DB],
[0x46, 0x26, 0x02, 0, 1, "", "Pumpe Heizkreis FBH", DISP | DB], # 0=Aus, 1=Ein
[0x2D, 0x26, 0x02, 0, 1, "", "Niveauanhebung Außentemperatur", 0],

[0x33, 0x26, 0x02, 0, 1, "", "Betriebsart", PARAM|DISP], # 1=Standby, 2=Zeitprogramm 1, 3=Zeitprogramm 2, 4=Zeitprogramm 3, 5=Sommer, 6=Komfort, 7=Normal, 8=Absenk
[0x40, 0x26, 0x02, 0, 1, "", "Betriebsart 1-3?", PARAM], # 0=Standby
[0x7E, 0x26, 0x03, 0, 1, "", "Status FBH", 0], # 7=7, 21=Normal, 22=Absenk, 24=Frostschutz ein, 255=Übertemperatur Alternativenergie
[0x7E, 0x26, 0x04, 0, 1, "", "Betriebsart FBH", 0], # 6->8 Zeitprogramm 1->3 / 9 / 13=Standby 12=Komfort

[0x37, 0x26, 0x02, 0, 1, "", "Priorität Warmwasser", PARAM], # 0=Vorrang, 1=Parallel, 2=Gleitend
[0x6E, 0x26, 0x02, 0, 1, "", "Gebäudebauweise", PARAM], # 0=sehr leicht, 1=mittel leicht, 2=leicht, 3=schwer, 4=mittel schwer, 5=sehr schwer
[0x7C, 0x26, 0x02, 0, 1, "", "Raumsolltemperatur Heizgrenze", PARAM],
[0x7F, 0x26, 0x02, 0, 0.1, "K", "Toleranzbereich Mischerregelung", PARAM],
[0xA3, 0x26, 0x02, 0, 1, "", "Aufheizoptimierung", PARAM],
[0xC8, 0x26, 0x02, 0, 1, "", "Vorlaufsolltemperatur Heizgrenze", PARAM],
[0xE8, 0x26, 0x02, 0, 1, "min", "Raumregelung I-Anteil Nachstellzeit", PARAM],
[0xA6, 0x26, 0x02, 0, 1, "", "Estrich", PARAM], # 1=Funktionsheizen, 2=Belegreifheizen, 3=Funktions- und Belegreifheizen


[0x87, 0x26, 0x02, 0, 1, "", "Party / Heizpause Funktion", PARAM], # 0=Aus, 1=Party / Heizpause, 2=Heizpause 
[0x89, 0x26, 0x02, 0, 1, "", "Party / Heizpause Raumsolltemperatur", PARAM], # 1=Absenk, 2=Normal, 3=Komfort

[0x93, 0x26, 0x00, 0, 1, "", "Party - Startzeit", 0], # byte3: 00=03?
[0x93, 0x26, 0x02, 0, 1, "", "Party - Startzeit Stunde", PARAM], # byte3: 02=Stunden 03=Minuten
[0x93, 0x26, 0x03, 0, 1, "", "Party - Startzeit Minute", PARAM],
[0x88, 0x26, 0x00, 0, 1, "", "Party - Endzeit", PARAM], # byte3: 00=03?
[0x88, 0x26, 0x02, 0, 1, "", "Party - Endzeit Stunde", PARAM], # byte3: 02=Stunden 03=Minuten
[0x88, 0x26, 0x03, 0, 1, "", "Party - Endzeit Minute", PARAM],

[0x8A, 0x26, 0x02, 0, 1, "", "Urlaub Funktion", PARAM], # 0=Aus, 1=Ein
[0x86, 0x26, 0x02, 0, 1, "", "Urlaub Raumsolltemperatur", PARAM], # 0=Frost, 1=Absenk

[0x84, 0x26, 0x00, 0, 1, "", "Urlaub - Beginn", 0], # byte3: 00=05?
[0x84, 0x26, 0x03, 0, 1, "", "Urlaub - Beginn Tag", PARAM], # byte3: 02=Jahr, 03=Tag, 04=Monat
[0x84, 0x26, 0x04, 0, 1, "", "Urlaub - Beginn Monat", PARAM],
[0x84, 0x26, 0x02, 0, 1, "", "Urlaub - Beginn Jahr", PARAM],
[0x85, 0x26, 0x00, 0, 1, "", "Urlaub - Ende", 0], # byte3: 00=05?
[0x85, 0x26, 0x03, 0, 1, "", "Urlaub - Ende Tag", PARAM], # byte3: 00=05? 02=Jahr, 03=Tag, 04=Monat
[0x85, 0x26, 0x04, 0, 1, "", "Urlaub - Ende Monat", PARAM],
[0x85, 0x26, 0x02, 0, 1, "", "Urlaub - Ende Jahr", PARAM],

[0x18, 0x25, 0x02, 0, 1, "", "Ausgangstest", PARAM], # 0=Aus, 1=Ein
[0x19, 0x25, 0x02, 0, 1, "", "Relaistest", PARAM], # 0=Aus, 1=Pumpe, 2=Mischer Auf, 3=Mischer Zu
[0x1A, 0x25, 0x02, 0, 1, "%", "PWM Signal", PARAM],

[0x3E, 0x26, 0x00, 0, 1, "", "", 0],
[0x07, 0x26, 0x00, 0, 1, "", "", 0],
[0x21, 0x26, 0x00, 0, 1, "", "", 0],
[0x21, 0x26, 0x02, 0, 1, "", "", 0],
[0x21, 0x26, 0x03, 0, 1, "", "", 0],
[0x21, 0x26, 0x04, 0, 1, "", "", 0],
[0x36, 0x26, 0x00, 0, 1, "", "", 0],
[0x3F, 0x26, 0x00, 0, 1, "", "", 0],
[0x51, 0x26, 0x00, 0, 1, "", "", 0],
[0x58, 0x26, 0x00, 0, 1, "", "", 0],
[0x59, 0x26, 0x00, 0, 1, "", "", 0],
[0x6D, 0x26, 0x00, 0, 1, "", "", 0],
[0x80, 0x26, 0x02, 0, 1, "", "", 0],
[0xA1, 0x26, 0x00, 0, 1, "", "", 0],
[0xD1, 0x26, 0x02, 0, 1, "", "", 0],
[0xD3, 0x26, 0x00, 0, 1, "", "", 0],
[0xE6, 0x26, 0x00, 0, 1, "", "", 0],
[0xEB, 0x26, 0x02, 0, 1, "", "", 0],
[0xEF, 0x26, 0x00, 0, 1, "", "", 0],
[0x18, 0x25, 0x00, 0, 1, "", "", 0],
[0xA2, 0x26, 0x02, 0, 1, "", "", 0],
[0x82, 0x26, 0x02, 0, 1, "", "", 0],
],

[0x584, 0x4B, "Solar"],
[
[0x01, 0x25, 0x02, 1, 0.1, "°C", "Puffer oben", DISP | DB],
[0x02, 0x25, 0x02, 1, 0.1, "°C", "Puffer unten", DISP | DB],
[0x00, 0x25, 0x02, 1, 0.1, "°C", "Speicher unten", DISP | DB],
#[0x02, 0x26, 0x00, 1, 0.1, "°C", "Speicher unten", 0],

[0x04, 0x25, 0x02, 1, 0.1, "°C", "Kollektor", SIGNED|DISP | DB],
[0x05, 0x25, 0x02, 1, 0.1, "°C", "Kollektor Vorlauf", DISP | DB],
[0x06, 0x25, 0x02, 1, 0.1, "°C", "Kollektor Rücklauf", DISP | DB],
[0x10, 0x26, 0x00, 2, 0.01, "l/min", "Volumenstrom", DISP | DB],
[0x11, 0x26, 0x00, 0, 1, "W", "Kollektorleistung Aktuell (Benutzer)", 0],
[0x21, 0x25, 0x02, 1, 0.1, "kW", "Leistung", DISP | DB],

[0x33, 0x26, 0x02, 0, 1, "", "Gesamtzähler Starts", TABLE],
[0x35, 0x26, 0x02, 0, 1, "", "Zähler seit Rücksetzen Starts", TABLE],

[0x05, 0x26, 0x00, 0, 0.1, "°C", "Kollektortemperatur maximal", PARAM],
[0x06, 0x26, 0x00, 0, 0.1, "°C", "Kollektortemperatur minimal", PARAM],
[0x09, 0x26, 0x00, 0, 0.1, "°C", "Kollektor Frostschutztemperatur", SIGNED|PARAM],
[0x0C, 0x26, 0x02, 0, 0.1, "K", "Einschaltdifferenz Kollektorkreis", PARAM],
[0x0D, 0x26, 0x02, 0, 0.1, "K", "Ausschaltdifferenz Kollektorkreis", PARAM],
[0x0E, 0x26, 0x00, 0, 0.1, "K", "Regeldifferenz", PARAM],
[0x0F, 0x26, 0x00, 0, 1, "W", "Untere Leistungsgrenze Kollektor", PARAM],
[0x13, 0x26, 0x02, 1, 0.01, "l/min", "Volumenstrom minimal", PARAM],
[0x14, 0x26, 0x02, 1, 0.01, "l/min", "Volumenstrom maximal", PARAM],
[0x1D, 0x26, 0x00, 0, 0.1, "°C", "Vorlauftemperatur maximal", PARAM],
[0x22, 0x26, 0x02, 0, 1, "W", "Ertrag minimal Warmwasserbetrieb", PARAM],
[0x23, 0x26, 0x02, 0, 1, "W", "Ertrag minimal Heizbetrieb", PARAM],

#[0x03, 0x21, 0x01, 0, 1, "", "", 0], # Pufferladestrategie
[0x00, 0x52, 0x01, 0, 1, "", "", 0],
[0x01, 0x25, 0x01, 0, 1, "", "", 0],
[0x01, 0x52, 0x01, 0, 1, "", "", 0],
[0x02, 0x25, 0x01, 0, 1, "", "", 0],
[0x07, 0x26, 0x00, 0, 1, "", "", 0],
[0x08, 0x26, 0x00, 0, 1, "", "", 0],
[0x29, 0x26, 0x01, 0, 1, "", "", 0],
[0x08, 0x26, 0x01, 0, 1, "", "", 0],
[0x07, 0x26, 0x01, 0, 1, "", "", 0],
[0x13, 0x26, 0x01, 0, 1, "", "", 0],
[0x14, 0x26, 0x01, 0, 1, "", "", 0],
[0x0C, 0x26, 0x01, 0, 1, "", "", 0],
[0x0D, 0x26, 0x01, 0, 1, "", "", 0],
[0x40, 0x26, 0x01, 0, 1, "", "", 0],

#4B 04 25 01 08 00 00 00         075 004 037 001 008 000 000 000         293     2049    8       8       0
#4B 00 25 01 08 00 00 00         075 000 037 001 008 000 000 000         293     2049    8       8       0
#4B 05 25 01 08 00 00 00         075 005 037 001 008 000 000 000         293     2049    8       8       0
#4B 06 25 01 08 00 00 00         075 006 037 001 008 000 000 000         293     2049    8       8       0
#4B 35 26 01 00 00 00 00         075 053 038 001 000 000 000 000         294     1       0       0       0
#4B 33 26 01 00 00 00 00         075 051 038 001 000 000 000 000         294     1       0       0       0
#4B 36 26 01 00 00 00 00         075 054 038 001 000 000 000 000         294     1       0       0       0
#4B 2C 26 01 00 00 00 00         075 044 038 001 000 000 000 000         294     1       0       0       0
#4B 34 26 01 00 00 00 00         075 052 038 001 000 000 000 000         294     1       0       0       0
#4B 42 26 01 00 00 00 00         075 066 038 001 000 000 000 000         294     1       0       0       0
#4B 41 26 01 00 00 00 00         075 065 038 001 000 000 000 000         294     1       0       0       0
#4B 2B 26 01 00 00 00 00         075 043 038 001 000 000 000 000         294     1       0       0       0
#4B 2A 26 01 00 00 00 00         075 042 038 001 000 000 000 000         294     1       0       0       0
#4B 39 26 01 00 00 00 00         075 057 038 001 000 000 000 000         294     1       0       0       0


],

[0x584, 0x4F, "Solar"],
[
[0x08, 0x25, 0x00, 0, 1, "%", "Solarpumpe Drehzahl", DISP | DB],
[0x1C, 0x26, 0x00, 0, 1, "", "Status Solarregler", DISP], # 4:'', 
[0x1E, 0x26, 0x00, 0, 1, "", "Status Schutzfunktion", DISP], # 0=Normalbetrieb, 6=Puffer Übertemperatur

[0x00, 0x26, 0x00, 0, 1, "", "Betriebsart", PARAM|DISP], # 0:'Not-Aus', 1:'Standby' 2:'Automatik', 3:'Hand: Entlüftung', 4:'Handfunktion 2'
[0x08, 0x26, 0x02, 0, 1, "%", "Pumpenleistung minimal", PARAM],
[0x07, 0x26, 0x02, 0, 1, "%", "Pumpenleistung maximal", PARAM],
[0x25, 0x26, 0x00, 0, 1, "", "Rückkühlung über Solarkreis", PARAM],

[0x10, 0x25, 0x02, 0, 1, "", "Ausgangstest", PARAM], # 0=Aus, 1=Ein
[0x11, 0x25, 0x02, 0, 1, "", "Pumpe", PARAM], # 0=Aus, 1=Ein
[0x12, 0x25, 0x02, 0, 1, "", "MFA1", PARAM], # 0=Aus, 1=Ein
[0x13, 0x25, 0x02, 0, 1, "%", "PWM Signal", PARAM],

[0x2D, 0x26, 0x00, 0, 1, "", "Solar Ertragszähler rückgesetzt", 0], # byte3: 0=5?
[0x2D, 0x26, 0x03, 0, 1, "", "Solar Ertragszähler rückgesetzt Tag", 0], # byte3: 0=5? 2=Jahr, 3=Tag, 4=Monat
[0x2D, 0x26, 0x04, 0, 1, "", "Solar Ertragszähler rückgesetzt Monat", 0],
[0x2D, 0x26, 0x02, 0, 1, "", "Solar Ertragszähler rückgesetzt Jahr", 0],

[0x37, 0x26, 0x00, 0, 1, "", "Solar Zähler rückgesetzt", 0], # byte3: 0=5?
[0x37, 0x26, 0x03, 0, 1, "", "Solar Zähler rückgesetzt Tag", 0], # byte3: 0=5? 2=Jahr, 3=Tag, 4=Monat
[0x37, 0x26, 0x04, 0, 1, "", "Solar Zähler rückgesetzt Monat", 0],
[0x37, 0x26, 0x02, 0, 1, "", "Solar Zähler rückgesetzt Jahr", 0],

[0x00, 0x00, 0x00, 0, 1, "", "", 0],
[0x00, 0x26, 0x02, 0, 1, "", "", 0],
[0x08, 0x26, 0x00, 0, 1, "", "", 0],
[0x07, 0x26, 0x00, 0, 1, "", "", 0],
[0x38, 0x26, 0x00, 0, 1, "", "", 0],
[0x2E, 0x26, 0x00, 0, 1, "", "", 0],

],

[0x584, 0x43, "Solar Zähler"],
[
[0x29, 0x26, 0x02, 2, 0.01, "kWh", "Solarertrag (Vortag)", DISP],
[0x34, 0x26, 0x02, 1, 0.1, "h", "Solar Gesamtzähler Betriebsstunden", TABLE],
[0x36, 0x26, 0x02, 1, 0.1, "h", "Solar Zähler seit Rücksetzen Betriebsstunden", TABLE],
[0x2A, 0x26, 0x02, 2, 0.01, "kWh", "Solarertrag (heute)", DISP],
[0x39, 0x26, 0x02, 2, 0.01, "kWh", "Rückkühlen ?", 0],
[0x40, 0x26, 0x02, 2, 0.01, "kWh", "Rückkühlen ?", 0],
[0x41, 0x26, 0x02, 2, 0.01, "kWh", "Rückkühlen ?", 0],
[0x42, 0x26, 0x02, 2, 0.01, "kWh", "Rückkühlen ?", 0],
[0x2B, 0x26, 0x02, 2, 0.01, "kWh", "Solarertrag Gesamtzähler", TABLE],
[0x2C, 0x26, 0x02, 2, 0.01, "kWh", "Solarertragszähler seit Rücksetzen", TABLE],
],

[0x602, 0x2B, "System"],
[
[0x2C, 0x25, 0x00, 1, 0.1, "°C", "Wärmeanforderung Heizung", DISP],
[0x2D, 0x25, 0x00, 1, 0.1, "°C", "Wärmeanforderung Warmwasser", DISP],

[0x05, 0x27, 0x01, 0, 1, "", "", 0],
[0x28, 0x25, 0x02, 0, 1, "", "", 0],

#[0x0A, 0x27, 0x00, 0, 1, "", "", 0],
#[0x2B, 0x27, 0x00, 0, 1, "", "", 0],
[0x2E, 0x25, 0x00, 0, 1, "", "", 0],
[0x2F, 0x25, 0x00, 0, 1, "", "", 0],
#[0x, 0x00, 0x00, 1, 0.1, "", "Wärmeanforderung Heizkreis FBH", 0],
],

[0x6C2, 0x2B, "WTC"],
[
[0x1E, 0x26, 0x01, 0, 1, "", "", 0], # Außentemperatur ?
[0x1E, 0x26, 0x02, 1, 0.1, "°C", "Außentemperatur", SIGNED | DISP | DB],
[0x29, 0x2A, 0x01, 0, 1, "", "", 0], # Warmwassertemperatur ?
[0x29, 0x2A, 0x02, 1, 0.1, "°C", "Warmwassertemperatur", DISP | DB],
[0x98, 0x26, 0x01, 2, 0.01, "%", "Sollleistung WE0", DISP],
[0x97, 0x26, 0x01, 1, 0.1, "°C", "Vorlauftemperatur VPT WE0", 0],
[0x99, 0x26, 0x01, 1, 0.1, "°C", "Rücklauftemperatur VPT WE0", 0],

[0x1F, 0x25, 0x01, 0, 1, "", "", 0],
[0x1F, 0x25, 0x02, 0, 1, "", "", 0],
[0x20, 0x25, 0x01, 0, 1, "", "", 0],
[0x20, 0x25, 0x02, 0, 1, "", "", 0],
[0x94, 0x26, 0x01, 0, 1, "", "", 0],

#[0x00, 0x00, None, 1, 0.1, "°C", "X ", 0],
],

[0x6C2, 0x2F, "WTC"],
[
[0x20, 0x25, 0x02, 0, 1, "", "", 0],
[0x94, 0x26, 0x01, 0, 1, "", "", 0], # Brenner Status 1=Brenner Aus, 10=Brenner Ein HZG, 15=Brenner Ein WW, Betriebsphase Brenner WE0
[0x1F, 0x25, 0x02, 0, 1, "", "", 0],
],

[0x6C3, 0x2B, "Heizkreis"],
[
[0x21, 0x26, 0x03, 1, 0.1, "°C", "Wärmeanforderung HK", 0],
[0x21, 0x26, 0x04, 1, 0.1, "°C", "Wärmeanforderung HK", 0],
[0x21, 0x26, 0x05, 1, 0.1, "°C", "Wärmeanforderung HK", 0],

[0x21, 0x26, 0x01, 0, 1, "", "", 0],
[0x21, 0x26, 0x02, 0, 1, "", "", 0],
],

[0x6C3, 0x2F, "Heizkreis"],
[
[0x21, 0x26, 0x07, 0, 1, "", "Status FBH", DISP], # 1=Frostschutz ein, 2=Eingang H1 Standby, 3=Normal
[0x21, 0x26, 0x00, 0, 1, "", "", 0], # 7?
[0x21, 0x26, 0x06, 0, 1, "", "", 0], # 1?
],

[0x6C4, 0x2B, "Solar"],
[
[0x60, 0x26, 0x02, 1, 0.1, "°C", "Puffer oben", 0],
[0x61, 0x26, 0x02, 1, 0.1, "°C", "Puffer unten", 0],
[0x97, 0x27, 0x02, 1, 0.1, "°C", "Speicher unten", 0],
[0x95, 0x27, 0x00, 0, 1, "W", "Leistung", 0],
[0x96, 0x27, 0x00, 0, 1, "", "", 0], # Zähler ?

[0x60, 0x26, 0x01, 0, 1, "", "", 0],
[0x60, 0x26, 0x03, 0, 1, "", "", 0],
[0x60, 0x26, 0x04, 0, 1, "", "", 0],
[0x61, 0x26, 0x01, 0, 1, "", "", 0],
[0x61, 0x26, 0x03, 0, 1, "", "", 0],
[0x61, 0x26, 0x04, 0, 1, "", "", 0],
[0x97, 0x27, 0x01, 0, 1, "", "", 0],
[0x97, 0x27, 0x03, 0, 1, "", "", 0],
[0x97, 0x27, 0x04, 0, 1, "", "", 0],
],

[0x6C4, 0x2F, "Solar"],
[
[0x94, 0x27, 0x00, 0, 1, "", "Status Solarregler", DISP],
[0xA2, 0x27, 0x00, 0, 1, "", "", 0], # ['3', '10:28', '0', '11:40', '3', '12:05', '0', '16:36', '3', '12:05', '0', '14:3

[0x60, 0x26, 0x00, 0, 1, "", "", 0],
[0x61, 0x26, 0x00, 0, 1, "", "", 0],
[0x93, 0x27, 0x00, 0, 1, "", "", 0],
[0x97, 0x27, 0x00, 0, 1, "", "", 0],
],

[0x604, 0x2B, "Solar"],
[
[0x02, 0x26, 0x00, 1, 0.1, "°C", "Speicher unten", 0],

[0x01, 0x25, 0x01, 0, 1, "", "", 0],
[0x01, 0x52, 0x01, 0, 1, "", "Pufferregelung", 0],
[0x02, 0x25, 0x01, 0, 1, "", "", 0], # Pufferregelung 0x10='P1', '0x0C'=P2
[0x00, 0x52, 0x01, 0, 1, "", "", 0],
#[0x, 0x25, 0x00, 0, 1, "", "", 0],
],

]

# Liste für Werte 'Aus', 'Ein'
code_text_onoff = [
[0x584, 0x4F, 0x10],
[0x584, 0x4F, 0x11],
[0x584, 0x4F, 0x12],
[0x584, 0x4F, 0x25],
[0x583, 0x4F, 0x18],
[0x583, 0x4B, 0xA2],
[0x583, 0x4F, 0xA3],
[0x582, 0x4F, 0x4E],
[0x582, 0x4F, 0x4F],
[0x583, 0x4F, 0x7C],
[0x583, 0x4F, 0x8A],
[0x583, 0x4F, 0x46],
]

# Liste für alle anderen Werte
code_text_variable = [
[0x181, 0x00, 0x00], {0:'Sonntag', 1:'Montag', 2:'Dienstag', 3:'Mittwoch', 4:'Donnerstag', 5:'Freitag', 6:'Samstag'},
[0x201, 0x00, 0x00], {0:'Aus', 1:'Standby', 2:'Sommer', 3:'Automatik'},
[0x582, 0x4F, 0x16], {0:'Leistungsproportional', 4:'Volumenstromregelung', 5:'Konstante Pumpenleistung'},
[0x583, 0x4F, 0x19], {0:'Aus', 1:'Pumpe', 2:'Mischer Auf', 3:'Mischer Zu'},
[0x582, 0x4F, 0x30], {0:'Standby', 1:'Aus', 10:'Heizbetrieb', 15:'Warmwasserbetrieb', 101:'Kaminfeger', 104:'Wartung'},
[0x583, 0x4F, 0x33], {1:'Standby', 2:'Zeitprogramm 1', 3:'Zeitprogramm 2', 4:'Zeitprogramm 3', 5:'Sommer', 6:'Komfort', 7:'Normal', 8:'Absenk'},
[0x583, 0x4F, 0x37], {0:'Vorrang', 1:'Parallel', 2:'Gleitend'},
[0x582, 0x4F, 0x6A], {0:'Leistungsproportional', 4:'Volumenstromregelung', 5:'Proportionaldruck Stufe 1', 6:'Proportionaldruck Stufe 2', 7:'Proportionaldruck Stufe 3', 8:'Konstantdruck Stufe 1', 9:'Konstantdruck Stufe 2', 10:'Konstantdruck Stufe 3', 11:'Proport.-druck Auto-Adaption', 12:'Konstantdruck Auto-Adaption'},
[0x583, 0x4F, 0x6E], {0:'sehr leicht', 1:'mittel leicht', 2:'leicht', 3:'schwer', 4:'mittel schwer', 5:'sehr schwer'},
[0x583, 0x4F, 0x86], {0:'Frost', 1:'Absenk'},

[0x583, 0x4F, 0x7E], {1:'1 ?', 5:'Urlaub', 6:'Zeitprogramm 1', 7:'Zeitprogramm 2', 8:'Zeitprogramm 3', 21:'Normal', 22:'Absenk', 24:'Frostschutz'},

[0x583, 0x4F, 0x87], {0:'Aus', 1:'Party / Heizpause', 2:'Heizpause'},
[0x583, 0x4F, 0x89], {1:'Absenk', 2:'Normal', 3:'Komfort'},
[0x583, 0x4F, 0xA6], {1:'Funktionsheizen', 2:'Belegreifheizen', 3:'Funktions- und Belegreifheizen'},
[0x584, 0x4F, 0x00], {0:'Not-Aus', 1:'Standby', 2:'Automatik', 3:'Hand: Entlüftung', 4:'Handfunktion 2'},
[0x584, 0x4F, 0x1C], {0:'Aus', 1:'Start', 2:'Sonderphase', 3:'Startphase', 4:'Regelung'},
[0x6C4, 0x2F, 0x94], {0:'Aus', 1:'Start', 2:'Sonderphase', 3:'Startphase', 4:'Regelung'},
[0x604, 0x2B, 0x01], {0:'Pufferregelung P2', 1:'Pufferregelung P1'}, # ?'Pufferumschaltung P1/P2'
[0x584, 0x4F, 0x1E], {0:'Normalbetrieb', 3:'Übertemperatur', 6:'Puffer Übertemperatur'},

[0x6C3, 0x2F, 0x21], {1:'Frostschutz ein', 2:'Eingang H1: Standby', 3:'Normal'},


#[0x, 0x, 0x], {0:'', 1:''},
#[0x, 0x, 0x], {0:'', 1:''},

#[{ 'code':[], 0:'', 1:''},
]
