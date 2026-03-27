// login.js
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

let loginForm, btnLogin, alertContainer;

// Capturar connection de la URL, localStorage o API por defecto
// connection = ID para buscar en BD central (ej: 10049)
// empresa_id = empresa_erp para filtros (ej: '1') - se obtiene después del login
async function getConnectionFromURL() {
    const urlParams = new URLSearchParams(window.location.search);

    // Si viene 'empresa' en lugar de 'connection', mostrar error
    const empresaParam = urlParams.get('empresa');
    if (empresaParam && !urlParams.get('connection')) {
        return 'INVALID_PARAM'; // Parámetro incorrecto
    }

    const connection = urlParams.get('connection');

    if (connection) {
        // Guardar connection en localStorage (ID para conexión BD)
        localStorage.setItem('connection', connection);
        console.log(`Connection seleccionada: ${connection}`);
        return connection;
    } else {
        // Si no viene en URL, verificar si hay una guardada
        const connectionGuardada = localStorage.getItem('connection');
        if (connectionGuardada) {
            console.log(`Usando connection guardada: ${connectionGuardada}`);
            return connectionGuardada;
        } else {
            // No hay en URL ni localStorage, obtener del servidor (configuración por defecto)
            try {
                const response = await fetch(`${API_URL}/api/default-connection`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.connection) {
                        localStorage.setItem('connection', data.connection);
                        console.log(`Usando connection por defecto del servidor: ${data.connection}`);
                        return data.connection;
                    }
                }
            } catch (error) {
                console.error('Error obteniendo connection por defecto:', error);
            }
            // ERROR: No hay connection disponible
            return null;
        }
    }
}

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
        'bronce': { primary: '#8b5a2b', primaryDark: '#5c3d1e', primaryLight: '#a0522d' },
        'elegante': { primary: '#FF4438', primaryDark: '#1a1a1a', primaryLight: '#FF6B5B' }
    };
    if (!themes[tema]) tema = 'rubi';
    const colors = themes[tema];
    document.documentElement.setAttribute('data-color-theme', tema);
    localStorage.setItem('colorTheme', tema);
    document.documentElement.style.setProperty('--primary', colors.primary, 'important');
    document.documentElement.style.setProperty('--primary-dark', colors.primaryDark, 'important');
    document.documentElement.style.setProperty('--primary-light', colors.primaryLight, 'important');
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

    const isDark = theme === 'dark';
    const iconText = isDark ? '☀️' : '🌙';

    // Actualizar switches e iconos (desktop + mobile)
    ['', '-mobile'].forEach(suffix => {
        const sw = document.getElementById('theme-switch' + suffix);
        const ic = document.getElementById('theme-icon' + suffix);
        if (sw) sw.checked = isDark;
        if (ic) ic.textContent = iconText;
    });
}

// Alternar tema
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

// Exponer función globalmente
window.toggleTheme = toggleTheme;

// Cargar tema de color desde la API
// Usa connection (empresa_cli_id) porque el endpoint necesita conectar a la BD del cliente
// Retorna true si la conexión fue exitosa, false si falló
async function cargarTemaColor(connection) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);
        const response = await fetch(`${API_URL}/api/empresa/${connection}/config`, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        const data = await response.json().catch(() => ({}));

        // Si el servidor responde con error 500/503, es problema de conexión a BD
        if (!response.ok || data.error === 'connection_error') {
            console.error('Error de conexión a BD Central:', data);
            applyColorTheme(data.tema || 'rubi');
            return false;
        }

        applyColorTheme(data.tema || 'rubi');
        return true;
    } catch (error) {
        console.error('Error cargando tema (posible problema de conexión):', error);
        applyColorTheme('rubi');
        return false;
    }
}

