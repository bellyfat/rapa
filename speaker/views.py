from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

# Create your views here.

def index(request):
    template = loader.get_template('speaker/index.html')
    return HttpResponse(template.render(None, request))