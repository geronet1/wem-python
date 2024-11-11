#!/usr/bin/env python3
# -*- coding: utf-8 -*-
PATH="/home/stefan/scripts/"

import sys
sys.path.append(PATH)
import telegram

import datetime, time, smbus, threading, can, os, subprocess
import curses
from curses import wrapper
from realtimesocket import *
from wem_codes import *
from influxdb import InfluxDBClient
import mqtt
MQTT_TOPIC = "solar"

ifclient = 0
bus, screen, rsocket, logfile = None, None, None, None

class wem():
	data = ""
	vpt_182_vorlauf = ""
	status = 0
	time = None
	at = ""
	unknown = ""
	waermeanforderung_heizkreis = ""
	puffer_oben = ""
	vpt_241_vorlauf = ""
	warmwasser = ""
	wtc_betrieb = None

wem_errors = [] # format:[ [id, time, error, data], [..], .. ]
DEBUG = 0
FILE_PATH = PATH + "can.log"

def get_code():
	# get_code = gibt alle Elemente einzeln aus der Codeliste als Liste zurück
	# [OID, BYTE0, OID_NAME, BYTE1, BYTE2, BYTE3, PREC, FACTOR, UNIT, NAME, FLAGS, VALUE]
	for i in range(0, len(codes), 2):
		for code in codes[i+1]:
			yield codes[i] + code

def get_code_text(oid, code0, code1, key):
	# get_code_text = gibt den Text als String anhand des Codes und des Werts zurück
	# [code, {0='Aus', 1='Ein'}, code, {}, ...]
	if [oid, code0, code1] in code_text_onoff:
		if key == 0:
			return 'Aus'
		else:
			return 'Ein' if key == 1 else key
	try:
		i = code_text_variable.index([oid, code0, code1])
		return code_text_variable[i+1].get(key, key)
	except ValueError:
		return key

def find_code(oid, bytes):
	# find_code = gibt den Index des Elements aus der Codeliste zurück
	#			  das oid und 'c' mit 4 bytes entspricht:
	for i in range(0, len(codes), 2):
		if codes[i][0:2] == [oid, bytes[0]]:
			for j in range(0, len(codes[i+1])):
				if codes[i+1][j][0:3] == [x for x in bytes[1:4]]:
					return codes[i] + codes[i+1][j], i, j
	return None, None, None

def debug(*args, end='\n'):
    if DEBUG == True:
        for i in list(args):
            print(i, end='')
        print(end, end='')

def pdb():
	curses.nocbreak()
	screen.keypad(0)
	curses.echo()
	curses.endwin()
	breakpoint()

def clear():
	for i in range(0, len(codes), 2):
		for j in range(0, len(codes[i+1])):
			codes[i+1][j][VALUE-3] = None

def refresh():
	global rsocket
	# refresh = Alle Werte aus der code-Liste an webrsocket senden
	td = wem_time_date_day(None)
	if isinstance(td, str):
		if td:
			rsocket.send(td)

	text = 'wem_182' + TZ + wem.data + '\n'
	text += 'wem_182_vpt_vorlauf' + TZ + wem.vpt_182_vorlauf + ' °C' + '\n'
	v = get_code_text(0x201, 0x00, 0x00, wem.status)
	text += 'wem_201_status' + TZ + str(v) + '\n'
	text += 'wem_at' + TZ + wem.at + ' °C' + '\n'
	text += 'wem_unknown' + TZ + wem.unknown + '\n'
	text += 'wem_241_waermeanforderung_heizkreis' + TZ + wem.waermeanforderung_heizkreis + ' °C' + '\n'
	text += 'wem_puffer_oben' + TZ + wem.puffer_oben + ' °C' + '\n'
	text += 'wem_241_vpt_vorlauf' + TZ + wem.vpt_241_vorlauf + ' °C' + '\n'
	text += 'wem_warmwasser' + TZ + wem.warmwasser + ' °C' + '\n'
	rsocket.send(text)

	for code in get_code():
		refresh_code(code)
			
