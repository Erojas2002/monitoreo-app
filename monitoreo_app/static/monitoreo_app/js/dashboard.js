// monitoreo_app/static/monitoreo_app/js/dashboard.js

// ============================================
// CONFIGURACIÓN GLOBAL
// ============================================
const apiUrl = '/api/nodes/';
const httpApiUrl = '/api/http-endpoints/';
let tiempoActualizacion = 60000;
let nodosInterval = null;
let serviciosInterval = null;
let nodoActualId = null;
let tabActual = 'nodos';

// Estado de paginación Nodos
let estadoNodos = {
    paginaActual: 1,
    tamanoPagina: 8,
    totalElementos: 0,
    totalPaginas: 0,
    datos: []
};

// Estado de paginación Servicios
let estadoServicios = {
    paginaActual: 1,
    tamanoPagina: 8,
    totalElementos: 0,
    totalPaginas: 0,
    datos: []
};

// Estado de paginación Predicciones
let estadoPredicciones = {
    paginaActual: 1,
    tamanoPagina: 4,
    totalElementos: 0,
    totalPaginas: 0,
    datos: []
};

let prediccionesInterval = null;

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
// UTILIDADES
// ============================================
function obtenerIcono(tipo) {
    const iconos = {
        'ROUTER': 'fa-route text-blue-400',
        'SWITCH': 'fa-server text-purple-400',
        'NVR': 'fa-video text-orange-400',
        'CAMERA': 'fa-camera text-orange-300',
        'SERVER': 'fa-database text-teal-400'
    };
    return iconos[tipo] || 'fa-desktop text-gray-400';
}

function obtenerColorEstado(estado) {
    if (estado === 'UP') return 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]';
    if (estado === 'DOWN') return 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]';
    if (estado === 'WARN') return 'bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.5)]';
    return 'bg-gray-500';
}

// ============================================
// TABS
// ============================================
function cambiarTab(tab) {
    tabActual = tab;
    
    const tabNodos = document.getElementById('tabNodos');
    const tabServicios = document.getElementById('tabServicios');
    const tabPredicciones = document.getElementById('tabPredicciones');
    const contenidoNodos = document.getElementById('contenidoNodos');
    const contenidoServicios = document.getElementById('contenidoServicios');
    const contenidoPredicciones = document.getElementById('contenidoPredicciones');
    
    // Resetear todos los tabs
    tabNodos.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-gray-400 hover:text-white transition-colors';
    tabServicios.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-gray-400 hover:text-white transition-colors';
    tabPredicciones.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-gray-400 hover:text-white transition-colors';
    
    // Ocultar todos los contenidos
    contenidoNodos.classList.add('hidden');
    contenidoServicios.classList.add('hidden');
    contenidoPredicciones.classList.add('hidden');
    
    if (tab === 'nodos') {
        tabNodos.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-blue-500 text-blue-400 transition-colors';
        contenidoNodos.classList.remove('hidden');
    } else if (tab === 'servicios') {
        tabServicios.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-green-500 text-green-400 transition-colors';
        contenidoServicios.classList.remove('hidden');
    } else if (tab === 'predicciones') {
        tabPredicciones.className = 'px-6 py-3 text-sm font-semibold border-b-2 border-purple-500 text-purple-400 transition-colors';
        contenidoPredicciones.classList.remove('hidden');
    }
}

// ============================================
// FUNCIONES DE PAGINACIÓN
// ============================================
function generarControlesPaginacion(paginaActual, totalPaginas, funcion) {
    let html = '';
    
    html += `
        <button onclick="${funcion}(${paginaActual - 1})" 
                class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors ${paginaActual <= 1 ? 'opacity-50 cursor-not-allowed' : ''}"
                ${paginaActual <= 1 ? 'disabled' : ''}>
            <i class="fa-solid fa-chevron-left"></i>
        </button>
    `;
    
    let startPage = Math.max(1, paginaActual - 2);
    let endPage = Math.min(totalPaginas, paginaActual + 2);
    
    if (startPage > 1) {
        html += `
            <button onclick="${funcion}(1)" 
                    class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors">1</button>
            ${startPage > 2 ? '<span class="text-gray-500 px-1">...</span>' : ''}
        `;
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const active = i === paginaActual ? 'bg-blue-600 text-white' : 'bg-gray-700 hover:bg-gray-600';
        html += `
            <button onclick="${funcion}(${i})" 
                    class="px-3 py-1.5 rounded-lg text-sm ${active} transition-colors">${i}</button>
        `;
    }
    
    if (endPage < totalPaginas) {
        html += `
            ${endPage < totalPaginas - 1 ? '<span class="text-gray-500 px-1">...</span>' : ''}
            <button onclick="${funcion}(${totalPaginas})" 
                    class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors">${totalPaginas}</button>
        `;
    }
    
    html += `
        <button onclick="${funcion}(${paginaActual + 1})" 
                class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors ${paginaActual >= totalPaginas ? 'opacity-50 cursor-not-allowed' : ''}"
                ${paginaActual >= totalPaginas ? 'disabled' : ''}>
            <i class="fa-solid fa-chevron-right"></i>
        </button>
    `;
    
    return html;
}

