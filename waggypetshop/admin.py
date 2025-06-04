from django.contrib.auth.models import Group, Permission
from django.contrib import admin
from .models import Carrito, ItemCarrito, OrdenTransbank
from django.utils.html import format_html
from django.urls import reverse
# Register your models here.


bodeguero_group, created = Group.objects.get_or_create(name='Bodeguero')
contador_group, created = Group.objects.get_or_create(name='Contador')

admin.site.register(Carrito)
admin.site.register(ItemCarrito)
admin.site.register(OrdenTransbank)

admin.site.site_header = "Panel de Administración"
admin.site.index_title = "Administración"
admin.site.site_title = "Admin"

def custom_admin_view(request):
    return format_html('<a href="{}">Volver al sitio</a>', reverse('index'))


admin.site.site_header = format_html(
    'Panel de Administración — <a href="{}" style="color: #fff; text-decoration: underline;">Volver al sitio</a>',
    reverse('index')  # Usa el nombre de tu URL para la vista 'index'
)
admin.site.site_title = "Administración SakamotoToys"
admin.site.index_title = "Administración del sitio"