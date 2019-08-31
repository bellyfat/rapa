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

def get_audio_packet_and_send(audio_packet_queue, audio_packet_sender, thread_terminated_event):
    while not thread_terminated_event.is_set():
        try:
            audio_packet = audio_packet_queue.get(True, 5)
            print("Sending audio packet", len(audio_packet))
            audio_packet_sender.send(bytes_data=audio_packet)
        except:
            print("Get audio packet queue timeout")
            thread_terminated_event.set()

class AudioRecordConsumer(WebsocketConsumer):
    def connect(self):
        print("Connecting to input")
        # Opus decoder
        CHANNELS = 2
        RATE = 48000
        self.CHUNK = 1920
        self.encoder = encoder.Encoder(RATE, CHANNELS, 'voip')
        print("Created encoder")

        # PyAudio Multiprocessing Wrapper
        self.audio_packet_queue = multiprocessing.Queue()
        self.pyaudio_process = pyaudio_asynchronous.start_input(self.audio_packet_queue)
        self.pyaudio_process.start()
        print("Process started")

        self.worker_thread_terminated = threading.Event()
        self.worker_thread_terminated.clear()
        self.worker_thread = threading.Thread(target=get_audio_packet_and_send,
            args=(self.audio_packet_queue, self, self.worker_thread_terminated))
        self.worker_thread.start()
        '''
        while not self.socket_terminated.is_set():
            try:
                audio_packet = self.audio_packet_queue.get(True, 30)
                print("Sending audio packet", len(audio_packet))
                self.send(bytes_data=audio_packet)
            except:
                print("Get audio packet timeout")
                self.socket_terminated.set()
                self.close()
        '''

        # Accept connection only if everything is ok
        self.accept()
        print("Connection accepted")

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
            encoded_data = self.encoder.encode(bytes_data, self.CHUNK)
            super().send(bytes_data=encoded_data)

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            print("Recieved text_data: ", len(text_data))
            '''
            while not self.socket_terminated.is_set():
                try:
                    audio_packet = self.audio_packet_queue.get(True, 5)
                    print("Sending audio packet", len(audio_packet))
                    self.send(bytes_data=audio_packet)
                except:
                    print("Get audio packet timeout")
                    self.socket_terminated.set()
                    self.close()
            '''
        if bytes_data:
            print("Recieved bytes_data: ", len(bytes_data))
