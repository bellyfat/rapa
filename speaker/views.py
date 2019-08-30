from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
import pyaudio

# Create your views here.

def index(request):
    template = loader.get_template('speaker/index.html')
    return HttpResponse(template.render(None, request))

def get_device_list(request):
    p = pyaudio.PyAudio()
    device_list = {}
    for device_index in range(p.get_device_count()):
        device_list[device_index] = p.get_device_info_by_index(device_index)
    response = JsonResponse(device_list)
    return response