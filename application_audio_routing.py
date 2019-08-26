import pyaudio
import wave
import asyncio
import websockets
import time
from opus import encoder as opus_encoder

chunk = 1920  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 2
fs = 44100  # Record at 44100 samples per second
seconds = 3

p = pyaudio.PyAudio()  # Create an interface to PortAudio

input_device_name = "CABLE Output"
input_device_info = None
for i in range(p.get_device_count()):
    device_info = p.get_device_info_by_index(i)
    print(device_info)
    if input_device_name in device_info["name"]:
        input_device_info = device_info

if not input_device_info:
    print("Input device not found")
    exit()

async def hello(uri):
    async with websockets.connect(uri) as websocket:
        print('Recording')
        stream = p.open(format=sample_format,
                        channels=channels,
                        rate=fs,
                        frames_per_buffer=chunk,
                        input=True,
                        input_device_index=input_device_info["index"])

        RATE = 48000
        CHANNELS = 2
        encoder = opus_encoder.Encoder(RATE,CHANNELS,'voip')

        try:
            # Run until user press Ctrl-C
            while True:
                #frames = b''  # Initialize byte array to store frames
                #ttl_bytes = 0

                # Store data in chunks for 3 seconds
                #for i in range(0, int(fs / chunk * seconds)):
                #    data = stream.read(chunk)
                #    #stream.write(data)
                #    frames = frames + data
                #    ttl_bytes += len(data)

                data = stream.read(chunk)
                encoded_data = encoder.encode(data, chunk)

                print("Sending some frames")
                #await websocket.send(frames)
                await websocket.send(encoded_data)
        except:
            print("This is a test")
            exit()

        # Stop and close the stream 
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        p.terminate()

        print('Finished recording')

asyncio.get_event_loop().run_until_complete(
    hello('ws://192.168.0.104:8000/ws/speaker/audioplayback/'))
# Save the recorded data as a WAV file
'''
wf = wave.open(filename, 'wb')
wf.setnchannels(channels)
wf.setsampwidth(p.get_sample_size(sample_format))
wf.setframerate(fs)
wf.writeframes(b''.join(frames))
wf.close()
'''