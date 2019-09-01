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
                        print("opus_encoded: ", self.opus_encoded)
                    if "number-of-output-channel" in configuration:
                        self.number_of_output_channel = configuration["number-of-output-channel"]
                        print("number_of_output_channel: ", self.number_of_output_channel)
                    if "channel-width" in configuration:
                        self.channel_width = configuration["channel-width"]
                        print("channel_width: ", self.channel_width)
                    if "sample-rate" in configuration:
                        self.sample_rate = configuration["sample-rate"]
                        print("sample_rate: ", self.sample_rate)
                    if "chunk-frame-length" in configuration:
                        self.chunk_frame_length = configuration["chunk-frame-length"]
                        print("chunk_frame_length: ", self.chunk_frame_length)
                    if "encoder-sample-rate" in configuration:
                        self.encoder_sample_rate = configuration["encoder-sample-rate"]
                        print("encoder_sample_rate: ", self.encoder_sample_rate)
                except json.decoder.JSONDecodeError:
                    print("json failed to parse configuration_text")
                    print(configuration_text)
                except:
                    print("Configuration error")
            elif text_data.startswith("output-open:"):
                if not self.audio_output_open:
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
                if self.pyaudio_process:
                    self.pyaudio_process.terminate()
                self.audio_output_open = False
        if bytes_data:
            print("Recieved bytes_data length: ", len(bytes_data))
            try:
                if self.opus_encoded and self.decoder:
                    bytes_data = self.decoder.decode(bytes_data, self.chunk_frame_length)
            except Exception as e:
                print(e)
                self.close()
            if self.audio_output_open:
                self.audio_packet_queue.put(bytes_data)

def get_audio_packet_and_send(audio_packet_queue, audio_packet_sender, thread_terminated_event):
    while not thread_terminated_event.is_set():
        try:
            audio_packet = audio_packet_queue.get(True, 5)
            audio_packet_sender.send(bytes_data=audio_packet)
        except Exception as e:
            print(e)
            thread_terminated_event.set()

class AudioRecordConsumer(WebsocketConsumer):
    def connect(self):
        # Audio configurations
        self.number_of_input_channel = 2
        self.sample_rate = 44100
        # Opus encoder
        self.encoder_sample_rate = 48000
        self.chunk_frame_length = 1920
        self.opus_encoded = True
        self.encoder = None

        # PyAudio Multiprocessing Wrapper
        #self.audio_packet_queue = multiprocessing.Queue()
        #self.pyaudio_process = pyaudio_asynchronous.start_input(self.audio_packet_queue)
        self.pyaudio_process = None
        #self.pyaudio_process.start()

        #self.worker_thread_terminated = threading.Event()
        #self.worker_thread_terminated.clear()
        #self.worker_thread = threading.Thread(target=get_audio_packet_and_send,
        #    args=(self.audio_packet_queue, self, self.worker_thread_terminated))
        self.worker_thread_terminated = None
        self.audio_input_open = False
        #self.worker_thread.start()

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
            try:
                if self.opus_encoded and self.encoder:
                    bytes_data = self.encoder.encode(bytes_data, self.chunk_frame_length)
            except Exception as e:
                print(e)
                self.close()
            super().send(bytes_data=bytes_data)

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
                        print("opus_encoded: ", self.opus_encoded)
                    if "number-of-input-channel" in configuration:
                        self.number_of_input_channel = configuration["number-of-input-channel"]
                        print("number_of_input_channel: ", self.number_of_input_channel)
                    if "sample-rate" in configuration:
                        self.sample_rate = configuration["sample-rate"]
                        print("sample_rate: ", self.sample_rate)
                    if "chunk-frame-length" in configuration:
                        self.chunk_frame_length = configuration["chunk-frame-length"]
                        print("chunk_frame_length: ", self.chunk_frame_length)
                    if "encoder-sample-rate" in configuration:
                        self.encoder_sample_rate = configuration["encoder-sample-rate"]
                        print("encoder_sample_rate: ", self.encoder_sample_rate)
                except json.decoder.JSONDecodeError:
                    print("json failed to parse configuration_text")
                    print(configuration_text)
                except:
                    print("Configuration error")
            elif text_data.startswith("input-open:"):
                if not self.audio_input_open:
                    self.encoder = encoder.Encoder(self.encoder_sample_rate, self.number_of_input_channel, 'voip')

                    # PyAudio Multiprocessing Wrapper
                    self.audio_packet_queue = multiprocessing.Queue()
                    self.pyaudio_process = pyaudio_asynchronous.start_input(self.audio_packet_queue)
                    self.pyaudio_process.number_of_input_channel = self.number_of_input_channel
                    self.pyaudio_process.sample_rate = self.sample_rate
                    self.pyaudio_process.chunk_frame_length = self.chunk_frame_length
                    self.pyaudio_process.start()

                    self.worker_thread_terminated = threading.Event()
                    self.worker_thread_terminated.clear()
                    self.worker_thread = threading.Thread(target=get_audio_packet_and_send,
                        args=(self.audio_packet_queue, self, self.worker_thread_terminated))
                    self.worker_thread.start()

                    self.audio_input_open = True

            elif text_data.startswith("input-close:"):
                if self.worker_thread_terminated:
                    self.worker_thread_terminated.set()
                if self.pyaudio_process:
                    self.pyaudio_process.terminate()
                self.audio_input_open = False
        if bytes_data:
            print("Recieved bytes_data length: ", len(bytes_data))
