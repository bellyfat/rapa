
import wave
import sys
from opus import encoder, decoder
import pyaudio_multiprocessing
import multiprocessing
import time
import logging

if len(sys.argv) < 2:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

wf = wave.open(sys.argv[1], 'rb')

# Initialize array to store frames
audio_frames = []

CHUNK = 1920
data = wf.readframes(CHUNK)
while data:
    audio_frames.append(data)
    data = wf.readframes(CHUNK)

# convert wav to opus
opus_frames = []
CHANNELS = 2
RATE = 48000
enc = encoder.Encoder(RATE,CHANNELS,'voip')
dec = decoder.Decoder(RATE,CHANNELS)

for data in audio_frames:
    opus_frames.append(enc.encode(data, CHUNK))
print("DATA LENGTH :", len(b''.join(audio_frames)))
print("ENCDATA LENGTH :", len(b''.join(opus_frames)))

frame_size_time = CHUNK/RATE
audio_packet_queue = multiprocessing.Queue()
period_sync_event = multiprocessing.Event()
pyaudio_multiprocessing.start(audio_packet_queue, period_sync_event)
opus_decoded_data = b''
drift_time = 0
for opus_data in opus_frames:
    if drift_time > frame_size_time:
        drift_time -= frame_size_time
        logging.info("Offset drift: %f", drift_time)
        continue

    tic = time.perf_counter()
    decoded_data = dec.decode(opus_data,CHUNK)
    #opus_decoded_data += decoded_data

    if (time.perf_counter() - tic) < frame_size_time:
        logging.info("Append audio")
        audio_packet_queue.put(decoded_data)
        drift_time = 0
    else:
        drift_time += time.perf_counter() - tic - frame_size_time
        logging.info("Skip audio with drift: %f", drift_time)
        continue
    pyaudio_multiprocessing.wait_data_play_start(period_sync_event)

print("DECDATA LENGTH :", len(opus_decoded_data))
pyaudio_multiprocessing.end()