// Cargar logo del cliente desde la API
async function cargarLogoCliente(connection) {
    const sidebarLogo = document.getElementById('sidebar-logo');
    const mobileLogo = document.getElementById('mobile-logo');

    try {
        const existsResp = await fetch(`${API_URL}/api/empresa/${connection}/logo/exists`);
        const existsData = await existsResp.json().catch(() => ({}));

        if (existsData.exists) {
            const logoUrl = `${API_URL}/api/empresa/${connection}/logo`;
            // Guardar en cache para evitar flash en próximas cargas
            localStorage.setItem('logoUrl', logoUrl);

            if (sidebarLogo) { sidebarLogo.src = logoUrl; sidebarLogo.style.visibility = 'visible'; }
            if (mobileLogo) { mobileLogo.src = logoUrl; mobileLogo.style.visibility = 'visible'; }

            // Mostrar el "Powered by" del desarrollador (sidebar desktop)
            const devBadge = document.querySelector('.sidebar-developer');
            if (devBadge) devBadge.style.display = 'flex';

            // Mostrar el "Powered by" del desarrollador (mobile)
            const mobileDevBadge = document.getElementById('mobile-developer');
            if (mobileDevBadge) mobileDevBadge.style.display = 'flex';

            // Guardar favicon si existe
            if (existsData.tiene_favicon !== undefined) {
                if (existsData.tiene_favicon) {
                    const faviconUrl = `${API_URL}/api/empresa/${connection}/favicon`;
                    localStorage.setItem('faviconUrl', faviconUrl);
                    let faviconLink = document.querySelector("link[rel='icon']");
                    if (!faviconLink) {
                        faviconLink = document.createElement('link');
                        faviconLink.rel = 'icon';
                        document.head.appendChild(faviconLink);
                    }
                    faviconLink.href = faviconUrl;
                }
            }
        } else {
            // No hay logo del cliente, mostrar logo por defecto
            localStorage.removeItem('logoUrl');
            if (sidebarLogo) { sidebarLogo.src = 'assets/logojobers.png'; sidebarLogo.style.visibility = 'visible'; }
            if (mobileLogo) { mobileLogo.src = 'assets/logojobers.png'; mobileLogo.style.visibility = 'visible'; }
        }
    } catch (error) {
        console.log('No se pudo cargar logo del cliente, usando logo por defecto');
        if (sidebarLogo) { sidebarLogo.src = 'assets/logojobers.png'; sidebarLogo.style.visibility = 'visible'; }
        if (mobileLogo) { mobileLogo.src = 'assets/logojobers.png'; mobileLogo.style.visibility = 'visible'; }
    }
}

// Helper: t() devuelve la clave si i18n no cargó (servidor caído), detectar y usar fallback
function ts(key, fallback) {
    const val = t(key);
    return (val && val !== key) ? val : fallback;
}

// Mostrar error de conexión a BD Central (usa estructura del login)
function showConnectionError(connection) {
    const container = document.querySelector('.login-container');
    const html = `
        <div class="login-box" style="text-align:center;">
            <div class="login-header">
                <div style="font-size:3.5rem;margin-bottom:0.5rem;">⚠️</div>
                <h1>${ts('auth.connectionErrorTitle', 'Error de conexión')}</h1>
                <p class="login-subtitle">${ts('auth.connectionErrorMessage', 'No se puede conectar con el servidor de datos. Es posible que el servicio esté temporalmente no disponible.')}</p>
            </div>
            <p style="color:var(--text-secondary, #888);font-size:0.85rem;margin-bottom:1.5rem;">
                ${ts('auth.connectionErrorHint', 'Inténtalo de nuevo en unos minutos. Si el problema persiste, contacta con el administrador.')}
            </p>
            <button onclick="location.reload()" class="btn-login">
                ${ts('common.retry', 'Reintentar')}
            </button>
        </div>
    `;
    if (container) {
        container.innerHTML = html;
    } else {
        document.body.innerHTML = `
            <div class="login-wrapper">
                <div class="login-container">${html}</div>
            </div>
        `;
    }
}

