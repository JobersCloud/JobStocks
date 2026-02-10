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

// Capturar connection de la URL (ID de conexión a BD del cliente)
function getConnectionFromURL() {
    const urlParams = new URLSearchParams(window.location.search);

    // Si viene 'empresa' en lugar de 'connection', mostrar error
    const empresaParam = urlParams.get('empresa');
    if (empresaParam && !urlParams.get('connection')) {
        return 'INVALID_PARAM'; // Parámetro incorrecto
    }

    const connection = urlParams.get('connection');

    if (connection) {
        localStorage.setItem('connection', connection);
        return connection;
    } else {
        return localStorage.getItem('connection') || null;
    }
}

// Mostrar error cuando se usa parámetro 'empresa' en lugar de 'connection'
function showInvalidParamError() {
    document.body.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 500px; text-align: center;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🚫</div>
                <h1 style="color: #333; margin-bottom: 1rem; font-size: 1.5rem;">Parámetro Incorrecto</h1>
                <p style="color: #666; margin-bottom: 1.5rem; line-height: 1.6;">
                    El parámetro <strong style="color: #e74c3c;">empresa</strong> no es válido.
                    Debe usar <strong style="color: #27ae60;">connection</strong> en su lugar.
                </p>
                <div style="background: #ffebee; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; font-family: 'Courier New', monospace; color: #c0392b; text-decoration: line-through;">
                    ?empresa=XXXXX
                </div>
                <div style="background: #e8f5e9; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-family: 'Courier New', monospace; color: #27ae60;">
                    ?connection=XXXXX
                </div>
                <p style="color: #999; font-size: 0.9rem;">
                    Por favor, actualice el enlace o contacte con el administrador.
                </p>
            </div>
        </div>
    `;
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

    if (connection === 'INVALID_PARAM') {
        // ERROR: Se usó 'empresa' en lugar de 'connection'
        showInvalidParamError();
        return;
    }

    if (!connection) {
        // ERROR: No hay connection
        showInvalidParamError();
        return;
    }

    console.log(`Registro con connection: ${connection}`);

    // Cargar tema de color y logo de la empresa (usan connection para la API)
    await cargarTemaColor(connection);
    await cargarLogoEmpresa(connection);

    await I18n.init();
    verificarRegistroHabilitado();
    cargarPaises();
    setupRegisterForm();
    injectRegPasswordRequirements();
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
        const connection = localStorage.getItem('connection') || localStorage.getItem('empresa_id') || '1';
        const response = await fetch(`${API_URL}/api/registro-habilitado?connection=${connection}`);
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

// ==================== PASSWORD POLICY ====================
let _regPasswordPolicy = null;

async function loadRegPasswordPolicy() {
    if (_regPasswordPolicy) return _regPasswordPolicy;
    try {
        const resp = await fetch(`${API_URL}/api/password-policy`);
        if (resp.ok) _regPasswordPolicy = await resp.json();
    } catch (e) { /* fallback */ }
    if (!_regPasswordPolicy) {
        _regPasswordPolicy = { min_length: 8, require_uppercase: true, require_lowercase: true, require_number: true, require_special: true };
    }
    return _regPasswordPolicy;
}

function buildRegPwdReqHtml(policy) {
    const items = [];
    if (policy.min_length) items.push({ key: 'min_length', text: (t('changePassword.reqMinLength') || `Mínimo ${policy.min_length} caracteres`).replace('{n}', policy.min_length) });
    if (policy.require_uppercase) items.push({ key: 'uppercase', text: t('changePassword.reqUppercase') || 'Al menos una mayúscula' });
    if (policy.require_lowercase) items.push({ key: 'lowercase', text: t('changePassword.reqLowercase') || 'Al menos una minúscula' });
    if (policy.require_number) items.push({ key: 'number', text: t('changePassword.reqNumber') || 'Al menos un número' });
    if (policy.require_special) items.push({ key: 'special', text: t('changePassword.reqSpecial') || 'Al menos un carácter especial' });
    return `<div class="password-requirements">
        <div class="password-requirements-title">${t('changePassword.requirementsTitle') || 'Requisitos de contraseña:'}</div>
        <ul class="password-req-list">
            ${items.map(i => `<li class="password-req-item" data-req="${i.key}"><span class="req-icon">&#10003;</span>${i.text}</li>`).join('')}
        </ul>
    </div>`;
}

function checkRegPwdReq(password, container) {
    if (!container) return;
    container.querySelectorAll('.password-req-item').forEach(item => {
        const req = item.getAttribute('data-req');
        let met = false;
        switch (req) {
            case 'min_length': met = password.length >= (_regPasswordPolicy?.min_length || 8); break;
            case 'uppercase': met = /[A-Z]/.test(password); break;
            case 'lowercase': met = /[a-z]/.test(password); break;
            case 'number': met = /[0-9]/.test(password); break;
            case 'special': met = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?~`]/.test(password); break;
        }
        item.classList.toggle('met', met);
    });
}

