import pyaudio
import logging
import threading
import multiprocessing
from collections import deque
import time

class PyAudioAsync(multiprocessing.Process):
    def __init__(self, audio_packet_queue, period_sync_event, *args, **kwargs):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.audio_packet_queue = audio_packet_queue
        self.period_sync_event = period_sync_event
        self.args = args
        self.kwargs = kwargs

    def stop(self):
        self.join()

    def run(self):
        p = pyaudio.PyAudio()
        CHUNK = 1920
        number_of_output_channel = 2
        channel_width = 2
        sample_rate = 44100

        silent_chunk = b'\x00'*CHUNK*channel_width*number_of_output_channel

        output_device_info = p.get_default_output_device_info()
        logging.info(output_device_info)
        stream = p.open(format=pyaudio.paInt16,
            channels=number_of_output_channel,
            rate=sample_rate,
            output=True,
            output_device_index=output_device_info["index"])

        while True:
            logging.info("Process: interating")
            audio_packet = None
            if not self.audio_packet_queue.empty():
                logging.info("Playing audio")
                audio_packet = self.audio_packet_queue.get()
            else:
                logging.info("Playing silent")
                audio_packet = silent_chunk
            self.period_sync_event.set()
            stream.write(audio_packet)


# initialize
# Pass in pyaudio object
# stream object?

# start
process_object = None
def start(audio_packet_queue, period_sync_event):
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    logging.info("Main    : before creating Process")
    global process_object
    process_object = PyAudioAsync(audio_packet_queue=audio_packet_queue,
        period_sync_event=period_sync_event)

    logging.info("Main    : before running Process")
    process_object.start()

# end
def end():
    pass

def wait_data_play_start(period_sync_event):
    tic = time.perf_counter()
    period_sync_event.wait()
    toc = time.perf_counter()
    logging.info("Waited for: %f s", toc-tic)
    period_sync_event.clear()