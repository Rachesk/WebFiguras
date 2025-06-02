from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('index', views.index, name='index'),
    path('carrito', views.carrito, name='carrito'),
    path('contacto', views.contacto, name='contacto'),
    path('vestuario', views.vestuario, name='vestuario'),
    path('inicioSesion/', views.inicioSesion, name='inicioSesion'),
    path('preguntas', views.preguntas, name='preguntas'),
    path('otros', views.otros, name='otros'),
    path('figuras', views.figuras, name='figuras'),
    path('register/', views.register_view, name='register'),  # CORREGIDO
    path('seguimiento', views.seguimiento, name='seguimiento'),
    path('transbank/', views.transbank_init, name='transbank'),
    path('transbank/return/', views.transbank_return, name='transbank_return'),
    path('logout/', views.logout_view, name='logout'),
]
