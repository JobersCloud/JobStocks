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

// Capturar connection de la URL (OBLIGATORIO)
// connection = ID para buscar en BD central (ej: 10049)
// empresa_id = empresa_erp para filtros (ej: '1') - se obtiene después del login
function getConnectionFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    // Aceptar tanto 'connection' como 'empresa' para compatibilidad
    const connection = urlParams.get('connection') || urlParams.get('empresa');

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
            // ERROR: No hay connection en URL ni en localStorage
            return null;
        }
    }
}

// Aplicar tema de color
function applyColorTheme(tema) {
    const validThemes = ['rubi', 'zafiro', 'esmeralda', 'amatista', 'ambar', 'grafito'];
    if (!validThemes.includes(tema)) tema = 'rubi';
    document.documentElement.setAttribute('data-color-theme', tema);
    localStorage.setItem('colorTheme', tema);
}

// Cargar tema de color desde la API
// Usa connection (empresa_cli_id) porque el endpoint necesita conectar a la BD del cliente
async function cargarTemaColor(connection) {
    try {
        const response = await fetch(`${API_URL}/api/empresa/${connection}/config`);
        const config = await response.json();
        applyColorTheme(config.tema || 'rubi');
    } catch (error) {
        console.log('Error cargando tema:', error);
        applyColorTheme('rubi');
    }
}

// Mostrar error crítico cuando falta el parámetro connection
function showCriticalError() {
    document.body.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 500px; text-align: center;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
                <h1 style="color: #333; margin-bottom: 1rem; font-size: 1.5rem;">Parámetro Obligatorio Faltante</h1>
                <p style="color: #666; margin-bottom: 1.5rem; line-height: 1.6;">
                    Esta aplicación requiere el parámetro <strong>connection</strong> en la URL para funcionar.
                </p>
                <div style="background: #f5f5f5; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-family: 'Courier New', monospace; color: #333;">
                    ${window.location.origin}${window.location.pathname}<strong style="color: #e74c3c;">?connection=10049</strong>
                </div>
                <p style="color: #999; font-size: 0.9rem;">
                    Por favor, contacte con el administrador del sistema para obtener la URL correcta.
                </p>
            </div>
        </div>
    `;
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
    // Capturar connection de la URL (OBLIGATORIO) - hacer esto primero
    const connection = getConnectionFromURL();

    if (!connection) {
        // ERROR CRÍTICO: No hay parámetro connection
        console.error('ERROR: Parámetro connection obligatorio no encontrado en URL ni en localStorage');
        showCriticalError();
        return; // Detener la inicialización
    }

    // Cargar tema de color (usa connection para conectar a BD del cliente)
    await cargarTemaColor(connection);

    // Inicializar i18n (necesario para mensajes)
    await I18n.init();

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
                body: JSON.stringify({ username, password, empresa_cli_id: connection })
            });

            const data = await response.json();

            if (data.success) {
                // ⭐ Guardar empresa_id (empresa_erp) devuelto por el servidor para filtros
                if (data.user && data.user.empresa_id) {
                    localStorage.setItem('empresa_id', data.user.empresa_id);
                    console.log(`empresa_id guardado: ${data.user.empresa_id}`);
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
            } else {
                showAlert(data.message || t('auth.loginError'));
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
        // Usar connection para la verificación (necesita conectar a BD del cliente)
        const connection = localStorage.getItem('connection');
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

// ==================== MODAL DE CAMBIO DE CONTRASEÑA ====================

// Configurar formulario de cambio de contraseña (llamar una sola vez)
function setupChangePasswordForm() {
    const form = document.getElementById('change-password-form');
    if (form) {
        form.addEventListener('submit', handlePasswordChange);
    }
}

function showPasswordChangeModal() {
    const modal = document.getElementById('change-password-modal');
    modal.style.display = 'flex';
    document.getElementById('new-password').focus();
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

    // Validaciones
    if (newPassword.length < 6) {
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
        const response = await fetch(`${API_URL}/api/usuarios/cambiar-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
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