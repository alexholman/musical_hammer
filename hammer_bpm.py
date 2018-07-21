#!/usr/bin/env python

from __future__ import print_function
from __future__ import division

import sys
import argparse
from collections import deque
import time
import os
import csv
import numpy as np
import pygame
from pygame.locals import *

import vlc
# import RPi.GPIO as GPIO


def main(args):

    delay_obj = Delays(args.stdev_thresh, args.sample_size)
    song_obj = Songs(args.bpm_file, args.pct_change_trigger)
    
    pygame.init()
    BLACK = (0,0,0)
    WIDTH = 100
    HEIGHT = 100
    windowSurface = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
    windowSurface.fill(BLACK)
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                key = event.key
                if key == pygame.K_a:
                    strike_event_handler(delay_obj, song_obj)
                elif key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

def strike_event_handler(delay_obj, song_obj):
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
        if len(self.delays) == self.delays.maxlen and np.std(self.delays) < self.stdev_thresh:
            bps = len(self.delays) / sum(self.delays)
            self.bpm = bps * 60
            return self.bpm
        else:
            return None

class Songs(object):
    def __init__(self, bpm_filename, pct_change_trigger):
        self.music_dir = os.path.dirname(os.path.abspath(bpm_filename))
        # Load BPM file
        with open(bpm_filename, 'rb') as bpm_file:
            bpm_reader = csv.reader(bpm_file, delimiter='\t')
            self.bpm_dict = {float(bpm): name for name, bpm in bpm_reader}
            self.bpm_array = np.array(self.bpm_dict.keys())
        self.pct_change_trigger = pct_change_trigger
        self.player = vlc.MediaPlayer()
        self.now_playing = None
        self.now_playing_bpm = 0

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
        if self.player.is_playing():
            self._fade_out()
        self.player = vlc.MediaPlayer('file://' + os.path.join(self.music_dir, song_file))
        self._fade_in()
        self.now_playing = song_file
        self.now_playing_bpm = song_bpm

    
    def _fade_in(self):
        self.player.audio_set_volume(0)
        if not self.player.is_playing():
            self.player.play()
        for i in range(100):
            self.player.audio_set_volume(i+1)
            time.sleep(1/100)

    def _fade_out(self):
        if not self.player.is_playing():
            return
        for i in range(100,0,-1):
            self.player.audio_set_volume(i-1)
            time.sleep(1/100)
        self.player.stop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('bpm_file', type=str, help='TSV file with bpm values in form: filename \t bpm')
    parser.add_argument('--sample_size', type=int, default=4, help='Number of inter-strike delay values to average for BPM calculation')
    parser.add_argument('--stdev_thresh', type=float, default=0.05, help='Max threshold of standard dev of delay counts to trigger a bpm calculation')
    parser.add_argument('--pct_change_trigger', type=float, default=0.10, help='The percent change in BPM to trigger a song change')
    return parser

if __name__ == '__main__':
    args = parse_args().parse_args()
    main(args)