function generarControlesPaginacionPredicciones(paginaActual, totalPaginas) {
    let html = '';
    
    html += `
        <button onclick="cargarPredicciones(${paginaActual - 1})" 
                class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors ${paginaActual <= 1 ? 'opacity-50 cursor-not-allowed' : ''}"
                ${paginaActual <= 1 ? 'disabled' : ''}>
            <i class="fa-solid fa-chevron-left"></i>
        </button>
    `;
    
    let startPage = Math.max(1, paginaActual - 2);
    let endPage = Math.min(totalPaginas, paginaActual + 2);
    
    if (startPage > 1) {
        html += `
            <button onclick="cargarPredicciones(1)" 
                    class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors">1</button>
            ${startPage > 2 ? '<span class="text-gray-500 px-1">...</span>' : ''}
        `;
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const active = i === paginaActual ? 'bg-purple-600 text-white' : 'bg-gray-700 hover:bg-gray-600';
        html += `
            <button onclick="cargarPredicciones(${i})" 
                    class="px-3 py-1.5 rounded-lg text-sm ${active} transition-colors">${i}</button>
        `;
    }
    
    if (endPage < totalPaginas) {
        html += `
            ${endPage < totalPaginas - 1 ? '<span class="text-gray-500 px-1">...</span>' : ''}
            <button onclick="cargarPredicciones(${totalPaginas})" 
                    class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors">${totalPaginas}</button>
        `;
    }
    
    html += `
        <button onclick="cargarPredicciones(${paginaActual + 1})" 
                class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors ${paginaActual >= totalPaginas ? 'opacity-50 cursor-not-allowed' : ''}"
                ${paginaActual >= totalPaginas ? 'disabled' : ''}>
            <i class="fa-solid fa-chevron-right"></i>
        </button>
    `;
    
    return html;
}

// ============================================
// NODOS DE RED
// ============================================
async function cargarNodos(pagina = 1) {
    try {
        estadoNodos.paginaActual = pagina;
        const pageSize = parseInt(document.getElementById('pageSizeNodos').value);
        estadoNodos.tamanoPagina = pageSize;
        
        const respuesta = await fetch(apiUrl);
        const todosLosNodos = await respuesta.json();
        
        estadoNodos.datos = todosLosNodos;
        estadoNodos.totalElementos = todosLosNodos.length;
        estadoNodos.totalPaginas = Math.ceil(estadoNodos.totalElementos / pageSize);
        
        document.getElementById('countNodos').textContent = estadoNodos.totalElementos;
        document.getElementById('resultCountNodos').textContent = `${estadoNodos.totalElementos} nodos`;
        
        const start = (pagina - 1) * pageSize;
        const end = start + pageSize;
        const nodosPagina = todosLosNodos.slice(start, end);
        
        renderizarNodos(nodosPagina);
        renderizarPaginacionNodos();
    } catch (error) {
        console.error("Error al cargar nodos:", error);
    }
}

