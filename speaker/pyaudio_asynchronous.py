import pyaudio
import logging
import threading
import multiprocessing
from collections import deque
import time
import signal

class PyAudioAsync(multiprocessing.Process):
    def __init__(self, audio_packet_queue, period_sync_event, *args, **kwargs):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.audio_packet_queue = audio_packet_queue
        self.period_sync_event = period_sync_event
        self.args = args
        self.kwargs = kwargs

        #format = "%(asctime)s: %(message)s"
        #logging.basicConfig(format=format, level=logging.INFO,
        #    datefmt="%H:%M:%S")
        multiprocessing.log_to_stderr()
        self.logger = multiprocessing.get_logger()
        self.logger.setLevel(logging.INFO)

        self.process_terminated = multiprocessing.Event()
        self.process_terminated.clear()

    def stop(self):
        self.join()

    def terminate_process(self, signum, frame):
        self.process_terminated.set()

    def run(self):
        signal.signal(signal.SIGTERM, self.terminate_process)
        p = pyaudio.PyAudio()
        CHUNK = 1920
        number_of_output_channel = 2
        channel_width = 2
        sample_rate = 44100

        silent_chunk = b'\x00'*CHUNK*channel_width*number_of_output_channel

        output_device_info = p.get_default_output_device_info()
        self.logger.info(output_device_info)
        stream = p.open(format=pyaudio.paInt16,
            channels=number_of_output_channel,
            rate=sample_rate,
            output=True,
            output_device_index=output_device_info["index"])

        while not self.process_terminated.is_set():
            self.logger.info("Process: interating")
            audio_packet = None
            if not self.audio_packet_queue.empty():
                self.logger.info("Playing audio")
                audio_packet = self.audio_packet_queue.get()
            else:
                self.logger.info("Playing silent")
                audio_packet = silent_chunk
            self.period_sync_event.set()
            stream.write(audio_packet)

# start
process_object = None
def start(audio_packet_queue, period_sync_event):
    #format = "%(asctime)s: %(message)s"
    #logging.basicConfig(format=format, level=logging.INFO,
    #                    datefmt="%H:%M:%S")

    global process_object
    process_object = PyAudioAsync(audio_packet_queue=audio_packet_queue,
        period_sync_event=period_sync_event)
    process_object.start()

# end
def end():
    #global process_object
    #process_object.terminate()
    pass

def wait_data_play_start(period_sync_event):
    tic = time.perf_counter()
    period_sync_event.wait()
    toc = time.perf_counter()
    logging.info("Waited for: %f s", toc-tic)
    period_sync_event.clear()