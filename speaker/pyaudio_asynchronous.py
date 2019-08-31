import pyaudio
import logging
import threading
import multiprocessing
from collections import deque
import time
import signal

class PyAudioAsync(multiprocessing.Process):
    CHUNK = 1920
    number_of_output_channel = 2
    channel_width = 2
    sample_rate = 44100

    def __init__(self, *args, **kwargs):
        super().__init__(target=self, args=args, kwargs=kwargs)
        self.daemon = True
        self.audio_packet_queue = kwargs["audio_packet_queue"]
        self.period_sync_event = kwargs["period_sync_event"]

        self.process_terminated = multiprocessing.Event()
        self.process_terminated.clear()

    def terminate_process(self, signum, frame):
        self.process_terminated.set()

    def run(self):
        self.logger = multiprocessing.get_logger()
        self.logger.setLevel(logging.INFO)

        signal.signal(signal.SIGTERM, self.terminate_process)
        silent_chunk = b'\x00'*self.CHUNK*self.channel_width*self.number_of_output_channel

        p = pyaudio.PyAudio()
        output_device_info = p.get_default_output_device_info()
        self.logger.info(output_device_info)
        stream = p.open(format=pyaudio.paInt16,
            channels=self.number_of_output_channel,
            rate=self.sample_rate,
            output=True,
            output_device_index=output_device_info["index"])

        while not self.process_terminated.is_set():
            self.logger.info("Process: iterating")
            audio_packet = None
            if not self.audio_packet_queue.empty():
                self.logger.info("Playing audio")
                audio_packet = self.audio_packet_queue.get()
            else:
                self.logger.info("Playing silent")
                audio_packet = silent_chunk
            self.period_sync_event.set()
            stream.write(audio_packet)

class PyAudioAsyncInput(multiprocessing.Process):
    CHUNK = 1920
    number_of_input_channel = 2
    sample_rate = 44100

    def __init__(self, *args, **kwargs):
        super().__init__(target=self, args=args, kwargs=kwargs)
        self.daemon = True
        self.audio_packet_sender = kwargs["audio_packet_sender"]

        self.process_terminated = multiprocessing.Event()
        self.process_terminated.clear()

    def terminate_process(self, signum, frame):
        self.process_terminated.set()

    def run(self):
        self.logger = multiprocessing.get_logger()
        self.logger.setLevel(logging.INFO)

        signal.signal(signal.SIGTERM, self.terminate_process)

        p = pyaudio.PyAudio()
        input_device_info = p.get_default_input_device_info()
        self.logger.info(input_device_info)
        stream = p.open(format=pyaudio.paInt16,
            channels=self.number_of_input_channel,
            rate=self.sample_rate,
            frames_per_buffer=self.CHUNK,
            input=True,
            input_device_index=input_device_info["index"])

        while not self.process_terminated.is_set():
            self.logger.info("Process Audio Input: iterating")
            audio_packet = stream.read(self.CHUNK)
            self.audio_packet_sender.put(audio_packet)

# start
#process_object = None
logger_created = False
def start(audio_packet_queue, period_sync_event):
    #format = "%(asctime)s: %(message)s"
    #logging.basicConfig(format=format, level=logging.INFO,
    #                    datefmt="%H:%M:%S")
    global logger_created
    if not logger_created:
        multiprocessing.log_to_stderr()
        logger_created = True

    #global process_object
    process_object = PyAudioAsync(audio_packet_queue=audio_packet_queue,
        period_sync_event=period_sync_event)
    #process_object.start()
    return process_object

def start_input(audio_packet_sender):
    global logger_created
    if not logger_created:
        multiprocessing.log_to_stderr()
        logger_created = True

    process_object = PyAudioAsyncInput(audio_packet_sender=audio_packet_sender)

    return process_object

# end
#def end():
#    global process_object
#    if process_object:
#        process_object.terminate()
#        process_object.join()

def wait_data_play_start(period_sync_event):
    tic = time.perf_counter()
    period_sync_event.wait()
    toc = time.perf_counter()
    logging.info("Waited for: %f s", toc-tic)
    period_sync_event.clear()