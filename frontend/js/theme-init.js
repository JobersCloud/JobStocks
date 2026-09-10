// theme-init.js - Inyectar colores del tema ANTES del CSS para evitar flash
// Este archivo se carga sincronamente en <head> de todas las paginas
//
// Expone window.ThemeInit.applyColorTheme(tema) como UNICO punto de aplicacion
// de tema de color. Todo el que necesite cambiar el tema (page-common.js,
// login.js, pantalla de parametros...) debe llamar aqui: asi se aplica SIEMPRE
// el paquete completo (atributos, variables, modo claro forzado, CSS critico y
// tipografia) y nunca queda una mezcla del tema antiguo con el nuevo.
(function () {
    var THEMES = {
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
        'elegante': { primary: '#FF4438', primaryDark: '#1a1a1a', primaryLight: '#FF6B5B' },
        'cristacer': { primary: '#1a1a1a', primaryDark: '#000000', primaryLight: '#444444' },
        'rocanet': { primary: '#61a229', primaryDark: '#4e8221', primaryLight: '#7bc043' }
    };

    // Temas custom: no soportan dark mode, se fuerza modo claro
    var CUSTOM_THEMES = ['cristacer', 'rocanet'];

    function isCustom(colorTheme) {
        return CUSTOM_THEMES.indexOf(colorTheme) !== -1;
    }

    function ls(key) {
        try { return localStorage.getItem(key); } catch (e) { return null; }
    }

    function lsSet(key, value) {
        try { localStorage.setItem(key, value); } catch (e) { /* modo privado sin storage */ }
    }

    // CSS critico por tema: evita el flash de fondo/header/sidebar mientras
    // carga styles.css. Se regenera en cada cambio de tema (vacio si no aplica).
    function criticalCss(colorTheme) {
        if (colorTheme !== 'cristacer') return '';
        return 'body{background:#F6EEE3!important}' +
            '.top-header{background:#F6EEE3!important;border-bottom:1px solid #1a1a1a!important}' +
            '.top-header-title,.header-logo-text,.top-header .user-name-display{color:#1a1a1a!important;-webkit-text-fill-color:#1a1a1a!important}' +
            '.top-header .menu-icon,.top-header .mobile-menu-btn svg{stroke:#1a1a1a!important}' +
            '.header-logo img{filter:none!important}' +
            '.sidebar{background:#F6EEE3!important;border-right:1px solid #1a1a1a!important}' +
            '.sidebar-item{color:#444!important}' +
            '.sidebar-item svg{stroke:#444!important}' +
            '.login-wrapper{background:#F6EEE3!important}' +
            '.login-sidebar{border-right:none!important}' +
            '.login-sidebar::before{display:none!important}' +
            '.btn-login{background:#1a1a1a!important}';
    }

    // Tipografias externas por tema (se cargan una sola vez)
    var FONTS = {
        'cristacer': 'https://use.typekit.net/cfu7yaq.css'
    };
    var fontsLoaded = {};

    function loadFont(colorTheme) {
        var href = FONTS[colorTheme];
        if (!href || fontsLoaded[colorTheme]) return;
        fontsLoaded[colorTheme] = true;
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        document.head.appendChild(link);
    }

    function criticalStyleEl() {
        var el = document.getElementById('theme-colors-inline');
        if (!el) {
            el = document.createElement('style');
            el.id = 'theme-colors-inline';
            document.head.appendChild(el);
        }
        return el;
    }

    // ==================== PRIMERA VISITA ====================
    // Sin cache (incognito, navegador nuevo, cache borrada) no sabemos el tema
    // hasta que responde /api/empresa/<id>/config. En vez de pintar el tema por
    // defecto y cambiarlo despues (se veia una mezcla del estilo antiguo), se
    // oculta el documento hasta que se resuelve, con timeout de seguridad.
    var revealed = false;

    function reveal() {
        if (revealed) return;
        revealed = true;
        document.documentElement.style.visibility = '';
    }

    // Aplica el tema de color COMPLETO. Es idempotente y sirve tanto para el
    // arranque (desde cache) como para cuando llega la config real de la API.
    function applyColorTheme(colorTheme) {
        if (!THEMES[colorTheme]) colorTheme = 'rubi';
        var colors = THEMES[colorTheme];

        // Modo claro/oscuro: los temas custom fuerzan claro, pero NO se persiste
        // para no perder la preferencia real del usuario en temas estandar.
        var theme = isCustom(colorTheme) ? 'light' : (ls('theme') || 'dark');

        var root = document.documentElement;
        root.setAttribute('data-theme', theme);
        root.setAttribute('data-color-theme', colorTheme);
        lsSet('colorTheme', colorTheme);

        // Inline en <html> con !important: gana a cualquier hoja de estilos
        root.style.setProperty('--primary', colors.primary, 'important');
        root.style.setProperty('--primary-dark', colors.primaryDark, 'important');
        root.style.setProperty('--primary-light', colors.primaryLight, 'important');

        criticalStyleEl().textContent = criticalCss(colorTheme);
        loadFont(colorTheme);

        reveal();
        return colorTheme;
    }

    window.ThemeInit = {
        applyColorTheme: applyColorTheme,
        isCustomTheme: isCustom,
        THEMES: THEMES,
        reveal: reveal
    };

    // Arranque: pintar ya el tema cacheado (si lo hay)
    var cachedColorTheme = ls('colorTheme');
    applyColorTheme(cachedColorTheme || 'rubi');

    if (!cachedColorTheme) {
        // No habia cache: 'rubi' es solo un provisional, no se da por bueno ni
        // se cachea. Se oculta el documento hasta que la API diga el tema real.
        try { localStorage.removeItem('colorTheme'); } catch (e) { }
        revealed = false;
        document.documentElement.style.visibility = 'hidden';
        setTimeout(reveal, 1500);
        window.addEventListener('load', function () { setTimeout(reveal, 500); });
    }

    // Favicon desde cache
    var faviconUrl = ls('faviconUrl');
    if (faviconUrl) {
        var link = document.createElement('link');
        link.rel = 'icon';
        link.href = faviconUrl;
        document.head.appendChild(link);
    }

    // Pre-cargar logo y nombre empresa desde cache para evitar flash
    var _logoUrl = ls('logoUrl');
    var _companyName = ls('companyName');
    var _logoInvert = ls('logoInvert');
    if (_logoUrl || _companyName) {
        document.addEventListener('DOMContentLoaded', function () {
            // App pages (header-logo)
            var logo = document.getElementById('header-logo');
            if (logo && _logoUrl) {
                logo.src = _logoUrl;
                logo.style.filter = _logoInvert === 'true' ? 'brightness(0) invert(1)' : 'none';
                logo.style.visibility = 'visible';
            }
            var name = document.getElementById('header-company-name');
            if (name && _companyName) name.textContent = _companyName;

            // Login page (sidebar-logo, mobile-logo)
            var sLogo = document.getElementById('sidebar-logo');
            var mLogo = document.getElementById('mobile-logo');
            if (sLogo && _logoUrl) { sLogo.src = _logoUrl; sLogo.style.visibility = 'visible'; }
            if (mLogo && _logoUrl) { mLogo.src = _logoUrl; mLogo.style.visibility = 'visible'; }
        });
    }
})();
