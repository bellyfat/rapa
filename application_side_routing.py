#!/usr/bin/env python

import asyncio
import websockets
import pyaudio
import wave
import sys
import time

CHUNK = 1024*512

wf = wave.open('test.wav', 'rb')

async def hello(uri):
    async with websockets.connect(uri) as websocket:
        #await websocket.send("Hello world!")
        data = wf.readframes(CHUNK)
        #await websocket.send(data)
        #text = await websocket.recv()
        #print("Should wait: ", text)
        ##time.sleep(CHUNK/44100)
        #time.sleep(int(text))
        #data = wf.readframes(CHUNK)
        #await websocket.send(data)
        #text = await websocket.recv()
        #print("Should wait: ", text)
        #time.sleep(int(text))
        #time.sleep(2)
        total = 0

        while data:
            #stream.write(data)
            await websocket.send(data)
            data = wf.readframes(CHUNK)
            #response = await websocket.recv()
            #time.sleep(int(response))
            #if len(data) < CHUNK:
            #    print(data)
            total = total + len(data)
        # wait a bit more for the buffered data to finish
        time.sleep(2)
        print("Read complete")
        print(total)

asyncio.get_event_loop().run_until_complete(
    hello('ws://localhost:8000/ws/speaker/audioplayback/'))