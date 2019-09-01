# chat/consumers.py
from channels.generic.websocket import WebsocketConsumer
from . import pyaudio_asynchronous
import multiprocessing
import threading
from opus import encoder, decoder

class AudioPlaybackConsumer(WebsocketConsumer):
    def connect(self):
        # Opus decoder
        CHANNELS = 2
        RATE = 48000
        self.CHUNK = 1920
        self.decoder = decoder.Decoder(RATE,CHANNELS)
        self.opus_encoded = True

        # PyAudio Multiprocessing Wrapper
        #self.audio_packet_queue = multiprocessing.Queue()
        #self.period_sync_event = multiprocessing.Event()
        #self.pyaudio_process = pyaudio_asynchronous.start(self.audio_packet_queue,
        #    self.period_sync_event)
        self.pyaudio_process = None
        self.audio_output_open = False
        #self.pyaudio_process.start()

        # Accept connection only if everything is ok
        self.accept()

    def disconnect(self, close_code):
        if self.pyaudio_process:
            self.pyaudio_process.terminate()
            self.pyaudio_process.join()

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            print("Recieved text_data length: ", len(text_data))
            if text_data.startswith("config:"):
                pass
            elif text_data.startswith("output-open:"):
                self.audio_packet_queue = multiprocessing.Queue()
                self.period_sync_event = multiprocessing.Event()
                self.pyaudio_process = pyaudio_asynchronous.start(self.audio_packet_queue,
                    self.period_sync_event)
                self.pyaudio_process.start()
                self.audio_output_open = True
            elif text_data.startswith("output-close:"):
                self.pyaudio_process.terminate()
                self.audio_output_open = False
        if bytes_data:
            print("Recieved bytes_data length: ", len(bytes_data))
            try:
                if self.opus_encoded:
                    bytes_data = self.decoder.decode(bytes_data, self.CHUNK)
            except:
                print("Failed to decode data")
                self.close()
            if self.audio_output_open:
                self.audio_packet_queue.put(bytes_data)

def get_audio_packet_and_send(audio_packet_queue, audio_packet_sender, thread_terminated_event):
    while not thread_terminated_event.is_set():
        try:
            audio_packet = audio_packet_queue.get(True, 5)
            audio_packet_sender.send(bytes_data=audio_packet)
        except:
            print("Get audio packet queue timeout")
            thread_terminated_event.set()

class AudioRecordConsumer(WebsocketConsumer):
    def connect(self):
        # Opus decoder
        CHANNELS = 2
        RATE = 48000
        self.CHUNK = 1920
        self.encoder = encoder.Encoder(RATE, CHANNELS, 'voip')

        # PyAudio Multiprocessing Wrapper
        self.audio_packet_queue = multiprocessing.Queue()
        self.pyaudio_process = pyaudio_asynchronous.start_input(self.audio_packet_queue)
        self.pyaudio_process.start()

        self.worker_thread_terminated = threading.Event()
        self.worker_thread_terminated.clear()
        self.worker_thread = threading.Thread(target=get_audio_packet_and_send,
            args=(self.audio_packet_queue, self, self.worker_thread_terminated))
        self.worker_thread.start()

        # Accept connection only if everything is ok
        self.accept()

    def disconnect(self, close_code):
        if self.worker_thread_terminated:
            print("Terminating worker thread")
            self.worker_thread_terminated.set()
        if self.pyaudio_process:
            print("Terminating process")
            self.pyaudio_process.terminate()
            self.pyaudio_process.join()

    def send(self, text_data=None, bytes_data=None):
        if bytes_data:
            print("Audio packet length:", len(bytes_data))
            encoded_data = self.encoder.encode(bytes_data, self.CHUNK)
            print("Encoded data length:", len(encoded_data))
            super().send(bytes_data=encoded_data)

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            print("Recieved text_data length: ", len(text_data))
        if bytes_data:
            print("Recieved bytes_data length: ", len(bytes_data))
