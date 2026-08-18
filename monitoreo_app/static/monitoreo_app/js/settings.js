// monitoreo_app/static/monitoreo_app/js/settings.js

// ============================================
// MOSTRAR/OCULTAR CAMPOS SENSIBLES
// ============================================
window.mostrarCampo = function(campoId) {
    console.log('Mostrando campo:', campoId);
    const mostrado = document.getElementById(campoId + '_mostrado');
    const visible = document.getElementById(campoId + '_visible');
    
    console.log('mostrado:', mostrado);
    console.log('visible:', visible);
    
    if (mostrado && visible) {
        mostrado.style.display = 'none';
        visible.classList.remove('hidden');
        visible.style.display = 'flex';
    } else {
        console.error('No se encontraron los elementos para:', campoId);
    }
};

window.ocultarCampo = function(campoId) {
    console.log('Ocultando campo:', campoId);
    const mostrado = document.getElementById(campoId + '_mostrado');
    const visible = document.getElementById(campoId + '_visible');
    
    console.log('mostrado:', mostrado);
    console.log('visible:', visible);
    
    if (mostrado && visible) {
        visible.classList.add('hidden');
        visible.style.display = 'none';
        mostrado.style.display = 'flex';
    } else {
        console.error('No se encontraron los elementos para:', campoId);
    }
};

// ============================================
// ENVIAR MENSAJE DE PRUEBA
// ============================================
window.enviarPrueba = function() {
    let token = document.getElementById('telegram_bot_token').value;
    let chatId = document.getElementById('telegram_chat_id').value;
    
    if (!token || !chatId) {
        alert('⚠️ Primero debes guardar el token y el chat ID');
        return;
    }
    
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/api/test-telegram/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ token: token, chat_id: chatId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Mensaje de prueba enviado correctamente');
        } else {
            alert('❌ Error al enviar mensaje: ' + data.message);
        }
    })
    .catch(error => {
        alert('❌ Error al enviar mensaje de prueba');
    });
};