function renderizarNodos(nodos) {
    const container = document.getElementById('nodos-container');
    container.innerHTML = '';
    
    if (nodos.length === 0) {
        container.innerHTML = `
            <div class="glass-panel p-8 rounded-xl col-span-4 text-center text-gray-400 border border-gray-700/50">
                <i class="fa-solid fa-inbox text-4xl mb-3 block text-gray-600"></i>
                <p class="text-lg font-semibold text-gray-300">No hay nodos registrados</p>
                <p class="text-sm mt-1">Haz clic en "Nuevo" para agregar tu primer dispositivo</p>
            </div>
        `;
        return;
    }
    
    nodos.forEach(nodo => {
        const icono = obtenerIcono(nodo.device_type);
        const colorEstado = obtenerColorEstado(nodo.status);
        const ultimaLatencia = nodo.recent_latency.length > 0 ? 
            `${nodo.recent_latency[0].latency_ms} ms` : 'N/A';
        const safeName = nodo.name.replace(/'/g, "\\'");
        const notificacionIcon = nodo.notify_telegram ? '🔔' : '🔕';
        const notificacionText = nodo.notify_telegram ? 'Notificaciones activas' : 'Notificaciones desactivadas';
        const notificacionColor = nodo.notify_telegram ? 'text-green-400' : 'text-gray-500';
        
        container.innerHTML += `
            <div class="nodo-card glass-panel rounded-xl p-5 hover:border-blue-500 transition-colors relative group" 
                data-nombre="${nodo.name}" 
                data-ip="${nodo.ip_address}">
                <div class="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="abrirGraficas('${nodo.id}', '${safeName}')" 
                            class="text-gray-400 hover:text-green-400 p-1">
                        <i class="fa-solid fa-chart-line text-sm"></i>
                    </button>
                    <button onclick="abrirModal('${nodo.id}', '${safeName}', '${nodo.ip_address}', '${nodo.device_type}', ${nodo.notify_telegram})" 
                            class="text-gray-400 hover:text-blue-400 p-1">
                        <i class="fa-solid fa-pen text-sm"></i>
                    </button>
                    <button onclick="eliminarNodo(${nodo.id}, '${safeName}')" 
                            class="text-gray-400 hover:text-red-400 p-1">
                        <i class="fa-solid fa-trash text-sm"></i>
                    </button>
                </div>
                
                <div class="flex justify-between items-start mb-4 mt-2">
                    <div class="flex items-center gap-3">
                        <div class="p-3 bg-gray-800 rounded-lg">
                            <i class="fa-solid ${icono} text-xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-lg leading-tight">${nodo.name}</h3>
                            <p class="text-xs text-gray-400 font-mono">${nodo.ip_address}</p>
                        </div>
                    </div>
                    <div class="h-3 w-3 rounded-full ${colorEstado}"></div>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mt-4 border-t border-gray-700 pt-4">
                    <div>
                        <p class="text-xs text-gray-400 uppercase tracking-wider">Latencia</p>
                        <p class="text-sm font-semibold">${ultimaLatencia}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400 uppercase tracking-wider">Estado</p>
                        <p class="text-sm font-semibold">${nodo.status === 'UP' ? 'En línea' : 'Caído'}</p>
                    </div>
                </div>
                
                <div class="mt-2 pt-2 border-t border-gray-700/50 flex justify-between items-center">
                    <p class="text-xs text-gray-400">
                        Pérdida: ${nodo.recent_latency.length > 0 ? nodo.recent_latency[0].packet_loss_pct + '%' : 'N/A'}
                    </p>
                    <p class="text-xs ${notificacionColor}">
                        ${notificacionIcon} ${notificacionText}
                    </p>
                </div>
            </div>
        `;
    });
    
    document.getElementById('filterNodos').value = '';
    document.getElementById('filterStatusNodos').textContent = '';
    document.getElementById('clearFilterNodos').classList.add('hidden');
    
    gsap.fromTo(".nodo-card", 
        { y: 30, opacity: 0 }, 
        { y: 0, opacity: 1, duration: 0.4, stagger: 0.08, ease: "back.out(1.7)" }
    );
}

function renderizarPaginacionNodos() {
    const { paginaActual, totalPaginas } = estadoNodos;
    
    if (totalPaginas <= 1) {
        document.getElementById('paginationNodos').innerHTML = '';
        return;
    }
    
    const controles = generarControlesPaginacion(paginaActual, totalPaginas, 'cargarNodos');
    document.getElementById('paginationNodos').innerHTML = `
        ${controles}
        <span class="text-xs text-gray-500 ml-2">Pág. ${paginaActual} de ${totalPaginas}</span>
    `;
}

// ============================================
// SERVICIOS WEB
// ============================================
async function cargarServiciosHTTP(pagina = 1) {
    try {
        estadoServicios.paginaActual = pagina;
        const pageSize = parseInt(document.getElementById('pageSizeServicios').value);
        estadoServicios.tamanoPagina = pageSize;
        
        const respuesta = await fetch(httpApiUrl);
        const todosLosServicios = await respuesta.json();
        
        estadoServicios.datos = todosLosServicios;
        estadoServicios.totalElementos = todosLosServicios.length;
        estadoServicios.totalPaginas = Math.ceil(estadoServicios.totalElementos / pageSize);
        
        document.getElementById('countServicios').textContent = estadoServicios.totalElementos;
        document.getElementById('resultCountServicios').textContent = `${estadoServicios.totalElementos} servicios`;
        
        const start = (pagina - 1) * pageSize;
        const end = start + pageSize;
        const serviciosPagina = todosLosServicios.slice(start, end);
        
        renderizarServiciosHTTP(serviciosPagina);
        renderizarPaginacionServicios();
    } catch (error) {
        console.error("Error al cargar servicios HTTP:", error);
    }
}

function renderizarServiciosHTTP(servicios) {
    const container = document.getElementById('http-container');
    container.innerHTML = '';
    
    if (servicios.length === 0) {
        container.innerHTML = `
            <div class="glass-panel p-8 rounded-xl col-span-4 text-center text-gray-400 border border-gray-700/50">
                <i class="fa-solid fa-inbox text-4xl mb-3 block text-gray-600"></i>
                <p class="text-lg font-semibold text-gray-300">No hay servicios web registrados</p>
                <p class="text-sm mt-1">Haz clic en "Nuevo" para agregar tu primer servicio</p>
            </div>
        `;
        return;
    }
    
    const serviceIcons = {
        'WEB': 'fa-globe text-blue-400',
        'API': 'fa-plug text-purple-400',
        'NVR_CAM': 'fa-video text-orange-400',
        'DATABASE': 'fa-database text-teal-400',
        'FILE': 'fa-folder-open text-indigo-400',
        'EMAIL': 'fa-envelope text-pink-400',
        'DNS': 'fa-globe text-cyan-400',
        'PROXY': 'fa-random text-gray-400',
        'LOAD_BALANCER': 'fa-balance-scale text-blue-400',
        'OTHER': 'fa-cube text-gray-400'
    };
    
    servicios.forEach(servicio => {
        const colorEstado = obtenerColorEstado(servicio.status);
        const ultimaRespuesta = servicio.last_response_time ? 
            `${servicio.last_response_time.toFixed(0)} ms` : 'N/A';
        const safeName = servicio.name.replace(/'/g, "\\'");
        const iconClass = serviceIcons[servicio.service_type] || 'fa-cube text-gray-400';
        const serviceTypeLabel = servicio.service_type_display || servicio.service_type || 'Otro';
        const notificacionIcon = servicio.notify_telegram ? '🔔' : '🔕';
        const notificacionText = servicio.notify_telegram ? 'Notificaciones activas' : 'Notificaciones desactivadas';
        const notificacionColor = servicio.notify_telegram ? 'text-green-400' : 'text-gray-500';
        
        container.innerHTML += `
            <div class="servicio-card glass-panel rounded-xl p-5 hover:border-green-500 transition-colors relative group" 
                data-nombre="${servicio.name}" 
                data-url="${servicio.url}" 
                data-tipo="${servicio.service_type}">
                <div class="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="abrirModalHTTP('${servicio.id}', '${safeName}', '${servicio.url}', '${servicio.service_type}', ${servicio.timeout || 5}, ${servicio.check_ssl}, ${servicio.notify_telegram})" 
                            class="text-gray-400 hover:text-blue-400 p-1">
                        <i class="fa-solid fa-pen text-sm"></i>
                    </button>
                    <button onclick="eliminarServicioHTTP(${servicio.id}, '${safeName}')" 
                            class="text-gray-400 hover:text-red-400 p-1">
                        <i class="fa-solid fa-trash text-sm"></i>
                    </button>
                </div>
                
                <div class="flex justify-between items-start mb-4 mt-2">
                    <div class="flex items-center gap-3">
                        <div class="p-3 bg-gray-800 rounded-lg">
                            <i class="fa-solid ${iconClass} text-xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-lg leading-tight">${servicio.name}</h3>
                            <p class="text-xs text-gray-400 font-mono truncate max-w-[150px]">${servicio.url}</p>
                            <p class="text-xs text-gray-500 mt-0.5">
                                <span class="px-2 py-0.5 bg-gray-700/50 rounded-full">${serviceTypeLabel}</span>
                            </p>
                        </div>
                    </div>
                    <div class="h-3 w-3 rounded-full ${colorEstado}"></div>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mt-4 border-t border-gray-700 pt-4">
                    <div>
                        <p class="text-xs text-gray-400 uppercase tracking-wider">Respuesta</p>
                        <p class="text-sm font-semibold">${ultimaRespuesta}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400 uppercase tracking-wider">Código</p>
                        <p class="text-sm font-semibold">${servicio.status_code || 'N/A'}</p>
                    </div>
                </div>
                
                <div class="mt-2 pt-2 border-t border-gray-700/50 flex justify-between items-center">
                    <p class="text-xs text-gray-400">
                        ${servicio.check_ssl ? '🔒 SSL Verificado' : '🔓 SSL No verificado'}
                        ${servicio.ssl_expiry_date ? ` · Expira: ${new Date(servicio.ssl_expiry_date).toLocaleDateString()}` : ''}
                    </p>
                    <p class="text-xs ${notificacionColor}">
                        ${notificacionIcon} ${notificacionText}
                    </p>
                </div>
            </div>
        `;
    });
    
    gsap.fromTo(".servicio-card", 
        { y: 30, opacity: 0 }, 
        { y: 0, opacity: 1, duration: 0.4, stagger: 0.08, ease: "back.out(1.7)" }
    );
}

function renderizarPaginacionServicios() {
    const { paginaActual, totalPaginas } = estadoServicios;
    
    if (totalPaginas <= 1) {
        document.getElementById('paginationServicios').innerHTML = '';
        return;
    }
    
    const controles = generarControlesPaginacion(paginaActual, totalPaginas, 'cargarServiciosHTTP');
    document.getElementById('paginationServicios').innerHTML = `
        ${controles}
        <span class="text-xs text-gray-500 ml-2">Pág. ${paginaActual} de ${totalPaginas}</span>
    `;
}

// ============================================
// PREDICCIONES
// ============================================
async function cargarPredicciones(pagina = 1) {
    try {
        estadoPredicciones.paginaActual = pagina;
        const pageSize = parseInt(document.getElementById('pageSizePredicciones').value);
        estadoPredicciones.tamanoPagina = pageSize;
        
        const response = await fetch('/api/nodes/predictions/');
        const todasLasPredicciones = await response.json();
        
        estadoPredicciones.datos = todasLasPredicciones;
        estadoPredicciones.totalElementos = todasLasPredicciones.length;
        estadoPredicciones.totalPaginas = Math.ceil(estadoPredicciones.totalElementos / pageSize);
        
        document.getElementById('resultCountPredicciones').textContent = `${estadoPredicciones.totalElementos} predicciones`;
        
        const start = (pagina - 1) * pageSize;
        const end = start + pageSize;
        const prediccionesPagina = todasLasPredicciones.slice(start, end);
        
        renderizarPredicciones(prediccionesPagina);
        renderizarPaginacionPredicciones();
    } catch (error) {
        console.error("Error cargando predicciones:", error);
    }
}

function renderizarPredicciones(predictions) {
    const container = document.getElementById('predictions-container');
    container.innerHTML = '';
    
    if (predictions.length === 0) {
        container.innerHTML = `
            <div class="glass-panel p-8 rounded-xl col-span-2 text-center text-gray-400 border border-gray-700/50">
                <i class="fa-solid fa-check-circle text-4xl mb-3 block text-green-400"></i>
                <p class="text-lg font-semibold text-white">✅ No se detectaron posibles fallos</p>
                <p class="text-sm mt-1">Todos los nodos parecen estar estables</p>
            </div>
        `;
        return;
    }
    
    const severityColors = {
        'critical': 'border-red-500 bg-red-500/5',
        'warning': 'border-orange-400 bg-orange-400/5',
        'info': 'border-blue-400 bg-blue-400/5'
    };
    
    const severityBadges = {
        'critical': 'bg-red-500/15 text-red-400 border border-red-500/20',
        'warning': 'bg-orange-400/15 text-orange-400 border border-orange-400/20',
        'info': 'bg-blue-400/15 text-blue-400 border border-blue-400/20'
    };
    
    const severityIcons = {
        'critical': '🚨',
        'warning': '⚠️',
        'info': 'ℹ️'
    };
    
    predictions.forEach(pred => {
        container.innerHTML += `
            <div class="prediccion-card glass-panel p-4 rounded-xl border-l-4 ${severityColors[pred.severity] || 'border-gray-500'} hover:border-l-6 transition-all hover:shadow-lg"
                data-nombre="${pred.node.name}" 
                data-mensaje="${pred.message}" 
                data-tipo="${pred.type}">
                <div class="flex items-start gap-3">
                    <div class="text-2xl">${severityIcons[pred.severity] || '📢'}</div>
                    <div class="flex-1">
                        <div class="flex items-center gap-2 flex-wrap">
                            <p class="font-semibold text-sm">${pred.node.name}</p>
                            <span class="text-xs px-2.5 py-0.5 rounded-full ${severityBadges[pred.severity] || 'bg-gray-700/50 text-gray-400'}">
                                ${pred.severity.toUpperCase()}
                            </span>
                        </div>
                        <p class="text-sm mt-1">${pred.message}</p>
                        <p class="text-xs text-gray-400 mt-1">${pred.detail}</p>
                    </div>
                </div>
            </div>
        `;
    });
    
    gsap.fromTo(".prediccion-card", 
        { y: 20, opacity: 0 }, 
        { y: 0, opacity: 1, duration: 0.3, stagger: 0.08, ease: "back.out(1.7)" }
    );
}

function renderizarPaginacionPredicciones() {
    const { paginaActual, totalPaginas } = estadoPredicciones;
    const paginationElement = document.getElementById('paginationPredicciones');
    
    if (!paginationElement) {
        console.warn('Elemento paginationPredicciones no encontrado');
        return;
    }
    
    if (totalPaginas <= 1) {
        paginationElement.innerHTML = '';
        return;
    }
    
    const controles = generarControlesPaginacionPredicciones(paginaActual, totalPaginas);
    paginationElement.innerHTML = `
        ${controles}
        <span class="text-xs text-gray-500 ml-2">Pág. ${paginaActual} de ${totalPaginas}</span>
    `;
}

// ============================================
// MODALES - NODOS
// ============================================
const modal = document.getElementById('nodoModal');
const form = document.getElementById('nodoForm');

function abrirModal(id = null, name = '', ip = '', type = 'OTHER', notify_telegram = true) {
    pausarActualizaciones();
    
    document.getElementById('modalTitle').innerText = id ? 'Editar Dispositivo' : 'Nuevo Dispositivo';
    document.getElementById('nodoId').value = id || '';
    document.getElementById('nodoName').value = name;
    document.getElementById('nodoIp').value = ip;
    document.getElementById('nodoType').value = type;
    document.getElementById('nodoNotifyTelegram').checked = notify_telegram;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    gsap.fromTo(modal.querySelector('.glass-panel'), 
        { scale: 0.9, opacity: 0, y: 30 }, 
        { scale: 1, opacity: 1, y: 0, duration: 0.3, ease: "back.out(1.7)" }
    );
}

function cerrarModal() {
    gsap.to(modal.querySelector('.glass-panel'), {
        scale: 0.9,
        opacity: 0,
        y: 30,
        duration: 0.2,
        ease: "power3.in",
        onComplete: () => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            form.reset();
            reanudarActualizaciones();
        }
    });
}

async function guardarNodo(event) {
    event.preventDefault();
    const id = document.getElementById('nodoId').value;
    const data = {
        name: document.getElementById('nodoName').value,
        ip_address: document.getElementById('nodoIp').value,
        device_type: document.getElementById('nodoType').value,
        is_monitored: true,
        notify_telegram: document.getElementById('nodoNotifyTelegram').checked,
    };
    
    const method = id ? 'PUT' : 'POST';
    const endpoint = id ? `${apiUrl}${id}/` : apiUrl;

    try {
        const response = await fetch(endpoint, {
            method: method,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            cerrarModal();
            cargarNodos(estadoNodos.paginaActual);
        } else {
            const errorData = await response.json();
            alert('Error al guardar: ' + JSON.stringify(errorData));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar el dispositivo');
    }
}

async function eliminarNodo(id, name) {
    if (confirm(`¿Eliminar "${name}"? Todo su historial se borrará.`)) {
        try {
            const response = await fetch(`${apiUrl}${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrftoken }
            });
            if (response.ok) cargarNodos(estadoNodos.paginaActual);
        } catch (error) {
            console.error('Error al eliminar:', error);
        }
    }
}

// ============================================
// MODALES - SERVICIOS HTTP
// ============================================
const httpModal = document.getElementById('httpModal');
const httpForm = document.getElementById('httpForm');

function abrirModalHTTP(id = null, name = '', url = '', service_type = 'WEB', timeout = 5, check_ssl = true, notify_telegram = true) {
    pausarActualizaciones();
    
    document.getElementById('httpModalTitle').innerText = id ? 'Editar Servicio' : 'Nuevo Servicio Web';
    document.getElementById('httpId').value = id || '';
    document.getElementById('httpName').value = name;
    document.getElementById('httpUrl').value = url;
    document.getElementById('httpServiceType').value = service_type || 'WEB';
    document.getElementById('httpTimeout').value = timeout || 5;
    document.getElementById('httpCheckSSL').checked = check_ssl;
    document.getElementById('httpNotifyTelegram').checked = notify_telegram;
    httpModal.classList.remove('hidden');
    httpModal.classList.add('flex');
    
    gsap.fromTo(httpModal.querySelector('.glass-panel'), 
        { scale: 0.9, opacity: 0, y: 30 }, 
        { scale: 1, opacity: 1, y: 0, duration: 0.3, ease: "back.out(1.7)" }
    );
}

function cerrarModalHTTP() {
    gsap.to(httpModal.querySelector('.glass-panel'), {
        scale: 0.9,
        opacity: 0,
        y: 30,
        duration: 0.2,
        ease: "power3.in",
        onComplete: () => {
            httpModal.classList.add('hidden');
            httpModal.classList.remove('flex');
            httpForm.reset();
            reanudarActualizaciones();
        }
    });
}

async function guardarServicioHTTP(event) {
    event.preventDefault();
    const id = document.getElementById('httpId').value;
    const data = {
        name: document.getElementById('httpName').value,
        url: document.getElementById('httpUrl').value,
        service_type: document.getElementById('httpServiceType').value,
        expected_status: 200,
        timeout: parseInt(document.getElementById('httpTimeout').value) || 5,
        check_ssl: document.getElementById('httpCheckSSL').checked,
        notify_telegram: document.getElementById('httpNotifyTelegram').checked,
        is_active: true
    };
    
    const method = id ? 'PUT' : 'POST';
    const endpoint = id ? `${httpApiUrl}${id}/` : httpApiUrl;

    try {
        const response = await fetch(endpoint, {
            method: method,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            cerrarModalHTTP();
            cargarServiciosHTTP(estadoServicios.paginaActual);
            alert('✅ Servicio web guardado correctamente');
        } else {
            const errorData = await response.json();
            alert('❌ Error al guardar: ' + JSON.stringify(errorData));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('❌ Error al guardar el servicio');
    }
}

async function eliminarServicioHTTP(id, name) {
    if (confirm(`¿Eliminar el servicio "${name}"?`)) {
        try {
            const response = await fetch(`${httpApiUrl}${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrftoken }
            });
            if (response.ok) cargarServiciosHTTP(estadoServicios.paginaActual);
        } catch (error) {
            console.error('Error al eliminar:', error);
        }
    }
}

// ============================================
// CONTROL DE MODALES
// ============================================
let modalAbierto = false;

function pausarActualizaciones() {
    modalAbierto = true;
}

function reanudarActualizaciones() {
    modalAbierto = false;
}

// ============================================
// CONFIGURACIÓN DE TIEMPO
// ============================================
function cambiarTiempoActualizacion() {
    tiempoActualizacion = parseInt(document.getElementById('refreshRate').value);
    
    if (nodosInterval) clearInterval(nodosInterval);
    nodosInterval = setInterval(() => {
        if (!modalAbierto) {
            cargarNodos(estadoNodos.paginaActual);
        }
    }, tiempoActualizacion);
    
    if (serviciosInterval) clearInterval(serviciosInterval);
    serviciosInterval = setInterval(() => {
        if (!modalAbierto) {
            cargarServiciosHTTP(estadoServicios.paginaActual);
        }
    }, tiempoActualizacion);
    
    if (graficasInterval && nodoActualId) {
        clearInterval(graficasInterval);
        graficasInterval = setInterval(() => {
            if (!modalAbierto) {
                cargarDatosGrafica(nodoActualId);
            }
        }, tiempoActualizacion);
    }
}

// ============================================
// FILTROS
// ============================================
function filtrarNodos() {
    const termino = document.getElementById('filterNodos').value.toLowerCase().trim();
    const container = document.getElementById('nodos-container');
    const tarjetas = container.querySelectorAll('.nodo-card');
    let visibleCount = 0;
    
    tarjetas.forEach(tarjeta => {
        const nombre = tarjeta.dataset.nombre ? tarjeta.dataset.nombre.toLowerCase() : '';
        const ip = tarjeta.dataset.ip ? tarjeta.dataset.ip.toLowerCase() : '';
        const coincide = nombre.includes(termino) || ip.includes(termino);
        
        tarjeta.style.display = coincide ? '' : 'none';
        if (coincide) visibleCount++;
    });
    
    const statusEl = document.getElementById('filterStatusNodos');
    const clearBtn = document.getElementById('clearFilterNodos');
    
    if (termino) {
        statusEl.textContent = `(${visibleCount} coincidencias)`;
        clearBtn.classList.remove('hidden');
    } else {
        statusEl.textContent = '';
        clearBtn.classList.add('hidden');
    }
}

function limpiarFiltroNodos() {
    document.getElementById('filterNodos').value = '';
    filtrarNodos();
}

function filtrarServicios() {
    const termino = document.getElementById('filterServicios').value.toLowerCase().trim();
    const container = document.getElementById('http-container');
    const tarjetas = container.querySelectorAll('.servicio-card');
    let visibleCount = 0;
    
    tarjetas.forEach(tarjeta => {
        const nombre = tarjeta.dataset.nombre ? tarjeta.dataset.nombre.toLowerCase() : '';
        const url = tarjeta.dataset.url ? tarjeta.dataset.url.toLowerCase() : '';
        const tipo = tarjeta.dataset.tipo ? tarjeta.dataset.tipo.toLowerCase() : '';
        const coincide = nombre.includes(termino) || url.includes(termino) || tipo.includes(termino);
        
        tarjeta.style.display = coincide ? '' : 'none';
        if (coincide) visibleCount++;
    });
    
    const statusEl = document.getElementById('filterStatusServicios');
    const clearBtn = document.getElementById('clearFilterServicios');
    
    if (termino) {
        statusEl.textContent = `(${visibleCount} coincidencias)`;
        clearBtn.classList.remove('hidden');
    } else {
        statusEl.textContent = '';
        clearBtn.classList.add('hidden');
    }
}

function limpiarFiltroServicios() {
    document.getElementById('filterServicios').value = '';
    filtrarServicios();
}

function filtrarPredicciones() {
    const termino = document.getElementById('filterPredicciones').value.toLowerCase().trim();
    const container = document.getElementById('predictions-container');
    const tarjetas = container.querySelectorAll('.prediccion-card');
    let visibleCount = 0;
    
    tarjetas.forEach(tarjeta => {
        const nombre = tarjeta.dataset.nombre ? tarjeta.dataset.nombre.toLowerCase() : '';
        const mensaje = tarjeta.dataset.mensaje ? tarjeta.dataset.mensaje.toLowerCase() : '';
        const tipo = tarjeta.dataset.tipo ? tarjeta.dataset.tipo.toLowerCase() : '';
        const coincide = nombre.includes(termino) || mensaje.includes(termino) || tipo.includes(termino);
        
        tarjeta.style.display = coincide ? '' : 'none';
        if (coincide) visibleCount++;
    });
    
    const statusEl = document.getElementById('filterStatusPredicciones');
    const clearBtn = document.getElementById('clearFilterPredicciones');
    
    if (termino) {
        statusEl.textContent = `(${visibleCount} coincidencias)`;
        clearBtn.classList.remove('hidden');
    } else {
        statusEl.textContent = '';
        clearBtn.classList.add('hidden');
    }
}

function limpiarFiltroPredicciones() {
    document.getElementById('filterPredicciones').value = '';
    filtrarPredicciones();
}

// ============================================
// CAMBIAR TAMAÑO DE PÁGINA
// ============================================
function cambiarTamanoPaginaNodos() {
    cargarNodos(1);
}

function cambiarTamanoPaginaServicios() {
    cargarServiciosHTTP(1);
}

function cambiarTamanoPaginaPredicciones() {
    cargarPredicciones(1);
}

// ============================================
// GRÁFICAS (funciones que dependen de Chart.js)
// ============================================
let chartInstanciaLatencia = null;
let chartInstanciaUptime = null;
let graficasInterval = null;
const graficasModal = document.getElementById('graficasModal');

async function abrirGraficas(id, name) {
    pausarActualizaciones();
    
    nodoActualId = id;
    document.getElementById('graficasTitle').innerText = `📊 Rendimiento: ${name}`;
    graficasModal.classList.remove('hidden');
    graficasModal.classList.add('flex');
    
    gsap.fromTo("#graficasContent", 
        { scale: 0.95, opacity: 0, y: 20 }, 
        { scale: 1, opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }
    );
    
    await cargarDatosGrafica(id);
    
    if (graficasInterval) clearInterval(graficasInterval);
    graficasInterval = setInterval(() => cargarDatosGrafica(id), tiempoActualizacion);
}

function cerrarGraficas() {
    if (graficasInterval) clearInterval(graficasInterval);
    gsap.to("#graficasContent", {
        scale: 0.95,
        opacity: 0,
        y: 20,
        duration: 0.2,
        ease: "power3.in",
        onComplete: () => {
            graficasModal.classList.add('hidden');
            graficasModal.classList.remove('flex');
            reanudarActualizaciones();
        }
    });
}

async function cargarDatosGrafica(id) {
    try {
        const respuesta = await fetch(`${apiUrl}${id}/history/`);
        let historial = await respuesta.json();
        historial = historial.reverse();
        
        const etiquetas = historial.map(log => {
            const fecha = new Date(log.timestamp);
            return `${fecha.getHours()}:${fecha.getMinutes().toString().padStart(2, '0')}`;
        });
        
        const metricsResp = await fetch(`${apiUrl}${id}/metrics/?days=7`);
        const metrics = await metricsResp.json();
        
        dibujarGraficas(etiquetas, historial, metrics);
    } catch (error) {
        console.error("Error cargando historial:", error);
    }
}

function dibujarGraficas(etiquetas, datosHistorial, metrics) {
    const ctxLatencia = document.getElementById('latenciaChart').getContext('2d');
    const ctxUptime = document.getElementById('uptimeChart').getContext('2d');
    
    if (chartInstanciaLatencia) chartInstanciaLatencia.destroy();
    if (chartInstanciaUptime) chartInstanciaUptime.destroy();

    Chart.defaults.color = '#9ca3af';
    Chart.defaults.borderColor = '#334155';
    Chart.defaults.font.family = 'ui-monospace, monospace';

    // === GRÁFICA 1: LATENCIA ===
    const gradientLatencia = ctxLatencia.createLinearGradient(0, 0, 0, 300);
    gradientLatencia.addColorStop(0, 'rgba(56, 189, 248, 0.4)');
    gradientLatencia.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

    const datosLatencia = datosHistorial.map(log => log.is_online ? log.latency_ms : 0);
    const datosPerdida = datosHistorial.map(log => log.packet_loss_pct);

    chartInstanciaLatencia = new Chart(ctxLatencia, {
        type: 'line',
        data: {
            labels: etiquetas,
            datasets: [
                {
                    label: 'Latencia (ms)',
                    data: datosLatencia,
                    borderColor: '#38bdf8',
                    backgroundColor: gradientLatencia,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    type: 'line',
                    label: 'Pérdida (%)',
                    data: datosPerdida,
                    borderColor: '#ef4444',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    stepped: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { labels: { usePointStyle: true } } },
            scales: {
                x: { grid: { drawBorder: false } },
                y: { type: 'linear', position: 'left', beginAtZero: true },
                y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, min: 0, max: 100 }
            }
        }
    });

    // === GRÁFICA 2: UPTIME ===
    const dias = 7;
    const uptimeData = [];
    const labels = [];
    for (let i = dias-1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString());
        
        const dayLogs = datosHistorial.filter(log => {
            const logDate = new Date(log.timestamp);
            return logDate.toDateString() === date.toDateString();
        });
        
        if (dayLogs.length > 0) {
            const onlineCount = dayLogs.filter(log => log.is_online).length;
            uptimeData.push((onlineCount / dayLogs.length) * 100);
        } else {
            uptimeData.push(0);
        }
    }

    chartInstanciaUptime = new Chart(ctxUptime, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Disponibilidad (%)',
                data: uptimeData,
                backgroundColor: uptimeData.map(val =>
                    val >= 95 ? 'rgba(34, 197, 94, 0.7)' :
                    val >= 80 ? 'rgba(234, 179, 8, 0.7)' :
                    'rgba(239, 68, 68, 0.7)'
                ),
                borderColor: '#2d3748',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { min: 0, max: 100, title: { display: true, text: 'Disponibilidad %' } }
            }
        }
    });
}

