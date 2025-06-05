/*Funcion para mostrar/ocultar contraseña*/
function visibilidadPassword() {
    const passCampo = $("#password");
    const icono = $("#mostrarIcono");
    if (passCampo.attr("type") === "password") {
        passCampo.attr("type", "text");
        icono.text("Ocultar");
    } else {
        passCampo.attr("type", "password");
        icono.text("Mostrar");
    }
}

$(document).ready(function() {
    $("#botonPassword").on('click', visibilidadPassword);
});

// Función para mostrar alertas
function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    const alertDiv = document.createElement('div');
    
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Eliminar la alerta después de 5 segundos
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Función para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Función para agregar al carrito
function addToCart(productoId, btnElement) {
    const btn = btnElement || event.target;
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';

    fetch("{% url 'agregar_al_carrito' %}", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ producto_id: productoId, cantidad: 1 })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('success', data.mensaje);
            updateCartCount();
        } else {
            showAlert('danger', data.mensaje);
        }
    })
    .catch(error => {
        showAlert('danger', 'Error al comunicarse con el servidor');
        console.error('Error:', error);
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalText;
    });
}

// Función para actualizar el contador del carrito
function updateCartCount() {
    const countElement = document.querySelector('#cart-count');
    if (countElement) {
        fetch("{% url 'carrito' %}")
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newCount = doc.querySelector('#cart-count')?.textContent || '0';
            countElement.textContent = newCount;
        })
        .catch(error => {
            console.error('Error al actualizar el carrito:', error);
        });
    }
}