// Mostrar error crítico cuando falta el parámetro connection
function showCriticalError() {
    const container = document.querySelector('.login-container');
    const html = `
        <div class="login-box" style="text-align:center;">
            <div class="login-header">
                <div style="font-size:3.5rem;margin-bottom:0.5rem;">⚠️</div>
                <h1>${ts('auth.missingConnectionTitle', 'Parámetro obligatorio')}</h1>
                <p class="login-subtitle">${ts('auth.missingConnectionMessage', 'Esta aplicación requiere un enlace válido para funcionar.')}</p>
            </div>
            <p style="color:var(--text-secondary, #888);font-size:0.85rem;margin-bottom:1.5rem;">
                ${ts('auth.missingConnectionHint', 'Por favor, contacta con el administrador del sistema para obtener la URL correcta.')}
            </p>
        </div>
    `;
    if (container) {
        container.innerHTML = html;
    } else {
        document.body.innerHTML = `
            <div class="login-wrapper">
                <div class="login-container">${html}</div>
            </div>
        `;
    }
}

// Mostrar error cuando se usa parámetro 'empresa' en lugar de 'connection'
function showInvalidParamError() {
    const container = document.querySelector('.login-container');
    const html = `
        <div class="login-box" style="text-align:center;">
            <div class="login-header">
                <div style="font-size:3.5rem;margin-bottom:0.5rem;">🚫</div>
                <h1>${ts('auth.invalidParamTitle', 'Enlace incorrecto')}</h1>
                <p class="login-subtitle">${ts('auth.invalidParamMessage', 'El enlace utilizado no es válido.')}</p>
            </div>
            <p style="color:var(--text-secondary, #888);font-size:0.85rem;margin-bottom:1.5rem;">
                ${ts('auth.missingConnectionHint', 'Por favor, contacta con el administrador del sistema para obtener la URL correcta.')}
            </p>
        </div>
    `;
    if (container) {
        container.innerHTML = html;
    } else {
        document.body.innerHTML = `
            <div class="login-wrapper">
                <div class="login-container">${html}</div>
            </div>
        `;
    }
}

// Verificar si el usuario ya está autenticado
async function verificarSesionActiva() {
    try {
        const response = await fetch(`${API_URL}/api/current-user`, {
            credentials: 'include'
        });

        if (response.ok) {
            const user = await response.json();

            // Si debe cambiar contraseña, NO redirigir (mostrar modal)
            if (user.debe_cambiar_password) {
                console.log('Usuario debe cambiar contraseña, mostrando modal...');
                showPasswordChangeModal();
                return true; // Sesión activa pero debe cambiar contraseña
            }

            // Usuario autenticado y sin cambio de contraseña pendiente
            console.log('Usuario ya autenticado, redirigiendo...');
            window.location.replace('/');
            return true;
        }
    } catch (error) {
        console.log('No hay sesión activa');
    }
    return false;
}


// Inicializar después de que i18n esté listo
async function initLogin() {
    // Cargar tema oscuro/claro inmediatamente
    loadTheme();

    // Capturar connection de la URL, localStorage o API por defecto - hacer esto primero
    const connection = await getConnectionFromURL();

    if (connection === 'INVALID_PARAM') {
        // ERROR: Se usó 'empresa' en lugar de 'connection'
        console.error('ERROR: Parámetro "empresa" no válido. Use "connection" en su lugar.');
        showInvalidParamError();
        return; // Detener la inicialización
    }

    if (!connection) {
        // ERROR CRÍTICO: No hay parámetro connection
        console.error('ERROR: Parámetro connection obligatorio no encontrado en URL ni en localStorage');
        showCriticalError();
        return; // Detener la inicialización
    }

    // Inicializar i18n primero (necesario para mensajes de error)
    await I18n.init();

    // Cargar tema de color (usa connection para conectar a BD del cliente)
    // También verifica si la conexión a BD Central funciona
    const conexionOk = await cargarTemaColor(connection);
    if (!conexionOk) {
        console.error('ERROR: No se pudo conectar con la BD Central');
        showConnectionError(connection);
        return; // Detener la inicialización
    }

    // Cargar logo del cliente (si existe, reemplaza el logo estático)
    await cargarLogoCliente(connection);

    console.log(`Iniciando con connection: ${connection}`);

    loginForm = document.getElementById('login-form');
    btnLogin = document.getElementById('btn-login');
    alertContainer = document.getElementById('alert-container');

    // Configurar formularios
    setupLoginForm();
    setupChangePasswordForm();

    // Verificar si ya hay sesión activa
    const yaAutenticado = await verificarSesionActiva();
    if (yaAutenticado) {
        return; // No continuar, ya se redirigió o se muestra modal
    }

    verificarRegistroHabilitado();
    document.getElementById('username').focus();
}

