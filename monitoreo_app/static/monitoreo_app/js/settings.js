// monitoreo_app/static/monitoreo_app/js/settings.js

// ============================================
// MODAL DE AYUDA PARA TELEGRAM
// ============================================
window.abrirAyudaTelegram = function() {
    const modal = document.getElementById('ayudaTelegramModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
    
    // Animación de entrada
    gsap.fromTo(modal.querySelector('.glass-panel'), 
        { scale: 0.95, opacity: 0, y: 20 }, 
        { scale: 1, opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }
    );
};

window.cerrarAyudaTelegram = function() {
    const modal = document.getElementById('ayudaTelegramModal');
    gsap.to(modal.querySelector('.glass-panel'), {
        scale: 0.95,
        opacity: 0,
        y: 20,
        duration: 0.2,
        ease: "power3.in",
        onComplete: () => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';
        }
    });
};

// Cerrar modal al hacer clic fuera
document.addEventListener('click', function(event) {
    const modal = document.getElementById('ayudaTelegramModal');
    if (event.target === modal) {
        window.cerrarAyudaTelegram();
    }
});

// Cerrar modal con tecla ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('ayudaTelegramModal');
        if (!modal.classList.contains('hidden')) {
            window.cerrarAyudaTelegram();
        }
    }
});

// ============================================
// MOSTRAR/OCULTAR CAMPOS SENSIBLES
// ============================================
window.mostrarCampo = function(campoId) {
    const mostrado = document.getElementById(campoId + '_mostrado');
    const visible = document.getElementById(campoId + '_visible');
    
    if (mostrado && visible) {
        mostrado.style.display = 'none';
        visible.classList.remove('hidden');
        visible.style.display = 'flex';
    }
};

window.ocultarCampo = function(campoId) {
    const mostrado = document.getElementById(campoId + '_mostrado');
    const visible = document.getElementById(campoId + '_visible');
    
    if (mostrado && visible) {
        visible.classList.add('hidden');
        visible.style.display = 'none';
        mostrado.style.display = 'flex';
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