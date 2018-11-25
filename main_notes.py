from math import sqrt, fabs
from utime import ticks_ms, ticks_diff, sleep
from ucollections import deque
import debounce as db 
from machine import Pin, ADC, UART
import dfplayer as df

import hammer_bpm_nodemcu as hb

BPM_FILE = 'bpm_list.tsv'
SAMPLE_SIZE = 4 
STDEV_THRESH = 0.05 
PCT_CHANGE_TRIGGER = 0.10
#SENSOR_PIN = Pin(5, Pin.IN, Pin.PULL_UP)
SENSOR_PIN = ADC(0)
LED_PIN = Pin(16, Pin.OUT)

DF_SERIAL_PIN = UART(1, 9600)
DF_SERIAL_PIN.init(9600, bits=8, parity=None, stop=1)
DF_BUSY_PIN = Pin(0, Pin.IN, Pin.PULL_UP)


delay_obj = hb.Delays(STDEV_THRESH, SAMPLE_SIZE)
song_obj = hb.Songs(BPM_FILE, PCT_CHANGE_TRIGGER)
     
# sensor_switch = db.DebouncedSwitch(SENSOR_PIN, hb.strike_event_handler, (delay_obj, song_obj))
sensor_switch = db.DebouncedSwitchAnalog(SENSOR_PIN, 100, hb.strike_event_handler, (delay_obj, song_obj))

