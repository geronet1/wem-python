#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, smbus, sys, threading, can, curses, os
from curses import wrapper
from curses.textpad import Textbox, rectangle

import wem
from wem_codes import *
from realtimesocket import *

logfile = None
logfile_path = "log.csv"
last_time = 0

#	msg_index			 						   data_index / byte_index
# [ arbitration_id, num, [data_num, data_num ..], [m.data, m.data, ...] ]
id_list = []
data = []

delay = 0.00
cursor_x = 0
cursor_y = 0
pause = False
log = False # write to logfile
cut = False # display and send

DEBUG = 0
PIPE_PATH = "can_log.fifo"

def debug(*args):
	wem.debug(*args)

def sort():
	global id_list
	# Nachrichten sortieren
	id_list = sorted(id_list, key=lambda x: (x[0]))
	
	for msg in id_list:
		# Zähler resetten
		msg[1] = 0
		msg[2] = [0 for item in msg[2]]
		# Datenbytes sortieren
		msg[3] = sorted(msg[3], key=lambda x: (x[0]))

def draw_header():
	s = " ID "
	if log:
		s += 'L'
	else:
		s += " "

	if cut:
		s += "T"
	else:
		s += " "
		
	wem.screen.addstr(0, 0, s + "#   %1.2f   #  0\t\t\t\t   #  1\t\t\t\t   #  2\t\t\t\t   #  3\t\t\t\t   #  4" % (delay), curses.color_pair(1)| curses.A_BOLD)

def redraw():
	try:
		wem.screen.clear()
		# redraw all elements
		y = 0
		draw_header()
		for i in id_list:
			color = 0
			wem.screen.addstr(y + 1, 0, "%03X (%4d)" % (i[0], i[1]), color)
			x = 0
			for i,j in zip(i[2], i[3]):
				color = 0
				if y == cursor_y and x == cursor_x:
					color = curses.color_pair(5)
				
				hex_data = "".join("%02X " % b for b in j)
				wem.screen.addstr("\t(%3d) " % (i) + hex_data, color)
				x += 1
			y += 1
	except curses.error:
		pass

def analyze(scr, m):	
	global id_list, data, num
	mid = m.arbitration_id
	msg_index = 0
			
	found = False
	for i in id_list:
		if mid == i[0]:
			found = True
			break
		msg_index += 1
		
	if not found:
		id_list.append([mid, 1, [1], [m.data]])
		scr.move(msg_index+1, 0)
		scr.clrtoeol()

	data_index = 0
	data_found = False
	
	for i in id_list[msg_index][3]:
		if i[0] == m.data[0]:
			data_found = True
			break
		else:
			data_index += 1

	if not data_found:
		id_list[msg_index][2].append(0)
		id_list[msg_index][3].append(m.data)
		data_index = 0
		for i in id_list[msg_index][3]:
			if i[0] == m.data[0]:
				break
			else:
				data_index += 1

	# Paketzähler inkrementieren
	id_list[msg_index][1] += 1
	# Datenzähler inkrementieren
	id_list[msg_index][2][data_index] += 1

	color = 0
	if msg_index == cursor_y:
		color = curses.color_pair(5) # magenta

	scr.addstr(msg_index+1, 0, "%03X (%4d)" % (mid, id_list[msg_index][1]), color)

	data_index_num = 0
	for i in id_list[msg_index][3]:
		color = 0
		scr.addstr("\t")
		if data_index == data_index_num:
			color = curses.color_pair(2) | curses.A_BOLD # blau
		scr.addstr("(%3d)" % (id_list[msg_index][2][data_index_num]), color)

		if msg_index == cursor_y and data_index_num == cursor_x:
			color = curses.color_pair(5) # magenta

		scr.addstr(" ", color) # 

		byte_index = 0
		for b in i:
			byte_color = color
			if data_index == data_index_num:
				if m.data[byte_index] != id_list[msg_index][3][data_index][byte_index]:
					byte_color = curses.color_pair(3) # grün
				
				id_list[msg_index][3][data_index][byte_index] = m.data[byte_index]
				
			scr.addstr("%02X" % id_list[msg_index][3][data_index_num][byte_index], byte_color)
			scr.addstr(" ", color)			
			byte_index += 1
			
		data_index_num += 1
	
	if msg_index != cursor_y or data_index != cursor_x or len(id_list) < 1:
		scr.refresh()
		return

	scr.move(len(id_list)+3, 0)
	if len(data) != 0:
		if data[-1] == m.data:
			return
	
	data.append(m.data)
	max_y, max_x = scr.getmaxyx()
	
	# Liste zu lang für Terminal?
	if len(id_list) + 3 + len(data) > max_y:
		data.pop(0)
		
	# Bytes der Nachricht
	for i, d in enumerate(data):
		byte_index = 0
		for b in d:
			byte_color = 0
			if i > 0:
				if byte_index < len(data[i-1]):
					if b != data[i-1][byte_index]:
						byte_color = curses.color_pair(3) # grün

			scr.addstr("%02X" % b, byte_color)
			scr.addstr(" ")
			byte_index += 1

		scr.addstr("\t")	
		# Dezimalzahlen einzeln
		byte_index = 0
		for b in d:
			byte_color = 0
			if i > 0:
				if byte_index < len(data[i-1]):
					if b != data[i-1][byte_index]:
						byte_color = curses.color_pair(3) # grün

			scr.addstr("%03d" % b, byte_color)
			scr.addstr(" ")
			byte_index += 1

		# Interpretierte Dezimalzahlen
		v = int.from_bytes(d[2:4], byteorder='little', signed=True)
		scr.addstr("\t%d" % v)
		v = int.from_bytes(d[3:5], byteorder='little', signed=True)
		scr.addstr("\t%d" % v)
		v = int.from_bytes(d[4:], byteorder='little', signed=True)
		scr.addstr("\t%d" % v)
		v = int.from_bytes(d[4:6], byteorder='little', signed=True)
		scr.addstr("\t%d" % v)
		v = int.from_bytes(d[6:8], byteorder='little', signed=True)
		scr.addstr("\t%d" % v)


		
		scr.addstr("\n")	
	scr.refresh()
	
