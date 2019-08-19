# rapa
## Remote Asynchronous Peripheral Access

The idea of this project is to expose attached peripherals such as mouse, keyboard, speaker or mass storage to web applications.

Making the computer into a webserver

### Virtual environment created using Pipenv
pipenv install
pipenv shell
pipenv run

### Django
django-admin startproject rapa_server .
python manage.py startapp speaker
python migrate
**add speaker app into settings.py**
python manage.py runserver

### Channels
Add channels app into settings.py
Create routing.py with ProtocolTypeRouter in rapa_server
HTTP protocol routing is automatically added
**Websocket**
Create routing.py in speaker
Create consumer.py in speaker
python manage.py runserver

### Authentication
N/A

## Speaker
**Deprecated**
~~Play song from browser
howler.js to play audio
socket to recieve audio data
open socket
authenticate
send audio~~
**Update**
Play audio on server (Python, wav file, mp3 converter), using pyaudio
Streamed through WebSocket
At server, open a WebSocket to wait for audio data. If audio is recieved, it is played through **pyaudio** module.
At application, install Virtual Audio Cable to route output audio to input internally.
Set Virtual Audio Cable as default output.
Use pyaudio to read from Virtual Audio Cable input.
Stream audio data to server.
Reference for Virtual Audio Cable:
https://www.howtogeek.com/364369/how-to-record-your-pc%E2%80%99s-audio-with-virtual-audio-cable/
https://www.vb-audio.com/Cable/index.htm
