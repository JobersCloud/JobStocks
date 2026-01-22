// app.js - VERSIÓN ESTABLE
const protocol = window.location.protocol;
const hostname = window.location.hostname;
const port = window.location.port;

// Construir API_URL: usar puerto solo si no es estándar (80/443) y no es localhost con puerto específico
let API_URL;
if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // En local siempre usar puerto 5000
    API_URL = `${protocol}//${hostname}:5000`;
} else {
    // En producción (túnel ngrok/cloudflare), usar el mismo host sin puerto
    API_URL = `${protocol}//${hostname}${port ? ':' + port : ''}`;
}

console.log('=== DEBUG INFO ===');
console.log('Protocol:', protocol);
console.log('Hostname:', hostname);
console.log('Port:', port);
console.log('API URL final:', API_URL);
console.log('==================');

let stocksData = [];
let carrito = [];
let currentUser = null;  // Usuario actual con rol
let propuestasHabilitadas = true;  // Control de funcionalidad de propuestas
let gridConImagenes = false;  // Control de imágenes en tabla/tarjetas (desactivado por defecto)
let whatsappConfig = { habilitado: false, numero: null };  // Configuración de WhatsApp
let csrfToken = null;  // Token CSRF para protección contra ataques

// ==================== PAGINACIÓN BACKEND ====================
let paginacionBackend = {
    habilitado: false,   // Si usar paginación backend (solo para grid sin imágenes)
    limite: 50,          // Registros por página
    total: 0,            // Total de registros
    pages: 1             // Total de páginas
};

// ==================== ORDENACIÓN Y FILTROS DE COLUMNAS ====================
let ordenActual = {
    columna: 'codigo',   // Columna actual de ordenación
    direccion: 'ASC'     // ASC o DESC
};

// Filtros acumulativos estilo WorkWithPlus (array de objetos {columna, operador, valor})
let filtrosColumna = [];

// Popup de filtro actualmente abierto
let popupFiltroAbierto = null;

// Operadores disponibles para columnas de texto
const operadoresTexto = [
    { key: 'contains', label: 'Contiene' },
    { key: 'eq', label: 'Igual a' },
    { key: 'starts', label: 'Empieza por' },
    { key: 'ends', label: 'Termina en' }
];

// Operadores disponibles para columnas numéricas
const operadoresNumero = [
    { key: 'eq', label: 'Igual a' },
    { key: 'gt', label: 'Mayor que' },
    { key: 'gte', label: 'Mayor o igual' },
    { key: 'lt', label: 'Menor que' },
    { key: 'lte', label: 'Menor o igual' },
    { key: 'neq', label: 'Diferente de' }
];

// Columnas disponibles para filtrar con su tipo
const columnasFiltrables = [
    { key: 'codigo', label: 'Código', tipo: 'texto' },
    { key: 'descripcion', label: 'Descripción', tipo: 'texto' },
    { key: 'formato', label: 'Formato', tipo: 'texto' },
    { key: 'serie', label: 'Serie', tipo: 'texto' },
    { key: 'color', label: 'Color', tipo: 'texto' },
    { key: 'calidad', label: 'Calidad', tipo: 'texto' },
    { key: 'tono', label: 'Tono', tipo: 'texto' },
    { key: 'calibre', label: 'Calibre', tipo: 'texto' },
    { key: 'existencias', label: 'Existencias', tipo: 'numero' }
];

// Para compatibilidad con panel lateral (filtros simples)
let filtrosActivos = [];

// ==================== CSRF TOKEN ====================

// Obtener CSRF token del servidor
async function obtenerCsrfToken() {
    try {
        const response = await fetch(`${API_URL}/api/csrf-token`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            csrfToken = data.csrf_token;
            localStorage.setItem('csrf_token', csrfToken);
            console.log('🔐 CSRF token obtenido');
        }
    } catch (e) {
        console.error('Error obteniendo CSRF token:', e);
    }
}

// Fetch con CSRF token automático para métodos mutantes
async function fetchWithCsrf(url, options = {}) {
    // Añadir CSRF token a métodos que modifican datos
    if (['POST', 'PUT', 'DELETE'].includes(options.method)) {
        options.headers = {
            ...options.headers,
            'X-CSRF-Token': csrfToken
        };
    }
    options.credentials = 'include';
    return fetch(url, options);
}


// Paginación (solo cuando gridConImagenes está activo)
let paginaActual = 1;
let itemsPorPagina = 20;
let totalItems = 0;
let allStocksData = [];  // Todos los datos sin paginar

// ==================== TEMA CLARO/OSCURO ====================

// Cargar tema guardado
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
}

// Aplicar tema
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    // Actualizar switch y icono
    const themeSwitch = document.getElementById('theme-switch');
    const themeIcon = document.getElementById('theme-icon');

    if (themeSwitch) {
        themeSwitch.checked = theme === 'dark';
    }
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }

    localStorage.setItem('theme', theme);
}

// Alternar tema
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

// ==================== LOGO DINÁMICO POR EMPRESA ====================

// Aplicar tema de color
function applyColorTheme(tema) {
    const validThemes = ['rubi', 'zafiro', 'esmeralda', 'amatista', 'ambar', 'grafito'];
    if (!validThemes.includes(tema)) {
        tema = 'rubi';
    }
    document.documentElement.setAttribute('data-color-theme', tema);
    localStorage.setItem('colorTheme', tema);
    console.log(`🎨 Tema de color aplicado: ${tema}`);
}

// Cargar logo y favicon de la empresa desde la BD
// Usa 'connection' (empresa_cli_id) porque el endpoint necesita conectar a la BD del cliente
async function cargarLogoEmpresa() {
    const connection = localStorage.getItem('connection');
    if (!connection) {
        console.warn('No hay connection en localStorage, usando valores por defecto');
        applyColorTheme('rubi');
        return;
    }
    const logoElements = document.querySelectorAll('.logo');

    try {
        // Obtener configuración completa del logo (incluye invertir_logo y tema)
        const configResponse = await fetch(`${API_URL}/api/empresa/${connection}/config`);
        const config = await configResponse.json();

        // Aplicar tema de color
        applyColorTheme(config.tema || 'rubi');

        // Determinar el filtro CSS según la configuración
        const invertirFilter = config.invertir_logo ? 'brightness(0) invert(1)' : 'none';

        if (config.tiene_logo) {
            // Cargar logo desde la API con timestamp para evitar caché
            const logoUrl = `${API_URL}/api/empresa/${connection}/logo?t=${Date.now()}`;
            // Guardar URL base en localStorage para otras páginas (registro, verificación)
            localStorage.setItem('logoUrl', `${API_URL}/api/empresa/${connection}/logo`);

            logoElements.forEach(el => {
                el.src = logoUrl;
                el.style.filter = invertirFilter;
                el.style.visibility = 'visible';
            });

            // Cargar favicon si existe y guardar en localStorage para otras páginas
            if (config.tiene_favicon) {
                const faviconUrl = `${API_URL}/api/empresa/${connection}/favicon`;
                localStorage.setItem('faviconUrl', faviconUrl);
                let faviconLink = document.querySelector("link[rel='icon']");
                if (!faviconLink) {
                    faviconLink = document.createElement('link');
                    faviconLink.rel = 'icon';
                    document.head.appendChild(faviconLink);
                }
                faviconLink.href = faviconUrl;
            } else {
                localStorage.removeItem('faviconUrl');
            }

            console.log(`Logo cargado desde BD para connection ${connection}, invertir: ${config.invertir_logo}`);
        } else {
            // Usar logo por defecto con filtro de inversión (para headers)
            localStorage.removeItem('logoUrl');
            logoElements.forEach(el => {
                el.src = 'assets/logo.svg';
                el.style.filter = 'brightness(0) invert(1)';
                el.style.visibility = 'visible';
            });
            console.log(`No hay logo en BD para connection ${connection}, usando default con inversión`);
        }
    } catch (error) {
        console.log('Error al cargar logo:', error);
        // En caso de error, mostrar logo por defecto con inversión y tema rubi
        applyColorTheme('rubi');
        logoElements.forEach(el => {
            el.src = 'assets/logo.svg';
            el.style.filter = 'brightness(0) invert(1)';
            el.style.visibility = 'visible';
        });
    }

    // Cargar nombre de la empresa
    try {
        const response = await fetch(`${API_URL}/api/empresa/current`);
        if (response.ok) {
            const data = await response.json();
            if (data.empresa && data.empresa.nombre) {
                const headerName = document.getElementById('header-company-name');
                if (headerName) {
                    headerName.textContent = data.empresa.nombre;
                    headerName.style.display = 'block';
                    document.title = `${data.empresa.nombre} - Gestión de Stocks`;
                }
            }
        }
    } catch (e) {
        console.log('Error cargando nombre empresa:', e);
    }
}

// Exponer función globalmente
window.toggleTheme = toggleTheme;

// Cargar tema inmediatamente para evitar flash
loadTheme();

// ==================== MULTI-EMPRESA ====================

// Obtener empresa_id del localStorage (OBLIGATORIO)
function getEmpresaId() {
    const empresaId = localStorage.getItem('empresa_id');
    if (!empresaId) {
        console.error('ERROR: No hay empresa_id en localStorage');
        return null;
    }
    console.log(`📍 Empresa actual: ${empresaId}`);
    return empresaId;
}

// Agregar empresa_id a los parámetros de búsqueda
function addEmpresaToParams(params) {
    const empresaId = getEmpresaId();
    if (empresaId) {
        params.append('empresa', empresaId);
    }
    return params;
}

