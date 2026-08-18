// monitoreo_app/static/monitoreo_app/js/alerts.js

const alertsApiUrl = '/api/alerts/';

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
const csrftoken = getCookie('csrftoken');

// ============================================
// ESTADO DE PAGINACIÓN
// ============================================
let estadoPaginacion = {
    paginaActual: 1,
    tamanoPagina: 20,
    totalElementos: 0,
    totalPaginas: 0,
    alertasActuales: []
};

// ============================================
// CARGAR ALERTAS
// ============================================
window.cargarAlertas = async function(pagina = null) {
    try {
        // Si no se especifica página, usar la actual
        if (pagina === null) {
            pagina = estadoPaginacion.paginaActual;
        }
        
        estadoPaginacion.paginaActual = pagina;
        const pageSize = parseInt(document.getElementById('pageSize').value);
        estadoPaginacion.tamanoPagina = pageSize;
        
        let url = `${alertsApiUrl}filter/?`;
        
        const type = document.getElementById('filterType').value;
        if (type) url += `type=${type}&`;
        
        const resolved = document.getElementById('filterResolved').value;
        if (resolved !== '') url += `resolved=${resolved}&`;
        
        const from = document.getElementById('filterFrom').value;
        if (from) url += `from=${from}T00:00:00&`;
        
        const to = document.getElementById('filterTo').value;
        if (to) url += `to=${to}T23:59:59&`;
        
        const offset = (pagina - 1) * pageSize;
        url += `limit=${pageSize}&offset=${offset}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.results) {
            estadoPaginacion.alertasActuales = data.results;
            estadoPaginacion.totalElementos = data.count || data.results.length;
        } else {
            estadoPaginacion.alertasActuales = data;
            estadoPaginacion.totalElementos = data.length;
        }
        
        estadoPaginacion.totalPaginas = Math.ceil(estadoPaginacion.totalElementos / pageSize);
        
        window.renderizarAlertas(estadoPaginacion.alertasActuales);
        window.renderizarPaginacion();
        
        document.getElementById('resultCount').textContent = 
            `${estadoPaginacion.totalElementos} resultados`;
        
        const statsResponse = await fetch(`${alertsApiUrl}stats/`);
        const stats = await statsResponse.json();
        window.renderizarEstadisticas(stats);
        
    } catch (error) {
        console.error("Error cargando alertas:", error);
    }
};

// ============================================
// MARCAR ALERTA COMO RESUELTA
// ============================================
window.marcarComoResuelta = async function(alertId) {
    if (!confirm('¿Marcar esta alerta como resuelta?')) {
        return;
    }
    
    try {
        const response = await fetch(`${alertsApiUrl}${alertId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                is_resolved: true,
                resolved_at: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            window.cargarAlertas(estadoPaginacion.paginaActual);
            mostrarNotificacion('✅ Alerta marcada como resuelta', 'success');
        } else {
            const error = await response.json();
            mostrarNotificacion('❌ Error al marcar como resuelta', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('❌ Error al marcar como resuelta', 'error');
    }
};

// ============================================
// NOTIFICACIONES (Toast)
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
// RENDERIZAR PAGINACIÓN
// ============================================
window.renderizarPaginacion = function() {
    const { paginaActual, totalPaginas } = estadoPaginacion;
    
    if (totalPaginas <= 1) {
        document.getElementById('paginationControls').innerHTML = '';
        document.getElementById('paginationBottom').innerHTML = '';
        return;
    }
    
    const generarControles = (pagina) => {
        let html = '';
        
        html += `
            <button onclick="window.cargarAlertas(${pagina - 1})" 
                    class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors ${pagina <= 1 ? 'opacity-50 cursor-not-allowed' : ''}"
                    ${pagina <= 1 ? 'disabled' : ''}>
                <i class="fa-solid fa-chevron-left"></i>
            </button>
        `;
        
        let startPage = Math.max(1, pagina - 2);
        let endPage = Math.min(totalPaginas, pagina + 2);
        
        if (startPage > 1) {
            html += `
                <button onclick="window.cargarAlertas(1)" 
                        class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors">1</button>
                ${startPage > 2 ? '<span class="text-gray-500 px-1">...</span>' : ''}
            `;
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const active = i === pagina ? 'bg-yellow-600 text-white' : 'bg-gray-700 hover:bg-gray-600';
            html += `
                <button onclick="window.cargarAlertas(${i})" 
                        class="px-3 py-1.5 rounded-lg text-sm ${active} transition-colors">${i}</button>
            `;
        }
        
        if (endPage < totalPaginas) {
            html += `
                ${endPage < totalPaginas - 1 ? '<span class="text-gray-500 px-1">...</span>' : ''}
                <button onclick="window.cargarAlertas(${totalPaginas})" 
                        class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors">${totalPaginas}</button>
            `;
        }
        
        html += `
            <button onclick="window.cargarAlertas(${pagina + 1})" 
                    class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors ${pagina >= totalPaginas ? 'opacity-50 cursor-not-allowed' : ''}"
                    ${pagina >= totalPaginas ? 'disabled' : ''}>
                <i class="fa-solid fa-chevron-right"></i>
            </button>
        `;
        
        return html;
    };
    
    const controlesHTML = generarControles(paginaActual);
    
    document.getElementById('paginationControls').innerHTML = `
        ${controlesHTML}
        <span class="text-xs text-gray-500 ml-2">Pág. ${paginaActual} de ${totalPaginas}</span>
    `;
    
    document.getElementById('paginationBottom').innerHTML = `
        <div class="flex items-center gap-2 glass-panel px-4 py-2 rounded-xl border border-gray-700/50">
            ${controlesHTML}
        </div>
    `;
};

// ============================================
// RENDERIZAR ESTADÍSTICAS
// ============================================
window.renderizarEstadisticas = function(stats) {
    document.getElementById('statTotal').textContent = stats.total || 0;
    document.getElementById('statPending').textContent = stats.pending || 0;
    document.getElementById('statResolved').textContent = stats.resolved || 0;
    document.getElementById('statRate').textContent = `${stats.resolution_rate || 0}%`;
};

// ============================================
// RENDERIZAR ALERTAS
// ============================================
window.renderizarAlertas = function(alerts) {
    const container = document.getElementById('alerts-container');
    container.innerHTML = '';
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = `
            <div class="glass-panel p-12 rounded-xl text-center text-gray-400 border border-gray-700/50">
                <i class="fa-solid fa-inbox text-5xl mb-4 block text-gray-600"></i>
                <p class="text-lg font-semibold text-gray-300">No hay alertas</p>
                <p class="text-sm mt-1">No se encontraron alertas que coincidan con los filtros seleccionados</p>
                <button onclick="window.limpiarFiltros()" 
                        class="mt-4 text-sm text-blue-400 hover:text-blue-300 transition-colors">
                    <i class="fa-solid fa-eraser mr-1"></i> Limpiar filtros
                </button>
            </div>
        `;
        return;
    }
    
    const typeEmojis = {
        'NODE_DOWN': '🚨',
        'NODE_RECOVERY': '✅',
        'HIGH_LATENCY': '⚠️',
        'HTTP_DOWN': '🌐',
        'HTTP_RECOVERY': '✅',
        'HTTP_ERROR': '❌',
        'SSL_EXPIRY': '🔒'
    };
    
    const typeColors = {
        'NODE_DOWN': 'border-red-500/30 bg-red-500/5',
        'NODE_RECOVERY': 'border-green-500/30 bg-green-500/5',
        'HIGH_LATENCY': 'border-yellow-500/30 bg-yellow-500/5',
        'HTTP_DOWN': 'border-red-500/30 bg-red-500/5',
        'HTTP_RECOVERY': 'border-green-500/30 bg-green-500/5',
        'HTTP_ERROR': 'border-orange-500/30 bg-orange-500/5',
        'SSL_EXPIRY': 'border-purple-500/30 bg-purple-500/5'
    };
    
    alerts.forEach(alert => {
        const statusBadge = alert.is_resolved ? 
            '<span class="text-xs bg-green-500/20 text-green-400 px-2.5 py-1 rounded-full border border-green-500/30">✅ Resuelta</span>' :
            '<span class="text-xs bg-red-500/20 text-red-400 px-2.5 py-1 rounded-full border border-red-500/30">🔴 Pendiente</span>';
        
        const emoji = typeEmojis[alert.event_type] || '📢';
        const borderColor = typeColors[alert.event_type] || 'border-gray-500/30 bg-gray-500/5';
        
        const createdDate = new Date(alert.created_at);
        const resolvedDate = alert.resolved_at ? new Date(alert.resolved_at) : null;
        
        container.innerHTML += `
            <div class="glass-panel p-4 rounded-xl border-l-4 ${borderColor} hover:border-l-6 transition-all hover:shadow-lg">
                <div class="flex flex-col sm:flex-row justify-between items-start gap-3">
                    <div class="flex items-start gap-3 flex-1 min-w-0">
                        <div class="text-2xl flex-shrink-0 mt-0.5">${emoji}</div>
                        <div class="flex-1 min-w-0">
                            <p class="font-semibold text-white">${alert.message}</p>
                            <div class="flex flex-wrap items-center gap-3 mt-1.5">
                                <span class="text-xs text-gray-400">
                                    <i class="fa-regular fa-clock mr-1"></i>
                                    ${createdDate.toLocaleString()}
                                </span>
                                ${resolvedDate ? `
                                    <span class="text-xs text-green-400">
                                        <i class="fa-regular fa-circle-check mr-1"></i>
                                        Resuelta: ${resolvedDate.toLocaleString()}
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="flex flex-wrap items-center gap-2 flex-shrink-0">
                        ${statusBadge}
                        ${!alert.is_resolved ? `
                            <button onclick="window.marcarComoResuelta(${alert.id})" 
                                    class="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded-lg transition-colors flex items-center gap-1">
                                <i class="fa-solid fa-check"></i> Resolver
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });
};

// ============================================
// FILTROS RÁPIDOS
// ============================================
window.limpiarFiltros = function() {
    document.getElementById('filterType').value = '';
    document.getElementById('filterResolved').value = '';
    document.getElementById('filterFrom').value = '';
    document.getElementById('filterTo').value = '';
    window.cargarAlertas(1);
};

window.filtroHoy = function() {
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('filterFrom').value = hoy;
    document.getElementById('filterTo').value = hoy;
    window.cargarAlertas(1);
};

window.filtroSemana = function() {
    const hoy = new Date();
    const semana = new Date(hoy);
    semana.setDate(hoy.getDate() - 7);
    document.getElementById('filterFrom').value = semana.toISOString().split('T')[0];
    document.getElementById('filterTo').value = hoy.toISOString().split('T')[0];
    window.cargarAlertas(1);
};

window.filtroMes = function() {
    const hoy = new Date();
    const mes = new Date(hoy);
    mes.setMonth(hoy.getMonth() - 1);
    document.getElementById('filterFrom').value = mes.toISOString().split('T')[0];
    document.getElementById('filterTo').value = hoy.toISOString().split('T')[0];
    window.cargarAlertas(1);
};

window.cambiarTamanoPagina = function() {
    window.cargarAlertas(1);
};

// ============================================
// EXPONER ESTADO AL ÁMBITO GLOBAL
// ============================================
window.estadoPaginacion = estadoPaginacion;

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener("DOMContentLoaded", () => {
    window.cargarAlertas(1);
    setInterval(() => window.cargarAlertas(estadoPaginacion.paginaActual), 60000);
});