function showAlert(message, type = 'error') {
    const alertClass = type === 'error' ? 'alert-error' : 'alert-success';
    alertContainer.innerHTML = `
        <div class="alert ${alertClass}">
            ${message}
        </div>
    `;
}

function clearAlert() {
    alertContainer.innerHTML = '';
}

function setLoading(loading) {
    if (loading) {
        btnLogin.disabled = true;
        btnLogin.innerHTML = `<span class="loading-spinner"></span>${t('auth.loggingIn')}`;
    } else {
        btnLogin.disabled = false;
        btnLogin.innerHTML = t('auth.loginButton');
    }
}

function setupLoginForm() {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert();

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        if (!username || !password) {
            showAlert(t('auth.fillAllFields'));
            return;
        }

        setLoading(true);

        try {
            // connection = ID para conexión a BD (ej: 10049)
            const connection = localStorage.getItem('connection');
            const response = await fetch(`${API_URL}/api/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    username,
                    password,
                    empresa_cli_id: connection,
                    device_info: {
                        screen: `${screen.width}x${screen.height}`,
                        viewport: `${window.innerWidth}x${window.innerHeight}`,
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                        language: navigator.language,
                        platform: navigator.platform,
                        cookiesEnabled: navigator.cookieEnabled,
                        touchscreen: navigator.maxTouchPoints > 0,
                        deviceMemory: navigator.deviceMemory || null,
                        hardwareConcurrency: navigator.hardwareConcurrency || null
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                // ⭐ Guardar empresa_id (empresa_erp) devuelto por el servidor para filtros
                if (data.user && data.user.empresa_id) {
                    localStorage.setItem('empresa_id', data.user.empresa_id);
                    console.log(`empresa_id guardado: ${data.user.empresa_id}`);
                }

                // ⭐ Guardar CSRF token para protección en peticiones POST/PUT/DELETE
                if (data.csrf_token) {
                    localStorage.setItem('csrf_token', data.csrf_token);
                    console.log('🔐 CSRF token guardado');
                }

                // Verificar si debe cambiar la contraseña
                if (data.debe_cambiar_password) {
                    showPasswordChangeModal();
                    setLoading(false);
                } else {
                    showAlert(t('auth.loginSuccess'), 'success');
                    setTimeout(() => {
                        // Usar replace para no añadir al historial (evita volver a login con botón atrás)
                        window.location.replace('/');
                    }, 1000);
                }
            } else if (response.status === 423) {
                // Cuenta bloqueada
                const mins = data.remaining_minutes || 15;
                const lockMsg = (t('auth.accountLocked') || 'Cuenta bloqueada.') + ' ' +
                    (t('auth.tryAgainIn') || 'Intenta de nuevo en') + ' ' + mins + ' ' +
                    (mins === 1 ? 'minuto' : 'minutos') + '.';
                showAlert(lockMsg);
                setLoading(false);
            } else if (response.status === 503 || data.error === 'database_connection') {
                // Error de conexión a BD del cliente
                showConnectionErrorModal();
                setLoading(false);
            } else {
                // Mostrar intentos restantes si están disponibles
                let msg = data.message || t('auth.loginError');
                if (data.attempts_remaining !== undefined && data.attempts_remaining !== null) {
                    msg += ` (${t('auth.attemptsRemaining') || 'Intentos restantes'}: ${data.attempts_remaining})`;
                }
                showAlert(msg);
                setLoading(false);
            }
        } catch (error) {
            console.error('Error en login:', error);
            showAlert(t('auth.connectionError'));
            setLoading(false);
        }
    });
}

// Verificar si el registro está habilitado
async function verificarRegistroHabilitado() {
    try {
        const connection = localStorage.getItem('connection');
        if (!connection) return;
        const response = await fetch(`${API_URL}/api/registro-habilitado?connection=${connection}`);
        const data = await response.json();

        if (data.habilitado) {
            // Mostrar enlace de registro
            document.getElementById('register-link-container').style.display = 'block';
            // Mostrar enlace de reenvío de verificación
            document.getElementById('resend-link-container').style.display = 'block';
        }
    } catch (error) {
        console.error('Error al verificar registro:', error);
    }
}

// Funciones para reenviar verificación
function mostrarFormularioReenvio(e) {
    e.preventDefault();
    document.getElementById('resend-form').style.display = 'block';
    document.getElementById('resend-email').focus();
}

function ocultarFormularioReenvio() {
    document.getElementById('resend-form').style.display = 'none';
    document.getElementById('resend-email').value = '';
    document.getElementById('resend-alert').innerHTML = '';
}

async function reenviarVerificacion() {
    const email = document.getElementById('resend-email').value.trim();
    const btnResend = document.getElementById('btn-resend');
    const resendAlert = document.getElementById('resend-alert');

    if (!email) {
        resendAlert.innerHTML = '<div class="alert alert-error">Por favor ingresa tu email</div>';
        return;
    }

    btnResend.disabled = true;
    btnResend.textContent = 'Enviando...';
    resendAlert.innerHTML = '';

    try {
        // Usar connection para reenvío (necesita conectar a BD del cliente)
        const connection = localStorage.getItem('connection');
        const response = await fetch(`${API_URL}/api/resend-verification`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, connection: connection })
        });

        const data = await response.json();

        if (data.success) {
            resendAlert.innerHTML = '<div class="alert alert-success">' + data.message + '</div>';
            setTimeout(() => {
                ocultarFormularioReenvio();
            }, 3000);
        } else {
            resendAlert.innerHTML = '<div class="alert alert-error">' + data.message + '</div>';
        }
    } catch (error) {
        console.error('Error al reenviar verificación:', error);
        resendAlert.innerHTML = '<div class="alert alert-error">Error de conexión. Intenta de nuevo.</div>';
    } finally {
        btnResend.disabled = false;
        btnResend.textContent = t('auth.resendButton');
    }
}

// ==================== RECUPERACIÓN DE CONTRASEÑA ====================

function mostrarFormularioRecuperacion(e) {
    e.preventDefault();
    document.getElementById('forgot-password-form').style.display = 'block';
    document.getElementById('forgot-email').focus();
}

function ocultarFormularioRecuperacion() {
    document.getElementById('forgot-password-form').style.display = 'none';
    document.getElementById('forgot-email').value = '';
    document.getElementById('forgot-alert').innerHTML = '';
}

async function enviarRecuperacion() {
    const email = document.getElementById('forgot-email').value.trim();
    const btnForgot = document.getElementById('btn-forgot');
    const forgotAlert = document.getElementById('forgot-alert');

    if (!email) {
        forgotAlert.innerHTML = `<div class="alert alert-error">${t('auth.fillAllFields') || 'Por favor ingresa tu email'}</div>`;
        return;
    }

    btnForgot.disabled = true;
    btnForgot.innerHTML = `<span class="loading-spinner"></span>${t('common.loading') || 'Enviando...'}`;
    forgotAlert.innerHTML = '';

    try {
        const connection = localStorage.getItem('connection');
        const response = await fetch(`${API_URL}/api/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, connection })
        });

        const data = await response.json();

        forgotAlert.innerHTML = `<div class="alert alert-success">${data.message || t('auth.forgotPasswordSent')}</div>`;
        setTimeout(() => {
            ocultarFormularioRecuperacion();
        }, 5000);
    } catch (error) {
        console.error('Error al enviar recuperación:', error);
        forgotAlert.innerHTML = '<div class="alert alert-error">Error de conexión. Intenta de nuevo.</div>';
    } finally {
        btnForgot.disabled = false;
        btnForgot.textContent = t('auth.forgotPasswordButton') || 'Enviar instrucciones';
    }
}

