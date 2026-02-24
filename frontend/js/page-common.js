// ============================================================
//      ██╗ ██████╗ ██████╗ ███████╗██████╗ ███████╗
//      ██║██╔═══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝
//      ██║██║   ██║██████╔╝█████╗  ██████╔╝███████╗
// ██   ██║██║   ██║██╔══██╗██╔══╝  ██╔══██╗╚════██║
// ╚█████╔╝╚██████╔╝██████╔╝███████╗██║  ██║███████║
//  ╚════╝  ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝
//
//                ──  Jobers - Iaucejo  ──
//
// Autor : iaucejo
// Fecha : 2026-02-06
// ============================================================

// ============================================
// ARCHIVO: js/page-common.js
// Descripcion: Funciones comunes reutilizables para todas las paginas admin/usuario
// Extrae el codigo duplicado de theme, auth, logo, menu, password, csrf, utilidades
// ============================================

(function() {
    'use strict';

    // ==================== CONFIGURACION ====================
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
    const API_URL = isLocalhost ? `${protocol}//${hostname}:5000` : `${protocol}//${hostname}`;

    let currentUser = null;
    let csrfToken = null;

    // ==================== TEMAS DE COLOR ====================
    const COLOR_THEMES = {
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

    // ==================== TEMA ====================
    function loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        applyTheme(savedTheme);
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const icon = document.getElementById('theme-icon');
        if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const newTheme = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    }

    // ==================== COLOR THEME ====================
    function applyColorTheme(tema) {
        if (!COLOR_THEMES[tema]) tema = 'rubi';
        const colors = COLOR_THEMES[tema];
        document.documentElement.setAttribute('data-color-theme', tema);
        localStorage.setItem('colorTheme', tema);
        document.documentElement.style.setProperty('--primary', colors.primary, 'important');
        document.documentElement.style.setProperty('--primary-dark', colors.primaryDark, 'important');
        document.documentElement.style.setProperty('--primary-light', colors.primaryLight, 'important');
    }

    // ==================== LOGO DINAMICO ====================
    async function cargarLogoEmpresa() {
        const connection = localStorage.getItem('connection');
        if (!connection) {
            applyColorTheme('rubi');
            return;
        }
        const logoElements = document.querySelectorAll('.logo, #header-logo');
        try {
            const configResponse = await fetch(`${API_URL}/api/empresa/${connection}/config`);
            const config = await configResponse.json();
            applyColorTheme(config.tema || 'rubi');
            const invertirFilter = config.invertir_logo ? 'brightness(0) invert(1)' : 'none';
            localStorage.setItem('logoInvert', config.invertir_logo ? 'true' : 'false');
            if (config.tiene_logo) {
                const logoUrl = `${API_URL}/api/empresa/${connection}/logo?t=${Date.now()}`;
                localStorage.setItem('logoUrl', `${API_URL}/api/empresa/${connection}/logo`);
                logoElements.forEach(el => {
                    el.src = logoUrl;
                    el.style.filter = invertirFilter;
                    el.style.visibility = 'visible';
                });
                if (config.tiene_favicon) {
                    const faviconUrl = `${API_URL}/api/empresa/${connection}/favicon`;
                    localStorage.setItem('faviconUrl', faviconUrl);
                } else {
                    localStorage.removeItem('faviconUrl');
                }
            } else {
                localStorage.removeItem('logoUrl');
                logoElements.forEach(el => {
                    el.src = 'assets/logo.svg';
                    el.style.filter = 'brightness(0) invert(1)';
                    el.style.visibility = 'visible';
                });
            }
        } catch (error) {
            applyColorTheme('rubi');
            logoElements.forEach(el => {
                el.src = 'assets/logo.svg';
                el.style.filter = 'brightness(0) invert(1)';
                el.style.visibility = 'visible';
            });
        }

        // Cargar nombre de la empresa
        try {
            const response = await fetch(`${API_URL}/api/empresa/current`, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                if (data.empresa && data.empresa.nombre) {
                    localStorage.setItem('companyName', data.empresa.nombre);
                    const headerName = document.getElementById('header-company-name');
                    if (headerName) {
                        headerName.textContent = data.empresa.nombre;
                    }
                }
            }
        } catch (e) {
            console.log('Error cargando nombre empresa:', e);
        }

        // Hacer logo clicable -> ir al home
        const headerLogo = document.querySelector('.header-logo');
        if (headerLogo) {
            headerLogo.style.cursor = 'pointer';
            headerLogo.addEventListener('click', () => {
                window.location.href = 'index.html';
            });
        }
    }

    // ==================== ACORDEON ====================
    function toggleAccordion(header) {
        const accordion = header.closest('.sidebar-accordion');
        accordion.classList.toggle('expanded');
    }

    // ==================== MENU USUARIO ====================
    function toggleUserMenu() {
        const dropdown = document.getElementById('menu-dropdown');
        dropdown.classList.toggle('show');
        // Cerrar sidebar móvil si está abierto
        if (dropdown.classList.contains('show')) {
            const mobileMenu = document.getElementById('mobile-menu-panel');
            if (mobileMenu) {
                mobileMenu.remove();
                const overlay = document.querySelector('.sidebar-overlay');
                if (overlay) overlay.style.display = '';
            }
        }
    }

    // Cerrar menu al hacer clic fuera
    document.addEventListener('click', (e) => {
        const menuContainer = document.querySelector('.menu-container');
        const dropdown = document.getElementById('menu-dropdown');
        if (menuContainer && !menuContainer.contains(e.target) && dropdown) {
            dropdown.classList.remove('show');
        }
    });

    // ==================== AUTENTICACION ====================

    /**
     * Verifica autenticacion y opcionalmente restringe acceso por rol.
     * @param {string} requiredRole - 'usuario' | 'administrador' | 'superusuario'
     *   'usuario' = cualquier usuario autenticado
     *   'administrador' = admin o superusuario
     *   'superusuario' = solo superusuario
     * @returns {object|null} datos del usuario o null si redirige
     */
    async function checkAuth(requiredRole) {
        try {
            const response = await fetch(`${API_URL}/api/current-user`, { credentials: 'include' });
            if (!response.ok) {
                window.location.href = 'login.html';
                return null;
            }
            const data = await response.json();
            currentUser = data;

            // Actualizar UI con datos del usuario
            const nameDisplay = document.getElementById('user-name-display');
            const menuName = document.getElementById('menu-user-name');
            const menuRol = document.getElementById('menu-user-rol');
            if (nameDisplay) nameDisplay.textContent = data.full_name || data.username;
            if (menuName) menuName.textContent = data.full_name || data.username;
            if (menuRol) menuRol.textContent = data.rol;

            // Mostrar opcion de contexto solo para superusuarios
            if (data.rol === 'superusuario') {
                const ctxItem = document.getElementById('menu-item-context');
                const ctxDivider = document.getElementById('menu-divider-context');
                if (ctxItem) ctxItem.style.display = 'flex';
                if (ctxDivider) ctxDivider.style.display = 'block';
            }

            // Verificar rol requerido
            if (requiredRole === 'administrador') {
                if (data.rol !== 'administrador' && data.rol !== 'superusuario') {
                    window.location.href = 'index.html';
                    return null;
                }
            } else if (requiredRole === 'superusuario') {
                if (data.rol !== 'superusuario') {
                    window.location.href = 'index.html';
                    return null;
                }
            }

            // Mostrar secciones admin si corresponde
            if (data.rol === 'administrador' || data.rol === 'superusuario') {
                const adminSection = document.getElementById('sidebar-admin-section');
                const configSection = document.getElementById('sidebar-config-section');
                if (adminSection) adminSection.style.display = 'block';
                if (configSection) configSection.style.display = 'block';
            }

            return data;
        } catch (error) {
            console.error('Error checking auth:', error);
            window.location.href = 'login.html';
            return null;
        }
    }

    async function logout() {
        try {
            await fetch(`${API_URL}/api/logout`, { method: 'POST', credentials: 'include' });
        } catch (e) {}
        localStorage.removeItem('csrf_token');
        window.location.href = 'login.html';
    }

    // ==================== CONTEXTO ====================
    async function showContextInfo() {
        try {
            const response = await fetch(`${API_URL}/api/context-info`, { credentials: 'include' });
            if (!response.ok) throw new Error('No se pudo obtener la informacion de contexto');
            const info = await response.json();
            let html = '<div style="font-family: monospace; font-size: 0.85rem; line-height: 1.6;">';
            html += '<h4 style="margin-bottom: 10px; color: var(--primary);">Usuario</h4>';
            html += '<div style="background: var(--bg-secondary, #f5f5f5); padding: 10px; border-radius: 8px; margin-bottom: 15px;">';
            html += `<div><strong>ID:</strong> ${info.user.id}</div>`;
            html += `<div><strong>Username:</strong> ${info.user.username}</div>`;
            html += `<div><strong>Nombre:</strong> ${info.user.full_name}</div>`;
            html += `<div><strong>Rol:</strong> ${info.user.rol}</div>`;
            html += `<div><strong>Cliente ID:</strong> ${info.user.cliente_id || 'N/A'}</div>`;
            html += '</div>';
            if (info.session) {
                html += '<h4 style="margin-bottom: 10px; color: var(--primary);">Sesion</h4>';
                html += '<div style="background: var(--bg-secondary, #f5f5f5); padding: 10px; border-radius: 8px; margin-bottom: 15px;">';
                html += `<div><strong>Connection:</strong> ${info.session.connection}</div>`;
                html += `<div><strong>Empresa ID:</strong> ${info.session.empresa_id}</div>`;
                html += `<div><strong>Empresa Nombre:</strong> ${info.session.empresa_nombre}</div>`;
                html += `<div><strong>User ID:</strong> ${info.session.user_id}</div>`;
                html += '</div>';
            }
            if (info.has_db_config !== undefined) {
                html += '<h4 style="margin-bottom: 10px; color: var(--primary);">DB Config</h4>';
                html += `<div style="background: ${info.has_db_config ? '#e8f5e9' : '#ffebee'}; padding: 10px; border-radius: 8px; margin-bottom: 15px;">`;
                html += `<div><strong>Cacheado:</strong> ${info.has_db_config ? 'Si' : 'No'}</div>`;
                if (info.has_db_config && info.db_config) {
                    html += `<div><strong>Server:</strong> ${info.db_config.dbserver}</div>`;
                    html += `<div><strong>Database:</strong> ${info.db_config.dbname}</div>`;
                }
                html += '</div>';
            }
            html += '<h4 style="margin-bottom: 10px; color: var(--primary);">LocalStorage</h4>';
            html += '<div style="background: var(--bg-secondary, #f5f5f5); padding: 10px; border-radius: 8px;">';
            html += `<div><strong>connection:</strong> ${localStorage.getItem('connection') || 'N/A'}</div>`;
            html += `<div><strong>empresa_id:</strong> ${localStorage.getItem('empresa_id') || 'N/A'}</div>`;
            html += '</div></div>';

            const modal = document.createElement('div');
            modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000;';
            modal.innerHTML = `<div style="background:var(--bg-primary, white);padding:20px;border-radius:12px;max-width:500px;max-height:80vh;overflow-y:auto;box-shadow:0 10px 40px rgba(0,0,0,0.3);"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;"><h3 style="margin:0;">Info de Contexto</h3><button onclick="this.closest('div').parentElement.remove()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;">&times;</button></div>${html}</div>`;
            modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
            document.body.appendChild(modal);
        } catch (error) {
            console.error('Error:', error);
            alert('Error: ' + error.message);
        }
    }

    // ==================== CSRF ====================
    async function obtenerCsrfToken() {
        try {
            csrfToken = localStorage.getItem('csrf_token');
            const response = await fetch(`${API_URL}/api/csrf-token`, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                csrfToken = data.csrf_token;
                localStorage.setItem('csrf_token', csrfToken);
            }
        } catch (e) {}
    }

    function getCsrfToken() {
        return csrfToken || localStorage.getItem('csrf_token');
    }

    // ==================== CAMBIO DE CONTRASENA ====================
    async function showChangePasswordModal() {
        const modal = document.getElementById('change-password-modal');
        if (!modal) return;
        modal.style.display = 'flex';
        document.getElementById('current-password').value = '';
        document.getElementById('new-password').value = '';
        document.getElementById('confirm-password').value = '';
        document.getElementById('change-password-error').style.display = 'none';
        document.getElementById('change-password-success').style.display = 'none';
        const btn = document.getElementById('change-password-btn');
        btn.disabled = false;
        btn.textContent = t('changePassword.changeButton');

        // Inject password requirements
        const policy = await loadPasswordPolicy();
        const newPwdInput = document.getElementById('new-password');
        let reqContainer = modal.querySelector('.password-requirements');
        if (!reqContainer && newPwdInput) {
            newPwdInput.insertAdjacentHTML('afterend', buildPasswordRequirementsHtml(policy));
            reqContainer = modal.querySelector('.password-requirements');
            newPwdInput.addEventListener('input', function() {
                checkPasswordRequirements(this.value, reqContainer);
            });
        }
        if (reqContainer) checkPasswordRequirements('', reqContainer);
    }

    function hideChangePasswordModal() {
        const modal = document.getElementById('change-password-modal');
        if (modal) modal.style.display = 'none';
    }

    async function handleVoluntaryPasswordChange() {
        const currentPwd = document.getElementById('current-password').value;
        const newPwd = document.getElementById('new-password').value;
        const confirmPwd = document.getElementById('confirm-password').value;
        const errorEl = document.getElementById('change-password-error');
        const successEl = document.getElementById('change-password-success');
        const btn = document.getElementById('change-password-btn');

        errorEl.style.display = 'none';
        successEl.style.display = 'none';

        if (!currentPwd) {
            errorEl.textContent = t('changePassword.currentPasswordRequired');
            errorEl.style.display = 'block';
            return;
        }
        const reqContainer = document.querySelector('#change-password-modal .password-requirements');
        if (reqContainer && !allRequirementsMet(reqContainer)) {
            errorEl.textContent = t('changePassword.minLength');
            errorEl.style.display = 'block';
            return;
        }
        if (newPwd.length < (_passwordPolicy?.min_length || 8)) {
            errorEl.textContent = t('changePassword.minLength');
            errorEl.style.display = 'block';
            return;
        }
        if (newPwd !== confirmPwd) {
            errorEl.textContent = t('changePassword.mismatch');
            errorEl.style.display = 'block';
            return;
        }

        btn.disabled = true;
        btn.textContent = t('changePassword.changing');

        try {
            const response = await fetch(`${API_URL}/api/usuarios/cambiar-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                },
                credentials: 'include',
                body: JSON.stringify({ current_password: currentPwd, new_password: newPwd })
            });
            const data = await response.json();
            if (response.ok && data.success) {
                successEl.textContent = t('changePassword.success');
                successEl.style.display = 'block';
                setTimeout(() => hideChangePasswordModal(), 2000);
            } else {
                errorEl.textContent = data.error || t('changePassword.error');
                errorEl.style.display = 'block';
                btn.disabled = false;
                btn.textContent = t('changePassword.changeButton');
            }
        } catch (error) {
            errorEl.textContent = t('changePassword.error');
            errorEl.style.display = 'block';
            btn.disabled = false;
            btn.textContent = t('changePassword.changeButton');
        }
    }

    // Cerrar modal de password al clic fuera (se registra tras DOMContentLoaded)
    function _initPasswordModal() {
        const modal = document.getElementById('change-password-modal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) hideChangePasswordModal();
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _initPasswordModal);
    } else {
        _initPasswordModal();
    }

    // ==================== PASSWORD POLICY ====================
    let _passwordPolicy = null;

    async function loadPasswordPolicy() {
        if (_passwordPolicy) return _passwordPolicy;
        try {
            const resp = await fetch(`${API_URL}/api/password-policy`);
            if (resp.ok) _passwordPolicy = await resp.json();
        } catch (e) { /* fallback defaults */ }
        if (!_passwordPolicy) {
            _passwordPolicy = { min_length: 8, require_uppercase: true, require_lowercase: true, require_number: true, require_special: true };
        }
        return _passwordPolicy;
    }

    function buildPasswordRequirementsHtml(policy) {
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

    function checkPasswordRequirements(password, container) {
        if (!container) return;
        const items = container.querySelectorAll('.password-req-item');
        items.forEach(item => {
            const req = item.getAttribute('data-req');
            let met = false;
            switch (req) {
                case 'min_length': met = password.length >= (_passwordPolicy?.min_length || 8); break;
                case 'uppercase': met = /[A-Z]/.test(password); break;
                case 'lowercase': met = /[a-z]/.test(password); break;
                case 'number': met = /[0-9]/.test(password); break;
                case 'special': met = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?~`]/.test(password); break;
            }
            item.classList.toggle('met', met);
        });
    }

    function allRequirementsMet(container) {
        if (!container) return true;
        const items = container.querySelectorAll('.password-req-item');
        return Array.from(items).every(i => i.classList.contains('met'));
    }

    // ==================== UTILIDADES ====================
    function formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', { year: 'numeric', month: '2-digit', day: '2-digit' });
    }

    function formatDateTime(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    }

    function formatCurrency(value) {
        if (value === null || value === undefined) return '0,00';
        const num = typeof value === 'string' ? parseFloat(value) : Number(value);
        if (isNaN(num)) return '0,00';
        const fixed = num.toFixed(2);
        const [intPart, decPart] = fixed.split('.');
        const miles = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        return miles + ',' + decPart;
    }

    function truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    function getEmpresaId() {
        return localStorage.getItem('empresa_id');
    }

    function getApiUrl() {
        return API_URL;
    }

    function getCurrentUser() {
        return currentUser;
    }

    // ==================== EXPONER API PUBLICA ====================
    window.PageCommon = {
        // Theme
        loadTheme,
        applyTheme,
        toggleTheme,
        applyColorTheme,
        // Logo
        cargarLogoEmpresa,
        // Accordion
        toggleAccordion,
        // Menu
        toggleUserMenu,
        showContextInfo,
        // Auth
        checkAuth,
        logout,
        // CSRF
        obtenerCsrfToken,
        getCsrfToken,
        // Password
        showChangePasswordModal,
        hideChangePasswordModal,
        handleVoluntaryPasswordChange,
        loadPasswordPolicy,
        buildPasswordRequirementsHtml,
        checkPasswordRequirements,
        allRequirementsMet,
        // Utilities
        formatDate,
        formatDateTime,
        formatCurrency,
        truncateText,
        getEmpresaId,
        getApiUrl,
        getCurrentUser,
        // Constants
        API_URL,
        COLOR_THEMES
    };

    // Exponer funciones globales para onclick inline en HTML
    window.loadTheme = loadTheme;
    window.toggleTheme = toggleTheme;
    window.toggleAccordion = toggleAccordion;
    window.toggleUserMenu = toggleUserMenu;
    window.showContextInfo = showContextInfo;
    window.logout = logout;
    window.showChangePasswordModal = showChangePasswordModal;
    window.hideChangePasswordModal = hideChangePasswordModal;
    window.handleVoluntaryPasswordChange = handleVoluntaryPasswordChange;

})();
