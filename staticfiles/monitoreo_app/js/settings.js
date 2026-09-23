// monitoreo_app/static/monitoreo_app/js/settings.js

// ============================================
// CSRF TOKEN
// ============================================
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

// ============================================
// NOTIFICACIONES TOAST
// ============================================
function mostrarNotificacion(mensaje, tipo = 'info') {
    const colores = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500',
        'warning': 'bg-yellow-500'
    };
    
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 ${colores[tipo] || 'bg-blue-500'} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-all transform translate-y-0 opacity-100`;
    toast.textContent = mensaje;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-4');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// TABS DE AJUSTES
// ============================================
window.cambiarTabAjustes = function(tab) {
    const tabGeneral = document.getElementById('tabGeneral');
    const tabUsuarios = document.getElementById('tabUsuarios');
    const contenidoGeneral = document.getElementById('contenidoGeneral');
    const contenidoUsuarios = document.getElementById('contenidoUsuarios');
    
    tabGeneral.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-gray-400 hover:text-white transition-colors';
    tabUsuarios.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-gray-400 hover:text-white transition-colors';
    
    contenidoGeneral.classList.add('hidden');
    contenidoUsuarios.classList.add('hidden');
    
    if (tab === 'general') {
        tabGeneral.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-blue-500 text-blue-400 transition-colors';
        contenidoGeneral.classList.remove('hidden');
    } else if (tab === 'usuarios') {
        tabUsuarios.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-purple-500 text-purple-400 transition-colors';
        contenidoUsuarios.classList.remove('hidden');
        window.cargarUsuarios(1);
    }
};

// ============================================
// MODAL DE AYUDA PARA TELEGRAM
// ============================================
window.abrirAyudaTelegram = function() {
    const modal = document.getElementById('ayudaTelegramModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
    
    gsap.fromTo(modal.querySelector('.glass-panel'), 
        { scale: 0.95, opacity: 0, y: 20 }, 
        { scale: 1, opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }
    );
};

window.cerrarAyudaTelegram = function() {
    const modal = document.getElementById('ayudaTelegramModal');
    gsap.to(modal.querySelector('.glass-panel'), {
        scale: 0.95, opacity: 0, y: 20, duration: 0.2, ease: "power3.in",
        onComplete: () => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';
        }
    });
};

document.addEventListener('click', function(event) {
    const modal = document.getElementById('ayudaTelegramModal');
    if (event.target === modal) {
        window.cerrarAyudaTelegram();
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('ayudaTelegramModal');
        if (modal && !modal.classList.contains('hidden')) {
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
// ENVIAR MENSAJE DE PRUEBA (GLOBAL)
// ============================================
window.enviarPrueba = function() {
    let token = document.getElementById('telegram_bot_token').value;
    let chatId = document.getElementById('telegram_chat_id').value;
    
    if (!token || !chatId) {
        alert('⚠️ Primero debes guardar el token y el chat ID');
        return;
    }
    
    const csrftoken = getCookie('csrftoken');
    
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

// ============================================
// GESTIÓN DE USUARIOS
// ============================================
const usersApiUrl = '/api/users/';

let estadoUsuarios = {
    paginaActual: 1,
    tamanoPagina: 8,
    totalElementos: 0,
    totalPaginas: 0,
    datos: []
};

// Cargar usuarios
window.cargarUsuarios = async function(pagina = 1) {
    try {
        estadoUsuarios.paginaActual = pagina;
        const pageSize = parseInt(document.getElementById('pageSizeUsuarios').value);
        estadoUsuarios.tamanoPagina = pageSize;
        
        const response = await fetch(usersApiUrl);
        const todosLosUsuarios = await response.json();
        
        estadoUsuarios.datos = todosLosUsuarios;
        estadoUsuarios.totalElementos = todosLosUsuarios.length;
        estadoUsuarios.totalPaginas = Math.ceil(estadoUsuarios.totalElementos / pageSize);
        
        // ❌ Eliminada: document.getElementById('countUsuarios').textContent = ...
        document.getElementById('resultCountUsuarios').textContent = `${estadoUsuarios.totalElementos} usuarios`;
        
        const start = (pagina - 1) * pageSize;
        const end = start + pageSize;
        const usuariosPagina = todosLosUsuarios.slice(start, end);
        
        window.renderizarUsuarios(usuariosPagina);
        window.renderizarPaginacionUsuarios();
    } catch (error) {
        console.error("Error al cargar usuarios:", error);
    }
};

// Renderizar usuarios
window.renderizarUsuarios = function(usuarios) {
    const tbody = document.getElementById('usuarios-tbody');
    tbody.innerHTML = '';
    
    if (usuarios.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="px-4 py-8 text-center text-gray-400">
                    <i class="fa-solid fa-inbox text-3xl mb-2 block text-gray-600"></i>
                    <p>No hay usuarios registrados</p>
                    <p class="text-xs mt-1">Haz clic en "Nuevo Usuario" para agregar uno</p>
                </td>
            </tr>
        `;
        return;
    }
    
    const roleColors = {
        'ADMIN': 'bg-red-500/20 text-red-400',
        'OPERATOR': 'bg-blue-500/20 text-blue-400',
        'VIEWER': 'bg-gray-500/20 text-gray-400'
    };
    
    const roleNames = {
        'ADMIN': 'Administrador',
        'OPERATOR': 'Operador',
        'VIEWER': 'Solo Lectura'
    };
    
    usuarios.forEach(usuario => {
        const safeUsername = usuario.user.username.replace(/'/g, "\\'");
        const fullName = [usuario.user.first_name, usuario.user.last_name].filter(Boolean).join(' ') || 'Sin nombre';
        
        const telegramBadge = usuario.has_telegram_configured ? 
            '<span class="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">✅ Configurado</span>' :
            '<span class="text-xs bg-gray-500/20 text-gray-400 px-2 py-0.5 rounded-full">⚠️ Sin configurar</span>';
        
        const statusBadge = usuario.is_active ? 
            '<span class="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">Activo</span>' :
            '<span class="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">Inactivo</span>';
        
        tbody.innerHTML += `
            <tr class="border-b border-gray-700/50 hover:bg-gray-800/30 transition-colors usuario-row" 
                data-nombre="${usuario.user.username}" 
                data-email="${usuario.user.email || ''}">
                <td class="px-4 py-3">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center">
                            <span class="text-sm font-bold text-blue-400">${usuario.user.username.charAt(0).toUpperCase()}</span>
                        </div>
                        <div>
                            <p class="font-semibold text-sm text-white">${usuario.user.username}</p>
                            <p class="text-xs text-gray-500">${fullName}</p>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3">
                    <span class="text-sm text-gray-400">${usuario.user.email || 'Sin email'}</span>
                </td>
                <td class="px-4 py-3">
                    <span class="text-xs px-2 py-1 rounded-full ${roleColors[usuario.role] || 'bg-gray-500/20 text-gray-400'}">
                        ${roleNames[usuario.role] || usuario.role}
                    </span>
                </td>
                <td class="px-4 py-3 text-center">${telegramBadge}</td>
                <td class="px-4 py-3 text-center">${statusBadge}</td>
                <td class="px-4 py-3">
                    <div class="flex items-center justify-center gap-2">
                        <button onclick="window.abrirModalUsuario(${usuario.id})" 
                                class="text-gray-400 hover:text-blue-400 p-1.5 bg-gray-800/50 hover:bg-gray-700 rounded-lg transition-colors"
                                title="Editar">
                            <i class="fa-solid fa-pen text-xs"></i>
                        </button>
                        ${usuario.has_telegram_configured ? `
                            <button onclick="window.probarTelegramUsuario(${usuario.id}, '${safeUsername}')" 
                                    class="text-gray-400 hover:text-green-400 p-1.5 bg-gray-800/50 hover:bg-gray-700 rounded-lg transition-colors"
                                    title="Probar Telegram">
                                <i class="fa-solid fa-paper-plane text-xs"></i>
                            </button>
                        ` : ''}
                        <button onclick="window.eliminarUsuario(${usuario.id}, '${safeUsername}')" 
                                class="text-gray-400 hover:text-red-400 p-1.5 bg-gray-800/50 hover:bg-gray-700 rounded-lg transition-colors"
                                title="Eliminar">
                            <i class="fa-solid fa-trash text-xs"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
};

// Paginación usuarios
window.renderizarPaginacionUsuarios = function() {
    const { paginaActual, totalPaginas } = estadoUsuarios;
    
    if (totalPaginas <= 1) {
        document.getElementById('paginationUsuarios').innerHTML = '';
        return;
    }
    
    let html = '';
    
    html += `
        <button onclick="window.cargarUsuarios(${paginaActual - 1})" 
                class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors ${paginaActual <= 1 ? 'opacity-50 cursor-not-allowed' : ''}"
                ${paginaActual <= 1 ? 'disabled' : ''}>
            <i class="fa-solid fa-chevron-left"></i>
        </button>
    `;
    
    let startPage = Math.max(1, paginaActual - 2);
    let endPage = Math.min(totalPaginas, paginaActual + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const active = i === paginaActual ? 'bg-purple-600 text-white' : 'bg-gray-700 hover:bg-gray-600';
        html += `
            <button onclick="window.cargarUsuarios(${i})" 
                    class="px-3 py-1.5 rounded-lg text-sm ${active} transition-colors">${i}</button>
        `;
    }
    
    html += `
        <button onclick="window.cargarUsuarios(${paginaActual + 1})" 
                class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors ${paginaActual >= totalPaginas ? 'opacity-50 cursor-not-allowed' : ''}"
                ${paginaActual >= totalPaginas ? 'disabled' : ''}>
            <i class="fa-solid fa-chevron-right"></i>
        </button>
    `;
    
    document.getElementById('paginationUsuarios').innerHTML = `
        ${html}
        <span class="text-xs text-gray-500 ml-2">Pág. ${paginaActual} de ${totalPaginas}</span>
    `;
};

// Abrir modal de usuario
window.abrirModalUsuario = async function(id = null) {
    const modal = document.getElementById('usuarioModal');
    const form = document.getElementById('usuarioForm');
    form.reset();
    
    document.getElementById('usuarioModalTitle').innerText = id ? 'Editar Usuario' : 'Nuevo Usuario';
    document.getElementById('usuarioId').value = id || '';
    
    if (id) {
        try {
            const response = await fetch(`${usersApiUrl}${id}/`);
            const usuario = await response.json();
            
            document.getElementById('usuarioUsername').value = usuario.user.username;
            document.getElementById('usuarioEmail').value = usuario.user.email || '';
            document.getElementById('usuarioFirstName').value = usuario.user.first_name || '';
            document.getElementById('usuarioLastName').value = usuario.user.last_name || '';
            document.getElementById('usuarioRole').value = usuario.role;
            document.getElementById('usuarioTelegramToken').value = usuario.telegram_bot_token || '';
            document.getElementById('usuarioTelegramChatId').value = usuario.telegram_chat_id || '';
            document.getElementById('notifyNodeDown').checked = usuario.notify_node_down;
            document.getElementById('notifyNodeRecovery').checked = usuario.notify_node_recovery;
            document.getElementById('notifyHttpDown').checked = usuario.notify_http_down;
            document.getElementById('notifyHttpRecovery').checked = usuario.notify_http_recovery;
            document.getElementById('notifySslExpiry').checked = usuario.notify_ssl_expiry;
            document.getElementById('notifyHighLatency').checked = usuario.notify_high_latency;
            document.getElementById('usuarioIsActive').checked = usuario.is_active;
        } catch (error) {
            console.error('Error al cargar usuario:', error);
        }
    }
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
};

window.cerrarModalUsuario = function() {
    const modal = document.getElementById('usuarioModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
};

// Guardar usuario
window.guardarUsuario = async function(event) {
    event.preventDefault();
    
    const id = document.getElementById('usuarioId').value;
    const data = {
        username: document.getElementById('usuarioUsername').value,
        email: document.getElementById('usuarioEmail').value,
        first_name: document.getElementById('usuarioFirstName').value,
        last_name: document.getElementById('usuarioLastName').value,
        role: document.getElementById('usuarioRole').value,
        telegram_bot_token: document.getElementById('usuarioTelegramToken').value,
        telegram_chat_id: document.getElementById('usuarioTelegramChatId').value,
        notify_node_down: document.getElementById('notifyNodeDown').checked,
        notify_node_recovery: document.getElementById('notifyNodeRecovery').checked,
        notify_http_down: document.getElementById('notifyHttpDown').checked,
        notify_http_recovery: document.getElementById('notifyHttpRecovery').checked,
        notify_ssl_expiry: document.getElementById('notifySslExpiry').checked,
        notify_high_latency: document.getElementById('notifyHighLatency').checked,
        is_active: document.getElementById('usuarioIsActive').checked
    };
    
    const password = document.getElementById('usuarioPassword').value;
    if (password) {
        data.password = password;
    }
    
    const method = id ? 'PUT' : 'POST';
    const endpoint = id ? `${usersApiUrl}${id}/` : usersApiUrl;
    
    try {
        const response = await fetch(endpoint, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            window.cerrarModalUsuario();
            window.cargarUsuarios(estadoUsuarios.paginaActual);
            mostrarNotificacion('✅ Usuario guardado correctamente', 'success');
        } else {
            const errorData = await response.json();
            alert('❌ Error al guardar: ' + JSON.stringify(errorData));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('❌ Error al guardar el usuario');
    }
};

// Eliminar usuario
window.eliminarUsuario = async function(id, username) {
    if (confirm(`¿Eliminar al usuario "${username}"? Esta acción no se puede deshacer.`)) {
        try {
            const response = await fetch(`${usersApiUrl}${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            
            if (response.ok) {
                window.cargarUsuarios(estadoUsuarios.paginaActual);
                mostrarNotificacion('✅ Usuario eliminado', 'success');
            }
        } catch (error) {
            console.error('Error al eliminar:', error);
        }
    }
};

// Probar Telegram de usuario
window.probarTelegramUsuario = async function(id, username) {
    if (!confirm(`¿Enviar mensaje de prueba a ${username}?`)) return;
    
    try {
        const response = await fetch(`${usersApiUrl}${id}/test_telegram/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarNotificacion('✅ Mensaje enviado correctamente', 'success');
        } else {
            mostrarNotificacion('❌ ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('❌ Error al enviar mensaje', 'error');
    }
};

// Filtros de usuarios
window.filtrarUsuarios = function() {
    const termino = document.getElementById('filterUsuarios').value.toLowerCase().trim();
    const filas = document.querySelectorAll('.usuario-row');
    let visibleCount = 0;
    
    filas.forEach(fila => {
        const nombre = fila.dataset.nombre ? fila.dataset.nombre.toLowerCase() : '';
        const email = fila.dataset.email ? fila.dataset.email.toLowerCase() : '';
        const coincide = nombre.includes(termino) || email.includes(termino);
        
        fila.style.display = coincide ? '' : 'none';
        if (coincide) visibleCount++;
    });
    
    const statusEl = document.getElementById('filterStatusUsuarios');
    const clearBtn = document.getElementById('clearFilterUsuarios');
    
    if (termino) {
        statusEl.textContent = `(${visibleCount} coincidencias)`;
        clearBtn.classList.remove('hidden');
    } else {
        statusEl.textContent = '';
        clearBtn.classList.add('hidden');
    }
};

window.limpiarFiltroUsuarios = function() {
    document.getElementById('filterUsuarios').value = '';
    window.filtrarUsuarios();
};

window.cambiarTamanoPaginaUsuarios = function() {
    window.cargarUsuarios(1);
};

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    window.cargarUsuarios(1);
});

// ============================================
// GESTIÓN DE "MI PERFIL"
// ============================================
let miPerfilData = null;

window.cargarMiPerfil = async function() {
    const loading = document.getElementById('miPerfilLoading');
    const form = document.getElementById('miPerfilForm');
    
    try {
        const response = await fetch(`${usersApiUrl}me/`);
        
        if (!response.ok) {
            throw new Error('Error al cargar perfil');
        }
        
        const perfil = await response.json();
        miPerfilData = perfil;
        
        // Rellenar formulario
        document.getElementById('miPerfilId').value = perfil.id;
        document.getElementById('miPerfilTelegramToken').value = perfil.telegram_bot_token || '';
        document.getElementById('miPerfilTelegramChatId').value = perfil.telegram_chat_id || '';
        
        // Preferencias
        document.getElementById('miNotifyNodeDown').checked = perfil.notify_node_down;
        document.getElementById('miNotifyNodeRecovery').checked = perfil.notify_node_recovery;
        document.getElementById('miNotifyHttpDown').checked = perfil.notify_http_down;
        document.getElementById('miNotifyHttpRecovery').checked = perfil.notify_http_recovery;
        document.getElementById('miNotifySslExpiry').checked = perfil.notify_ssl_expiry;
        document.getElementById('miNotifyHighLatency').checked = perfil.notify_high_latency;
        
        // Mostrar estado
        actualizarEstadoMiPerfil(perfil);
        
        loading.classList.add('hidden');
        form.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error:', error);
        loading.innerHTML = `
            <i class="fa-solid fa-exclamation-triangle text-red-400 text-2xl"></i>
            <p class="text-sm text-red-400 mt-2">Error al cargar tu perfil</p>
        `;
    }
};

function actualizarEstadoMiPerfil(perfil) {
    const estado = document.getElementById('miPerfilEstado');
    
    if (perfil.has_telegram_configured) {
        estado.className = 'mb-4 p-3 rounded-lg border border-green-500/30 bg-green-500/10';
        estado.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span class="text-sm text-green-400 font-semibold">✅ Telegram configurado</span>
            </div>
            <p class="text-xs text-green-400/70 mt-1">
                Recibirás notificaciones en tu chat personal de Telegram
            </p>
        `;
    } else {
        estado.className = 'mb-4 p-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10';
        estado.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="inline-block w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></span>
                <span class="text-sm text-yellow-400 font-semibold">⚠️ Telegram no configurado</span>
            </div>
            <p class="text-xs text-yellow-400/70 mt-1">
                Configura tu Token y Chat ID para recibir notificaciones personales
            </p>
        `;
    }
    
    estado.classList.remove('hidden');
}

window.guardarMiPerfil = async function(event) {
    event.preventDefault();
    
    const data = {
        telegram_bot_token: document.getElementById('miPerfilTelegramToken').value,
        telegram_chat_id: document.getElementById('miPerfilTelegramChatId').value,
        notify_node_down: document.getElementById('miNotifyNodeDown').checked,
        notify_node_recovery: document.getElementById('miNotifyNodeRecovery').checked,
        notify_http_down: document.getElementById('miNotifyHttpDown').checked,
        notify_http_recovery: document.getElementById('miNotifyHttpRecovery').checked,
        notify_ssl_expiry: document.getElementById('miNotifySslExpiry').checked,
        notify_high_latency: document.getElementById('miNotifyHighLatency').checked,
    };
    
    try {
        const response = await fetch(`${usersApiUrl}update_me/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const perfil = await response.json();
            miPerfilData = perfil;
            actualizarEstadoMiPerfil(perfil);
            mostrarNotificacion('✅ Tu configuración se guardó correctamente', 'success');
        } else {
            const error = await response.json();
            mostrarNotificacion('❌ Error al guardar: ' + JSON.stringify(error), 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('❌ Error al guardar tu configuración', 'error');
    }
};

window.probarMiTelegram = async function() {
    if (!confirm('¿Enviar mensaje de prueba a tu Telegram?')) return;
    
    try {
        const response = await fetch(`${usersApiUrl}test_my_telegram/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarNotificacion('✅ Mensaje enviado a tu Telegram', 'success');
        } else {
            mostrarNotificacion('❌ ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('❌ Error al enviar mensaje', 'error');
    }
};

// ============================================
// TABS DE AJUSTES (ACTUALIZADO)
// ============================================
window.cambiarTabAjustes = function(tab) {
    const tabGeneral = document.getElementById('tabGeneral');
    const tabMiPerfil = document.getElementById('tabMiPerfil');
    const tabUsuarios = document.getElementById('tabUsuarios');
    const contenidoGeneral = document.getElementById('contenidoGeneral');
    const contenidoMiPerfil = document.getElementById('contenidoMiPerfil');
    const contenidoUsuarios = document.getElementById('contenidoUsuarios');
    
    // Resetear tabs
    tabGeneral.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-gray-400 hover:text-white transition-colors';
    tabMiPerfil.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-gray-400 hover:text-white transition-colors';
    tabUsuarios.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-gray-400 hover:text-white transition-colors';
    
    // Ocultar contenidos
    contenidoGeneral.classList.add('hidden');
    contenidoMiPerfil.classList.add('hidden');
    contenidoUsuarios.classList.add('hidden');
    
    if (tab === 'general') {
        tabGeneral.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-blue-500 text-blue-400 transition-colors';
        contenidoGeneral.classList.remove('hidden');
    } else if (tab === 'perfil') {
        tabMiPerfil.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-purple-500 text-purple-400 transition-colors';
        contenidoMiPerfil.classList.remove('hidden');
        window.cargarMiPerfil();
    } else if (tab === 'usuarios') {
        tabUsuarios.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-purple-500 text-purple-400 transition-colors';
        contenidoUsuarios.classList.remove('hidden');
        window.cargarUsuarios(1);
    }
};