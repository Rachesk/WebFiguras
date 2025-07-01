from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse

#########################################PRUEBA AUTENTICACION #################################################################


from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse

class RegisterViewTestCase(TestCase):
    def setUp(self):
        # Crear los grupos necesarios para las pruebas
        Group.objects.create(name='Bodeguero')
        Group.objects.create(name='Contador')
        Group.objects.create(name='Vendedor')

    def test_register_success(self):
        # Probar el registro exitoso de un usuario con contraseñas coincidentes
        response = self.client.post(reverse('register'), {
            'username': 'usuario1',
            'email': 'usuario1@test.com',
            'password': 'password123',
            'password2': 'password123',
        })

        # Verificar que el registro fue exitoso y que redirige a la página de inicio de sesión
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('inicioSesion'))

    def test_password_mismatch(self):
        # Intentar registrar un usuario con contraseñas que no coinciden
        response = self.client.post(reverse('register'), {
            'username': 'usuario2',
            'email': 'usuario2@test.com',
            'password': 'password123',
            'password2': 'password124',  # Contraseña diferente
        })

        # Verificar que la vista redirige al formulario de registro
        self.assertRedirects(response, reverse('register'))

        # Verificar que el mensaje de error esté presente
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "Las contraseñas no coinciden")

    def test_username_taken(self):
        # Crear un usuario con el mismo nombre de usuario
        User.objects.create_user(username='usuario3', email='usuario3@test.com', password='password123')

        # Intentar registrar otro usuario con el mismo nombre
        response = self.client.post(reverse('register'), {
            'username': 'usuario3',  # Nombre de usuario duplicado
            'email': 'usuario4@test.com',
            'password': 'password123',
            'password2': 'password123',
        })

        # Verificar que la vista redirige al formulario de registro
        self.assertRedirects(response, reverse('register'))

        # Verificar que el mensaje de error esté presente
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "El nombre de usuario ya existe")

    def test_role_assignment_bodeguero(self):
        # Probar asignación de rol 'Bodeguero' cuando el nombre de usuario contiene 'bodeguero'
        response = self.client.post(reverse('register'), {
            'username': 'bodeguero123',
            'email': 'bodeguero123@test.com',
            'password': 'password123',
            'password2': 'password123',
        })

        # Verificar que el usuario haya sido asignado al grupo Bodeguero
        user = User.objects.get(username='bodeguero123')
        self.assertTrue(user.groups.filter(name='Bodeguero').exists())

    def test_role_assignment_contador(self):
        # Probar asignación de rol 'Contador' cuando el nombre de usuario contiene 'contador'
        response = self.client.post(reverse('register'), {
            'username': 'contador123',
            'email': 'contador123@test.com',
            'password': 'password123',
            'password2': 'password123',
        })

        # Verificar que el usuario haya sido asignado al grupo Contador
        user = User.objects.get(username='contador123')
        self.assertTrue(user.groups.filter(name='Contador').exists())

    def test_role_assignment_vendedor(self):
        # Probar asignación de rol 'Vendedor' cuando el nombre de usuario contiene 'vendedor'
        response = self.client.post(reverse('register'), {
            'username': 'vendedor123',
            'email': 'vendedor123@test.com',
            'password': 'password123',
            'password2': 'password123',
        })

        # Verificar que el usuario haya sido asignado al grupo Vendedor
        user = User.objects.get(username='vendedor123')
        self.assertTrue(user.groups.filter(name='Vendedor').exists())

    def test_no_role_assignment(self):
        # Probar que no se asigna un rol si el nombre de usuario no contiene las palabras clave
        response = self.client.post(reverse('register'), {
            'username': 'usuario123',
            'email': 'usuario123@test.com',
            'password': 'password123',
            'password2': 'password123',
        })

        # Verificar que el usuario no tenga grupo asignado
        user = User.objects.get(username='usuario123')
        self.assertFalse(user.groups.exists())


######################################################################################################################################################################

#PRUEBAS CARRITO / PRUEBAS UNITARIAS PARA EL PAGO CON TRANSBANK (asegurarse de tener instalado el sdk de transbank mas django, mas entorno activado)

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from waggypetshop.models import Carrito, Producto, ItemCarrito, OrdenTransbank, Venta, DetalleVenta
from django.contrib import messages
from unittest.mock import patch

