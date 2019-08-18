import pyaudio
import wave

chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 2
fs = 44100  # Record at 44100 samples per second
seconds = 10
filename = "output.wav"

p = pyaudio.PyAudio()  # Create an interface to PortAudio

input_device_name = "CABLE Output"
output_device_name = "Speakers (Realtek"
input_device_info = None
output_device_info = None
for i in range(p.get_device_count()):
    device_info = p.get_device_info_by_index(i)
    print(device_info)
    if input_device_name in device_info["name"]:
        input_device_info = device_info
    if output_device_name in device_info["name"]:
        output_device_info = device_info

if not input_device_info:
    print("Input device not found")
    exit()

if not output_device_info:
    print("Output device not found")
    exit()

print('Recording')

stream = p.open(format=sample_format,
                channels=channels,
                rate=fs,
                frames_per_buffer=chunk,
                input=True,
                input_device_index=input_device_info["index"],
                output=True,
                output_device_index=output_device_info["index"])

frames = []  # Initialize array to store frames

# Store data in chunks for 3 seconds
for i in range(0, int(fs / chunk * seconds)):
    data = stream.read(chunk)
    stream.write(data)
    #frames.append(data)

# Stop and close the stream 
stream.stop_stream()
stream.close()
# Terminate the PortAudio interface
p.terminate()

print('Finished recording')

# Save the recorded data as a WAV file
'''
wf = wave.open(filename, 'wb')
wf.setnchannels(channels)
wf.setsampwidth(p.get_sample_size(sample_format))
wf.setframerate(fs)
wf.writeframes(b''.join(frames))
wf.close()
'''