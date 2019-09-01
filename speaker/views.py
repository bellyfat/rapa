from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
import pyaudio

# Create your views here.
p = pyaudio.PyAudio()

def index(request):
    template = loader.get_template('speaker/index.html')
    return HttpResponse(template.render(None, request))

def get_input_device_list(request):
    global p
    input_device_list = {}
    for device_index in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(device_index)
        if device_info['maxInputChannels'] is not 0:
            input_device_list[device_index] = device_info
    response = JsonResponse(input_device_list)
    return response

def get_output_device_list(request):
    global p
    output_device_list = {}
    for device_index in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(device_index)
        if device_info['maxOutputChannels'] is not 0:
            output_device_list[device_index] = device_info
    response = JsonResponse(output_device_list)
    return response