// ==================== MODAL DE CAMBIO DE CONTRASEÑA ====================

// Configurar formulario de cambio de contraseña (llamar una sola vez)
function setupChangePasswordForm() {
    const form = document.getElementById('change-password-form');
    if (form) {
        form.addEventListener('submit', handlePasswordChange);
    }
}

let _loginPasswordPolicy = null;

async function loadLoginPasswordPolicy() {
    if (_loginPasswordPolicy) return _loginPasswordPolicy;
    try {
        const resp = await fetch(`${API_URL}/api/password-policy`);
        if (resp.ok) _loginPasswordPolicy = await resp.json();
    } catch (e) { /* fallback */ }
    if (!_loginPasswordPolicy) {
        _loginPasswordPolicy = { min_length: 8, require_uppercase: true, require_lowercase: true, require_number: true, require_special: true };
    }
    return _loginPasswordPolicy;
}

function buildLoginPwdReqHtml(policy) {
    const items = [];
    if (policy.min_length) items.push({ key: 'min_length', text: t('changePassword.reqMinLength').replace('{n}', policy.min_length) });
    if (policy.require_uppercase) items.push({ key: 'uppercase', text: t('changePassword.reqUppercase') });
    if (policy.require_lowercase) items.push({ key: 'lowercase', text: t('changePassword.reqLowercase') });
    if (policy.require_number) items.push({ key: 'number', text: t('changePassword.reqNumber') });
    if (policy.require_special) items.push({ key: 'special', text: t('changePassword.reqSpecial') });
    return `<div class="password-requirements">
        <div class="password-requirements-title">${t('changePassword.requirementsTitle')}</div>
        <ul class="password-req-list">
            ${items.map(i => `<li class="password-req-item" data-req="${i.key}"><span class="req-icon">&#10003;</span>${i.text}</li>`).join('')}
        </ul>
    </div>`;
}

function checkLoginPwdReq(password, container) {
    if (!container) return;
    container.querySelectorAll('.password-req-item').forEach(item => {
        const req = item.getAttribute('data-req');
        let met = false;
        switch (req) {
            case 'min_length': met = password.length >= (_loginPasswordPolicy?.min_length || 8); break;
            case 'uppercase': met = /[A-Z]/.test(password); break;
            case 'lowercase': met = /[a-z]/.test(password); break;
            case 'number': met = /[0-9]/.test(password); break;
            case 'special': met = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?~`]/.test(password); break;
        }
        item.classList.toggle('met', met);
    });
}

