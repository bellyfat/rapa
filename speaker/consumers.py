# chat/consumers.py
from channels.generic.websocket import WebsocketConsumer
import json
import pyaudio
import wave
import sys

AUDIO_QUEUE = []
# Assuming a module will only be loaded once per python instance
# Multiple import won't load it multiple times
p = pyaudio.PyAudio()
output_device_name = "Speakers (Realtek"
output_device_info = None
for i in range(p.get_device_count()):
    device_info = p.get_device_info_by_index(i)
    print(device_info)
    if output_device_name in device_info["name"]:
        output_device_info = device_info
bit_width = 16
byte_width = int(bit_width/8)
number_of_channel = 2

def get_audio_data(frame_count):
    global AUDIO_QUEUE
    if not AUDIO_QUEUE:
        return b''
    global byte_width, number_of_channel
    ttl_bytes = frame_count*byte_width*number_of_channel
    print("Total bytes required: ", ttl_bytes)

    audio_data = b''
    while AUDIO_QUEUE and (len(audio_data) < ttl_bytes):
        if len(AUDIO_QUEUE[0]) <= ttl_bytes:
            print("Getting element")
            audio_data += AUDIO_QUEUE.pop(0)
        elif len(AUDIO_QUEUE[0]) > ttl_bytes:
            print("Getting partial element")
            audio_data += AUDIO_QUEUE[0][:ttl_bytes]
            AUDIO_QUEUE[0] = AUDIO_QUEUE[0][ttl_bytes:]

    print("Got data length of: ", len(audio_data))
    return audio_data

def get_audio_data_length_in_seconds():
    global AUDIO_QUEUE
    if not AUDIO_QUEUE:
        return 0
    global byte_width, number_of_channel

    total_bytes_in_queue = 0
    for audio_data in AUDIO_QUEUE:
        total_bytes_in_queue = total_bytes_in_queue + len(audio_data)

    audio_in_seconds = int(total_bytes_in_queue/byte_width/number_of_channel/44100)
    return audio_in_seconds

def audio_callback(in_data, frame_count, time_info, status):
    # Check if there is data in queue
    # return data if there is with paContinue
    print("Callback getting: ", frame_count, " frames")
    audio_data = get_audio_data(frame_count)
    return (audio_data, pyaudio.paContinue)

class AudioPlaybackConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        #self.stream = self.create_stream()
        self.audio_stream = None

        # clear data queue
        global AUDIO_QUEUE
        AUDIO_QUEUE = []

    def create_stream(self):
        global p, output_device_info
        return p.open(format=pyaudio.paInt16,
            channels=output_device_info['maxOutputChannels'],
            rate=int(output_device_info['defaultSampleRate']),
            output=True,
            output_device_index=output_device_info["index"],
            stream_callback=audio_callback)

    def disconnect(self, close_code):
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()

    def maybe_start_stream(self, data_length_queued):
        MINIMUM_SECONDS_QUEUED = 2
        if data_length_queued < MINIMUM_SECONDS_QUEUED:
            return
        if not self.audio_stream or not self.audio_stream.is_active():
            print("Starting stream")
            self.audio_stream = self.create_stream()
            self.audio_stream.start_stream()

    def respond(self, data_length_queued):
        MINIMUM_SECONDS_QUEUED = 2
        seconds_to_wait = data_length_queued-MINIMUM_SECONDS_QUEUED
        self.send(text_data=str(seconds_to_wait))

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            print("Recieved text_data: ", len(text_data))
        if bytes_data:
            print("Recieved bytes_data: ", len(bytes_data))
            global AUDIO_QUEUE
            AUDIO_QUEUE.append(bytes_data)
            data_length_queued = get_audio_data_length_in_seconds()
            print(data_length_queued)
            self.respond(data_length_queued)
            self.maybe_start_stream(data_length_queued)