class CarritoTestCase(TestCase):

    def setUp(self):
        # Crear usuario para las pruebas
        self.user = User.objects.create_user(username='usuario1', password='password123')
        
        # Crear productos para el carrito
        self.producto1 = Producto.objects.create(nombre='Figura 1', precio=1000, stock=10)
        self.producto2 = Producto.objects.create(nombre='Figura 2', precio=2000, stock=5)
        
        # Crear un carrito de compras para el usuario
        self.carrito, _ = Carrito.objects.get_or_create(usuario=self.user)
    
    def test_carrito_creation(self):
        # Verificar que el carrito se haya creado correctamente
        self.assertEqual(self.carrito.usuario, self.user)

    def test_add_item_to_carrito(self):
        # Agregar productos al carrito
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto1, cantidad=2)
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto2, cantidad=3)

        # Verificar que los productos se agregaron correctamente al carrito
        self.assertEqual(self.carrito.itemcarrito_set.count(), 2)

    def test_check_stock_warning(self):
        # Intentar agregar más productos de los que hay en stock
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto1, cantidad=15)  # Más de 10 disponibles

        # Hacer la petición para verificar el stock
        response = self.client.get(reverse('carrito'))  # La vista de carrito

        # Verificar que se muestra el mensaje de advertencia por falta de stock
        self.assertContains(response, f"El producto {self.producto1.nombre} no tiene suficiente stock")

    def test_calculate_total_carrito(self):
        # Agregar productos al carrito
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto1, cantidad=2)
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto2, cantidad=3)

        # Verificar que el total se calcule correctamente
        total_esperado = (2 * self.producto1.precio) + (3 * self.producto2.precio)
        self.assertEqual(self.carrito.calcular_total(), total_esperado)

class TransbankTestCase(TestCase):

    def setUp(self):
        # Crear usuario para las pruebas
        self.user = User.objects.create_user(username='usuario1', password='password123')
        
        # Crear productos para el carrito
        self.producto1 = Producto.objects.create(nombre='Figura 1', precio=1000, stock=10)
        self.producto2 = Producto.objects.create(nombre='Figura 2', precio=2000, stock=5)
        
        # Crear un carrito de compras para el usuario
        self.carrito, _ = Carrito.objects.get_or_create(usuario=self.user)

        # Agregar productos al carrito
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto1, cantidad=2)
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto2, cantidad=3)

    @patch('waggypetshop.views.Transaction')
    def test_transbank_init_empty_cart(self, MockTransaction):
        # Simular un carrito vacío
        self.carrito.itemcarrito_set.all().delete()

        # Realizar el pago
        response = self.client.post(reverse('transbank_init'))

        # Verificar que se redirige con el mensaje de carrito vacío
        self.assertRedirects(response, reverse('carrito'))
        self.assertContains(response, "Tu carrito está vacío")

    @patch('waggypetshop.views.Transaction')
    def test_transbank_init_insufficient_stock(self, MockTransaction):
        # Intentar agregar más productos de los que hay en stock
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto1, cantidad=15)  # Más de 10 disponibles

        # Realizar el pago
        response = self.client.post(reverse('transbank_init'))

        # Verificar que se redirige con el mensaje de stock insuficiente
        self.assertRedirects(response, reverse('carrito'))
        self.assertContains(response, f"El producto {self.producto1.nombre} no tiene suficiente stock")

    @patch('waggypetshop.views.Transaction')
    def test_transbank_init_successful_payment(self, MockTransaction):
        # Simular una transacción exitosa de Transbank
        mock_transaction = MockTransaction.return_value
        mock_transaction.create.return_value = {'url': 'http://example.com', 'token': 'dummy_token'}
        
        # Realizar el pago
        response = self.client.post(reverse('transbank_init'))

        # Verificar que la transacción se haya creado y se redirige correctamente
        self.assertRedirects(response, 'http://example.com?token_ws=dummy_token')

        # Verificar que se haya creado una orden en la base de datos
        orden = OrdenTransbank.objects.get(token='dummy_token')
        self.assertEqual(orden.usuario, self.user)

    @patch('waggypetshop.views.Transaction')
    def test_transbank_init_invalid_amount(self, MockTransaction):
        # Hacer que el monto sea inválido
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto1, cantidad=-1)  # Cantidad negativa

        # Realizar el pago
        response = self.client.post(reverse('transbank_init'))

        # Verificar que se redirige con el mensaje de monto inválido
        self.assertRedirects(response, reverse('carrito'))
        self.assertContains(response, "Monto inválido para la transacción")



##################################################################PRUEBA PASARELA DE PAGO(INICIAR EL PROCESO DE WEBPAY / SIMULAR UN PAGO EXITOSO Y VERIFICAR / SIMULAR UN PAGO FALLIDO)#################################################################


