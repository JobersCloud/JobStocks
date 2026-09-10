// reset-password.js
const protocol = window.location.protocol;
const hostname = window.location.hostname;
const port = window.location.port;

let API_URL;
if (hostname === 'localhost' || hostname === '127.0.0.1') {
    API_URL = `${protocol}//${hostname}:5000`;
} else {
    API_URL = `${protocol}//${hostname}${port ? ':' + port : ''}`;
}

// ==================== MODO OSCURO ====================

function loadTheme() {
    // Los temas custom no soportan dark mode: se fuerza claro sin pisar la
    // preferencia guardada del usuario (si vuelve a un tema estandar, se respeta)
    const colorTheme = document.documentElement.getAttribute('data-color-theme');
    if (window.ThemeInit && window.ThemeInit.isCustomTheme(colorTheme)) {
        document.documentElement.setAttribute('data-theme', 'light');
        return;
    }
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    const themeSwitch = document.getElementById('theme-switch');
    const themeIcon = document.getElementById('theme-icon');

    if (themeSwitch) themeSwitch.checked = theme === 'dark';
    if (themeIcon) themeIcon.textContent = theme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
}

window.toggleTheme = toggleTheme;

// ==================== TEMA DE COLOR ====================

function applyColorTheme(tema) {
    // Delega en theme-init.js (unico punto de aplicacion de tema): aplica ademas el
    // CSS critico, la tipografia y el modo claro forzado de los temas custom.
    if (window.ThemeInit) window.ThemeInit.applyColorTheme(tema);
}

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

async function cargarLogoEmpresa(connection) {
    try {
        const response = await fetch(`${API_URL}/api/empresa/${connection}/logo/exists`);
        const data = await response.json();

        if (data.exists) {
            const logoUrl = `${API_URL}/api/empresa/${connection}/logo`;
            const sidebarLogo = document.getElementById('sidebar-logo');
            const mobileLogo = document.getElementById('mobile-logo');

            if (sidebarLogo) sidebarLogo.src = logoUrl;
            if (mobileLogo) mobileLogo.src = logoUrl;
        }
    } catch (error) {
        console.log('Error cargando logo:', error);
    }
}

// ==================== TOGGLE MOSTRAR/OCULTAR CONTRASENA ====================

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

// ==================== PASSWORD POLICY ====================

let _resetPasswordPolicy = null;

async function loadResetPasswordPolicy() {
    if (_resetPasswordPolicy) return _resetPasswordPolicy;
    try {
        const resp = await fetch(`${API_URL}/api/password-policy`);
        if (resp.ok) _resetPasswordPolicy = await resp.json();
    } catch (e) { /* fallback */ }
    if (!_resetPasswordPolicy) {
        _resetPasswordPolicy = { min_length: 8, require_uppercase: true, require_lowercase: true, require_number: true, require_special: true };
    }
    return _resetPasswordPolicy;
}

function buildResetPwdReqHtml(policy) {
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

function checkResetPwdReq(password, container) {
    if (!container) return;
    container.querySelectorAll('.password-req-item').forEach(item => {
        const req = item.getAttribute('data-req');
        let met = false;
        switch (req) {
            case 'min_length': met = password.length >= (_resetPasswordPolicy?.min_length || 8); break;
            case 'uppercase': met = /[A-Z]/.test(password); break;
            case 'lowercase': met = /[a-z]/.test(password); break;
            case 'number': met = /[0-9]/.test(password); break;
            case 'special': met = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?~`]/.test(password); break;
        }
        item.classList.toggle('met', met);
    });
}

// ==================== ALERTAS ====================

function showAlert(message, type = 'error') {
    const container = document.getElementById('alert-container');
    const icon = type === 'error' ? '\u26A0\uFE0F' : '\u2705';
    container.innerHTML = `
        <div class="alert alert-${type}">
            <span>${icon}</span>
            <span>${message}</span>
        </div>
    `;
}

// ==================== INICIALIZACION ====================

function getUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    return {
        token: urlParams.get('token'),
        connection: urlParams.get('connection') || localStorage.getItem('connection')
    };
}

async function initResetPassword() {
    loadTheme();

    const { token, connection } = getUrlParams();

    if (connection) {
        localStorage.setItem('connection', connection);
    }

    // Configurar enlace "Volver al login"
    const backLink = document.getElementById('back-to-login-link');
    if (backLink) backLink.href = '/login';

    // Cargar tema y logo
    if (connection) {
        await cargarTemaColor(connection);
        await cargarLogoEmpresa(connection);
    }

    await I18n.init();

    // Verificar que hay token
    if (!token) {
        showAlert(t('auth.resetPasswordExpired') || 'El enlace no es válido. Solicita uno nuevo.', 'error');
        document.getElementById('reset-password-form').style.display = 'none';
        return;
    }

    // Inyectar requisitos de contraseña
    const policy = await loadResetPasswordPolicy();
    const pwdInput = document.getElementById('new-password');
    if (pwdInput) {
        const formGroup = pwdInput.closest('.form-group') || pwdInput.parentElement;
        formGroup.insertAdjacentHTML('afterend', buildResetPwdReqHtml(policy));
        const reqContainer = document.querySelector('.password-requirements');
        pwdInput.addEventListener('input', function() {
            checkResetPwdReq(this.value, reqContainer);
        });
    }

    // Configurar formulario
    setupResetForm(token, connection);
}

function setupResetForm(token, connection) {
    const form = document.getElementById('reset-password-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        const btnReset = document.getElementById('btn-reset');

        // Validar contra política
        const reqContainer = document.querySelector('.password-requirements');
        if (reqContainer) {
            checkResetPwdReq(newPassword, reqContainer);
            const allMet = Array.from(reqContainer.querySelectorAll('.password-req-item')).every(i => i.classList.contains('met'));
            if (!allMet) {
                showAlert(t('changePassword.minLength') || 'La contraseña no cumple los requisitos', 'error');
                return;
            }
        }

        if (newPassword !== confirmPassword) {
            showAlert(t('changePassword.mismatch') || 'Las contraseñas no coinciden', 'error');
            return;
        }

        const originalText = btnReset.textContent;
        btnReset.disabled = true;
        btnReset.innerHTML = `<span class="loading-spinner"></span>${t('changePassword.changing') || 'Cambiando...'}`;

        try {
            const response = await fetch(`${API_URL}/api/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token,
                    new_password: newPassword,
                    connection
                })
            });

            const data = await response.json();

            if (data.success) {
                showAlert(data.message || t('auth.resetPasswordSuccess'), 'success');
                form.style.display = 'none';

                // Redirigir al login tras 3 segundos
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            } else {
                showAlert(data.message || t('auth.resetPasswordExpired'), 'error');
                btnReset.disabled = false;
                btnReset.textContent = originalText;
            }
        } catch (error) {
            console.error('Error al restablecer contraseña:', error);
            showAlert(t('auth.connectionError') || 'Error de conexión. Intenta de nuevo.', 'error');
            btnReset.disabled = false;
            btnReset.textContent = originalText;
        }
    });
}

// Inicializar
initResetPassword();
