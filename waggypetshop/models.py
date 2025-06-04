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


class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d-%m-%Y %H:%M')}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    

class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrito')

    def __str__(self):
        return f"Carrito de {self.usuario.username}"
    
class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
class OrdenTransbank(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    buy_order = models.CharField(max_length=40, unique=True)
    session_id = models.CharField(max_length=61)
    amount = models.IntegerField()
    token = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=20, default='CREATED')
    respuesta_transbank = models.JSONField(null=True, blank=True)  # Campo nuevo
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Orden {self.buy_order} - {self.amount}"
    
    class Meta:
        verbose_name = "Orden Transbank"
        verbose_name_plural = "Órdenes Transbank"