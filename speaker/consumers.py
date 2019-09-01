# chat/consumers.py
from channels.generic.websocket import WebsocketConsumer
from . import pyaudio_asynchronous
import multiprocessing
import threading
from opus import encoder, decoder
import json

class AudioPlaybackConsumer(WebsocketConsumer):
    def connect(self):
        # Audio configurations
        self.number_of_output_channel = 2
        self.channel_width = 2
        self.sample_rate = 44100
        # Opus decoder
        self.encoder_sample_rate = 48000
        self.chunk_frame_length = 1920
        self.opus_encoded = True
        self.decoder = None

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
                print(text_data)
                configuration_text = text_data[7:]
                try:
                    configuration = json.loads(configuration_text)
                    if "opus-encoded" in configuration:
                        self.opus_encoded = configuration["opus-encoded"]
                    if "number-of-output-channel" in configuration:
                        self.number_of_output_channel = configuration["number-of-output-channel"]
                    if "channel-width" in configuration:
                        self.channel_width = configuration["channel-width"]
                    if "sample-rate" in configuration:
                        self.sample_rate = configuration["sample-rate"]
                    if "chunk-frame-length" in configuration:
                        self.chunk_frame_length = configuration["chunk-frame-length"]
                    if "encoder-sample-rate" in configuration:
                        self.encoder_sample_rate = configuration["encoder-sample-rate"]
                except json.decoder.JSONDecodeError:
                    print("json failed to parse configuration_text")
                    print(configuration_text)
                except:
                    print("Configuration error")
            elif text_data.startswith("output-open:"):
                self.decoder = decoder.Decoder(self.encoder_sample_rate, self.number_of_output_channel)

                self.audio_packet_queue = multiprocessing.Queue()
                self.period_sync_event = multiprocessing.Event()
                self.pyaudio_process = pyaudio_asynchronous.start(self.audio_packet_queue,
                    self.period_sync_event)
                self.pyaudio_process.number_of_output_channel = self.number_of_output_channel
                self.pyaudio_process.channel_width = self.channel_width
                self.pyaudio_process.sample_rate = self.sample_rate
                self.pyaudio_process.chunk_frame_length = self.chunk_frame_length

                self.pyaudio_process.start()
                self.audio_output_open = True

            elif text_data.startswith("output-close:"):
                self.pyaudio_process.terminate()
                self.audio_output_open = False
        if bytes_data:
            print("Recieved bytes_data length: ", len(bytes_data))
            try:
                if self.opus_encoded and self.decoder:
                    bytes_data = self.decoder.decode(bytes_data, self.chunk_frame_length)
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