// ============================================
// ACTUALIZAR CONTADORES
// ============================================
function actualizarContadores() {
    fetch(apiUrl)
        .then(res => res.json())
        .then(data => {
            document.getElementById('countNodos').textContent = data.length;
        })
        .catch(err => console.error('Error al obtener contador de nodos:', err));
    
    fetch(httpApiUrl)
        .then(res => res.json())
        .then(data => {
            document.getElementById('countServicios').textContent = data.length;
        })
        .catch(err => console.error('Error al obtener contador de servicios:', err));
    
    fetch('/api/nodes/predictions/')
        .then(res => res.json())
        .then(data => {
            document.getElementById('countPredicciones').textContent = data.length;
        })
        .catch(err => console.error('Error al obtener contador de predicciones:', err));
}

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener("DOMContentLoaded", () => {
    cargarNodos(1);
    cargarServiciosHTTP(1);
    cargarPredicciones(1);
    
    actualizarContadores();
    
    nodosInterval = setInterval(() => {
        if (!modalAbierto && tabActual === 'nodos') {
            cargarNodos(estadoNodos.paginaActual);
        }
    }, tiempoActualizacion);
    
    serviciosInterval = setInterval(() => {
        if (!modalAbierto && tabActual === 'servicios') {
            cargarServiciosHTTP(estadoServicios.paginaActual);
        }
    }, tiempoActualizacion);
    
    prediccionesInterval = setInterval(() => {
        if (!modalAbierto && tabActual === 'predicciones') {
            cargarPredicciones(estadoPredicciones.paginaActual);
        }
    }, 60000);
});

