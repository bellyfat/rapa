# chat/consumers.py
from channels.generic.websocket import WebsocketConsumer
import json
import pyaudio
import wave
import sys
from . import pyaudio_asynchronous
import multiprocessing


class AudioPlaybackConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.audio_packet_queue = multiprocessing.Queue()
        self.period_sync_event = multiprocessing.Event()
        pyaudio_asynchronous.start(self.audio_packet_queue,
            self.period_sync_event)

    def disconnect(self, close_code):
        pyaudio_asynchronous.end()

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            print("Recieved text_data: ", len(text_data))
        if bytes_data:
            print("Recieved bytes_data: ", len(bytes_data))
            self.audio_packet_queue.put(bytes_data)