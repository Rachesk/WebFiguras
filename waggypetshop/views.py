from django.shortcuts import render

# Create your views here.
def index(request):
    context={}
    return render(request,'waggypetshop/index.html',context)

def carrito(request):
    return render(request, 'waggypetshop/carrito.html')

def contacto(request):
    return render(request, 'waggypetshop/Contacto.html')

def vestuario(request):
    return render(request, 'waggypetshop/vestuario.html')

def inicioSesion(request):
    return render(request, 'waggypetshop/inicioSesion.html')

def preguntas(request):
    return render(request, 'waggypetshop/preguntas.html')

def otros(request):
    return render(request, 'waggypetshop/otros.html')

def figuras(request):
    return render(request, 'waggypetshop/figuras.html')

def register(request):
    return render(request, 'waggypetshop/register.html')

def seguimiento(request):
    return render(request, 'waggypetshop/seguimiento.html')



from django.shortcuts import redirect, render
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType
from django.urls import reverse

# ConfiguraConfiguracion  credenciales de prueba
Transaction.commerce_code = '597055555532'
Transaction.api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'
Transaction.integration_type = IntegrationType.TEST

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







#######VALIDACION DE PAGOS "FALLIDOS O EXITOSO"######
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from transbank.webpay.webpay_plus.transaction import Transaction

@csrf_exempt
def transbank_return(request):
    token = request.GET.get('token_ws') or request.POST.get('token_ws')

    if not token:
        return render(request, 'pago_fallido.html', {'error': 'Token no encontrado'})

    transaction = Transaction()

    try:
        response = transaction.commit(token)

        # TEMPORAL: Mostrar toda la respuesta en consola
        print("RESPUESTA TRANSBANK:")
        print(response)

        if response['status'] == 'AUTHORIZED':
            return render(request, 'pago_exitoso.html', {'response': response})
        else:
            return render(request, 'pago_fallido.html', {'response': response})

    except Exception as e:
        print("Error al procesar el pago:", str(e))
        return render(request, 'pago_fallido.html', {'error': str(e)})

