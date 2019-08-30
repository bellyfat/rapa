# chat/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_device_list/', views.get_device_list, name='get_device_list'),
]