// Mostrar error crítico cuando falta el parámetro connection
function showCriticalError() {
    document.body.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 500px; text-align: center;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
                <h1 style="color: #333; margin-bottom: 1rem; font-size: 1.5rem;">Sesión Inválida</h1>
                <p style="color: #666; margin-bottom: 1.5rem; line-height: 1.6;">
                    No se ha detectado una conexión válida para esta sesión.
                </p>
                <p style="color: #999; font-size: 0.9rem; margin-bottom: 1.5rem;">
                    Por favor, inicie sesión desde la URL correcta con el parámetro <strong>connection</strong>.
                </p>
                <a href="/login" style="display: inline-block; background: #667eea; color: white; padding: 0.75rem 2rem; border-radius: 6px; text-decoration: none; font-weight: 500;">
                    Ir a Login
                </a>
            </div>
        </div>
    `;
}

// ==================== PROPUESTAS ====================

// Verificar si las propuestas están habilitadas
async function verificarPropuestasHabilitadas() {
    try {
        const empresaId = localStorage.getItem('empresa_id') || '1';
        const response = await fetch(`${API_URL}/api/parametros/propuestas-habilitadas?empresa_id=${empresaId}`);
        const data = await response.json();
        propuestasHabilitadas = data.habilitado;
        console.log(`📋 Propuestas habilitadas: ${propuestasHabilitadas}`);

        // Ocultar/mostrar elementos según el estado
        aplicarEstadoPropuestas();

        return propuestasHabilitadas;
    } catch (error) {
        console.error('Error al verificar propuestas:', error);
        // Por defecto, habilitar propuestas si hay error
        propuestasHabilitadas = true;
        return true;
    }
}

// Cargar configuración de WhatsApp
async function cargarConfigWhatsApp() {
    try {
        const empresaId = localStorage.getItem('empresa_id') || '1';
        const response = await fetch(`${API_URL}/api/consultas/whatsapp-config?empresa_id=${empresaId}`, {
            credentials: 'include'
        });
        const data = await response.json();
        whatsappConfig = {
            habilitado: data.habilitado || false,
            numero: data.numero || null
        };
        console.log(`📱 WhatsApp habilitado: ${whatsappConfig.habilitado}`);
    } catch (error) {
        console.error('Error al cargar config WhatsApp:', error);
        whatsappConfig = { habilitado: false, numero: null };
    }
}

// Aplicar estado de propuestas a los elementos de la UI
function aplicarEstadoPropuestas() {
    // Botón flotante del carrito
    const carritoBtn = document.querySelector('.carrito-btn');
    if (carritoBtn) {
        carritoBtn.style.display = propuestasHabilitadas ? 'flex' : 'none';
    }

    // Opciones del menú relacionadas con propuestas
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes('propuesta') || text.includes('proposal')) {
            item.style.display = propuestasHabilitadas ? 'flex' : 'none';
        }
    });

    // Si hay datos cargados, re-renderizar la tabla
    if (stocksData && stocksData.length > 0) {
        mostrarTabla(stocksData);
    }
}

// ==================== GRID CON IMÁGENES ====================

// Verificar si se deben mostrar imágenes en la tabla/tarjetas
async function verificarGridConImagenes() {
    try {
        const empresaId = localStorage.getItem('empresa_id') || '1';
        const response = await fetch(`${API_URL}/api/parametros/grid-con-imagenes?empresa_id=${empresaId}`);
        const data = await response.json();
        gridConImagenes = data.habilitado;
        console.log(`🖼️ Grid con imágenes: ${gridConImagenes}`);

        // Si hay datos cargados, re-renderizar la tabla con/sin imágenes
        if (stocksData && stocksData.length > 0) {
            mostrarTabla(stocksData);
        }

        return gridConImagenes;
    } catch (error) {
        console.error('Error al verificar grid con imágenes:', error);
        // Por defecto, desactivar imágenes si hay error
        gridConImagenes = false;
        return false;
    }
}

// ==================== PAGINACIÓN BACKEND (GRID SIN IMÁGENES) ====================

// Cargar configuración de paginación para el grid sin imágenes
async function cargarConfigPaginacion() {
    try {
        const empresaId = localStorage.getItem('empresa_id') || '1';
        const response = await fetch(`${API_URL}/api/parametros/paginacion-config?empresa_id=${empresaId}`);
        const data = await response.json();
        paginacionBackend.habilitado = data.habilitado;
        paginacionBackend.limite = data.limite || 50;
        console.log(`📄 Paginación backend: ${paginacionBackend.habilitado}, límite: ${paginacionBackend.limite}`);
        return paginacionBackend;
    } catch (error) {
        console.error('Error al cargar config paginación:', error);
        paginacionBackend.habilitado = false;
        return paginacionBackend;
    }
}

// ==================== CARGA DE THUMBNAILS ====================

// Cola de códigos pendientes de cargar
let thumbnailQueue = [];
let thumbnailTimeout = null;

// Cargar thumbnails en batch (más eficiente que peticiones individuales)
async function cargarThumbnailsBatch(codigos) {
    if (codigos.length === 0) return;

    try {
        const response = await fetchWithCsrf(`${API_URL}/api/stocks/thumbnails`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ codigos: codigos })
        });

        if (response.ok) {
            const thumbnails = await response.json();
            // Aplicar thumbnails a las imágenes correspondientes
            // Buscar por cada imagen porque los códigos pueden tener espacios
            document.querySelectorAll('.stock-thumb[data-codigo]').forEach(imgElement => {
                const codigoImg = imgElement.dataset.codigo.trim();
                const imagen = thumbnails[codigoImg];
                if (imagen && !imgElement.classList.contains('loaded')) {
                    imgElement.src = `data:image/jpeg;base64,${imagen}`;
                    imgElement.classList.add('loaded');
                }
            });
        }
    } catch (error) {
        console.log('Error al cargar thumbnails en batch:', error);
    }
}

// Procesar cola de thumbnails pendientes
function procesarColaThumbnails() {
    if (thumbnailQueue.length === 0) return;

    // Tomar hasta 50 códigos de la cola (límite del endpoint)
    const codigos = thumbnailQueue.splice(0, 50);
    cargarThumbnailsBatch(codigos);
}

// Añadir código a la cola y programar carga
function encolarThumbnail(codigo) {
    const codigoTrim = codigo.trim();
    if (!thumbnailQueue.includes(codigoTrim)) {
        thumbnailQueue.push(codigoTrim);
    }

    // Cancelar timeout anterior y programar uno nuevo
    // Esto agrupa múltiples imágenes que entran en viewport casi simultáneamente
    if (thumbnailTimeout) {
        clearTimeout(thumbnailTimeout);
    }
    thumbnailTimeout = setTimeout(procesarColaThumbnails, 50);
}

// Inicializar Intersection Observer para lazy loading de imágenes
function initImageObserver() {
    if (!gridConImagenes) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const codigo = img.dataset.codigo;
                if (codigo && !img.classList.contains('loaded')) {
                    encolarThumbnail(codigo);
                }
                observer.unobserve(img);
            }
        });
    }, {
        rootMargin: '100px',
        threshold: 0.1
    });

    // Observar todas las imágenes de thumbnail
    document.querySelectorAll('.stock-thumb[data-codigo]').forEach(img => {
        observer.observe(img);
    });
}

// ==================== AUTENTICACIÓN ====================

// Verificar autenticación
async function checkAuth() {
    try {
        console.log('🔐 Verificando autenticación...');
        const response = await fetch(`${API_URL}/api/current-user`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log('Auth response status:', response.status);

        if (!response.ok) {
            console.log('❌ No autenticado, redirigiendo a login...');
            window.location.href = '/login';
            return false;
        }

        const user = await response.json();
        console.log('✅ Usuario autenticado:', user.username);

        // Si debe cambiar contraseña, redirigir al login
        if (user.debe_cambiar_password) {
            console.log('⚠️ Usuario debe cambiar contraseña, redirigiendo a login...');
            const connection = localStorage.getItem('connection');
            window.location.replace(`/login?connection=${connection}`);
            return false;
        }

        displayUserInfo(user);
        return true;
    } catch (error) {
        console.error('❌ Error verificando autenticación:', error);
        window.location.href = '/login';
        return false;
    }
}

// Mostrar información del usuario en el menú
function displayUserInfo(user) {
    currentUser = user;

    // Actualizar nombre en el botón del menú
    const userNameDisplay = document.getElementById('user-name-display');
    if (userNameDisplay) {
        userNameDisplay.textContent = user.full_name || user.username;
    }

    // Actualizar nombre y rol en el header del menú
    const menuUserName = document.getElementById('menu-user-name');
    const menuUserRol = document.getElementById('menu-user-rol');
    if (menuUserName) {
        menuUserName.textContent = user.full_name || user.username;
    }
    if (menuUserRol) {
        const rolTexts = {
            'usuario': t('roles.user') || 'Usuario',
            'administrador': t('roles.admin') || 'Administrador',
            'superusuario': t('roles.superuser') || 'Superusuario'
        };
        menuUserRol.textContent = rolTexts[user.rol] || user.rol;
    }

    // Mostrar sección de admin si el usuario es administrador o superusuario
    const adminSection = document.getElementById('menu-admin-section');
    if (adminSection) {
        if (user.rol === 'administrador' || user.rol === 'superusuario') {
            adminSection.style.display = 'block';
        } else {
            adminSection.style.display = 'none';
        }
    }

    console.log(`👤 Usuario: ${user.username}, Rol: ${user.rol}`);
}

// Toggle del menú de usuario
function toggleUserMenu() {
    const menuBtn = document.getElementById('menu-btn');
    const menuDropdown = document.getElementById('menu-dropdown');

    if (menuDropdown.classList.contains('show')) {
        menuDropdown.classList.remove('show');
        menuBtn.classList.remove('active');
    } else {
        menuDropdown.classList.add('show');
        menuBtn.classList.add('active');
    }
}

// Cerrar menú al hacer clic fuera
document.addEventListener('click', function (event) {
    const menuContainer = document.querySelector('.menu-container');
    const menuDropdown = document.getElementById('menu-dropdown');
    const menuBtn = document.getElementById('menu-btn');

    if (menuContainer && !menuContainer.contains(event.target)) {
        if (menuDropdown) menuDropdown.classList.remove('show');
        if (menuBtn) menuBtn.classList.remove('active');
    }
});

// Navegar a diferentes secciones
// NO se pasa empresa en la URL - el backend obtiene empresa_id de la sesión
function navigateTo(section) {
    // Cerrar el menú
    const menuDropdown = document.getElementById('menu-dropdown');
    const menuBtn = document.getElementById('menu-btn');
    if (menuDropdown) menuDropdown.classList.remove('show');
    if (menuBtn) menuBtn.classList.remove('active');

    // Navegar según la sección (sin parámetros - el backend usa la sesión)
    switch (section) {
        case 'mis-propuestas':
            window.location.href = 'mis-propuestas.html';
            break;
        case 'todas-propuestas':
            window.location.href = 'todas-propuestas.html';
            break;
        case 'todas-consultas':
            window.location.href = 'todas-consultas.html';
            break;
        case 'usuarios':
            window.location.href = 'usuarios.html';
            break;
        case 'email-config':
            window.location.href = 'email-config.html';
            break;
        case 'parametros':
            window.location.href = 'parametros.html';
            break;
        case 'dashboard':
            window.location.href = 'dashboard.html';
            break;
        case 'empresa-logo':
            window.location.href = 'empresa-logo.html';
            break;
        default:
            console.log('Sección no reconocida:', section);
    }
}

// Cerrar sesión
async function logout() {
    if (confirm(t('auth.logoutConfirm'))) {
        try {
            await fetchWithCsrf(`${API_URL}/api/logout`, {
                method: 'POST',
                credentials: 'include'
            });
            window.location.href = '/login';
        } catch (error) {
            console.error('Error al cerrar sesión:', error);
            alert(t('auth.logoutError'));
        }
    }
}

// ==================== FUNCIONES DE STOCKS ====================

// Cargar opciones de los filtros desplegables
async function cargarOpcionesFiltros() {
    try {
        console.log('📊 Cargando opciones de filtros...');
        const params = new URLSearchParams();
        addEmpresaToParams(params);

        const response = await fetch(`${API_URL}/api/stocks?${params}`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log('Filtros response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const stocks = await response.json();
        console.log('✅ Stocks cargados:', stocks.length, 'registros');

        // Extraer valores únicos
        const formatos = [...new Set(stocks.map(s => s.formato).filter(Boolean))].sort();
        const series = [...new Set(stocks.map(s => s.serie).filter(Boolean))].sort();
        const calidades = [...new Set(stocks.map(s => s.calidad).filter(Boolean))].sort();
        const colores = [...new Set(stocks.map(s => s.color).filter(Boolean))].sort();

        console.log('Formatos únicos:', formatos.length);
        console.log('Series únicas:', series.length);
        console.log('Calidades únicas:', calidades.length);
        console.log('Colores únicos:', colores.length);

        // Llenar select de formatos
        const selectFormato = document.getElementById('filter-formato');
        formatos.forEach(formato => {
            const option = document.createElement('option');
            option.value = formato;
            option.textContent = formato;
            selectFormato.appendChild(option);
        });

        // Llenar select de series
        const selectSerie = document.getElementById('filter-serie');
        series.forEach(serie => {
            const option = document.createElement('option');
            option.value = serie;
            option.textContent = serie;
            selectSerie.appendChild(option);
        });

        // Llenar select de calidades
        const selectCalidad = document.getElementById('filter-calidad');
        calidades.forEach(calidad => {
            const option = document.createElement('option');
            option.value = calidad;
            option.textContent = calidad;
            selectCalidad.appendChild(option);
        });

        // Llenar select de colores
        const selectColor = document.getElementById('filter-color');
        colores.forEach(color => {
            const option = document.createElement('option');
            option.value = color;
            option.textContent = color;
            selectColor.appendChild(option);
        });

        console.log('✅ Filtros cargados correctamente');
    } catch (error) {
        console.error('❌ Error al cargar opciones de filtros:', error);
        if (error.message.includes('401')) {
            window.location.href = '/login';
        }
    }
}

// Cargar todos los stocks
async function cargarTodos() {
    mostrarCargando();
    try {
        console.log('📦 Cargando todos los stocks...');
        const params = new URLSearchParams();
        addEmpresaToParams(params);

        // Si no hay imágenes y paginación backend está habilitada, usar paginación del servidor
        const usarPaginacionBackend = !gridConImagenes && paginacionBackend.habilitado;

        if (usarPaginacionBackend) {
            params.append('page', paginaActual);
            params.append('limit', paginacionBackend.limite);
            params.append('order_by', ordenActual.columna);
            params.append('order_dir', ordenActual.direccion);

            // Añadir filtros de columna (con operadores: columna__operador=valor)
            filtrosColumna.forEach(filtro => {
                params.append(`${filtro.columna}__${filtro.operador}`, filtro.valor);
            });

            // Añadir filtros del panel lateral (sin operador)
            filtrosActivos.forEach(filtro => {
                params.append(filtro.columna, filtro.valor);
            });
        }

        const endpoint = usarPaginacionBackend ? '/api/stocks/search' : '/api/stocks';
        const response = await fetch(`${API_URL}${endpoint}?${params}`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log('Stocks response status:', response.status);

        if (response.status === 401) {
            console.log('❌ 401 - Redirigiendo a login...');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (usarPaginacionBackend) {
            // Respuesta con metadatos de paginación
            allStocksData = data.data;
            totalItems = data.total;
            paginacionBackend.total = data.total;
            paginacionBackend.pages = data.pages;
            console.log(`✅ Stocks cargados (paginación backend): ${allStocksData.length} de ${totalItems} registros, página ${paginaActual}/${paginacionBackend.pages}`);
        } else {
            // Respuesta sin paginación (array directo)
            allStocksData = data;
            totalItems = allStocksData.length;
            console.log('✅ Stocks cargados:', totalItems, 'registros');
        }

        mostrarDatos();
    } catch (error) {
        console.error('❌ Error al cargar stocks:', error);
        mostrarError(t('errors.loadingStocks'));
    }
}

// Mostrar datos con o sin paginación según gridConImagenes y paginacionBackend
function mostrarDatos() {
    const usarPaginacionBackend = !gridConImagenes && paginacionBackend.habilitado;

    if (gridConImagenes) {
        // Con imágenes: paginación frontend
        const inicio = (paginaActual - 1) * itemsPorPagina;
        const fin = inicio + itemsPorPagina;
        stocksData = allStocksData.slice(inicio, fin);
        mostrarTabla(stocksData);
        mostrarPaginacion();
    } else if (usarPaginacionBackend) {
        // Sin imágenes con paginación backend: datos ya vienen paginados
        stocksData = allStocksData;
        mostrarTabla(stocksData);
        mostrarPaginacion();
    } else {
        // Sin imágenes sin paginación: mostrar todo
        stocksData = allStocksData;
        mostrarTabla(stocksData);
        ocultarPaginacion();
    }
}

// Cambiar de página
async function irAPagina(pagina) {
    const usarPaginacionBackend = !gridConImagenes && paginacionBackend.habilitado;

    if (usarPaginacionBackend) {
        // Paginación backend: recargar del servidor
        const totalPaginas = paginacionBackend.pages;
        if (pagina < 1 || pagina > totalPaginas) return;
        paginaActual = pagina;
        await cargarTodos();  // Recarga con la nueva página
    } else {
        // Paginación frontend
        const totalPaginas = Math.ceil(totalItems / itemsPorPagina);
        if (pagina < 1 || pagina > totalPaginas) return;
        paginaActual = pagina;
        mostrarDatos();
    }
    // Scroll al inicio del contenido
    document.getElementById('table-container').scrollIntoView({ behavior: 'smooth' });
}

// Mostrar controles de paginación
function mostrarPaginacion() {
    const usarPaginacionBackend = !gridConImagenes && paginacionBackend.habilitado;
    const registrosPorPagina = usarPaginacionBackend ? paginacionBackend.limite : itemsPorPagina;
    const totalPaginas = usarPaginacionBackend ? paginacionBackend.pages : Math.ceil(totalItems / itemsPorPagina);

    if (totalPaginas <= 1) {
        ocultarPaginacion();
        return;
    }

    let container = document.getElementById('pagination-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'pagination-container';
        container.className = 'pagination-container';
        document.getElementById('table-container').after(container);
    }

    // Generar botones de página
    let paginasHTML = '';
    const maxBotones = 5;
    let inicio = Math.max(1, paginaActual - Math.floor(maxBotones / 2));
    let fin = Math.min(totalPaginas, inicio + maxBotones - 1);

    if (fin - inicio < maxBotones - 1) {
        inicio = Math.max(1, fin - maxBotones + 1);
    }

    for (let i = inicio; i <= fin; i++) {
        paginasHTML += `<button class="pagination-btn ${i === paginaActual ? 'active' : ''}"
                                onclick="irAPagina(${i})">${i}</button>`;
    }

    const registroInicio = ((paginaActual - 1) * registrosPorPagina) + 1;
    const registroFin = Math.min(paginaActual * registrosPorPagina, totalItems);

    container.innerHTML = `
        <div class="pagination-info">
            ${t('common.showing') || 'Mostrando'} ${registroInicio}-${registroFin}
            ${t('common.of') || 'de'} ${totalItems}
        </div>
        <div class="pagination-buttons">
            <button class="pagination-btn" onclick="irAPagina(1)" ${paginaActual === 1 ? 'disabled' : ''}>««</button>
            <button class="pagination-btn" onclick="irAPagina(${paginaActual - 1})" ${paginaActual === 1 ? 'disabled' : ''}>«</button>
            ${paginasHTML}
            <button class="pagination-btn" onclick="irAPagina(${paginaActual + 1})" ${paginaActual === totalPaginas ? 'disabled' : ''}>»</button>
            <button class="pagination-btn" onclick="irAPagina(${totalPaginas})" ${paginaActual === totalPaginas ? 'disabled' : ''}>»»</button>
        </div>
    `;
    container.style.display = 'flex';
}

// Ocultar paginación
function ocultarPaginacion() {
    const container = document.getElementById('pagination-container');
    if (container) {
        container.style.display = 'none';
    }
}

// ==================== ORDENACIÓN POR COLUMNAS ====================

// Cambiar ordenación al hacer clic en cabecera
async function ordenarPorColumna(columna) {
    // Si es la misma columna, cambiar dirección; si es otra, ordenar ASC
    if (ordenActual.columna === columna) {
        ordenActual.direccion = ordenActual.direccion === 'ASC' ? 'DESC' : 'ASC';
    } else {
        ordenActual.columna = columna;
        ordenActual.direccion = 'ASC';
    }

    console.log(`📊 Ordenando por ${ordenActual.columna} ${ordenActual.direccion}`);

    const usarPaginacionBackend = !gridConImagenes && paginacionBackend.habilitado;

    if (usarPaginacionBackend) {
        // Ordenación en backend: recargar datos
        paginaActual = 1;  // Volver a primera página
        await cargarTodos();
    } else {
        // Ordenación en frontend: ordenar array local
        allStocksData.sort((a, b) => {
            let valA = a[ordenActual.columna] || '';
            let valB = b[ordenActual.columna] || '';

            // Para existencias, ordenar numéricamente
            if (ordenActual.columna === 'existencias') {
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            } else {
                valA = valA.toString().toLowerCase();
                valB = valB.toString().toLowerCase();
            }

            if (ordenActual.direccion === 'ASC') {
                return valA > valB ? 1 : valA < valB ? -1 : 0;
            } else {
                return valA < valB ? 1 : valA > valB ? -1 : 0;
            }
        });
        paginaActual = 1;
        mostrarDatos();
    }
}

// ==================== FILTROS ESTILO WORKWITHPLUS ====================

// Obtener operadores según tipo de columna
function getOperadoresPorTipo(columna) {
    const col = columnasFiltrables.find(c => c.key === columna);
    return col?.tipo === 'numero' ? operadoresNumero : operadoresTexto;
}

// Obtener label del operador
function getLabelOperador(operadorKey) {
    const op = [...operadoresTexto, ...operadoresNumero].find(o => o.key === operadorKey);
    return op?.label || operadorKey;
}

// Verificar si una columna tiene filtro activo
function tieneFiltroColumna(columna) {
    return filtrosColumna.some(f => f.columna === columna);
}

// Icono SVG de filtro para usar en popups
const iconoFiltroSVG = `<svg viewBox="0 0 16 16" fill="currentColor" width="16" height="16"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>`;

// Mostrar popup de filtro para una columna
function mostrarPopupFiltro(columna, elemento) {
    // Cerrar popup anterior si existe
    cerrarPopupFiltro();

    const col = columnasFiltrables.find(c => c.key === columna);
    if (!col) {
        console.error('Columna no encontrada:', columna);
        return;
    }

    console.log('🔽 Abriendo popup filtro para:', columna);

    const operadores = getOperadoresPorTipo(columna);
    const filtroExistente = filtrosColumna.find(f => f.columna === columna);

    // Crear el popup
    const popup = document.createElement('div');
    popup.className = 'filter-popup';
    popup.id = `filter-popup-${columna}`;

    popup.innerHTML = `
        <div class="filter-popup-header">
            <span class="filter-popup-icon">${iconoFiltroSVG}</span>
            <span class="filter-popup-title">${col.label}</span>
            <button class="filter-popup-close" onclick="cerrarPopupFiltro()" title="Cerrar">×</button>
        </div>
        <div class="filter-popup-body">
            <div class="filter-popup-section">
                <label class="filter-popup-label">Condición</label>
                <div class="filter-popup-operators">
                    ${operadores.map((op, idx) => `
                        <label class="filter-popup-operator">
                            <input type="radio" name="op-${columna}" value="${op.key}"
                                   ${(filtroExistente?.operador === op.key || (!filtroExistente && idx === 0)) ? 'checked' : ''}>
                            <span class="filter-radio-custom"></span>
                            <span class="filter-operator-text">${op.label}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
            <div class="filter-popup-section">
                <label class="filter-popup-label" for="filter-value-${columna}">Valor</label>
                <input type="text" class="filter-popup-input" id="filter-value-${columna}"
                       placeholder="Escribir valor..." value="${filtroExistente?.valor || ''}"
                       onkeypress="if(event.key==='Enter') aplicarFiltroColumna('${columna}')">
            </div>
        </div>
        <div class="filter-popup-footer">
            <button class="btn-filter-clear" onclick="limpiarFiltroColumna('${columna}')">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14" height="14"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                Limpiar
            </button>
            <button class="btn-filter-apply" onclick="aplicarFiltroColumna('${columna}')">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14" height="14"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg>
                Aplicar filtro
            </button>
        </div>
    `;

    // Posicionar el popup debajo del icono
    const rect = elemento.getBoundingClientRect();

    popup.style.position = 'fixed';
    popup.style.top = `${rect.bottom + 5}px`;
    popup.style.left = `${Math.min(rect.left, window.innerWidth - 220)}px`;
    popup.style.zIndex = '1000';

    document.body.appendChild(popup);
    popupFiltroAbierto = popup;

    // Enfocar el input
    setTimeout(() => {
        document.getElementById(`filter-value-${columna}`)?.focus();
    }, 100);
}

// Cerrar popup de filtro
function cerrarPopupFiltro() {
    if (popupFiltroAbierto) {
        popupFiltroAbierto.remove();
        popupFiltroAbierto = null;
    }
}

// Aplicar filtro de una columna
async function aplicarFiltroColumna(columna) {
    const inputValor = document.getElementById(`filter-value-${columna}`);
    const radioSeleccionado = document.querySelector(`input[name="op-${columna}"]:checked`);

    const valor = inputValor?.value.trim();
    const operador = radioSeleccionado?.value || 'contains';

    if (!valor) {
        // Si no hay valor, limpiar el filtro de esta columna
        limpiarFiltroColumna(columna);
        return;
    }

    // Eliminar filtro anterior de esta columna si existe
    filtrosColumna = filtrosColumna.filter(f => f.columna !== columna);

    // Añadir nuevo filtro
    filtrosColumna.push({ columna, operador, valor });

    console.log(`🔍 Filtro columna: ${columna} ${operador} "${valor}"`);

    // Cerrar popup
    cerrarPopupFiltro();

    // Actualizar UI
    renderizarChipsFiltrosColumna();
    actualizarIconosFiltro();

    // Aplicar filtros
    paginaActual = 1;
    await aplicarFiltros();
}

// Limpiar filtro de una columna
async function limpiarFiltroColumna(columna) {
    filtrosColumna = filtrosColumna.filter(f => f.columna !== columna);

    console.log(`🗑️ Filtro columna eliminado: ${columna}`);

    // Cerrar popup
    cerrarPopupFiltro();

    // Actualizar UI
    renderizarChipsFiltrosColumna();
    actualizarIconosFiltro();

    // Aplicar filtros
    paginaActual = 1;
    await aplicarFiltros();
}

// Quitar filtro de columna por índice (desde chips)
async function quitarFiltroColumna(index) {
    filtrosColumna.splice(index, 1);

    console.log(`🗑️ Filtro columna eliminado`);

    // Actualizar UI
    renderizarChipsFiltrosColumna();
    actualizarIconosFiltro();

    // Aplicar filtros
    paginaActual = 1;
    await aplicarFiltros();
}

// Limpiar todos los filtros de columna
async function limpiarTodosFiltrosColumna() {
    filtrosColumna = [];
    filtrosActivos = [];  // También limpiar filtros del panel lateral

    // Limpiar inputs del panel lateral
    const inputsLaterales = ['filter-formato', 'filter-serie', 'filter-calidad', 'filter-color', 'filter-existencias'];
    inputsLaterales.forEach(id => {
        const input = document.getElementById(id);
        if (input) input.value = '';
    });

    // Actualizar UI
    renderizarChipsFiltrosColumna();
    actualizarIconosFiltro();

    // Resetear ordenación
    ordenActual.columna = 'codigo';
    ordenActual.direccion = 'ASC';

    // Recargar datos
    paginaActual = 1;
    await cargarTodos();
}

// Actualizar iconos de filtro en headers (cambiar color si hay filtro activo)
function actualizarIconosFiltro() {
    columnasFiltrables.forEach(col => {
        const icono = document.querySelector(`.column-filter-icon[data-columna="${col.key}"]`);
        if (icono) {
            if (tieneFiltroColumna(col.key)) {
                icono.classList.add('active');
            } else {
                icono.classList.remove('active');
            }
        }
    });
}

// Renderizar chips de filtros de columna
function renderizarChipsFiltrosColumna() {
    const container = document.getElementById('column-filters-chips');
    if (!container) return;

    // Combinar filtros de columna + filtros del panel lateral
    const todosFiltros = [
        ...filtrosColumna.map((f, idx) => ({
            ...f,
            tipo: 'columna',
            index: idx
        })),
        ...filtrosActivos.map((f, idx) => ({
            columna: f.columna,
            operador: 'contains',
            valor: f.valor,
            tipo: 'lateral',
            index: idx
        }))
    ];

    if (todosFiltros.length === 0) {
        container.innerHTML = '';
        container.style.display = 'none';
        return;
    }

    container.style.display = 'flex';

    const chipsHTML = todosFiltros.map((filtro, idx) => {
        const labelColumna = columnasFiltrables.find(c => c.key === filtro.columna)?.label || filtro.columna;
        const labelOperador = getLabelOperador(filtro.operador);
        const onclickFn = filtro.tipo === 'columna'
            ? `quitarFiltroColumna(${filtro.index})`
            : `quitarFiltro(${filtro.index})`;

        return `
            <span class="filter-chip">
                <span class="filter-chip-column">${labelColumna}:</span>
                <span class="filter-chip-operator">${labelOperador.toLowerCase()}</span>
                <span class="filter-chip-value" title="${filtro.valor}">"${filtro.valor}"</span>
                <span class="filter-chip-remove" onclick="${onclickFn}">✕</span>
            </span>
        `;
    }).join('');

    container.innerHTML = chipsHTML + `
        <button class="btn-clear-filters" onclick="limpiarTodosFiltrosColumna()">Limpiar todo</button>
    `;
}

// Aplicar filtros (backend o frontend según configuración)
async function aplicarFiltros() {
    const usarPaginacionBackend = !gridConImagenes && paginacionBackend.habilitado;

    if (usarPaginacionBackend) {
        // Filtros en backend: recargar datos
        await cargarTodos();
    } else {
        // Filtros en frontend: aplicar a datos locales
        aplicarFiltrosFrontend();
    }
}

// Aplicar filtros en frontend (cuando no hay paginación backend)
function aplicarFiltrosFrontend() {
    let datosFiltrados = [...allStocksData];

    // Aplicar filtros de columna (con operadores)
    filtrosColumna.forEach(filtro => {
        datosFiltrados = datosFiltrados.filter(item => {
            const valorItem = (item[filtro.columna] || '').toString();
            const valorBuscar = filtro.valor;

            switch (filtro.operador) {
                case 'eq':
                    return valorItem.toLowerCase() === valorBuscar.toLowerCase();
                case 'neq':
                    return valorItem.toLowerCase() !== valorBuscar.toLowerCase();
                case 'contains':
                    return valorItem.toLowerCase().includes(valorBuscar.toLowerCase());
                case 'starts':
                    return valorItem.toLowerCase().startsWith(valorBuscar.toLowerCase());
                case 'ends':
                    return valorItem.toLowerCase().endsWith(valorBuscar.toLowerCase());
                case 'gt':
                    return parseFloat(valorItem) > parseFloat(valorBuscar);
                case 'gte':
                    return parseFloat(valorItem) >= parseFloat(valorBuscar);
                case 'lt':
                    return parseFloat(valorItem) < parseFloat(valorBuscar);
                case 'lte':
                    return parseFloat(valorItem) <= parseFloat(valorBuscar);
                default:
                    return valorItem.toLowerCase().includes(valorBuscar.toLowerCase());
            }
        });
    });

    // Aplicar filtros del panel lateral (siempre usa "contiene")
    filtrosActivos.forEach(filtro => {
        const valorBuscar = filtro.valor.toLowerCase();
        datosFiltrados = datosFiltrados.filter(item => {
            const valorItem = (item[filtro.columna] || '').toString().toLowerCase();
            return valorItem.includes(valorBuscar);
        });
    });

    stocksData = datosFiltrados;
    totalItems = datosFiltrados.length;
    mostrarTabla(stocksData);

    if (gridConImagenes) {
        mostrarPaginacion();
    } else {
        ocultarPaginacion();
    }
}

// Generar HTML del contenedor de chips de filtros (sin barra de añadir)
function generarContenedorChips() {
    return `
        <div class="column-filters-chips" id="column-filters-chips" style="display: none;"></div>
    `;
}

// Mantener compatibilidad: Añadir un filtro desde panel lateral
async function agregarFiltro() {
    // Esta función se usa desde el panel lateral
    // Los filtros se añaden desde buscarStocks()
}

// Quitar un filtro del panel lateral por índice
async function quitarFiltro(index) {
    filtrosActivos.splice(index, 1);

    console.log(`🗑️ Filtro lateral eliminado`);

    // Actualizar UI de chips
    renderizarChipsFiltrosColumna();

    // Aplicar filtros
    paginaActual = 1;
    await aplicarFiltros();
}

// Mantener compatibilidad
function renderizarChipsFiltros() {
    renderizarChipsFiltrosColumna();
}

// Cerrar popup al hacer clic fuera
document.addEventListener('click', (e) => {
    if (popupFiltroAbierto && !popupFiltroAbierto.contains(e.target) &&
        !e.target.classList.contains('column-filter-icon')) {
        cerrarPopupFiltro();
    }
});

// Cerrar popup con Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && popupFiltroAbierto) {
        cerrarPopupFiltro();
    }
});

