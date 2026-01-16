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

// Capturar empresa_id de la URL
function getEmpresaFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const empresa = urlParams.get('empresa');

    if (empresa) {
        localStorage.setItem('empresa_id', empresa);
        return empresa;
    } else {
        return localStorage.getItem('empresa_id') || '1';
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
    // Capturar empresa de la URL
    const empresaId = getEmpresaFromURL();
    console.log(`Registro con empresa_id: ${empresaId}`);

    // Cargar tema de color y logo de la empresa
    await cargarTemaColor(empresaId);
    await cargarLogoEmpresa(empresaId);

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
        const formData = {
            full_name: document.getElementById('full_name').value.trim(),
            username: document.getElementById('username').value.trim(),
            email: document.getElementById('email').value.trim(),
            pais: document.getElementById('pais').value,
            password: document.getElementById('password').value,
            empresa_id: empresaId
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