function showConnectionErrorModal() {
    // Reemplazar el contenido del login-container con el mensaje de error
    const container = document.querySelector('.login-container');
    const html = `
        <div class="login-box" style="text-align:center;">
            <div class="login-header">
                <div style="font-size:3.5rem;margin-bottom:0.5rem;">⚠️</div>
                <h1>${ts('auth.connectionErrorTitle', 'Error de conexión')}</h1>
                <p class="login-subtitle">${ts('auth.connectionErrorMessage', 'No se puede conectar con el servidor de datos. Es posible que el servicio esté temporalmente no disponible.')}</p>
            </div>
            <p style="color:var(--text-secondary, #888);font-size:0.85rem;margin-bottom:1.5rem;">
                ${ts('auth.connectionErrorHint', 'Inténtalo de nuevo en unos minutos. Si el problema persiste, contacta con el administrador.')}
            </p>
            <button onclick="location.reload()" class="btn-login">
                ${ts('common.retry', 'Reintentar')}
            </button>
        </div>
    `;
    if (container) {
        container.innerHTML = html;
    } else {
        document.body.innerHTML = `
            <div class="login-wrapper">
                <div class="login-container">${html}</div>
            </div>
        `;
    }
}

async function showPasswordChangeModal() {
    const modal = document.getElementById('change-password-modal');
    modal.style.display = 'flex';

    // Inject password requirements
    const policy = await loadLoginPasswordPolicy();
    const newPwdInput = document.getElementById('new-password');
    let reqContainer = modal.querySelector('.password-requirements');
    if (!reqContainer && newPwdInput) {
        newPwdInput.insertAdjacentHTML('afterend', buildLoginPwdReqHtml(policy));
        reqContainer = modal.querySelector('.password-requirements');
        newPwdInput.addEventListener('input', function() {
            checkLoginPwdReq(this.value, reqContainer);
        });
    }
    if (reqContainer) checkLoginPwdReq('', reqContainer);
    newPwdInput.focus();
}

