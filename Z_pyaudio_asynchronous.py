import pyaudio
import logging
import threading
from collections import deque
import time

pyaudio_stream = None

class PyAudioAsync(threading.Thread):
    def __init__(self, audio_packet_queue, period_sync_event, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = True
        self.audio_packet_queue = audio_packet_queue
        self.period_sync_event = period_sync_event
        self.args = args
        self.kwargs = kwargs
        self.previous_thread = None

    def stop(self):
        self.join()

    def run(self):
        global pyaudio_stream
        CHUNK = 1920
        number_of_channels = 2
        channel_width = 2
        silent_chunk = b'\x00'*CHUNK*channel_width*number_of_channels
        while True:
            logging.info("Thread: interating")
            audio_packet = None
            if self.audio_packet_queue:
                logging.info("Playing audio")
                audio_packet = self.audio_packet_queue.popleft()
            else:
                logging.info("Playing silent")
                audio_packet = silent_chunk
            self.period_sync_event.set()
            pyaudio_stream.write(audio_packet)

# start
main_thread = None
def start(audio_packet_queue, period_sync_event):
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    logging.info("Main    : before creating thread")
    global main_thread
    main_thread = PyAudioAsync(audio_packet_queue=audio_packet_queue,
        period_sync_event=period_sync_event)

    logging.info("Main    : before running thread")
    main_thread.start()

# end
def end():
    pass

def set_stream_object(pyaudio_stream_object):
    global pyaudio_stream
    pyaudio_stream = pyaudio_stream_object

# insert audio data
def insert_packet(data_queue, packet):
    while data_queue:
        data_queue.pop()
    data_queue.append(packet)

def wait_data_play_start(period_sync_event):
    tic = time.perf_counter()
    period_sync_event.wait()
    toc = time.perf_counter()
    logging.info("Waited for: %f s", toc-tic)
    period_sync_event.clear()