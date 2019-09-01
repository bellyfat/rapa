# chat/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_input_device_list/', views.get_input_device_list, name='get_input_device_list'),
    path('get_output_device_list/', views.get_output_device_list, name='get_output_device_list'),
]