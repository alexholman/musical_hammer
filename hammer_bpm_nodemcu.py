#!/usr/bin/env python

from __future__ import print_function
from __future__ import division

import sys
from math import sqrt
import time
import os
from ucollections import deque
import debounce as db
from machine import Pin


'''
BPM_FILE:           TSV file with bpm values in form: filename \t bpm
SAMPLE_SIZE:        Number of inter-strike delay values to average for BPM calculation 
STDEV_THRESH:       Max threshold of standard dev of delay counts to trigger a bpm calculation
PCT_CHANGE_TRIGGER: The percent change in BPM to trigger a song change
'''

BPM_FILE = 'filename'
SAMPLE_SIZE = 4 
STDEV_THRESH = 0.05 
PCT_CHANGE_TRIGGER = 0.10
SENSOR_PIN = 1


def main(args):

    delay_obj = Delays(STDEV_THRESH, SAMPLE_SIZE)
    song_obj = Songs(BPM_FILE, PCT_CHANGE_TRIGGER)
    
    pin_obj = Pin(SENSOR_PIN, Pin.IN)
    led = Pin(ledpin, Pin.OUT)
    
    sensor_switch = DebouncedSwitch(pin_obj, strike_event_handler, (delay_obj, song_obj))
    
    while True:
        pass
                    #strike_event_handler(delay_obj, song_obj)


def strike_event_handler(args):
    delay_obj, song_obj = args
    delay_obj.add_event(time.time())
    bpm = delay_obj.calc_bpm()
    print('Detected bpm: {0}'.format(bpm))
    if bpm:
        song_obj.select_song(bpm)
        

class Delays(object):
    def __init__(self, stdev_thresh, sample_size):
        self.stdev_thresh = stdev_thresh
        self.delays = deque(maxlen=sample_size)
        self.last_timestamp = 0
        self.bpm = None

    def add_event(self, event_time):
        # debounce
        if event_time - self.last_timestamp < 0.2:
            return

        self.delays.append(event_time - self.last_timestamp )
        self.last_timestamp = event_time
    
        #print('delays: {0}'.format(self.delays))
        #print('stdev: {0}'.format(np.std(self.delays)))

    def calc_bpm(self):
        if len(self.delays) == self.delays.maxlen and stdev(self.delays) < self.stdev_thresh:
            bps = len(self.delays) / sum(self.delays)
            self.bpm = bps * 60
            return self.bpm
        else:
            return None

class Songs(object):
    def __init__(self, bpm_filename, pct_change_trigger):
        self.music_dir = os.path.dirname(os.path.abspath(bpm_filename))

        # Load BPM file
#Data[]
#i=0
#with open('FileName.csv','r') as file:
	#for line in file:
		#line_Str=line_Str.rstrip('\n')
		#line_Str=line_Str.rstrip('\r')
		#Data.append(line_Str.split(','))
        
        with open(bpm_filename, 'rb') as bpm_file:
            bpm_reader = csv.reader(bpm_file, delimiter='\t')
            self.bpm_dict = {float(bpm): name for name, bpm in bpm_reader}
            self.bpm_array = np.array(self.bpm_dict.keys())
        self.pct_change_trigger = pct_change_trigger
        null = open('/dev/null', 'wb')
        self.player = subprocess.Popen(['mpg123', '--mono', '--quiet', '--remote', '--fifo', '/tmp/fifo'],  stdin=null, stdout=null, stderr=null)

        self.now_playing = None
        self.now_playing_bpm = 0
        self.playing = False # Flag to store the play/pause state of the player because mpg123 uses a toggle mode

    #def _send_command(self, args):
        #print(' '.join(['echo',] + args))
        #self.command_pipe.append(' '.join(['echo',] + args), '--')
        #fifo_handle = self.command_pipe.open('/tmp/fifo', 'w')
        #fifo_handle.close()

    def _send_command(self, args):
        with open('/tmp/fifo', 'w') as fifo:
            fifo.write(' '.join(args)+'\n')
            
    def select_song(self, bpm):
        pct_change = np.abs((self.now_playing_bpm - bpm) / bpm)
        print('Now playing: {0}, BPM: {1}, % Change: {2}'.format(self.now_playing_bpm, bpm, pct_change))
        if pct_change > self.pct_change_trigger:
            nearest_index = (np.abs(self.bpm_array-bpm)).argmin()
            song_file = self.bpm_dict[self.bpm_array[nearest_index]]
            song_bpm = self.bpm_array[nearest_index]
            if song_file != self.now_playing:
                print('Playing song: {0} with BPM {1}'.format(song_file, song_bpm))
                self.play_song(song_file, song_bpm)
        return self.now_playing

    def play_song(self, song_file, song_bpm):
        if self.playing: 
            self._fade_out()
        self._send_command(['loadpaused', os.path.join(self.music_dir, song_file)])
        self.playing = False
        self._fade_in()
        self.now_playing = song_file
        self.now_playing_bpm = song_bpm

    def _true_play(self):
        # send <pause> toggle command only if already paused
        if self.playing == False:
            self._send_command(['pause'])
            self.playing = True

    def _true_pause(self):
        # send <pause> toggle command only if not playing
        if self.playing == True:
            self._send_command(['pause'])
            self.playing = False

    def _fade_in(self):
        self._send_command(['volume', '0'])
        self._true_play()
        for i in range(100):
            self._send_command(['volume', str(i+1)])
            time.sleep(1/100)

    def _fade_out(self):
        for i in range(100,0,-1):
            self._send_command(['volume', str(i-1)])
            time.sleep(1/100)
        self._send_command(['stop'])
        self.playing = False


def stdev(lst, population=True):
    """Calculates the standard deviation for a list of numbers."""
    num_items = float(len(lst))
    mean = sum(lst) / num_items
    differences = [x - mean for x in lst]
    sq_differences = [d ** 2 for d in differences]
    ssd = sum(sq_differences)

    if population is True:
        # print('This is POPULATION standard deviation.')
        variance = ssd / num_items
    else:
        # print('This is SAMPLE standard deviation.')
        variance = ssd / (num_items - 1)
    sd = sqrt(variance)
    return sd

if __name__ == '__main__':
    args = parse_args().parse_args()
    main(args)
