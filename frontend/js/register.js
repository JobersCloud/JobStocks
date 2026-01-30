// register.js
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

// Capturar connection de la URL (y empresa para compatibilidad)
function getConnectionFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    // Aceptar tanto 'connection' como 'empresa' para compatibilidad
    const connection = urlParams.get('connection') || urlParams.get('empresa');

    if (connection) {
        localStorage.setItem('connection', connection);
        return connection;
    } else {
        return localStorage.getItem('connection') || localStorage.getItem('empresa_id') || '1';
    }
}

// ==================== MODO OSCURO ====================

// Cargar tema guardado
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
}

// Aplicar tema oscuro/claro
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // Actualizar switch y icono
    const themeSwitch = document.getElementById('theme-switch');
    const themeIcon = document.getElementById('theme-icon');

    if (themeSwitch) {
        themeSwitch.checked = theme === 'dark';
    }
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Alternar tema
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

// Exponer función globalmente
window.toggleTheme = toggleTheme;

// ==================== TEMA DE COLOR ====================

// Aplicar tema de color
function applyColorTheme(tema) {
    const themes = {
        'rubi': { primary: '#FF4338', primaryDark: '#D32F2F', primaryLight: '#FF6B6B' },
        'zafiro': { primary: '#2196F3', primaryDark: '#1565C0', primaryLight: '#64B5F6' },
        'esmeralda': { primary: '#4CAF50', primaryDark: '#2E7D32', primaryLight: '#81C784' },
        'amatista': { primary: '#9C27B0', primaryDark: '#6A1B9A', primaryLight: '#BA68C8' },
        'ambar': { primary: '#FF9800', primaryDark: '#E65100', primaryLight: '#FFB74D' },
        'grafito': { primary: '#607D8B', primaryDark: '#37474F', primaryLight: '#90A4AE' },
        'corporativo': { primary: '#1a365d', primaryDark: '#0d1b2a', primaryLight: '#2c5282' },
        'ejecutivo': { primary: '#2d3748', primaryDark: '#1a202c', primaryLight: '#4a5568' },
        'oceano': { primary: '#0077b6', primaryDark: '#023e8a', primaryLight: '#0096c7' },
        'bosque': { primary: '#2d6a4f', primaryDark: '#1b4332', primaryLight: '#40916c' },
        'vino': { primary: '#722f37', primaryDark: '#4a1c23', primaryLight: '#a4343a' },
        'medianoche': { primary: '#1e3a5f', primaryDark: '#0d1b2a', primaryLight: '#2e5077' },
        'titanio': { primary: '#4a5568', primaryDark: '#2d3748', primaryLight: '#718096' },
        'bronce': { primary: '#8b5a2b', primaryDark: '#5c3d1e', primaryLight: '#a0522d' }
    };
    if (!themes[tema]) tema = 'rubi';
    const colors = themes[tema];
    document.documentElement.setAttribute('data-color-theme', tema);
    localStorage.setItem('colorTheme', tema);
    document.documentElement.style.setProperty('--primary', colors.primary, 'important');
    document.documentElement.style.setProperty('--primary-dark', colors.primaryDark, 'important');
    document.documentElement.style.setProperty('--primary-light', colors.primaryLight, 'important');
}

// Cargar tema de color desde la API
async function cargarTemaColor(empresaId) {
    try {
        const response = await fetch(`${API_URL}/api/empresa/${empresaId}/config`);
        const config = await response.json();
        applyColorTheme(config.tema || 'rubi');
    } catch (error) {
        console.log('Error cargando tema:', error);
        applyColorTheme('rubi');
    }
}

// Cargar logo de la empresa desde la BD
async function cargarLogoEmpresa(empresaId) {
    try {
        const response = await fetch(`${API_URL}/api/empresa/${empresaId}/logo/exists`);
        const data = await response.json();

        if (data.exists) {
            const logoUrl = `${API_URL}/api/empresa/${empresaId}/logo`;
            // Guardar en localStorage para evitar flash en próximas visitas
            localStorage.setItem('logoUrl', logoUrl);

            const sidebarLogo = document.getElementById('sidebar-logo');
            const mobileLogo = document.getElementById('mobile-logo');

            if (sidebarLogo) sidebarLogo.src = logoUrl;
            if (mobileLogo) mobileLogo.src = logoUrl;
        } else {
            // Si no existe logo en BD, limpiar localStorage
            localStorage.removeItem('logoUrl');
        }
    } catch (error) {
        console.log('Error cargando logo:', error);
    }
}