def refresh_code(code):
	global rsocket
	if code[VALUE] != None:
		try:
			index = "a%03X-%02X-%02X-%02X-%02X" % ((code[OID], code[BYTE0]) + tuple(code[BYTE1:BYTE3+1]))
			if isinstance(code[VALUE], list):
				value = code[VALUE]
			else:
				value = get_code_text(code[OID], code[BYTE0], code[BYTE1], code[VALUE])
			text = index + TZ + str(value) + (' ' + code[UNIT] if code[UNIT] else '')
			#debug(text)
			rsocket.send(text + "\n")
			send_mqtt(index, value)
		except TypeError:
			debug("TypeError: wrong format in code:" + str(code))
			breakpoint()

def send_mqtt(index, value):
	if index == "a584-4B-04-25-02":
		mqtt.publish(MQTT_TOPIC + '/' + 'Kollektor', value)
	elif index == "a584-4B-21-25-02":
		mqtt.publish(MQTT_TOPIC + '/' + 'Leistung', value)

def update():
	# update = Alle Werte aus der code-Liste über den can-Bus anfragen
	for code in get_code():
		request(code[OID] & 0x00F, code[BYTE1:BYTE3+1])
		time.sleep(0.1)

def update_disp():
	# update = Alle Werte mit Flag 'DISP' oder 'TABLE' aus der code-Liste über den can-Bus anfragen
	for code in get_code():
		if code[FLAGS] & DISP or code[FLAGS] & TABLE:
			request(code[OID] & 0x00F, code[BYTE1:BYTE3+1])
			time.sleep(0.1)

def wem_time_date_day(time_date):
	if time_date != None:
		wem.time = time_date
			
	if wem.time == None:
		return

	t = time.strftime("%H:%M", wem.time)
	d = time.strftime("%d.%m.%Y", wem.time)
	wt = get_code_text(0x181, 0x00, 0x00, int(time.strftime("%w", wem.time)))
	return 'wem_time' + TZ + t + '\n' + 'wem_date' + TZ + d + '\n' + 'wem_day' + TZ + wt + '\n'

def rsocket_listen():
	global rsocket
	while True:
		data = rsocket.receive()
		if data:
			commands = data.decode().split('\n')
			for command in commands:
				if command != '':
					debug("received command: " + command)
				if command == "refresh":
					refresh()
				elif command == "update":
					update()
				elif command == "update_disp":
					update_disp()
				elif command == "clear":
					clear()
				elif command.startswith("request"):
					try:
						c = command.split(TZ)[1].split('-')
						id = int(c[0], 16) & 0x00F
						request(id, [int(i, 16) for i in c[2:]])
					except (IndexError, ValueError) as error:
						debug(str(error) + ": wrong command format")

def print_canm(m, sep=' '):
	l = []
	for i in m.data:
		l.append("%02X" % i + sep)	
	return "[%03X]" % (m.arbitration_id) + sep + ''.join(l)

def request(id, bytes):
	# Request über CAN Bus senden
	# id = Nummer des Geräts (1-4)
	# bytes = Liste: [BYTE1, BYTE2, BYTE3]
	if id < 1 or id > 4 or len(bytes) != 3:
		return
	oid = 0x600 + id
	data = [0xA4] + bytes + [0x40, 0x40, 0x00, 0x00]
	m = can.Message(arbitration_id=oid, is_extended_id=False, data=data)
	debug("can.Message:" + print_canm(m))
	try:
		bus.send(m, 2)
	except can.CanError:
		pass

def error_message(id, data):
	global wem_errors
	
	if data[0:2] == [0xFF, 0xFF]:
		# neuer Fehler
		error = [id, time.time(), data[5], data]

		wem_errors.append(error)
		telegram_notification(error)
				
#	else if data[0:2] == [0x00, 0x00]:
		# Fehler behoben/entstört
		#wem_errors

#	error = [1, time.time(), 23, [1,2,3,4,5,6]]


def telegram_notification(error):
#	global delay

	modul = ['WEM', 'WTC', 'EM Heizkreis', 'EM Solar']

	try:
		modul_name = modul[error[0] - 1]
	except IndexError:
		modul_name = 'ID ' + str(error[0])
		
	text = 'Störung ' + modul_name + ':' + str(error[2]) + \
	" Time: " + str(time.ctime(error[1])) + \
	" Data: " + str(error[3])

#	if delay[i] == 0:
	telegram.send(text)
#		delay[i] = 1


