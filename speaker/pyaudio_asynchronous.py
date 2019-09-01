import pyaudio
import logging
import threading
import multiprocessing
from collections import deque
import time
import signal

class PyAudioAsync(multiprocessing.Process):
    chunk_frame_length = 1920
    number_of_output_channel = 2
    number_of_input_channel = 2
    channel_width = 2
    sample_rate = 44100
    audio_input = False
    audio_output = False

    def __init__(self, *args, **kwargs):
        super().__init__(target=self, args=args, kwargs=kwargs)
        self.daemon = True
        self.save_kwargs(kwargs)

        self.process_terminated = multiprocessing.Event()
        self.process_terminated.clear()

    def save_kwargs(self, kwargs):
        if "audio_packet_queue" in kwargs:
            self.audio_packet_queue = kwargs["audio_packet_queue"]
        if "period_sync_event" in kwargs:
            self.period_sync_event = kwargs["period_sync_event"]
        if "audio_input" in kwargs:
            self.audio_input = kwargs["audio_input"]
        if "audio_output" in kwargs:
            self.audio_output = kwargs["audio_output"]

    def terminate_process(self, signum, frame):
        self.process_terminated.set()

    def run_audio_output(self):
        bytes_per_frame = self.channel_width * self.number_of_output_channel
        silent_chunk = b'\x00' * self.chunk_frame_length * bytes_per_frame
        output_device_info = self.p.get_default_output_device_info()
        '''
        output_device_name = "Speakers "
        output_device_info = None
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if output_device_name in device_info["name"]:
                output_device_info = device_info
        if not output_device_info:
            print("Output device not found")
            return
        '''
        self.logger.info(output_device_info)
        stream = self.p.open(format=pyaudio.paInt16,
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

    def run_audio_input(self):
        input_device_info = self.p.get_default_input_device_info()
        self.logger.info(input_device_info)
        stream = self.p.open(format=pyaudio.paInt16,
            channels=self.number_of_input_channel,
            rate=self.sample_rate,
            frames_per_buffer=self.chunk_frame_length,
            input=True,
            input_device_index=input_device_info["index"])

        while not self.process_terminated.is_set():
            self.logger.info("Process Audio Input: iterating")
            audio_packet = stream.read(self.chunk_frame_length)
            self.audio_packet_queue.put(audio_packet)

    def run(self):
        self.logger = multiprocessing.get_logger()
        self.logger.setLevel(logging.INFO)

        signal.signal(signal.SIGTERM, self.terminate_process)

        self.p = pyaudio.PyAudio()
        if self.audio_output:
            self.run_audio_output()
        elif self.audio_input:
            self.run_audio_input()
        else:
            self.logger.info("Neither output or input enabled")

# start
#process_object = None
logger_created = False
def init_logger():
    #format = "%(asctime)s: %(message)s"
    #logging.basicConfig(format=format, level=logging.INFO,
    #                    datefmt="%H:%M:%S")
    global logger_created
    if not logger_created:
        multiprocessing.log_to_stderr()
        logger_created = True

'''
def wait_data_play_start(period_sync_event):
    tic = time.perf_counter()
    period_sync_event.wait()
    toc = time.perf_counter()
    logging.info("Waited for: %f s", toc-tic)
    period_sync_event.clear()
'''