from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from waggypetshop.models import Carrito, Producto, ItemCarrito, OrdenTransbank, Venta, DetalleVenta
from django.contrib import messages

class WebpayPaymentTestCase(TestCase):

    def setUp(self):
        # Crear usuario para las pruebas
        self.user = User.objects.create_user(username='usuario1', password='password123')
       
        # Crear productos para el carrito
        self.producto1 = Producto.objects.create(nombre='Figura 1', precio=1000, stock=10)
        self.producto2 = Producto.objects.create(nombre='Figura 2', precio=2000, stock=5)
       
        # Crear un carrito de compras para el usuario
        self.carrito, _ = Carrito.objects.get_or_create(usuario=self.user)

        # Agregar productos al carrito
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto1, cantidad=2)
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto2, cantidad=3)

    @patch('waggypetshop.views.Transaction')
    def test_transbank_init_successful_payment(self, MockTransaction):
        # Simular una transacción exitosa de Transbank
        mock_transaction = MockTransaction.return_value
        mock_transaction.create.return_value = {'url': 'http://example.com', 'token': 'dummy_token'}

        # Realizar el pago
        response = self.client.post(reverse('transbank_init'))

        # Verificar que la transacción se haya creado y se redirige correctamente
        self.assertRedirects(response, 'http://example.com?token_ws=dummy_token')

        # Verificar que se haya creado una orden en la base de datos
        orden = OrdenTransbank.objects.get(token='dummy_token')
        self.assertEqual(orden.usuario, self.user)

    @patch('waggypetshop.views.Transaction')
    def test_transbank_init_failed_payment(self, MockTransaction):
        # Simular un pago fallido (por ejemplo, tarjeta rechazada)
        mock_transaction = MockTransaction.return_value
        mock_transaction.create.return_value = {'url': '', 'token': '', 'status': 'REJECTED'}

        # Realizar el pago
        response = self.client.post(reverse('transbank_init'))

        # Verificar que se redirige con un mensaje de error
        self.assertRedirects(response, reverse('carrito'))
        self.assertContains(response, "Error en la respuesta de Transbank")

    @patch('waggypetshop.views.Transaction')
    def test_transbank_return_successful_payment(self, MockTransaction):
        # Simular una respuesta exitosa de Transbank al recibir la devolución
        mock_transaction = MockTransaction.return_value
        mock_transaction.commit.return_value = {'status': 'AUTHORIZED'}

        # Crear la orden en la base de datos (simulación de pago exitoso)
        orden = OrdenTransbank.objects.create(
            usuario=self.user,
            buy_order='123',
            session_id='456',
            amount=5000,
            token='dummy_token',
            status='INITIALIZED'
        )

        # Simular el retorno de la transacción desde Transbank
        response = self.client.get(reverse('transbank_return'), {'token_ws': 'dummy_token'})

        # Verificar que la orden se haya actualizado correctamente
        orden.refresh_from_db()
        self.assertEqual(orden.status, 'AUTHORIZED')

        # Verificar que se haya creado una venta
        venta = Venta.objects.get(usuario=self.user)
        self.assertEqual(venta.total, 5000)

        # Verificar que los detalles de la venta y la actualización del stock sean correctos
        detalle_venta = DetalleVenta.objects.filter(venta=venta)
        self.assertEqual(detalle_venta.count(), 2)  # Verificar que se hayan agregado dos productos
        self.assertEqual(self.producto1.stock, 8)  # El stock debe haberse reducido correctamente
        self.assertEqual(self.producto2.stock, 2)

    @patch('waggypetshop.views.Transaction')
    def test_transbank_return_failed_payment(self, MockTransaction):
        # Simular una respuesta fallida de Transbank al recibir la devolución
        mock_transaction = MockTransaction.return_value
        mock_transaction.commit.return_value = {'status': 'REJECTED'}

        # Crear la orden en la base de datos (simulación de pago fallido)
        orden = OrdenTransbank.objects.create(
            usuario=self.user,
            buy_order='123',
            session_id='456',
            amount=5000,
            token='dummy_token',
            status='INITIALIZED'
        )

        # Simular el retorno de la transacción desde Transbank
        response = self.client.get(reverse('transbank_return'), {'token_ws': 'dummy_token'})

        # Verificar que la orden se haya actualizado correctamente
        orden.refresh_from_db()
        self.assertEqual(orden.status, 'REJECTED')

        # Verificar que el pago fallido redirige a la página de pago fallido
        self.assertTemplateUsed(response, 'waggypetshop/pago_fallido.html')