def receive(m):
	text = ''
	t = time.strftime('%d.%m/%H:%M:%S', time.localtime(time.time()))

	if m.arbitration_id & 0xFF0 == 0x700:
		# Heartbeat
		return
	elif m.arbitration_id & 0xFF0 == 0x080:
		# Fehlermeldung
		error_message(m.arbitration_id & 0x00F, m.data)
		return
	elif m.arbitration_id == 0x181:
		# Datum und Zeit
		try:
			time_date = (m.data[2] + 2000,
						m.data[3],
						m.data[4], 
						m.data[0],
						m.data[1], 
						0,
						m.data[5] - 1,
						0,
						-1)
			return wem_time_date_day(time_date)
		except IndexError:
			return
	elif m.arbitration_id == 0x182:
		# Status? und VPT Vorlauf
		x = " ".join("%02X" % x for x in m.data[0:5])
		#x = "%02X %02X %02X %02X %02X" % (m.data[0], m.data[1], m.data[2], m.data[3], m.data[4])
		if wem.data != x:
			wem.data = x
			text += 'wem_182' + TZ + x + '\n'
			x += '\t' + t + '\n'
			if logfile != None:
				logfile.write(x)
				logfile.flush()

		# VPT Vorlauf
		f = "%0.1f" % (int.from_bytes(m.data[5:7], byteorder='little', signed=True) / 10)
		if wem.vpt_182_vorlauf != f:
			wem.vpt_182_vorlauf = f
			text += 'wem_182_vpt_vorlauf' + TZ + f + ' °C' + '\n'
		
		if text:
			return text
		
	elif m.arbitration_id == 0x201:
		# Status
		if m.data[0] <= 3:
			if wem.status != m.data[0]:
				wem.status = m.data[0]
				v = get_code_text(0x201, 0x00, 0x00, m.data[0])
				text += 'wem_201_status' + TZ + str(v) + '\n'
	
		# Außentemperatur
		at = "%0.1f" % (int.from_bytes(m.data[1:3], byteorder='little', signed=True) / 10)
		if wem.at != at:
			wem.at = at
			text += 'wem_at' + TZ + at + ' °C' + '\n'
			mqtt.publish("solar/Aussentemperatur", at)
	
		# Statusbyte
		unknown = "0x%02X" % (m.data[3])
		if wem.unknown != unknown:
			wem.unknown = unknown
			text += 'wem_unknown' + TZ + unknown + '\n'
		
		if text:
			return text

	elif m.arbitration_id == 0x241:
		# Wärmeanforderung Heizkreis
		vs = "%0.1f" % (int.from_bytes(m.data[0:2], byteorder='little', signed=True) * 0.1)
		if wem.waermeanforderung_heizkreis != vs:
			wem.waermeanforderung_heizkreis = vs
			text += 'wem_241_waermeanforderung_heizkreis' + TZ + vs + ' °C' + '\n'
		# Puffer oben
		po = "%0.1f" % (int.from_bytes(m.data[2:4], byteorder='little', signed=True) * 0.1)
		if wem.puffer_oben != po:
			wem.puffer_oben = po
			text += 'wem_puffer_oben' + TZ + po + ' °C' + '\n'
		# VPT Vorlauf
		vv = "%0.1f" % (int.from_bytes(m.data[4:6], byteorder='little', signed=True) * 0.1)
		if wem.vpt_241_vorlauf != vv:
			wem.vpt_241_vorlauf = vv
			text += 'wem_241_vpt_vorlauf' + TZ + vv + ' °C' + '\n'
		# Warmwasser
		ww = "%0.1f" % (int.from_bytes(m.data[6:8], byteorder='little', signed=True) * 0.1)
		if wem.warmwasser != ww:
			wem.warmwasser = ww
			text += 'wem_warmwasser' + TZ + ww + ' °C' + '\n'
		
		if text:
			return text
		
	elif m.arbitration_id & 0xFF0 == 0x600:
		dev = m.arbitration_id & 0x00F
		# Anforderung
		if m.data[0] == 0xA4:
			id = m.data[1]
			data = m.data[2:]
			#text = 'REQ' + TZ + "%03X" % (m.arbitration_id) + '#%02X' % (id) + TZ + str(['%02X' % (x) for x in data])
			#debug(text)
			return #text

		# Wert setzen
		elif m.data[0] == 0x2F:
			id = m.data[1]
			data = m.data[2:]
			#text = 'SET' + TZ + "%03X" % (m.arbitration_id) + '#%02X' % (id) + TZ + str(['%02X' % (x) for x in data])
			#debug(text)
			return

	elif m.arbitration_id == 0x583:
		if m.data[0] != 0x43 or m.data[2] != 0x26:
			return m
		if m.data[1] == 0x3E:
			# Zeitprogramm 1
			# 113 Elemente:
			#index = m.data[3]
			#data = m.data[4:]
			return
		elif m.data[1] == 0x3F:
			# Zeitprogramm 2
			return
		elif m.data[1] == 0x51:
			# Zeitprogramm 3
			return
	elif m.arbitration_id == 0x582:
		if m.data[0] == 0x4F and m.data[1] == 0x30 and m.data[2] == 0x25 and m.data[3] == 0x00:
			# Betriebsphase WTC: Gaszähler stoppen
			value = int.from_bytes(m.data[4:6], byteorder='little', signed=False)
			if wem.wtc_betrieb != value:
				wem.wtc_betrieb = value
				rsocket.send('wtc_betrieb' + ':' + str(value) + '\n')
							
	return m


