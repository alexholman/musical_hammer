from math import sqrt, fabs
from utime import ticks_ms, ticks_diff, sleep
from ucollections import deque
# import debounce as db
# from machine import Pin, UART
import dfplayer as df
import uasyncio as asyncio


def strike_event_handler(args):
    delay_obj, song_obj = args
    delay_obj.add_event(ticks_ms())
    bpm = delay_obj.calc_bpm()
    print('Detected bpm: {0}'.format(bpm))
    if bpm:
        song_obj.select_song(bpm)
        

class Delays(object):
    def __init__(self, stdev_thresh, sample_size):
        self.stdev_thresh = stdev_thresh
        self.delays = deque((), sample_size)
        self.sample_size = sample_size
        self.last_timestamp = 0
        self.bpm = None

    def add_event(self, event_time):
        elapsed_seconds = ticks_diff(event_time, self.last_timestamp)/1000
        self.delays.append(elapsed_seconds)
        self.last_timestamp = event_time

    def calc_bpm(self):
        if len(self.delays) == self.sample_size and stdev(deque_to_list(self.delays)) < self.stdev_thresh:
            bps = len(self.delays) / sum(deque_to_list(self.delays))
            self.bpm = bps * 60
            return self.bpm
        else:
            return None

class Songs(object):
    def __init__(self, bpm_filename, pct_change_trigger):
        # Load BPM file
        self.bpm_dict = {}
        self.bpm_list = []
        with open(bpm_filename, 'r') as bpm_file:
            for i,line in enumerate(bpm_file):
                # if i > 25:
                #    break
                line = line.rstrip('\n')
                line = line.rstrip('\r')
                if not line:
                    continue
                print(line)
                folder, file_name, bpm = line.split('\t')
                folder = int(folder)
                number = int(file_name[:3])
                # name = file_name[:4]
                bpm = float(bpm)

                self.bpm_dict[float(bpm)] = {'folder':folder, 'number':number}
                self.bpm_list.append(bpm)
        self.bpm_list = sorted(self.bpm_list)

        self.pct_change_trigger = PCT_CHANGE_TRIGGER

        self.player = df.Player(uart=DF_SERIAL_PIN, busy_pin=DF_BUSY_PIN)
        self.now_playing_bpm = 0
        self.now_playing = None

        self.loop = asyncio.get_event_loop()

    def select_song(self, bpm):
        pct_change = fabs((self.now_playing_bpm - bpm) / bpm)
        print('Continuing: {0}, detected BPM: {1}, % Change: {2}'.format(self.now_playing_bpm, bpm, pct_change))
        if pct_change > self.pct_change_trigger:
            
            song_bpm = get_closest_value(self.bpm_list, bpm)
            song_dict = self.bpm_dict[song_bpm]
            if (song_dict['folder'],song_dict['number']) != self.now_playing:
                print('Changing to song: {0}:{1} with BPM {2}'.format(song_dict['folder'], song_dict['number'], song_bpm))
                self.play_song(song_dict['folder'], song_dict['number'], song_bpm)
        return self.now_playing

    def play_song(self, folder, number, bpm):
        if self.now_playing and self.player.playing():
            self.loop.create_task(self._fade_out())
        else:
            self.player.volume(0)
        self.player.play(folder, number)
        self.loop.create_task(self._fade_in())
        self.now_playing = (folder,number)
        self.now_playing_bpm = bpm

    async def _fade_in(self):
        await asyncio.sleep_ms(500)
        self.player.volume(0)
        for i in range(10):
            self.player.volume((float(i)+1)/10)
            await asyncio.sleep_ms(100)
        await asyncio.sleep_ms(500)

    async def _fade_out(self):
        await asyncio.sleep_ms(500)
        for i in range(10,0,-1):
            self.player.volume((float(i)-1)/10)
            await asyncio.sleep_ms(100)
        await asyncio.sleep_ms(500)

#------------------------
# Define helper functions

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

def get_closest_value(arr, target):
    n = len(arr)
    left = 0
    right = n - 1
    mid = 0

    # edge case - last or above all
    if target >= arr[n - 1]:
        return arr[n - 1]
    # edge case - first or below all
    if target <= arr[0]:
        return arr[0]
    # BSearch solution: Time & Space: Log(N)

    while left < right:
        mid = (left + right) // 2  # find the mid
        if target < arr[mid]:
            right = mid
        elif target > arr[mid]:
            left = mid + 1
        else:
            return arr[mid]

    if target < arr[mid]:
        return find_closest(arr[mid - 1], arr[mid], target)
    else:
        return find_closest(arr[mid], arr[mid + 1], target)

# findClosest
# We find the closest by taking the difference
# between the target and both values. It assumes
# that val2 is greater than val1 and target lies
# between these two. 
def find_closest(val1, val2, target):
    return val2 if target - val1 >= val2 - target else val1

def deque_to_list(in_deque):
    deque_list = []
    for i in range(len(in_deque)):
        deque_list.append(in_deque.popleft())
    for item in deque_list:
        # print('appending: {0}, len: {1}'.format(item, len(deque_list)))
        in_deque.append(item)
    return deque_list


if __name__ == '__main__':
    main()
