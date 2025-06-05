from django.urls import path
from . import views
from waggypetshop import views

urlpatterns = [
    path('index', views.index, name='index'),
    path('carrito', views.carrito, name='carrito'),
    path('contacto', views.contacto, name='contacto'),
    path('vestuario', views.vestuario, name='vestuario'),
    path('inicioSesion/', views.inicioSesion, name='inicioSesion'),
    path('preguntas', views.preguntas, name='preguntas'),
    path('otros', views.otros, name='otros'),
    path('figuras', views.figuras, name='figuras'),
    path('register/', views.register_view, name='register'),
    path('seguimiento', views.seguimiento, name='seguimiento'),
    path('transbank/', views.transbank_init, name='transbank'),
    path('transbank/return/', views.transbank_return, name='transbank_return'),
    path('logout/', views.logout_view, name='logout'),

    # Rutas por rol
    path('bodeguero/', views.agregar_producto, name='rol_bodeguero'),
    path('bodeguero/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('contador/', views.rol_contador, name='rol_contador'),
    path('bodeguero/agregar/', views.agregar_producto, name='agregar_producto'),
    path('waggypetshop/bodeguero/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('waggypetshop/historial/', views.historial_movimientos, name='historial'),
    path('waggypetshop/vendedor/', views.vista_vendedor, name='vista_vendedor'),
    path('waggypetshop/agregar_al_carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar_item_carrito/<int:item_id>/', views.eliminar_item_carrito, name='eliminar_item_carrito'),
    path('', views.index, name='index'),
]
