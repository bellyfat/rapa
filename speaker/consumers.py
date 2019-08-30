# chat/consumers.py
from channels.generic.websocket import WebsocketConsumer
import json
import pyaudio
import wave
import sys
from . import pyaudio_asynchronous
import multiprocessing
from opus import decoder

class AudioPlaybackConsumer(WebsocketConsumer):
    def connect(self):
        # Opus decoder
        CHANNELS = 2
        RATE = 48000
        self.CHUNK = 1920
        self.decoder = decoder.Decoder(RATE,CHANNELS)
        self.opus_encoded = True

        # PyAudio Multiprocessing Wrapper
        self.audio_packet_queue = multiprocessing.Queue()
        self.period_sync_event = multiprocessing.Event()
        self.pyaudio_process = pyaudio_asynchronous.start(self.audio_packet_queue,
            self.period_sync_event)
        self.pyaudio_process.start()

        # Accept connection only if everything is ok
        self.accept()

    def disconnect(self, close_code):
        if self.pyaudio_process:
            self.pyaudio_process.terminate()
            self.pyaudio_process.join()

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            print("Recieved text_data: ", len(text_data))
        if bytes_data:
            print("Recieved bytes_data: ", len(bytes_data))
            if self.opus_encoded:
                bytes_data = self.decoder.decode(bytes_data, self.CHUNK)
            self.audio_packet_queue.put(bytes_data)