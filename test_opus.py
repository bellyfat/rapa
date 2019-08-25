
import wave
import sys
from opus import encoder, decoder
import pyaudio
import pyaudio_asynchronous
import time
from collections import deque
import threading

if len(sys.argv) < 2:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

wf = wave.open(sys.argv[1], 'rb')

#dst = "test.opus"

frames = []  # Initialize array to store frames

CHUNK = 1920
data = wf.readframes(CHUNK)

while data:
    frames.append(data)
    data = wf.readframes(CHUNK)

p = pyaudio.PyAudio()
'''
output_device_name = "default"
output_device_info = None
print(p.get_device_count())
for i in range(p.get_device_count()):
    device_info = p.get_device_info_by_index(i)
    print(device_info)
    if output_device_name in device_info["name"]:
        output_device_info = device_info
'''
output_device_info = p.get_default_output_device_info()
bit_width = 16
byte_width = int(bit_width/8)
number_of_output_channel = 2
sample_rate = 44100
stream = p.open(format=pyaudio.paInt16,
    channels=number_of_output_channel,
    rate=sample_rate,
    output=True,
    output_device_index=output_device_info["index"])

# convert wav to opus
opus_frames = []
CHANNELS = 2
RATE = 48000
enc = encoder.Encoder(RATE,CHANNELS,'voip')
dec = decoder.Decoder(RATE,CHANNELS)
for data in frames:
    opus_frames.append(enc.encode(data, CHUNK))
print("DATA LENGTH :", len(b''.join(frames)))
print("ENCDATA LENGTH :", len(b''.join(opus_frames)))

frame_size_time = CHUNK/RATE
audio_packet_queue = deque()
period_sync_event = threading.Event()
pyaudio_asynchronous.set_stream_object(stream)
pyaudio_asynchronous.start(audio_packet_queue, period_sync_event)
opus_dec_data = b''
total_drift_time = 0
for opus_data in opus_frames:
    if total_drift_time > frame_size_time:
        total_drift_time -= frame_size_time
        continue

    tic = time.perf_counter()
    decoded_data = dec.decode(opus_data,CHUNK)
    #opus_dec_data += decoded_data

    if (time.perf_counter() - tic) < frame_size_time:
        pyaudio_asynchronous.insert_packet(audio_packet_queue, decoded_data)
        total_drift_time = 0
    else:
        total_drift_time += time.perf_counter() - tic - frame_size_time
        continue
    pyaudio_asynchronous.wait_data_play_start(period_sync_event)
pyaudio_asynchronous.end()

stream.stop_stream()
stream.close()

p.terminate()