def decode(m):
	global code

	try:
		m = receive(m)
	except IndexError:
		return
	if m == None:
		return
	if isinstance(m, str):
		return m
	if len(m.data) < 2:
		return m
	code, i, j = find_code(m.arbitration_id, m.data[:4])
	if not code:
		return m

	length = None
	signed = False
	if code[FLAGS] & SIGNED:
		# signed value
		length = 6
		signed = True

	# Zahl aus Nachricht extrahieren
	value = int.from_bytes(m.data[4:length], byteorder='little', signed=signed)
	if value == 0x8000:
		# Sensor defekt
		value = 0
	else:
		value *= code[FACTOR]

	# Zahl mit Tabelle umwandeln in String falls vorhanden
	value_str = get_code_text(m.arbitration_id, m.data[0], m.data[1], value)

	# Code nicht gefunden?
	if not isinstance(value_str, str):
		value = round(value, code[PREC])
		#value = "{:.{prec}f}".format(value_num, prec=(code[PREC]))

	t = time.strftime('%d.%m/%H:%M:%S', time.localtime(time.time()))

	if code[NAME] == '':
		value = '%X' % value
		if not isinstance(code[VALUE], list):
			codes[i+1][j][VALUE-3] = code[VALUE] = [value, t]
			return refresh_code(code)
		else:
			if code[VALUE][-2] == value:
				return
			code[VALUE].extend([value, t])
			if len(code[VALUE]) > 20:
				code[VALUE] = code[VALUE][2:]
	
			codes[i+1][j][VALUE-3] = code[VALUE]
			return refresh_code(code)

	if value != code[VALUE]: # or True:
		codes[i+1][j][VALUE-3] = code[VALUE] = value
		return refresh_code(code)


def generate_js_html_table():
	# generate html-list from codes
	print("document.getElementById('wem').innerHTML += '")

	for i in range(0, len(codes), 2):
		print('<table class="tbox center"><tr>')
		print('<th colspan="3">' + codes[i][OID_NAME] + ' [%03X-%02X]</th>' % (codes[i][OID], codes[i][BYTE0]))

		for c in codes[i+1]:
			code = codes[i] + c
			index = 'a%03X-%02X-%02X-%02X-%02X' % (code[OID], code[BYTE0], code[BYTE1], code[BYTE2], code[BYTE3])
			# ID einsetzen falls Name leer
			name = index if code[NAME] == '' else code[NAME]
			name_class = 'wem_name_param' if code[FLAGS] & PARAM else ''
			value_class = 'wem_value wem_param' if code[FLAGS] & PARAM else 'wem_value'

			print('<tr><td class="' + name_class + '">' + name + '</td><td id="' + index + '" class="' + value_class + '" title="' + index + '"></td></tr>')
		
		print('</tr></table>')

	print("';", end='')
	sys.exit(0)

