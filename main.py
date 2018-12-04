from machine import Pin, ADC, UART
from aswitch import AnalogSwitch
import hammer_bpm_nodemcu as hb
import uasyncio as asyncio

#-----
# BPM_FILE:           TSV file with bpm values in form: filename \t bpm
# SAMPLE_SIZE:        Number of inter-strike delay values to average for BPM calculation
# STDEV_THRESH:       Max threshold of standard dev of delay counts to trigger a bpm calculation
# PCT_CHANGE_TRIGGER: The percent change in BPM to trigger a song change

BPM_FILE = 'bpm_list.tsv'
SAMPLE_SIZE = 4
STDEV_THRESH = 0.05
PCT_CHANGE_TRIGGER = 0.10
# SENSOR_PIN = Pin(5, Pin.IN, Pin.PULL_UP)
SENSOR_PIN = ADC(0)
LED_PIN = Pin(16, Pin.OUT)

DF_SERIAL_PIN = UART(1, 9600)
DF_SERIAL_PIN.init(9600, bits=8, parity=None, stop=1)
DF_BUSY_PIN = Pin(0, Pin.IN, Pin.PULL_UP)


delay_obj = hb.Delays(STDEV_THRESH, SAMPLE_SIZE)
song_obj = hb.Songs(BPM_FILE, PCT_CHANGE_TRIGGER)
sensor_switch = AnalogSwitch(SENSOR_PIN, thresh=15)
sensor_switch.trigger_func(hb.strike_event_handler, args=(delay_obj, song_obj))
# sensor_switch = db.DebouncedSwitch(SENSOR_PIN, strike_event_handler, (delay_obj, song_obj))

async def killer():
    pin = Pin(5, Pin.IN, Pin.PULL_UP)
    while pin.value():
        await asyncio.sleep_ms(500)

loop = asyncio.get_event_loop()
loop.run_until_complete(killer())
