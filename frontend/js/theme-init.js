// theme-init.js - Inyectar colores del tema ANTES del CSS para evitar flash
// Este archivo se carga sincronamente en <head> de todas las paginas
(function () {
    var themes = {
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
    var theme = localStorage.getItem('theme') || 'dark';
    var colorTheme = localStorage.getItem('colorTheme') || 'rubi';
    var colors = themes[colorTheme] || themes['rubi'];

    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-color-theme', colorTheme);

    // Inyectar colores como CSS inline con !important para ganar especificidad
    var style = document.createElement('style');
    style.id = 'theme-colors-inline';
    style.textContent = ':root{--primary:' + colors.primary + '!important;--primary-dark:' + colors.primaryDark + '!important;--primary-light:' + colors.primaryLight + '!important}';
    document.head.appendChild(style);

    // Favicon desde cache
    var faviconUrl = localStorage.getItem('faviconUrl');
    if (faviconUrl) {
        var link = document.createElement('link');
        link.rel = 'icon';
        link.href = faviconUrl;
        document.head.appendChild(link);
    }

    // Pre-cargar logo y nombre empresa desde cache para evitar flash
    var _logoUrl = localStorage.getItem('logoUrl');
    var _companyName = localStorage.getItem('companyName');
    var _logoInvert = localStorage.getItem('logoInvert');
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