async function injectRegPasswordRequirements() {
    const policy = await loadRegPasswordPolicy();
    const pwdInput = document.getElementById('password');
    if (!pwdInput) return;
    let reqContainer = document.querySelector('#register-form .password-requirements');
    if (!reqContainer) {
        // Insert after the password field's parent (form-group)
        const formGroup = pwdInput.closest('.form-group') || pwdInput.parentElement;
        formGroup.insertAdjacentHTML('afterend', buildRegPwdReqHtml(policy));
        reqContainer = document.querySelector('#register-form .password-requirements');
        pwdInput.addEventListener('input', function() {
            checkRegPwdReq(this.value, reqContainer);
        });
    }
}

// Configurar formulario de registro
function setupRegisterForm() {
    document.getElementById('register-form').addEventListener('submit', async function(e) {
        e.preventDefault();

        const btn = document.getElementById('btn-register');
        const originalText = btn.innerHTML;

        // Obtener datos del formulario
        const connection = localStorage.getItem('connection') || localStorage.getItem('empresa_id') || '1';
        const formData = {
            full_name: document.getElementById('full_name').value.trim(),
            company_name: document.getElementById('company_name').value.trim(),
            cif_nif: document.getElementById('cif_nif').value.trim(),
            username: document.getElementById('username').value.trim(),
            email: document.getElementById('email').value.trim(),
            pais: document.getElementById('pais').value,
            password: document.getElementById('password').value,
            connection: connection
        };

        const passwordConfirm = document.getElementById('password_confirm').value;

        // Validar contraseñas
        if (formData.password !== passwordConfirm) {
            showAlert(t('auth.passwordMismatch'), 'error');
            return;
        }

        // Validar contraseña contra política
        const reqContainer = document.querySelector('#register-form .password-requirements');
        if (reqContainer) {
            checkRegPwdReq(formData.password, reqContainer);
            const allMet = Array.from(reqContainer.querySelectorAll('.password-req-item')).every(i => i.classList.contains('met'));
            if (!allMet) {
                showAlert(t('auth.passwordMinLength'), 'error');
                return;
            }
        } else if (formData.password.length < (_regPasswordPolicy?.min_length || 8)) {
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

            // Si hay error (usuario o email ya existe, validación fallida, etc.)
            if (!response.ok || !data.success) {
                showAlert(data.message || t('auth.registerError'), 'error');
                btn.disabled = false;
                btn.innerHTML = originalText;
                // NO resetear formulario, NO redirigir - el usuario debe corregir los datos
                return;
            }

            // Solo si el registro fue exitoso
            document.getElementById('register-form').reset();

            // Mostrar modal de éxito con mensaje de verificación
            const connection = localStorage.getItem('connection') || localStorage.getItem('empresa_id') || '1';
            const loginUrl = `/login.html?connection=${connection}`;

            const modal = document.createElement('div');
            modal.className = 'register-success-overlay';
            modal.innerHTML = `
                <div class="register-success-modal">
                    <div class="register-success-icon">
                        <svg viewBox="0 0 24 24" fill="none" width="48" height="48">
                            <circle cx="12" cy="12" r="11" stroke="var(--primary, #4CAF50)" stroke-width="2"/>
                            <path d="M7 12.5l3 3 7-7" stroke="var(--primary, #4CAF50)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <h2 class="register-success-title">${t('auth.registerSuccessTitle') || 'Registro completado'}</h2>
                    <p class="register-success-message">${data.message}</p>
                    <p class="register-success-hint">${t('auth.registerSuccessHint') || 'Revisa tu bandeja de entrada y la carpeta de spam.'}</p>
                    <button class="register-success-btn" onclick="window.location.href='${loginUrl}'">${t('auth.goToLogin') || 'Ir al Login'}</button>
                </div>
            `;
            document.body.appendChild(modal);

            // Auto-redirigir tras 15 segundos si no pulsa el botón
            setTimeout(() => {
                window.location.href = loginUrl;
            }, 15000);

        } catch (error) {
            console.error('Error:', error);
            showAlert(t('auth.registerConnectionError'), 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
            // NO resetear formulario en caso de error de conexión
            return;
        }
    });
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
initRegister();