def textbox(stdscr):
	stdscr.clear()
	stdscr.addstr(0, 0, "Enter new filter: (hit Ctrl-G to send)")
	editwin = curses.newwin(5,20, 2,1)
	rectangle(stdscr, 1,0, 1+5+1, 1+30+1)

	box = Textbox(editwin)
	curses.curs_set(1)
	stdscr.refresh()
	# Let the user edit until Ctrl-G is struck.
	box.edit()
	curses.curs_set(0)

	# Get resulting contents
	return box.gather()
	
def write_logfile(m, delta):
	l = []
	for i in m.data:
		l.append(",%02X" % i)
	
	dec = "%0.2f" % (time.time() - int(time.time()))
	dec = dec.split('.')
	t = time.strftime("%H:%M:%S.", time.localtime()) + dec[1]
	d = '%0.4f' % delta
	text = t + ',' + d + ',%03X' % (m.arbitration_id) + ''.join(l)
	logfile.write(text + '\n')
	logfile.flush()
	
def main(stdscr):
	global delay, id_list, data, cursor_x, cursor_y, pause, logfile, log, cut, DEBUG
	
	# An jedes Element 'None' als Value dranhängen
	for i in range(0, len(codes), 2):
		for j in range(0, len(codes[i+1])):
			codes[i+1][j].append(None)

	# Kommandozeile prüfen
	if len(sys.argv) > 1:
		if sys.argv[1] == "-d":
			DEBUG = True

	logfile = open(logfile_path, 'w')

	if DEBUG:
		if not os.path.exists(PIPE_PATH):
			os.mkfifo(PIPE_PATH)
		pipe = open(PIPE_PATH, "w")

	# Socket öffnen
	wem.rsocket = RealTimeSocket(HOST, PORT)
	t = threading.Thread(target=wem.rsocket_listen)
	t.daemon=True
	t.start()

	wem.bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=50000)
	wem.screen = curses.initscr()
	curses.start_color()
	curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
	curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
	curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_RED)
	curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
	curses.curs_set(0)
	wem.screen.nodelay(True)
	redraw()

	filters = [{"can_id": 0x6C2, "can_mask": 0xFFF}]
	#bus.set_filters(filters)

	last_time = 0

	try:
		while True:
			m = wem.bus.recv(0.2)
			if m:
				try:
					ret = wem.decode(m)
					if isinstance(ret, can.message.Message) or cut:
						delta = m.timestamp - last_time
						last_time = m.timestamp
						# not found, examine message
						debug("%02.4f" % (delta) + " " + wem.print_canm(m))
						if not pause:
							analyze(wem.screen, m)
						if log:
							write_logfile(m, delta)
					
					if isinstance(ret, str):
						# parser found code, send it
						wem.rsocket.send(ret + "\n")

				except curses.error:
			 		pass
			
			time.sleep(delay)
			c = wem.screen.getch()
			if c == ord('q'):
				break
			elif c == ord(' '):
				pause = not pause
			elif c == ord('l'):
				log = not log
				draw_header()
			elif c == ord('t'):
				cut = not cut
				draw_header()
			elif c == ord('s'):
				sort()
				redraw()
			elif c == ord('+'):
				delay += 0.01
				draw_header()
			elif c == ord('-'):
				draw_header()
				delay -= 0.01
				if delay <= 0:
					delay = 0.0001
			elif c == ord('f'):
					f = textbox(wem.screen).split()
					if not f:
						bus.set_filters(0)						
					elif len(f) == 2:
						filters = [{"can_id": int(f[0], 0), "can_mask": int(f[1], 0)}]
						wem.bus.set_filters(filters)
						wem.screen.clear()
						wem.screen.addstr("New filter: 0x%03X mask: 0x%03X" % (filters[0]["can_id"], filters[0]["can_mask"]))
						wem.screen.refresh()
						time.sleep(1)
					id_list, data = [], [] 
					cursor_y, cursor_x = 0, 0
					redraw()
			elif c == ord('c'):
				id_list = []
				data = []
				redraw()
			elif c == curses.KEY_DOWN:
				cursor_y += 1
				if cursor_y > len(id_list) - 1:
					cursor_y = len(id_list) - 1
				else:
					data = []
					redraw()
			elif c == curses.KEY_UP:
				cursor_y -= 1
				if cursor_y < 0:
					cursor_y = 0
				else:
					data = []
					redraw()
			elif c == curses.KEY_RIGHT:
				cursor_x += 1
				data = []
				redraw()
			elif c == curses.KEY_LEFT:
				cursor_x -= 1
				if cursor_x < 0:
					cursor_x = 0				
				else:
					data = []
					redraw()

	except KeyboardInterrupt:
		pass
	if DEBUG:
		pipe.close()	
	logfile.close()
	wem.rsocket.close()
	curses.endwin()
	wem.bus.shutdown()

wrapper(main)
