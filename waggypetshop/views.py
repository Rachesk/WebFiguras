from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from .models import Producto, MovimientoStock, Venta, Carrito, ItemCarrito, DetalleVenta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime

from .forms import ProductoForm

import random
import string
from django.utils import timezone
from django.db.models import Sum, F, FloatField

from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_type import IntegrationType

from .models import OrdenTransbank
import logging
logger = logging.getLogger(__name__)


# CONFIGURACIÓN TRANSBANK (TEST)
commerce_code = IntegrationCommerceCodes.WEBPAY_PLUS
api_key = IntegrationApiKeys.WEBPAY
integration_type = IntegrationType.TEST

tx_options = WebpayOptions(commerce_code, api_key, integration_type)


def index(request):
    return render(request, 'waggypetshop/index.html')

@login_required
# views.py
@login_required
def carrito(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    items = ItemCarrito.objects.filter(carrito=carrito).select_related('producto')
    
    # Verificar stock para cada item
    for item in items:
        if not item.producto.verificar_stock(item.cantidad):
            messages.warning(
                request, 
                f"El producto {item.producto.nombre} no tiene suficiente stock. " 
                f"Stock actual: {item.producto.stock}, en carrito: {item.cantidad}"
            )
    
    datos = [{
        'id': item.id,
        'producto': {
            'nombre': item.producto.nombre,
            'precio': item.producto.precio,
            'stock': item.producto.stock,  # Añadir stock a la respuesta
        },
        'cantidad': item.cantidad
    } for item in items]
    
    return render(request, 'waggypetshop/carrito.html', {
        'items': items,
        'items_json': json.dumps(datos, cls=DjangoJSONEncoder)
    })

def contacto(request):
    return render(request, 'waggypetshop/Contacto.html')

def vestuario(request):
    productos = Producto.objects.filter(categoria="Polera manga corta")
    return render(request, 'waggypetshop/vestuario.html', {'productos': productos})

def preguntas(request):
    return render(request, 'waggypetshop/preguntas.html')

def otros(request):
    productos = Producto.objects.filter(categoria__icontains="model kit")
    return render(request, 'waggypetshop/otros.html', {'productos': productos})

def figuras(request):
    productos = Producto.objects.filter(categoria__icontains="Figura")
    return render(request, 'waggypetshop/figuras.html', {'productos': productos})

def seguimiento(request):
    return render(request, 'waggypetshop/seguimiento.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        if 'bodeguero' in username.lower():
            grupo = Group.objects.get(name='Bodeguero')
        elif 'contador' in username.lower():
            grupo = Group.objects.get(name='Contador')
        elif 'vendedor' in username.lower():
            grupo = Group.objects.get(name='Vendedor')
        else:
            grupo = None
        if grupo:
            user.groups.add(grupo)

        Carrito.objects.create(usuario=user)
        messages.success(request, "Cuenta creada exitosamente. Inicia sesión.")
        return redirect('inicioSesion')

    return render(request, 'waggypetshop/register.html')

def inicioSesion(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.groups.filter(name='Bodeguero').exists():
                return redirect('rol_bodeguero')
            elif user.groups.filter(name='Contador').exists():
                return redirect('rol_contador')
            elif user.groups.filter(name='Vendedor').exists():
                return redirect('vista_vendedor')
            else:
                return redirect('index')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return redirect('inicioSesion')

    return render(request, 'waggypetshop/inicioSesion.html')

def logout_view(request):
    logout(request)
    return redirect('index')

###TRANSBANK#############################################################################################################

@login_required
def transbank_init(request):
    try:
        logger.info("Iniciando transacción Transbank")
        
        # Validar carrito y monto
        carrito = Carrito.objects.get(usuario=request.user)
        items = ItemCarrito.objects.filter(carrito=carrito).select_related('producto')
        
        if not items.exists():
            logger.warning("Carrito vacío")
            messages.error(request, "Tu carrito está vacío")
            return redirect('carrito')
        
        # Verificación de stock antes de proceder al pago
        for item in items:
            if not item.producto.verificar_stock(item.cantidad):
                messages.error(
                    request,
                    f"El producto {item.producto.nombre} no tiene suficiente stock. "
                    f"Stock actual: {item.producto.stock}, en carrito: {item.cantidad}"
                )
                return redirect('carrito')
        
        amount = sum(item.producto.precio * item.cantidad for item in items)
        logger.info(f"Monto calculado: {amount}")
        
        if amount <= 0:
            logger.warning(f"Monto inválido: {amount}")
            messages.error(request, "Monto inválido para la transacción")
            return redirect('carrito')

        # Generar identificadores
        buy_order = f"{request.user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        session_id = request.session.session_key or f"sesion_{request.user.id}"
        
        logger.info(f"Creando orden - buy_order: {buy_order}, session_id: {session_id}")

        # Crear transacción en Transbank
        return_url = request.build_absolute_uri(reverse('transbank_return'))
        logger.info(f"Return URL: {return_url}")

        transaction = Transaction(tx_options)
        response = transaction.create(
            buy_order=buy_order,
            session_id=session_id,
            amount=amount,
            return_url=return_url
        )
        
        logger.info(f"Respuesta Transbank: {response}")

        if 'url' not in response or 'token' not in response:
            logger.error("Respuesta de Transbank incompleta")
            messages.error(request, "Error en la respuesta de Transbank")
            return redirect('carrito')

        # Guardar la transacción en la base de datos
        orden = OrdenTransbank.objects.create(
            usuario=request.user,
            buy_order=buy_order,
            session_id=session_id,
            amount=amount,
            token=response['token'],
            status='INITIALIZED'
        )

        return redirect(response['url'] + '?token_ws=' + response['token'])

    except Carrito.DoesNotExist:
        logger.error("El usuario no tiene carrito creado")
        messages.error(request, "No tienes un carrito activo")
        return redirect('carrito')
    except Exception as e:
        logger.error(f"Error en transbank_init: {str(e)}", exc_info=True)
        messages.error(request, f"Error al procesar el pago: {str(e)}")
        return redirect('carrito')
    
#######################################################################################################################

@csrf_exempt
def transbank_return(request):
    token = request.GET.get('token_ws') or request.POST.get('token_ws')
    
    if not token:
        logger.error("Token no encontrado en transbank_return")
        return render(request, 'waggypetshop/pago_fallido.html', {'error': 'Token no encontrado'})

    try:
        transaction = Transaction(tx_options)  # Usar las opciones configuradas
        response = transaction.commit(token)
        
        # Buscar la orden correspondiente
        orden = OrdenTransbank.objects.get(token=token)
        orden.respuesta_transbank = response
        orden.status = response.get('status', 'UNKNOWN')
        orden.save()
        
        if response['status'] == 'AUTHORIZED':
            # Procesar pago exitoso
            venta = Venta.objects.create(
                usuario=request.user,
                total=orden.amount,
                fecha=timezone.now()
            )
            
            carrito = Carrito.objects.get(usuario=request.user)
            items = ItemCarrito.objects.filter(carrito=carrito)
            
            for item in items:
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.producto.precio
                )
                # Actualizar stock
                item.producto.stock -= item.cantidad
                item.producto.save()
            
            # Vaciar carrito
            items.delete()
            
            return render(request, 'waggypetshop/pago_exitoso.html', {
                'response': response,
                'venta': venta
            })
        else:
            return render(request, 'waggypetshop/pago_fallido.html', {
                'response': response
            })
            
    except OrdenTransbank.DoesNotExist:
        logger.error(f"Orden no encontrada para token: {token}")
        return render(request, 'waggypetshop/pago_fallido.html', {
            'error': 'Orden no encontrada en nuestros registros'
        })
    except Exception as e:
        logger.error(f"Error en transbank_return: {str(e)}", exc_info=True)
        return render(request, 'waggypetshop/pago_fallido.html', {
            'error': str(e)
        })
    
#######################################################################################################################    

def es_bodeguero(user):
    return user.groups.filter(name='Bodeguero').exists()

def es_contador(user):
    return user.groups.filter(name='Contador').exists()

def es_vendedor(user):
    return user.groups.filter(name='Vendedor').exists()

@login_required
@user_passes_test(es_bodeguero)
def panel_bodeguero(request):
    form = ProductoForm()
    productos = Producto.objects.all()
    return render(request, 'waggypetshop/rol_bodeguero.html', {'form': form, 'productos': productos})

@login_required
@user_passes_test(es_vendedor)
def vista_vendedor(request):
    ventas = Venta.objects.select_related('usuario').prefetch_related('detalles__producto').order_by('-fecha')

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio:
        ventas = ventas.filter(fecha__date__gte=fecha_inicio)
    if fecha_fin:
        ventas = ventas.filter(fecha__date__lte=fecha_fin)

    # Calcular total vendido para las ventas filtradas
    total_vendido = DetalleVenta.objects.filter(venta__in=ventas).aggregate(
        total=Sum(F('cantidad') * F('precio_unitario'), output_field=FloatField())
    )['total'] or 0

    return render(request, 'waggypetshop/vendedor.html', {
        'ventas': ventas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_vendido': total_vendido
    })

@login_required
@user_passes_test(es_contador)
def rol_contador(request):
    estado = request.GET.get('estado')  # puede ser AUTHORIZED o FAILED

    pagos = OrdenTransbank.objects.all().order_by('-fecha_creacion')
    if estado in ['AUTHORIZED', 'FAILED']:
        pagos = pagos.filter(status=estado)

    total_ventas = pagos.filter(status='AUTHORIZED').aggregate(total=Sum('amount'))['total'] or 0
    total_transacciones = pagos.count()
    ganancias_netas = round(total_ventas * 0.8)  # por ejemplo, 80% utilidad

    return render(request, 'waggypetshop/rol_contador.html', {
        'pagos': pagos,
        'total_ventas': total_ventas,
        'total_transacciones': total_transacciones,
        'ganancias_netas': ganancias_netas,
        'estado_seleccionado': estado
    })

@login_required
@user_passes_test(es_bodeguero)
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            nuevo_producto = form.save()
            MovimientoStock.objects.create(producto=nuevo_producto, usuario=request.user, accion='CREACIÓN')
            return redirect('rol_bodeguero')
    else:
        form = ProductoForm()
    productos = Producto.objects.all()
    return render(request, 'waggypetshop/rol_bodeguero.html', {'form': form, 'productos': productos})

@login_required
@user_passes_test(es_bodeguero)
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre')
        producto.precio = request.POST.get('precio')
        producto.stock = request.POST.get('stock')
        producto.categoria = request.POST.get('categoria')
        producto.descripcion = request.POST.get('descripcion')
        producto.save()
        MovimientoStock.objects.create(producto=producto, usuario=request.user, accion='EDICIÓN')
        return redirect('rol_bodeguero')
    return render(request, 'waggypetshop/editar_producto.html', {'producto': producto})

@login_required
@user_passes_test(es_bodeguero)
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    producto.delete()
    MovimientoStock.objects.create(producto=producto, usuario=request.user, accion='ELIMINACIÓN')
    return redirect('rol_bodeguero')

@login_required
def historial_movimientos(request):
    movimientos = MovimientoStock.objects.all().order_by('-fecha')
    return render(request, 'waggypetshop/historial.html', {'movimientos': movimientos})


@require_POST
@login_required
def agregar_al_carrito(request):
    try:
        data = json.loads(request.body)
        producto_id = data.get('producto_id')
        cantidad = int(data.get('cantidad', 1))
        
        if cantidad < 1:
            return JsonResponse({
                'success': False, 
                'mensaje': 'La cantidad debe ser al menos 1'
            }, status=400)

        producto = Producto.objects.get(id=producto_id)
        
        # Verificar stock antes de agregar
        if not producto.verificar_stock(cantidad):
            return JsonResponse({
                'success': False,
                'mensaje': f'No hay suficiente stock disponible. Solo quedan {producto.stock} unidades.'
            }, status=400)
            
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        item, creado = ItemCarrito.objects.get_or_create(
            carrito=carrito, 
            producto=producto
        )

        if not creado:
            # Verificar si al agregar la cantidad supera el stock
            if not producto.verificar_stock(item.cantidad + cantidad):
                return JsonResponse({
                    'success': False,
                    'mensaje': f'No hay suficiente stock disponible. Solo quedan {producto.stock} unidades.'
                }, status=400)
            item.cantidad += cantidad
        else:
            item.cantidad = cantidad

        item.save()
        return JsonResponse({
            'success': True, 
            'mensaje': 'Producto agregado al carrito'
        })
        
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'mensaje': 'Producto no encontrado'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'mensaje': f'Error inesperado: {str(e)}'
        }, status=500)

@require_POST
@login_required
def eliminar_item_carrito(request, item_id):
    try:
        item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
        item.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)})