#!/usr/bin/env python

import asyncio
import websockets
import pyaudio
import wave
import sys
import time

#CHUNK = 1024*512
CHUNK=1920

wf = wave.open('test.wav', 'rb')

async def hello(uri):
    from opus import encoder
    async with websockets.connect(uri) as websocket:
        CHANNELS = 2
        RATE = 48000
        encoder = encoder.Encoder(RATE,CHANNELS,'voip')
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
            encoded_data = encoder.encode(data, CHUNK)
            #await websocket.send(data)
            await websocket.send(encoded_data)
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
    hello('ws://192.168.0.104:8000/ws/speaker/audioplayback/'))