// Cerrar popup al hacer scroll
window.addEventListener('scroll', () => {
    if (popupFiltroAbierto) {
        cerrarPopupFiltro();
    }
}, true);  // Capture phase para detectar scroll en cualquier elemento

// Buscar con filtros (panel lateral) - Convierte filtros laterales a filtros activos
async function buscarStocks() {
    // Obtener filtros del panel lateral
    const filtrosLaterales = {
        formato: document.getElementById('filter-formato').value.trim(),
        serie: document.getElementById('filter-serie').value.trim(),
        calidad: document.getElementById('filter-calidad').value.trim(),
        color: document.getElementById('filter-color').value.trim(),
        existencias_min: document.getElementById('filter-existencias').value.trim()
    };

    // Convertir filtros laterales a filtros activos (sin duplicar)
    Object.keys(filtrosLaterales).forEach(key => {
        const valor = filtrosLaterales[key];
        if (valor) {
            // Verificar si ya existe este filtro
            const existe = filtrosActivos.some(f => f.columna === key && f.valor === valor);
            if (!existe) {
                filtrosActivos.push({ columna: key, valor: valor });
            }
        }
    });

    // Actualizar chips
    renderizarChipsFiltrosColumna();

    // Construir query string
    const params = new URLSearchParams();
    addEmpresaToParams(params);

    // Añadir filtros de columna (con operadores: columna__operador=valor)
    filtrosColumna.forEach(filtro => {
        params.append(`${filtro.columna}__${filtro.operador}`, filtro.valor);
    });

    // Añadir filtros del panel lateral (sin operador, backend usa LIKE por defecto)
    filtrosActivos.forEach(filtro => {
        params.append(filtro.columna, filtro.valor);
    });

    // Si paginación backend está activa, añadir parámetros de paginación y ordenación
    const usarPaginacionBackend = !gridConImagenes && paginacionBackend.habilitado;

    if (usarPaginacionBackend) {
        paginaActual = 1;  // Resetear a primera página
        params.append('page', paginaActual);
        params.append('limit', paginacionBackend.limite);
        params.append('order_by', ordenActual.columna);
        params.append('order_dir', ordenActual.direccion);
    }

    mostrarCargando();
    try {
        const url = `${API_URL}/api/stocks/search?${params}`;
        console.log('🔍 Buscando con URL:', url);

        const response = await fetch(url, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }

        const data = await response.json();

        if (usarPaginacionBackend) {
            // Respuesta con metadatos de paginación
            allStocksData = data.data;
            totalItems = data.total;
            paginacionBackend.total = data.total;
            paginacionBackend.pages = data.pages;
            console.log(`✅ Búsqueda completada (paginación backend): ${allStocksData.length} de ${totalItems} resultados`);
        } else {
            // Respuesta sin paginación
            allStocksData = data;
            totalItems = allStocksData.length;
            paginaActual = 1;
            console.log('✅ Búsqueda completada:', totalItems, 'resultados');
        }

        mostrarDatos();
    } catch (error) {
        console.error('❌ Error al buscar stocks:', error);
        mostrarError(t('errors.searchingStocks'));
    }
}