function hidePasswordChangeModal() {
    document.getElementById('change-password-modal').style.display = 'none';
}

function showPasswordAlert(message, type = 'error') {
    const container = document.getElementById('password-alert-container');
    const alertClass = type === 'error' ? 'alert-error' : 'alert-success';
    container.innerHTML = `
        <div class="alert ${alertClass}">
            ${message}
        </div>
    `;
}

function clearPasswordAlert() {
    document.getElementById('password-alert-container').innerHTML = '';
}

async function handlePasswordChange(e) {
    e.preventDefault();
    clearPasswordAlert();

    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const btnChange = document.getElementById('btn-change-password');

    // Validaciones contra política
    const reqContainer = document.querySelector('#change-password-modal .password-requirements');
    if (reqContainer) {
        checkLoginPwdReq(newPassword, reqContainer);
        const allMet = Array.from(reqContainer.querySelectorAll('.password-req-item')).every(i => i.classList.contains('met'));
        if (!allMet) {
            showPasswordAlert(t('changePassword.minLength'));
            return;
        }
    } else if (newPassword.length < (_loginPasswordPolicy?.min_length || 8)) {
        showPasswordAlert(t('changePassword.minLength'));
        return;
    }

    if (newPassword !== confirmPassword) {
        showPasswordAlert(t('changePassword.mismatch'));
        return;
    }

    // Deshabilitar botón y mostrar loading
    const originalText = btnChange.textContent;
    btnChange.disabled = true;
    btnChange.innerHTML = `<span class="loading-spinner"></span>${t('changePassword.changing')}`;

    try {
        // Obtener CSRF token guardado en el login
        const csrfToken = localStorage.getItem('csrf_token');

        const response = await fetch(`${API_URL}/api/usuarios/cambiar-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken || ''
            },
            credentials: 'include',
            body: JSON.stringify({ new_password: newPassword })
        });

        const data = await response.json();

        if (data.success) {
            showPasswordAlert(t('changePassword.success'), 'success');
            setTimeout(() => {
                hidePasswordChangeModal();
                window.location.replace('/');
            }, 1500);
        } else {
            showPasswordAlert(data.error || t('changePassword.error'));
            btnChange.disabled = false;
            btnChange.textContent = originalText;
        }
    } catch (error) {
        console.error('Error al cambiar contraseña:', error);
        showPasswordAlert(t('changePassword.error'));
        btnChange.disabled = false;
        btnChange.textContent = originalText;
    }
}

// ==================== TOGGLE MOSTRAR/OCULTAR CONTRASEÑA ====================

function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    const eyeIcon = button.querySelector('.eye-icon');
    const eyeOffIcon = button.querySelector('.eye-off-icon');

    if (input.type === 'password') {
        input.type = 'text';
        eyeIcon.style.display = 'none';
        eyeOffIcon.style.display = 'block';
        button.setAttribute('aria-label', 'Ocultar contraseña');
    } else {
        input.type = 'password';
        eyeIcon.style.display = 'block';
        eyeOffIcon.style.display = 'none';
        button.setAttribute('aria-label', 'Mostrar contraseña');
    }
}

// Inicializar al cargar la página
initLogin();