// Inicializar después de que i18n esté listo
async function initRegister() {
    // Cargar tema oscuro/claro inmediatamente
    loadTheme();

    // Capturar connection de la URL
    const connection = getConnectionFromURL();
    console.log(`Registro con connection: ${connection}`);

    // Cargar tema de color y logo de la empresa (usan connection para la API)
    await cargarTemaColor(connection);
    await cargarLogoEmpresa(connection);

    await I18n.init();
    verificarRegistroHabilitado();
    cargarPaises();
    setupRegisterForm();
}

// Cargar países al iniciar
async function cargarPaises() {
    try {
        const response = await fetch(`${API_URL}/api/paises`);
        const paises = await response.json();

        const select = document.getElementById('pais');
        paises.forEach(pais => {
            const option = document.createElement('option');
            option.value = pais.alfa2;
            option.textContent = pais.nombre;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error al cargar países:', error);
    }
}

// Verificar si el registro está habilitado
async function verificarRegistroHabilitado() {
    try {
        const empresaId = localStorage.getItem('empresa_id') || '1';
        const response = await fetch(`${API_URL}/api/registro-habilitado?empresa_id=${empresaId}`);
        const data = await response.json();

        if (!data.habilitado) {
            showAlert(t('auth.registrationDisabled'), 'error');
            document.getElementById('register-form').style.display = 'none';
        }
    } catch (error) {
        console.error('Error al verificar registro:', error);
    }
}

// Mostrar alerta
function showAlert(message, type) {
    const container = document.getElementById('alert-container');
    const icon = type === 'error' ? '⚠️' : '✅';
    container.innerHTML = `
        <div class="alert alert-${type}">
            <span>${icon}</span>
            <span>${message}</span>
        </div>
    `;
}

// Configurar formulario de registro
function setupRegisterForm() {
    document.getElementById('register-form').addEventListener('submit', async function(e) {
        e.preventDefault();

        const btn = document.getElementById('btn-register');
        const originalText = btn.innerHTML;

        // Obtener datos del formulario
        const empresaId = localStorage.getItem('empresa_id') || '1';
        const connection = localStorage.getItem('connection') || localStorage.getItem('empresa_id') || '1';
        const formData = {
            full_name: document.getElementById('full_name').value.trim(),
            username: document.getElementById('username').value.trim(),
            email: document.getElementById('email').value.trim(),
            pais: document.getElementById('pais').value,
            password: document.getElementById('password').value,
            empresa_id: empresaId,
            connection: connection
        };

        const passwordConfirm = document.getElementById('password_confirm').value;

        // Validar contraseñas
        if (formData.password !== passwordConfirm) {
            showAlert(t('auth.passwordMismatch'), 'error');
            return;
        }

        // Validar longitud de contraseña
        if (formData.password.length < 6) {
            showAlert(t('auth.passwordMinLength'), 'error');
            return;
        }

        // Deshabilitar botón
        btn.disabled = true;
        btn.innerHTML = `<span class="loading-spinner"></span>${t('auth.registering')}`;

        try {
            const response = await fetch(`${API_URL}/api/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert(data.message, 'success');
                document.getElementById('register-form').reset();

                // Redirigir al login después de 3 segundos (manteniendo empresa_id)
                setTimeout(() => {
                    const empresaId = localStorage.getItem('empresa_id') || '1';
                    window.location.href = `/login.html?empresa=${empresaId}`;
                }, 3000);
            } else {
                showAlert(data.message || t('auth.registerError'), 'error');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert(t('auth.registerConnectionError'), 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    });
}

// Inicializar al cargar la página
initRegister();