// Limpiar filtros (panel lateral + barra de filtros)
function limpiarFiltros() {
    // Limpiar filtros laterales (inputs)
    document.getElementById('filter-formato').value = '';
    document.getElementById('filter-serie').value = '';
    document.getElementById('filter-calidad').value = '';
    document.getElementById('filter-color').value = '';
    document.getElementById('filter-existencias').value = '';

    // Limpiar filtros activos (panel lateral y columnas)
    filtrosActivos = [];
    filtrosColumna = [];
    renderizarChipsFiltrosColumna();
    actualizarIconosFiltro();

    // Resetear ordenación
    ordenActual.columna = 'codigo';
    ordenActual.direccion = 'ASC';

    paginaActual = 1;
    cargarTodos();
}

function mostrarTabla(stocks) {
    const container = document.getElementById('table-container');

    if (!stocks || stocks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📦</div>
                <h3>${t('empty.noResults')}</h3>
                <p>${t('empty.tryOtherFilters')}</p>
            </div>
        `;
        return;
    }

    // Si gridConImagenes está activo, mostrar vista de tarjetas con imagen prominente
    if (gridConImagenes) {
        const htmlGrid = `
            <div class="stock-grid-images">
                ${stocks.map(stock => `
                    <div class="stock-image-card" onclick='verDetalle(${JSON.stringify(stock).replace(/'/g, "&apos;")})'>
                        <div class="stock-image-card-img">
                            <img class="stock-thumb" data-codigo="${stock.codigo}"
                                 src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
                                 alt="${stock.descripcion}" loading="lazy">
                        </div>
                        <div class="stock-image-card-info">
                            <div class="stock-image-card-code">${stock.codigo}</div>
                            <div class="stock-image-card-desc" title="${stock.descripcion}">${stock.descripcion}</div>
                            <div class="stock-image-card-details">
                                ${stock.formato || '-'} | ${stock.calidad || '-'} | ${stock.tono || '-'}/${stock.calibre || '-'}
                            </div>
                            <div class="stock-image-card-stock">
                                ${getBadgeWithUnit(stock.existencias, stock.unidad)}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        container.innerHTML = htmlGrid;
        initImageObserver();
        return;
    }

    // Icono SVG de ordenación
    const iconoOrdenASC = `<svg class="sort-arrow" viewBox="0 0 10 6" fill="currentColor"><path d="M5 0L10 6H0L5 0Z"/></svg>`;
    const iconoOrdenDESC = `<svg class="sort-arrow" viewBox="0 0 10 6" fill="currentColor"><path d="M5 6L0 0H10L5 6Z"/></svg>`;
    const iconoOrdenNeutro = `<svg class="sort-arrow neutral" viewBox="0 0 10 14" fill="currentColor"><path d="M5 0L10 5H0L5 0Z M5 14L0 9H10L5 14Z"/></svg>`;

    // Icono SVG de filtro (embudo)
    const iconoFiltro = `<svg class="filter-icon-svg" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>`;

    // Función helper para generar icono de ordenación
    const getOrdenIcono = (columna) => {
        if (ordenActual.columna === columna) {
            return ordenActual.direccion === 'ASC' ? iconoOrdenASC : iconoOrdenDESC;
        }
        return iconoOrdenNeutro;
    };

    // Verificar si la columna es filtrable
    const esColumnaFiltrable = (columna) => {
        return columnasFiltrables.some(c => c.key === columna);
    };

    // Función helper para generar header con ordenación e icono de filtro
    const getHeaderConOrden = (columna, label) => {
        const esColumnaActual = ordenActual.columna === columna;
        const tieneFiltro = tieneFiltroColumna(columna);
        const puedeFiltrarse = esColumnaFiltrable(columna);

        return `
            <div class="column-header-wrapper">
                <div class="sortable-header ${esColumnaActual ? 'active' : ''}" onclick="ordenarPorColumna('${columna}')">
                    <span class="header-label">${label}</span>
                    <span class="sort-icon ${esColumnaActual ? 'active' : ''}">${getOrdenIcono(columna)}</span>
                </div>
                ${puedeFiltrarse ? `
                    <button class="column-filter-btn ${tieneFiltro ? 'active' : ''}"
                          data-columna="${columna}"
                          onclick="event.stopPropagation(); mostrarPopupFiltro('${columna}', this)"
                          title="Filtrar por ${label}">${iconoFiltro}</button>
                ` : ''}
            </div>
        `;
    };

    // Vista normal: chips de filtros + tabla en desktop, tarjetas en móvil
    const html = `
        <!-- Chips de filtros activos -->
        ${generarContenedorChips()}

        <!-- Vista de tabla para desktop -->
        <table class="stock-table-advanced">
            <thead>
                <tr class="header-row">
                    <th class="sortable-th">${getHeaderConOrden('codigo', t('table.code'))}</th>
                    <th class="sortable-th">${getHeaderConOrden('descripcion', t('table.description'))}</th>
                    <th class="sortable-th">${getHeaderConOrden('formato', t('table.format'))}</th>
                    <th class="sortable-th">${getHeaderConOrden('color', t('table.color'))}</th>
                    <th class="sortable-th">${getHeaderConOrden('calidad', t('table.quality'))}</th>
                    <th class="sortable-th">${getHeaderConOrden('tono', t('table.tone'))}</th>
                    <th class="sortable-th">${getHeaderConOrden('calibre', t('table.caliber'))}</th>
                    <th class="sortable-th">${getHeaderConOrden('existencias', t('table.stock'))}</th>
                    <th>${t('table.action')}</th>
                </tr>
            </thead>
            <tbody>
                ${stocks.map(stock => `
                    <tr>
                        <td><strong>${stock.codigo}</strong></td>
                        <td>${stock.descripcion}</td>
                        <td>${stock.formato || '-'}</td>
                        <td>${stock.color || '-'}</td>
                        <td>${stock.calidad || '-'}</td>
                        <td>${stock.tono || '-'}</td>
                        <td>${stock.calibre || '-'}</td>
                        <td>${getBadgeWithUnit(stock.existencias, stock.unidad)}</td>
                        <td class="actions-cell">
                            <button class="btn-primary btn-table" onclick='verDetalle(${JSON.stringify(stock).replace(/'/g, "&apos;")})'>
                                ${t('table.view')}
                            </button>${propuestasHabilitadas ? `<button class="btn-secondary btn-table" onclick='agregarAlCarrito(${JSON.stringify(stock).replace(/'/g, "&apos;")})'>
                                ${t('table.addToCart')}
                            </button>` : ''}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>

        <!-- Vista de tarjetas para móvil -->
        <div class="cards-container">
            ${stocks.map(stock => `
                <div class="stock-card">
                    <div class="stock-card-header">
                        <div class="stock-card-title">${stock.descripcion}</div>
                        ${getBadgeWithUnit(stock.existencias, stock.unidad)}
                    </div>
                    <div class="stock-card-body">
                        <div class="stock-card-field">
                            <span class="stock-card-label">${t('cards.code')}</span>
                            <span class="stock-card-value">${stock.codigo}</span>
                        </div>
                        <div class="stock-card-field">
                            <span class="stock-card-label">${t('cards.format')}</span>
                            <span class="stock-card-value">${stock.formato || '-'}</span>
                        </div>
                        <div class="stock-card-field">
                            <span class="stock-card-label">${t('cards.model')}</span>
                            <span class="stock-card-value">${stock.serie || '-'}</span>
                        </div>
                        <div class="stock-card-field">
                            <span class="stock-card-label">${t('cards.color')}</span>
                            <span class="stock-card-value">${stock.color || '-'}</span>
                        </div>
                        <div class="stock-card-field">
                            <span class="stock-card-label">${t('cards.quality')}</span>
                            <span class="stock-card-value">${stock.calidad || '-'}</span>
                        </div>
                        <div class="stock-card-field">
                            <span class="stock-card-label">${t('cards.tone')}</span>
                            <span class="stock-card-value">${stock.tono || '-'}</span>
                        </div>
                        <div class="stock-card-field">
                            <span class="stock-card-label">${t('cards.caliber')}</span>
                            <span class="stock-card-value">${stock.calibre || '-'}</span>
                        </div>
                    </div>
                    <div class="stock-card-footer">
                        <button class="btn-primary" style="padding: 8px 16px; font-size: 0.9em; ${propuestasHabilitadas ? 'margin-right: 5px;' : ''}"
                                onclick='verDetalle(${JSON.stringify(stock).replace(/'/g, "&apos;")})'>
                            ${t('cards.viewDetail')}
                        </button>
                        ${propuestasHabilitadas ? `<button class="btn-secondary" style="padding: 8px 16px; font-size: 0.9em;"
                                onclick='agregarAlCarrito(${JSON.stringify(stock).replace(/'/g, "&apos;")})'>
                            ${t('cards.addToCart')}
                        </button>` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    container.innerHTML = html;

    // Re-renderizar los chips de filtros activos
    renderizarChipsFiltros();
}


