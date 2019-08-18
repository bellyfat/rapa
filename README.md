# rapa
Remote Asynchronous Peripheral Access

Virtual environment created using Pipenv
pipenv install
pipenv shell
pipenv run

The idea of this project is to expose attached peripherals such as mouse, keyboard, speaker or mass storage to web applications.

API in REST API

Making the computer into a webserver

Django
django-admin startproject myproject .
python manage.py startapp polls
python migrate
# add polls app into settings.py
python manage.py runserver

Authentication

First is speaker
# Deprecated
Play song from browser
howler.js to play audio
socket to recieve audio data
open socket
authenticate
send audio
# Update
Play audio on server (Python, wav file, mp3 converter)
Channel socket server
receive audio packet from socket, in chunks
browser connect to socket
browser upload audio file through socket

on application side, install Virtual Audio Cable to route output audio to input
use pyaudio at application side to read from the input device provided by Virtual Audio Cable
use pyaudio at server side to output to real speaker
Reference for Virtual Audio Cable:
https://www.howtogeek.com/364369/how-to-record-your-pc%E2%80%99s-audio-with-virtual-audio-cable/
https://www.vb-audio.com/Cable/index.htm
