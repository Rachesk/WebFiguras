from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Usuario(models.Model):
    nombre_usuario = models.CharField(primary_key=True, max_length=10)
    contraseña = models.CharField(max_length=20)
    email = models.EmailField(unique=True, max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre_usuario


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.IntegerField()
    stock = models.IntegerField()
    categoria = models.CharField(max_length=100, null=True, blank=True)  

    def __str__(self):
        return self.nombre
    
class MovimientoStock(models.Model):
    ACCIONES = [
        ('CREACIÓN', 'Creación'),
        ('EDICIÓN', 'Edición'),
        ('ELIMINACIÓN', 'Eliminación'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE) 
    accion = models.CharField(max_length=20, choices=ACCIONES)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.producto.nombre} - {self.accion} - {self.fecha.strftime('%d-%m-%Y %H:%M')}"