def generate_html_values():
	# generate html-value list from codes
	print(wem_system)
	
	for i in range(0, len(codes), 2):
		for c in codes[i+1]:
			code = codes[i] + c
			index = 'a%03X-%02X-%02X-%02X-%02X' % (code[OID], code[BYTE0], code[BYTE1], code[BYTE2], code[BYTE3])
			# ID einsetzen falls Name leer
			if code[FLAGS] & DISP:
				print('<div class="value wem tag" id="' + index + '" data-title="' + code[NAME] + '"></div>')
		
	sys.exit(0)

def init_can_bus():
	global bus
	bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=50000)

def read_can_bus():
	try:
		m = bus.recv()
		if m:
			ret = decode(m)
			if isinstance(ret, str):
				# parser found code, send it
				#debug(ret)
				rsocket.send(ret + "\n")
			elif isinstance(ret, can.message.Message):
				# not found, examine message
				#print(print_canm(ret))
				#debug2(print_canm(m))
				pass
					
	except OSError:
		bus.shutdown()
		time.sleep(3)
		init_can_bus()

def heartbeat_updater():
	while True:
		time.sleep(10)
		update_disp()

def heartbeat_influx_writer():
	while True:
		time.sleep(60)
		write_influx_temperature()
		write_influx_counter()

def write_influx_temperature():
	# take a timestamp for this measurement
	time = datetime.datetime.utcnow()

	# format the data as a single measurement for influx
	influx_body = [
		{
			"measurement": "temperature",
			"tags": {
				"device": "wem"
					},
			"time": time,
			"fields":
			{
			}
		}
	]

	# insert fields
	for code in get_code():
		if code[FLAGS] & DB and code[VALUE] != None:
			if code[PREC] == 0:
				value = int(code[VALUE])
			else:
				value = float(code[VALUE])
	
			influx_body[0]["fields"][code[NAME]] = value

	debug("influx:", "data:", influx_body)

	# write the measurement
	ifclient.write_points(influx_body)

def write_influx_counter():
	try:
		# "Solarertrag Gesamtzähler"
		value = int(codes[influx_solar_counter[0]][influx_solar_counter[1]][VALUE-3])# * codes[15][8][FACTOR-3])
	except (IndexError, TypeError):
		debug('Index Error Solarertrag Gesamtzähler')
		return
	
	if value != None:
		if value != write_influx_counter.value:
			write_influx_counter.value = value
			# take a timestamp for this measurement
			time = datetime.datetime.utcnow()

			# format the data as a single measurement for influx
			influx_body = [
				{
					"measurement": "counter",
					"tags": {
						"device": "wem"
							},
					"time": time,
					"fields":
					{
						"solar": value
					}
				}
			]

			# write the measurement
			ifclient.write_points(influx_body)

if __name__ == "__main__":
	# An jedes Element 'None' als Value dranhängen
	for i in range(0, len(codes), 2):
		for j in range(0, len(codes[i+1])):
			codes[i+1][j].append(None)
			# 'Solarertrag Gesamtzähler' Index in codes finden und speichern für influxdb
			if codes[i+1][j][NAME-3] == 'Solarertrag Gesamtzähler':
				influx_solar_counter=(i+1,j)
			
	# Kommandozeile prüfen
	if len(sys.argv) > 1:
		if sys.argv[1] == "-d":
			DEBUG = True
		elif sys.argv[1] == "-h":
			generate_js_html_table()
		elif sys.argv[1] == "-t":
			generate_html_values()

	logfile = open(FILE_PATH, "a")
	
	#Socket öffnen
	rsocket = RealTimeSocket(HOST, PORT)
	t1 = threading.Thread(target=rsocket_listen)
	t1.daemon=True
	t1.start()

	init_can_bus()
	
	# InfluxDB verbinden
	ifclient = InfluxDBClient(username='python', password='python', database='Haustechnik', retries=0)

	# MQTT verbinden
	mqtt.init()

	t2 = threading.Thread(target=heartbeat_updater)
	t2.daemon=True
	t2.start()

	write_influx_counter.value = 0
	t3 = threading.Thread(target=heartbeat_influx_writer)
	t3.daemon=True
	t3.start()

	try:
		while True:
			read_can_bus()
	except KeyboardInterrupt:
		mqtt.exit()
		bus.shutdown()
		logfile.close()
		rsocket.close()
		sys.exit()