// Ver detalle en modal
async function verDetalle(stock) {
    const modal = document.getElementById('detail-modal');
    const content = document.getElementById('detail-content');

    // Formatear existencias con separador de miles
    const existenciasFormatted = parseFloat(stock.existencias).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    // Mostrar modal con datos básicos y loading para imágenes
    content.innerHTML = `
        <div class="detail-item">
            <span class="detail-label">${t('detail.code')}:</span>
            <span class="detail-value">${stock.codigo}</span>
        </div>
        ${stock.ean13 ? `
        <div class="detail-item">
            <span class="detail-label">${t('detail.ean13')}:</span>
            <span class="detail-value">${stock.ean13}</span>
        </div>
        ` : ''}
        <div class="detail-item">
            <span class="detail-label">${t('detail.description')}:</span>
            <span class="detail-value">${stock.descripcion}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.format')}:</span>
            <span class="detail-value">${stock.formato || '-'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.model')}:</span>
            <span class="detail-value">${stock.serie || '-'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.color')}:</span>
            <span class="detail-value">${stock.color || '-'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.quality')}:</span>
            <span class="detail-value">${stock.calidad || '-'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.tone')}:</span>
            <span class="detail-value">${stock.tono || '-'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.caliber')}:</span>
            <span class="detail-value">${stock.calibre || '-'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.pallet')}:</span>
            <span class="detail-value">${stock.pallet || '-'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.box')}:</span>
            <span class="detail-value">${stock.caja || '-'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">${t('detail.stock')}:</span>
            <span class="detail-value"><strong>${existenciasFormatted} ${stock.unidad || ''}</strong></span>
        </div>
        ${stock.unidadescaja || stock.cajaspallet || stock.pesocaja || stock.pesopallet ? `
        <div class="detail-packaging-section">
            <div class="detail-packaging-title">${t('detail.packaging')}</div>
            <div class="detail-packaging-grid">
                ${stock.unidadescaja ? `
                <div class="detail-packaging-item">
                    <div class="detail-packaging-icon">📦</div>
                    <div class="detail-packaging-info">
                        <div class="detail-packaging-label">${t('detail.unitsPerBox')}</div>
                        <div class="detail-packaging-value">${formatearCantidadEmpaquetado(stock.unidadescaja)} ${stock.unidad || ''}</div>
                    </div>
                </div>
                ` : ''}
                ${stock.cajaspallet ? `
                <div class="detail-packaging-item">
                    <div class="detail-packaging-icon">🏗️</div>
                    <div class="detail-packaging-info">
                        <div class="detail-packaging-label">${t('detail.boxesPerPallet')}</div>
                        <div class="detail-packaging-value">${formatearCantidadEmpaquetado(stock.cajaspallet)}</div>
                    </div>
                </div>
                ` : ''}
                ${stock.unidadescaja && stock.cajaspallet ? `
                <div class="detail-packaging-item">
                    <div class="detail-packaging-icon">📊</div>
                    <div class="detail-packaging-info">
                        <div class="detail-packaging-label">${t('detail.unitsPerPallet')}</div>
                        <div class="detail-packaging-value">${(() => {
                    const decimalesUnidadesCaja = getDecimalPlaces(stock.unidadescaja);
                    const unidadesPallet = stock.unidadescaja * stock.cajaspallet;
                    const unidadesPalletRedondeado = redondearADecimales(unidadesPallet, decimalesUnidadesCaja);
                    return parseFloat(unidadesPalletRedondeado).toLocaleString('en-US', {
                        minimumFractionDigits: decimalesUnidadesCaja,
                        maximumFractionDigits: decimalesUnidadesCaja
                    });
                })()} ${stock.unidad || ''}</div>
                    </div>
                </div>
                ` : ''}
                ${stock.pesocaja ? `
                <div class="detail-packaging-item">
                    <div class="detail-packaging-icon">⚖️</div>
                    <div class="detail-packaging-info">
                        <div class="detail-packaging-label">${t('detail.weightPerBox')}</div>
                        <div class="detail-packaging-value">${stock.pesocaja.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                })} kg</div>
                    </div>
                </div>
                ` : ''}
                ${stock.pesopallet ? `
                <div class="detail-packaging-item">
                    <div class="detail-packaging-icon">🏋️</div>
                    <div class="detail-packaging-info">
                        <div class="detail-packaging-label">${t('detail.weightPerPallet')}</div>
                        <div class="detail-packaging-value">${stock.pesopallet.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                })} kg</div>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
        ` : ''}
        <div id="detail-imagenes" class="detail-imagenes">
            <div class="detail-imagenes-loading">${t('detail.loadingImages')}</div>
        </div>
        <div id="detail-ficha-tecnica" class="detail-ficha-tecnica" style="display: none;"></div>
        <div class="detail-contact-block" style="border: 1px solid var(--border); border-radius: 8px; padding: 15px; margin-top: 15px;">
            <div class="detail-label" style="margin-bottom: 12px;">${t('detail.contact')}:</div>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                <button class="btn-inquiry" style="padding: 10px 20px; font-size: 14px; background: #2196F3; color: white; border: none; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;"
                        onclick="window.abrirModalConsulta()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    ${t('inquiry.askQuestion')}
                </button>
                ${whatsappConfig.habilitado ? `
                <button class="btn-whatsapp" style="padding: 10px 20px; font-size: 14px; background: #25D366; color: white; border: none; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;"
                        onclick="window.abrirWhatsApp()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                    </svg>
                    ${t('inquiry.whatsapp')}
                </button>
                ` : ''}
            </div>
        </div>
        <div class="detail-actions" style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 20px;">
            ${propuestasHabilitadas ? `
            <button class="btn-secondary" style="padding: 12px 24px; font-size: 1em;"
                    onclick="agregarAlCarritoDesdeDetalle()">
                ${t('detail.addToCart')}
            </button>
            ` : ''}
            <button class="btn-close-detail" onclick="cerrarModal()" style="padding: 12px 24px; font-size: 1em; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;">
                ${t('common.close')}
            </button>
        </div>
    `;

    // Guardar referencia al stock actual para el botón del carrito
    window.stockActualDetalle = stock;

    modal.style.display = 'flex';

    // Cargar imágenes del artículo
    try {
        const response = await fetch(`${API_URL}/api/stocks/${encodeURIComponent(stock.codigo)}/imagenes`, {
            credentials: 'include'
        });

        const imagenesContainer = document.getElementById('detail-imagenes');

        if (response.ok) {
            const imagenes = await response.json();

            if (imagenes.length > 0) {
                let imagenesHtml = `<div class="detail-label" style="width:100%; margin-bottom: 10px;">${t('detail.images')}:</div>`;
                imagenesHtml += '<div class="detail-imagenes-grid">';
                imagenes.forEach((img, index) => {
                    imagenesHtml += `
                        <div class="detail-imagen-item" onclick="ampliarImagen('${img.imagen}')">
                            <img src="data:image/jpeg;base64,${img.imagen}" alt="${t('detail.imageAlt', { number: index + 1 })}">
                        </div>
                    `;
                });
                imagenesHtml += '</div>';
                imagenesContainer.innerHTML = imagenesHtml;
            } else {
                imagenesContainer.innerHTML = `<div class="detail-no-imagenes">${t('detail.noImages')}</div>`;
            }
        } else {
            imagenesContainer.innerHTML = `<div class="detail-no-imagenes">${t('detail.noImages')}</div>`;
        }
    } catch (error) {
        console.error('Error al cargar imágenes:', error);
        document.getElementById('detail-imagenes').innerHTML = `<div class="detail-no-imagenes">${t('detail.errorLoadingImages')}</div>`;
    }

    // Cargar ficha técnica si existe
    try {
        const fichaTecnicaResponse = await fetch(`${API_URL}/api/stocks/${encodeURIComponent(stock.codigo)}/ficha-tecnica`, {
            credentials: 'include'
        });

        const fichaContainer = document.getElementById('detail-ficha-tecnica');

        if (fichaTecnicaResponse.ok) {
            const fichaTecnicaData = await fichaTecnicaResponse.json();
            if (fichaTecnicaData && fichaTecnicaData.ficha) {
                fichaContainer.style.display = 'block';
                fichaContainer.innerHTML = `
                    <div class="ficha-tecnica-block" style="border: 1px solid var(--border); border-radius: 8px; padding: 15px; margin-top: 15px;">
                        <div class="detail-label" style="margin-bottom: 12px;">${t('detail.technicalSheet')}:</div>
                        <a href="data:application/pdf;base64,${fichaTecnicaData.ficha}"
                           download="ficha_tecnica_${stock.codigo}.pdf"
                           class="btn-download-ficha"
                           style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: #FF5722; color: white; text-decoration: none; border-radius: 6px; font-size: 14px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            ${t('detail.downloadPdf')}
                        </a>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Error al cargar ficha técnica:', error);
    }
}

