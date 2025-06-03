from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from .models import Producto
from .forms import ProductoForm

from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType

# CONFIGURACIÓN TRANSBANK (TEST)
Transaction.commerce_code = '597055555532'
Transaction.api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'
Transaction.integration_type = IntegrationType.TEST

# ====================
# VISTAS PRINCIPALES
# ====================

def index(request):
    return render(request, 'waggypetshop/index.html')

def carrito(request):
    return render(request, 'waggypetshop/carrito.html')

def contacto(request):
    return render(request, 'waggypetshop/Contacto.html')

def vestuario(request):
    return render(request, 'waggypetshop/vestuario.html')

def preguntas(request):
    return render(request, 'waggypetshop/preguntas.html')

def otros(request):
    return render(request, 'waggypetshop/otros.html')

def figuras(request):
    return render(request, 'waggypetshop/figuras.html')

def seguimiento(request):
    return render(request, 'waggypetshop/seguimiento.html')


# ====================
# AUTH - REGISTRO / LOGIN / LOGOUT
# ====================

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
        user.save()
        messages.success(request, "Cuenta creada exitosamente. Inicia sesión.")
        return redirect('inicioSesion')

    return render(request, 'waggypetshop/register.html')


def inicioSesion(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Redirección automática según grupo
            if user.groups.filter(name='Bodeguero').exists():
                return redirect('rol_bodeguero')
            elif user.groups.filter(name='Contador').exists():
                return redirect('rol_contador')
            else:
                return redirect('index')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return redirect('inicioSesion')

    return render(request, 'waggypetshop/inicioSesion.html')


def logout_view(request):
    logout(request)
    return redirect('index')


# ====================
# TRANSBANK
# ====================

def transbank_init(request):
    buy_order = str(request.session.session_key) + "_order"
    session_id = request.session.session_key or "session1234"
    amount = int(request.POST.get('amount', 0))

    if amount <= 0:
        return redirect('carrito')

    return_url = request.build_absolute_uri(reverse('transbank_return'))
    transaction = Transaction()
    response = transaction.create(buy_order=buy_order, session_id=session_id, amount=amount, return_url=return_url)

    return redirect(response['url'] + '?token_ws=' + response['token'])


@csrf_exempt
def transbank_return(request):
    token = request.GET.get('token_ws') or request.POST.get('token_ws')

    if not token:
        return render(request, 'pago_fallido.html', {'error': 'Token no encontrado'})

    transaction = Transaction()

    try:
        response = transaction.commit(token)
        if response['status'] == 'AUTHORIZED':
            return render(request, 'pago_exitoso.html', {'response': response})
        else:
            return render(request, 'pago_fallido.html', {'response': response})

    except Exception as e:
        return render(request, 'pago_fallido.html', {'error': str(e)})


# ====================
# VISTAS POR ROL
# ====================

def es_bodeguero(user):
    return user.groups.filter(name='Bodeguero').exists()

def es_contador(user):
    return user.groups.filter(name='Contador').exists()

@login_required
@user_passes_test(es_bodeguero)
def panel_bodeguero(request):
    form = ProductoForm()
    productos = Producto.objects.all()
    return render(request, 'waggypetshop/rol_bodeguero.html', {
        'form': form,
        'productos': productos
    })

@login_required
@user_passes_test(es_contador)
def vista_contador(request):
    return render(request, 'waggypetshop/rol_contador.html')


@login_required
@user_passes_test(es_bodeguero)
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rol_bodeguero')
    else:
        form = ProductoForm()

    productos = Producto.objects.all()
    return render(request, 'waggypetshop/rol_bodeguero.html', {
        'form': form,
        'productos': productos
    })


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
        return redirect('rol_bodeguero')

    return render(request, 'waggypetshop/editar_producto.html', {'producto': producto})

def vestuario(request):
    productos = Producto.objects.filter(categoria="Polera manga corta")
    return render(request, 'waggypetshop/vestuario.html', {'productos': productos})

def figuras(request):
    productos = Producto.objects.filter(categoria__icontains="Figura")
    return render(request, 'waggypetshop/figuras.html', {'productos': productos})




