#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, signal, time
import paho.mqtt.client as paho

verbose = True
mqtt_client = None

MQTT_ADDRESS = '127.0.0.1'
MQTT_PORT = 1883
MQTT_USER = 'wem'
MQTT_PASSWORD = 'wem'
#MQTT_TOPIC =  'solar'
MQTT_CLIENT_ID = 'wem'

mqtt_error = {
	0: 'Connection successful',
	1: 'Incorrect protocol version',
	2: 'Invalid client identifier',
	3: 'Server unavailable',
	4: 'Bad username or password',
	5: 'Not authorised'
}

def debug(*args, end='\n'):
	if verbose:
		for i in list(args):
			print(i, end='')
		print(end, end='')

def on_connect(client, userdata, flags, rc):
	if rc == 0:
		debug('Connected to mqtt broker')
#		client.subscribe(MQTT_TOPIC)
	else:
		print('mqtt connection failed: ' + mqtt_error[rc])

def on_message(client, userdata, msg):
	if verbose:
		print(msg.topic + ' ' + str(msg.payload))
	
	if msg.payload == '':
		return

def publish(topic, value):
	ret = mqtt_client.publish(topic, value)#, retain=True)
	if ret.rc != 0:
		print('Error: mqtt publish failed')

def exit_handler(sig, frame):
	if verbose:
		print("Signal:" + str(sig))
	exit()
	
def init():
	global mqtt_client
	signal.signal(signal.SIGTERM, exit_handler)
	signal.signal(signal.SIGINT,  exit_handler)
	
	mqtt_client = paho.Client(MQTT_CLIENT_ID)
	mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
	mqtt_client.on_connect = on_connect
	mqtt_client.on_message = on_message

	mqtt_client.connect(MQTT_ADDRESS, MQTT_PORT)
	mqtt_client.loop_start()

def exit():
	mqtt_client.disconnect()
	mqtt_client.loop_stop()
	