// Ampliar imagen en modal
function ampliarImagen(base64) {
    const modalImg = document.createElement('div');
    modalImg.className = 'imagen-modal-overlay';
    modalImg.innerHTML = `
        <div class="imagen-modal-content" onclick="event.stopPropagation()">
            <img src="data:image/jpeg;base64,${base64}" alt="Imagen ampliada">
            <button class="imagen-modal-close" onclick="this.parentElement.parentElement.remove()">✕</button>
        </div>
    `;
    modalImg.onclick = () => modalImg.remove();
    document.body.appendChild(modalImg);
}

function cerrarModal() {
    document.getElementById('detail-modal').style.display = 'none';
}

// Agregar al carrito desde el modal de detalle
function agregarAlCarritoDesdeDetalle() {
    if (window.stockActualDetalle) {
        window.agregandoDesdeDetalle = true;  // Flag para cerrar modal de detalle después
        agregarAlCarrito(window.stockActualDetalle);
    }
}

// ==================== CONSULTAS SOBRE PRODUCTOS ====================

// Abrir modal de consulta
function abrirModalConsulta() {
    const stock = window.stockActualDetalle;
    if (!stock) return;

    // Crear modal si no existe
    let modal = document.getElementById('inquiry-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'inquiry-modal';
        modal.className = 'modal-overlay';
        document.body.appendChild(modal);
    }

    // Pre-rellenar datos del usuario si está logueado
    const userName = currentUser?.full_name || '';
    const userEmail = currentUser?.email || '';

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header" style="background: linear-gradient(135deg, #2196F3 0%, #1565C0 100%); padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0; color: white; font-size: 1.3em;">${t('inquiry.title')}</h2>
                <button class="modal-close" onclick="cerrarModalConsulta()" style="background: none; border: none; color: white; font-size: 1.5em; cursor: pointer; position: absolute; right: 15px; top: 15px;">&times;</button>
            </div>
            <div style="padding: 20px;">
                <p style="color: #666; margin-bottom: 15px;">${t('inquiry.subtitle')}</p>

                <div style="background: #f5f5f5; padding: 12px; border-radius: 6px; margin-bottom: 20px;">
                    <strong>${stock.codigo}</strong> - ${stock.descripcion || ''}
                    <br><small style="color: #666;">${stock.formato || ''} | ${stock.calidad || ''} | ${stock.tono || ''} | ${stock.calibre || ''}</small>
                </div>

                <form id="inquiry-form" onsubmit="enviarConsulta(event)">
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">${t('inquiry.name')} *</label>
                        <input type="text" id="inquiry-name" value="${userName}" required
                               style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                    </div>

                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">${t('inquiry.email')} *</label>
                        <input type="email" id="inquiry-email" value="${userEmail}" required
                               style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                    </div>

                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">${t('inquiry.phone')}</label>
                        <input type="tel" id="inquiry-phone"
                               style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                    </div>

                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">${t('inquiry.message')} *</label>
                        <textarea id="inquiry-message" rows="4" required
                                  placeholder="${t('inquiry.messagePlaceholder')}"
                                  style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; resize: vertical;"></textarea>
                    </div>

                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button type="button" onclick="cerrarModalConsulta()"
                                style="padding: 12px 24px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer;">
                            ${t('common.cancel')}
                        </button>
                        <button type="submit" id="inquiry-submit-btn"
                                style="padding: 12px 24px; background: #2196F3; color: white; border: none; border-radius: 6px; cursor: pointer;">
                            ${t('inquiry.send')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}

// Cerrar modal de consulta
function cerrarModalConsulta() {
    const modal = document.getElementById('inquiry-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Enviar consulta
async function enviarConsulta(event) {
    event.preventDefault();

    const stock = window.stockActualDetalle;
    if (!stock) return;

    const nombre = document.getElementById('inquiry-name').value.trim();
    const email = document.getElementById('inquiry-email').value.trim();
    const telefono = document.getElementById('inquiry-phone').value.trim();
    const mensaje = document.getElementById('inquiry-message').value.trim();

    // Validar campos requeridos
    if (!nombre || !email || !mensaje) {
        alert(t('inquiry.requiredFields'));
        return;
    }

    // Validar email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert(t('inquiry.invalidEmail'));
        return;
    }

    const submitBtn = document.getElementById('inquiry-submit-btn');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = t('inquiry.sending');
    submitBtn.disabled = true;

    try {
        const empresaId = localStorage.getItem('empresa_id') || '1';
        const response = await fetchWithCsrf(`${API_URL}/api/consultas?empresa_id=${empresaId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                codigo_producto: stock.codigo,
                descripcion_producto: stock.descripcion,
                formato: stock.formato,
                calidad: stock.calidad,
                color: stock.color,
                tono: stock.tono,
                calibre: stock.calibre,
                nombre_cliente: nombre,
                email_cliente: email,
                telefono_cliente: telefono,
                mensaje: mensaje
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(t('inquiry.success'));
            cerrarModalConsulta();
            cerrarModal();  // Cerrar también el modal de detalle
        } else {
            alert(t('inquiry.error') + ': ' + (data.error || ''));
        }
    } catch (error) {
        console.error('Error al enviar consulta:', error);
        alert(t('inquiry.error'));
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

// Abrir WhatsApp con mensaje pre-rellenado
function abrirWhatsApp() {
    const stock = window.stockActualDetalle;
    if (!stock || !whatsappConfig.numero) return;

    // Construir mensaje con los datos del producto
    const mensaje = t('inquiry.whatsappMessage', {
        code: stock.codigo,
        description: stock.descripcion || '-',
        format: stock.formato || '-',
        quality: stock.calidad || '-',
        tone: stock.tono || '-',
        caliber: stock.calibre || '-'
    });

    // Codificar mensaje para URL
    const mensajeCodificado = encodeURIComponent(mensaje);

    // Abrir WhatsApp (web o app según dispositivo)
    const url = `https://wa.me/${whatsappConfig.numero}?text=${mensajeCodificado}`;
    window.open(url, '_blank');
}

// Exponer funciones de consulta en window para acceso desde HTML dinámico
window.abrirModalConsulta = abrirModalConsulta;
window.cerrarModalConsulta = cerrarModalConsulta;
window.enviarConsulta = enviarConsulta;
window.abrirWhatsApp = abrirWhatsApp;

// ==================== UTILIDADES ====================

// Badge con unidad incluida y formato de miles
function getBadgeWithUnit(existencias, unidad) {
    const num = parseFloat(existencias);
    let badgeClass = 'badge-success';

    if (num < 100) badgeClass = 'badge-danger';
    else if (num < 500) badgeClass = 'badge-warning';

    const unidadText = unidad ? ` ${unidad}` : '';
    // Formatear con separador de miles
    const numFormatted = num.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    return `<span class="badge ${badgeClass}">${numFormatted}${unidadText}</span>`;
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
}

function mostrarCargando() {
    document.getElementById('table-container').innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>${t('common.loadingData')}</p>
        </div>
    `;
}

function mostrarError(mensaje) {
    document.getElementById('table-container').innerHTML = `
        <div class="error-message">
            <strong>⚠️ Error:</strong> ${mensaje}
        </div>
    `;
}

// ==================== FUNCIONES DEL CARRITO ====================

// Cargar carrito desde el servidor
async function cargarCarrito() {
    try {
        const response = await fetch(`${API_URL}/api/carrito`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            carrito = await response.json();
            actualizarContadorCarrito();
        }
    } catch (error) {
        console.error('Error al cargar carrito:', error);
    }
}

// Función helper para obtener cantidad de decimales de un número
function getDecimalPlaces(num) {
    if (!num || num === 0) return 0;
    const numStr = num.toString();
    if (numStr.indexOf('.') === -1) return 0;
    return numStr.split('.')[1].length;
}

// Función helper para formatear números con la precisión adecuada
function formatearCantidadEmpaquetado(cantidad) {
    if (!cantidad || cantidad === 0) return '0';

    // Detectar decimales del número
    const decimales = getDecimalPlaces(cantidad);

    // Formatear con los decimales detectados
    return parseFloat(cantidad).toLocaleString('en-US', {
        minimumFractionDigits: decimales,
        maximumFractionDigits: decimales
    });
}

// Función helper para redondear números a un número específico de decimales
function redondearADecimales(numero, decimales) {
    if (decimales === 0) {
        return Math.round(numero);
    }
    const factor = Math.pow(10, decimales);
    return Math.round(numero * factor) / factor;
}

// Modal para pedir cantidad con botones + y -
function mostrarModalCantidad(stock) {
    const existenciasFormatted = parseFloat(stock.existencias).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    // Formatear cantidades de empaquetado con precisión correcta
    const decimalesEmpaquetado = getDecimalPlaces(stock.unidadescaja || 0);
    const unidadesCajaFormatted = stock.unidadescaja ? formatearCantidadEmpaquetado(stock.unidadescaja) : '0';

    // Calcular y redondear unidades por pallet para evitar errores de punto flotante
    let unidadesPallet = 0;
    if (stock.cajaspallet && stock.unidadescaja) {
        unidadesPallet = stock.cajaspallet * stock.unidadescaja;
        unidadesPallet = redondearADecimales(unidadesPallet, decimalesEmpaquetado);
    }
    const unidadesPalletFormatted = unidadesPallet > 0 ? formatearCantidadEmpaquetado(unidadesPallet) : '0';

    // Crear modal
    const modalHTML = `
        <div class="quantity-modal-overlay" id="quantity-modal-overlay">
            <div class="quantity-modal">
                <div class="quantity-modal-header">
                    <h3>${t('cart.addToCart')}</h3>
                    <button class="quantity-modal-close" onclick="cerrarModalCantidad()">✕</button>
                </div>

                <div class="quantity-modal-body">
                    <div class="quantity-product-info">
                        <div class="quantity-product-title">${stock.descripcion}</div>
                        <div class="quantity-product-details">
                            <span class="quantity-detail-item"><strong>${t('table.code')}:</strong> ${stock.codigo}</span>
                            ${stock.formato ? `<span class="quantity-detail-item"><strong>${t('table.format')}:</strong> ${stock.formato}</span>` : ''}
                            ${stock.calidad ? `<span class="quantity-detail-item"><strong>${t('table.quality')}:</strong> ${stock.calidad}</span>` : ''}
                            ${stock.tono ? `<span class="quantity-detail-item"><strong>${t('table.tone')}:</strong> ${stock.tono}</span>` : ''}
                            ${stock.calibre ? `<span class="quantity-detail-item"><strong>${t('table.caliber')}:</strong> ${stock.calibre}</span>` : ''}
                        </div>
                        <div class="quantity-stock-info">
                            <span class="quantity-stock-label">${t('table.stock')}:</span>
                            <span class="quantity-stock-value">${existenciasFormatted} ${stock.unidad || ''}</span>
                        </div>
                    </div>

                    <div class="quantity-input-section">
                        <label class="quantity-label">${t('cart.quantity')}:</label>
                        <div class="quantity-control">
                            <button class="quantity-btn quantity-btn-minus" onclick="cambiarCantidad(-1)">−</button>
                            <input type="number"
                                   id="quantity-input"
                                   class="quantity-input"
                                   value="0"
                                   min="0"
                                   max="${stock.existencias}"
                                   step="1">
                            <button class="quantity-btn quantity-btn-plus" onclick="cambiarCantidad(1)">+</button>
                        </div>
                        <div class="quantity-quick-buttons">
                            ${stock.unidadescaja && stock.unidadescaja > 0 ? `
                                <div class="quantity-package-group">
                                    <span class="quantity-package-label">${t('cart.box')}: ${unidadesCajaFormatted} ${stock.unidad || ''}</span>
                                    <div class="quantity-package-controls">
                                        <button class="quantity-package-btn" onclick="cambiarCantidadPorUnidad(-${stock.unidadescaja})" title="Restar 1 caja">
                                            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                                <path d="M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                            </svg>
                                        </button>
                                        <button class="quantity-package-btn quantity-package-btn-primary" onclick="cambiarCantidadPorUnidad(${stock.unidadescaja})" title="Agregar 1 caja">
                                            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                                <path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            ` : ''}
                            ${unidadesPallet > 0 ? `
                                <div class="quantity-package-group">
                                    <span class="quantity-package-label">${t('cart.pallet')}: ${unidadesPalletFormatted} ${stock.unidad || ''}</span>
                                    <div class="quantity-package-controls">
                                        <button class="quantity-package-btn" onclick="cambiarCantidadPorUnidad(-${unidadesPallet})" title="Restar 1 pallet">
                                            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                                <path d="M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                            </svg>
                                        </button>
                                        <button class="quantity-package-btn quantity-package-btn-primary" onclick="cambiarCantidadPorUnidad(${unidadesPallet})" title="Agregar 1 pallet">
                                            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                                <path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>

                <div class="quantity-modal-footer">
                    <button class="quantity-btn-cancel" onclick="cerrarModalCantidad()">${t('common.cancel')}</button>
                    <button class="quantity-btn-confirm" onclick="confirmarAgregarAlCarrito()">${t('cart.addToCart')}</button>
                </div>
            </div>
        </div>
    `;

    // Guardar stock actual en variable global temporal con información de decimales
    window.stockTemporal = stock;
    window.stockTemporal.decimalesEmpaquetado = getDecimalPlaces(stock.unidadescaja || 0);

    // Agregar modal al DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Focus en el input
    setTimeout(() => {
        document.getElementById('quantity-input').select();
    }, 100);
}

// Cambiar cantidad con botones + y -
function cambiarCantidad(delta) {
    const input = document.getElementById('quantity-input');
    const maxStock = parseFloat(input.max);
    let currentValue = parseFloat(input.value) || 0;

    currentValue += delta;

    // Obtener decimales de precisión desde el stock temporal
    const decimalesPrecision = window.stockTemporal?.decimalesEmpaquetado || 0;

    // Redondear para evitar errores de punto flotante
    currentValue = redondearADecimales(currentValue, decimalesPrecision);

    // Validar límites
    if (currentValue < 0) currentValue = 0;
    if (currentValue > maxStock) currentValue = maxStock;

    input.value = currentValue;
    input.focus();
}

// Cambiar cantidad por unidades de empaquetado (caja/pallet)
function cambiarCantidadPorUnidad(unidades) {
    const input = document.getElementById('quantity-input');
    const maxStock = parseFloat(input.max);
    let currentValue = parseFloat(input.value) || 0;

    // Calcular nueva cantidad
    let newValue = currentValue + unidades;

    // Obtener decimales de precisión desde el stock temporal
    const decimalesPrecision = window.stockTemporal?.decimalesEmpaquetado || 0;

    // Redondear al número correcto de decimales para evitar errores de punto flotante
    newValue = redondearADecimales(newValue, decimalesPrecision);

    // Validar límites
    if (newValue < 0) {
        newValue = 0;
    }

    if (newValue > maxStock) {
        // Si excede el stock, mostrar alerta y establecer el máximo
        const unidadNombre = unidades > 0 ?
            (unidades > 100 ? t('cart.pallet') : t('cart.box')) :
            (Math.abs(unidades) > 100 ? t('cart.pallet') : t('cart.box'));

        alert(t('cart.exceedsStock', {
            requested: newValue,
            available: maxStock
        }));
        newValue = maxStock;
    }

    input.value = newValue;
    input.focus();
}

// Establecer cantidad directa (para botones rápidos)
function setCantidad(cantidad) {
    const input = document.getElementById('quantity-input');
    const maxStock = parseFloat(input.max);

    if (cantidad > maxStock) {
        alert(t('cart.exceedsStock', { requested: cantidad, available: maxStock }));
        input.value = maxStock;
    } else {
        input.value = cantidad;
    }
    input.focus();
}

// Cerrar modal de cantidad
function cerrarModalCantidad() {
    const modal = document.getElementById('quantity-modal-overlay');
    if (modal) {
        modal.remove();
    }
    window.stockTemporal = null;
    window.agregandoDesdeDetalle = false;  // Reset flag al cancelar
}

// Confirmar y agregar al carrito
async function confirmarAgregarAlCarrito() {
    const input = document.getElementById('quantity-input');
    const cantidadNum = parseFloat(input.value);
    const stock = window.stockTemporal;

    if (!stock) {
        alert('Error: No hay producto seleccionado');
        return;
    }

    if (isNaN(cantidadNum) || cantidadNum <= 0) {
        alert(t('cart.invalidQuantity'));
        input.focus();
        return;
    }

    if (cantidadNum > stock.existencias) {
        alert(t('cart.exceedsStock', { requested: cantidadNum, available: stock.existencias }));
        input.focus();
        return;
    }

    // Guardar flag antes de cerrar modal (cerrarModalCantidad lo resetea)
    const desdeDetalle = window.agregandoDesdeDetalle;

    // Cerrar modal
    cerrarModalCantidad();

    // Agregar al carrito
    try {
        const response = await fetchWithCsrf(`${API_URL}/api/carrito/add`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                codigo: stock.codigo,
                descripcion: stock.descripcion,
                formato: stock.formato,
                calidad: stock.calidad,
                color: stock.color,
                tono: stock.tono,
                calibre: stock.calibre,
                pallet: stock.pallet,
                caja: stock.caja,
                existencias: stock.existencias,
                unidad: stock.unidad,
                cantidad_solicitada: cantidadNum
            })
        });

        if (response.ok) {
            const data = await response.json();
            carrito = data.carrito;
            actualizarContadorCarrito();

            // Si se agregó desde el modal de detalle, cerrarlo
            if (desdeDetalle) {
                cerrarModal();
            }

            alert(t('cart.addedSuccess', { quantity: cantidadNum, unit: stock.unidad || '' }));
        } else {
            alert(t('cart.addError'));
        }
    } catch (error) {
        console.error('Error al agregar al carrito:', error);
        alert(t('cart.addError'));
    }
}

// Agregar producto al carrito (versión con modal moderno)
async function agregarAlCarrito(stock) {
    mostrarModalCantidad(stock);
}

// Actualizar contador del carrito
function actualizarContadorCarrito() {
    const badge = document.getElementById('carrito-badge');
    if (badge) {
        badge.textContent = carrito.length;
        badge.style.display = carrito.length > 0 ? 'inline-block' : 'none';
    }
}

// Ver carrito
function verCarrito() {
    if (carrito.length === 0) {
        alert(t('cart.empty'));
        return;
    }

    const modal = document.getElementById('carrito-modal');
    const content = document.getElementById('carrito-content');

    let html = '<div class="carrito-items">';

    carrito.forEach((item, index) => {
        // Formatear existencias y cantidad con separador de miles
        const existenciasFormatted = parseFloat(item.existencias).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        const cantidadFormatted = parseFloat(item.cantidad_solicitada).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        html += `
            <div class="carrito-item">
                <div class="carrito-item-info">
                    <strong>${item.codigo}</strong> - ${item.descripcion}<br>
                    <small>${t('cart.format')}: ${item.formato || '-'} | ${t('cart.quality')}: ${item.calidad || '-'} | ${t('cart.tone')}: ${item.tono || '-'} | ${t('cart.caliber')}: ${item.calibre || '-'}</small><br>
                    <small>${t('cart.pallet')}: ${item.pallet || '-'} | ${t('cart.box')}: ${item.caja || '-'}</small><br>
                    <small>${t('cart.availableStock')}: ${existenciasFormatted} ${item.unidad || ''}</small>
                </div>
                <div class="carrito-item-cantidad">
                    <strong>${t('cart.requested')}:</strong>
                    <div class="cantidad-value">${cantidadFormatted} ${item.unidad || ''}</div>
                </div>
                <div class="carrito-item-actions">
                    <button class="btn-danger" onclick="eliminarDelCarrito(${index})">${t('cart.remove')}</button>
                </div>
            </div>
        `;
    });

    html += '</div>';
    html += `
        <div class="carrito-footer">
            <button class="btn-danger" onclick="vaciarCarrito()">${t('cart.clearCart')}</button>
            <button class="btn-primary" onclick="mostrarFormularioEnvio()">${t('cart.sendRequest')}</button>
        </div>
    `;

    content.innerHTML = html;
    modal.style.display = 'flex';
}

// Eliminar del carrito por índice
async function eliminarDelCarrito(index) {
    if (!confirm(t('cart.confirmRemove'))) return;

    try {
        const response = await fetchWithCsrf(`${API_URL}/api/carrito/remove/${index}`, {
            method: 'DELETE',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            carrito = data.carrito;
            actualizarContadorCarrito();

            if (carrito.length === 0) {
                cerrarCarrito();
                alert(t('cart.emptyNow'));
            } else {
                verCarrito();
            }
        } else {
            alert(t('cart.removeError'));
        }
    } catch (error) {
        console.error('Error al eliminar del carrito:', error);
        alert(t('cart.removeError'));
    }
}

// Vaciar carrito
async function vaciarCarrito() {
    if (!confirm(t('cart.confirmClear'))) return;

    try {
        const response = await fetchWithCsrf(`${API_URL}/api/carrito/clear`, {
            method: 'DELETE',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            carrito = [];
            actualizarContadorCarrito();
            cerrarCarrito();
            alert(t('cart.cleared'));
        }
    } catch (error) {
        console.error('Error al vaciar carrito:', error);
    }
}

// Mostrar formulario de envío
function mostrarFormularioEnvio() {
    const content = document.getElementById('carrito-content');

    // Pre-llenar cliente si el usuario tiene uno asignado
    const clientePreseleccionado = currentUser?.cliente_id || '';
    const clienteNombrePreseleccionado = currentUser?.cliente_razon || '';

    content.innerHTML = `
        <div class="envio-form">
            <h3>${t('shipping.title')}</h3>
            <p>${t('shipping.description')}</p>
            <div class="form-group">
                <label>${t('shipping.clientLabel') || 'Cliente'}: <span class="required">*</span></label>
                <div class="client-search-container">
                    <div class="client-search-input-wrapper" id="client-search-wrapper-envio" style="${clientePreseleccionado ? 'display:none' : ''}">
                        <input type="text" id="client-search-envio" placeholder="${t('shipping.clientPlaceholder') || 'Buscar cliente...'}" autocomplete="off">
                        <span class="client-search-icon">🔍</span>
                    </div>
                    <div class="client-suggestions" id="client-suggestions-envio"></div>
                    <div class="client-selected" id="client-selected-envio" style="${clientePreseleccionado ? '' : 'display:none'}">
                        <div class="client-selected-info">
                            <span class="client-selected-code" id="selected-client-code-envio">${clientePreseleccionado}</span>
                            <span class="client-selected-name" id="selected-client-name-envio">${clienteNombrePreseleccionado}</span>
                        </div>
                        <button type="button" class="client-clear-btn" onclick="clearClientSelectionEnvio()" title="${t('common.clear') || 'Limpiar'}">×</button>
                    </div>
                </div>
                <input type="hidden" id="cliente-id-envio" value="${clientePreseleccionado}">
                <p class="form-help">${t('shipping.clientHelp') || 'Escribe al menos 3 caracteres para buscar'}</p>
            </div>
            <div class="form-group">
                <label>${t('shipping.referenceLabel')}:</label>
                <input type="text" id="referencia-envio" maxlength="100" placeholder="${t('shipping.referencePlaceholder')}">
            </div>
            <div class="form-group">
                <label>${t('shipping.commentsLabel')}:</label>
                <textarea id="comentarios-envio" rows="4" placeholder="${t('shipping.commentsPlaceholder')}"></textarea>
            </div>
            <div class="form-group checkbox-group">
                <label class="checkbox-label">
                    <input type="checkbox" id="enviar-copia" checked>
                    <span>${t('shipping.sendCopy')}</span>
                </label>
            </div>
            <div class="carrito-footer">
                <button class="btn-secondary" onclick="verCarrito()">${t('shipping.back')}</button>
                <button class="btn-primary" onclick="enviarSolicitud()">${t('shipping.send')}</button>
            </div>
        </div>
    `;

    // Inicializar autocomplete del cliente
    initClientAutocompleteEnvio();
}

// Enviar solicitud
async function enviarSolicitud() {
    const referencia = document.getElementById('referencia-envio').value;
    const comentarios = document.getElementById('comentarios-envio').value;
    const enviarCopia = document.getElementById('enviar-copia').checked;
    const cliente_id = document.getElementById('cliente-id-envio').value;
    const empresa_id = getEmpresaId(); // Multi-empresa support

    // Validar cliente obligatorio
    if (!cliente_id) {
        alert(t('shipping.clientRequired') || 'Debe seleccionar un cliente');
        return;
    }

    if (!confirm(t('shipping.confirmSend'))) return;

    // Mostrar indicador de envio
    mostrarEnviando(true);

    try {
        const response = await fetchWithCsrf(`${API_URL}/api/carrito/enviar`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ referencia, comentarios, empresa_id, enviar_copia: enviarCopia, cliente_id })
        });

        // Ocultar indicador de envio
        mostrarEnviando(false);

        if (response.ok) {
            alert(t('shipping.success'));
            carrito = [];
            actualizarContadorCarrito();
            cerrarCarrito();
        } else {
            const error = await response.json();
            alert(t('shipping.error', { error: error.error }));
        }
    } catch (error) {
        // Ocultar indicador de envio en caso de error
        mostrarEnviando(false);
        console.error('Error al enviar solicitud:', error);
        alert(t('shipping.sendError'));
    }
}

// Mostrar/ocultar indicador de envio
function mostrarEnviando(mostrar) {
    let overlay = document.getElementById('enviando-overlay');

    if (mostrar) {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'enviando-overlay';
            overlay.innerHTML = `
                <div class="enviando-content">
                    <div class="enviando-spinner"></div>
                    <p>${t('shipping.sending') || 'Enviando solicitud...'}</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    } else {
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
}

// Cerrar carrito
function cerrarCarrito() {
    document.getElementById('carrito-modal').style.display = 'none';
}

// ==================== AUTOCOMPLETE CLIENTE ENVIO ====================

let clientSearchTimeoutEnvio = null;

function initClientAutocompleteEnvio() {
    const searchInput = document.getElementById('client-search-envio');
    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        const query = this.value.trim();

        // Cancelar búsqueda anterior
        if (clientSearchTimeoutEnvio) {
            clearTimeout(clientSearchTimeoutEnvio);
        }

        // Mínimo 3 caracteres
        if (query.length < 3) {
            const suggestions = document.getElementById('client-suggestions-envio');
            suggestions.innerHTML = '';
            suggestions.classList.remove('show');
            return;
        }

        // Debounce de 300ms
        clientSearchTimeoutEnvio = setTimeout(() => {
            searchClientsEnvio(query);
        }, 300);
    });

    // Cerrar sugerencias al hacer clic fuera
    document.addEventListener('click', function (e) {
        const container = document.querySelector('.client-search-container');
        if (container && !container.contains(e.target)) {
            const suggestions = document.getElementById('client-suggestions-envio');
            if (suggestions) suggestions.classList.remove('show');
        }
    });
}

async function searchClientsEnvio(query) {
    const suggestionsContainer = document.getElementById('client-suggestions-envio');
    const empresaId = getEmpresaId();

    // Mostrar loading
    suggestionsContainer.innerHTML = `<div class="client-suggestions-loading">${t('common.searching') || 'Buscando...'}</div>`;
    suggestionsContainer.classList.add('show');

    try {
        const response = await fetch(`${API_URL}/api/clientes/search?empresa=${empresaId}&razon=${encodeURIComponent(query)}`, {
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Error al buscar clientes');

        const clientes = await response.json();

        if (clientes.length === 0) {
            suggestionsContainer.innerHTML = `<div class="client-suggestions-empty">${t('common.noResults') || 'No se encontraron resultados'}</div>`;
        } else {
            suggestionsContainer.innerHTML = clientes.map(c => `
                <div class="client-suggestion" onclick="selectClientEnvio('${c.codigo}', '${c.razon.replace(/'/g, "\\'")}')">
                    <span class="client-suggestion-code">${c.codigo}</span>
                    <span class="client-suggestion-name">${c.razon}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error buscando clientes:', error);
        suggestionsContainer.innerHTML = `<div class="client-suggestions-empty">${t('errors.searchError') || 'Error al buscar'}</div>`;
    }
}

function selectClientEnvio(codigo, razon) {
    // Guardar en input hidden
    document.getElementById('cliente-id-envio').value = codigo;

    // Mostrar tarjeta de cliente seleccionado
    document.getElementById('selected-client-code-envio').textContent = codigo;
    document.getElementById('selected-client-name-envio').textContent = razon;
    document.getElementById('client-selected-envio').classList.add('show');
    document.getElementById('client-selected-envio').style.display = 'flex';

    // Ocultar input de búsqueda y sugerencias
    document.getElementById('client-search-wrapper-envio').style.display = 'none';
    document.getElementById('client-suggestions-envio').classList.remove('show');
    document.getElementById('client-search-envio').value = '';
}

function clearClientSelectionEnvio() {
    // Limpiar input hidden
    document.getElementById('cliente-id-envio').value = '';

    // Ocultar tarjeta de selección
    document.getElementById('client-selected-envio').classList.remove('show');
    document.getElementById('client-selected-envio').style.display = 'none';

    // Mostrar input de búsqueda
    document.getElementById('client-search-wrapper-envio').style.display = 'flex';
    document.getElementById('client-search-envio').focus();
}

// Exponer funciones para onclick en HTML dinámico
window.selectClientEnvio = selectClientEnvio;
window.clearClientSelectionEnvio = clearClientSelectionEnvio;

// Funciones de filtros y ordenación
window.agregarFiltro = agregarFiltro;
window.quitarFiltro = quitarFiltro;
window.limpiarTodosFiltros = limpiarTodosFiltrosColumna;  // Alias para compatibilidad
window.ordenarPorColumna = ordenarPorColumna;

// Funciones de filtros por columna estilo WorkWithPlus
window.mostrarPopupFiltro = mostrarPopupFiltro;
window.cerrarPopupFiltro = cerrarPopupFiltro;
window.aplicarFiltroColumna = aplicarFiltroColumna;
window.limpiarFiltroColumna = limpiarFiltroColumna;
window.quitarFiltroColumna = quitarFiltroColumna;
window.limpiarTodosFiltrosColumna = limpiarTodosFiltrosColumna;

// ==================== EVENT LISTENERS ====================

// Cerrar modal al hacer clic fuera
window.onclick = function (event) {
    const modal = document.getElementById('detail-modal');
    const carritoModal = document.getElementById('carrito-modal');
    if (event.target === modal) {
        cerrarModal();
    }
    if (event.target === carritoModal) {
        cerrarCarrito();
    }
}

// Cargar datos al iniciar
window.onload = async function () {
    console.log('🚀 Iniciando aplicación...');

    // Cargar logo y favicon de la empresa (usa connection de localStorage si existe)
    await cargarLogoEmpresa();

    // Inicializar sistema de idiomas
    await I18n.init();

    const isAuth = await checkAuth();
    if (isAuth) {
        console.log('✅ Autenticado, cargando datos...');

        // Cargar CSRF token (primero de localStorage, luego del servidor)
        csrfToken = localStorage.getItem('csrf_token');
        await obtenerCsrfToken();

        await verificarPropuestasHabilitadas();
        await verificarGridConImagenes();
        await cargarConfigPaginacion();
        await cargarConfigWhatsApp();
        await cargarOpcionesFiltros();
        await cargarTodos();
        // Solo cargar carrito si las propuestas están habilitadas
        if (propuestasHabilitadas) {
            await cargarCarrito();
        }
    } else {
        console.log('❌ No autenticado');
    }
};

// Buscar al presionar Enter en los filtros
document.addEventListener('DOMContentLoaded', function () {
    const inputs = document.querySelectorAll('.filters input');
    inputs.forEach(input => {
        input.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                buscarStocks();
            }
        });
    });

    // Cerrar modal de detalle al hacer clic fuera del contenido
    const detailModal = document.getElementById('detail-modal');
    if (detailModal) {
        detailModal.addEventListener('click', function (e) {
            if (e.target === this) {
                cerrarModal();
            }
        });
    }

    // Cerrar modal de detalle con tecla Escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            const detailModal = document.getElementById('detail-modal');
            if (detailModal && detailModal.style.display === 'flex') {
                cerrarModal();
            }
        }
    });
});

// Re-renderizar tabla cuando cambie el idioma
document.addEventListener('languageChanged', function () {
    if (stocksData && stocksData.length > 0) {
        mostrarTabla(stocksData);
    }
});