// ============================================
// EXPONER FUNCIONES AL ÁMBITO GLOBAL
// ============================================
window.abrirModal = abrirModal;
window.cerrarModal = cerrarModal;
window.guardarNodo = guardarNodo;
window.eliminarNodo = eliminarNodo;

window.abrirModalHTTP = abrirModalHTTP;
window.cerrarModalHTTP = cerrarModalHTTP;
window.guardarServicioHTTP = guardarServicioHTTP;
window.eliminarServicioHTTP = eliminarServicioHTTP;

window.abrirGraficas = abrirGraficas;
window.cerrarGraficas = cerrarGraficas;

window.cargarNodos = cargarNodos;
window.cargarServiciosHTTP = cargarServiciosHTTP;
window.cargarPredicciones = cargarPredicciones;

window.cambiarTamanoPaginaNodos = cambiarTamanoPaginaNodos;
window.cambiarTamanoPaginaServicios = cambiarTamanoPaginaServicios;
window.cambiarTamanoPaginaPredicciones = cambiarTamanoPaginaPredicciones;

window.filtrarNodos = filtrarNodos;
window.limpiarFiltroNodos = limpiarFiltroNodos;
window.filtrarServicios = filtrarServicios;
window.limpiarFiltroServicios = limpiarFiltroServicios;
window.filtrarPredicciones = filtrarPredicciones;
window.limpiarFiltroPredicciones = limpiarFiltroPredicciones;

window.cambiarTiempoActualizacion = cambiarTiempoActualizacion;
window.cambiarTab = cambiarTab;

window.obtenerIcono = obtenerIcono;
window.obtenerColorEstado = obtenerColorEstado;