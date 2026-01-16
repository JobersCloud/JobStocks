// i18n.js - Sistema de internacionalización
const I18n = (function() {
    const DEFAULT_LANG = 'es';
    const SUPPORTED_LANGS = ['es', 'en', 'fr'];
    const STORAGE_KEY = 'preferred_language';

    let currentLang = DEFAULT_LANG;
    let translations = {};
    let isLoaded = false;

    // Obtener idioma guardado o detectar del navegador
    function detectLanguage() {
        // 1. Verificar localStorage
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved && SUPPORTED_LANGS.includes(saved)) {
            return saved;
        }

        // 2. Detectar del navegador
        const browserLang = navigator.language.split('-')[0];
        if (SUPPORTED_LANGS.includes(browserLang)) {
            return browserLang;
        }

        return DEFAULT_LANG;
    }

    // Cargar archivo de traducciones
    async function loadTranslations(lang) {
        try {
            // Usar ruta relativa simple
            const response = await fetch(`/js/i18n/${lang}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load ${lang}.json: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error loading translations for ${lang}:`, error);
            // Fallback al idioma por defecto
            if (lang !== DEFAULT_LANG) {
                console.log(`Trying fallback to ${DEFAULT_LANG}...`);
                return loadTranslations(DEFAULT_LANG);
            }
            // Devolver objeto vacío para que la app no se bloquee
            console.warn('Using empty translations - app will show translation keys');
            return {};
        }
    }

    // Inicializar sistema i18n
    async function init() {
        try {
            currentLang = detectLanguage();
            translations = await loadTranslations(currentLang);
            isLoaded = true;
            translatePage();
            updateLangSelector();
            console.log(`I18n initialized with language: ${currentLang}`);
            return currentLang;
        } catch (error) {
            console.error('Error initializing i18n:', error);
            isLoaded = true; // Marcar como cargado para que t() funcione
            return DEFAULT_LANG;
        }
    }

    // Obtener traducción con soporte de variables
    // Uso: t('auth.welcomeUser', { name: 'Juan' })
    function t(key, params = {}) {
        if (!isLoaded) {
            console.warn('I18n not loaded yet');
            return key;
        }

        // Navegar por la clave con notación de punto
        const keys = key.split('.');
        let value = translations;

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                console.warn(`Translation key not found: ${key}`);
                return key; // Devolver la clave si no existe
            }
        }

        if (typeof value !== 'string') {
            console.warn(`Translation value is not a string: ${key}`);
            return key;
        }

        // Reemplazar variables {variable}
        return value.replace(/\{(\w+)\}/g, (match, varName) => {
            return params[varName] !== undefined ? params[varName] : match;
        });
    }

    // Cambiar idioma
    async function setLanguage(lang) {
        if (!SUPPORTED_LANGS.includes(lang)) {
            console.error(`Unsupported language: ${lang}`);
            return false;
        }

        if (lang === currentLang) return true;

        translations = await loadTranslations(lang);
        currentLang = lang;
        localStorage.setItem(STORAGE_KEY, lang);

        translatePage();
        updateLangSelector();

        // Disparar evento personalizado
        document.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: lang }
        }));

        return true;
    }

    // Traducir elementos HTML con data-i18n
    function translatePage() {
        // Textos de elementos
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = t(key);
        });

        // Placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = t(key);
        });

        // Títulos (title attribute)
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = t(key);
        });

        // Actualizar atributo lang del HTML
        document.documentElement.lang = currentLang;
    }

    // Actualizar selector de idioma
    function updateLangSelector() {
        const selectors = document.querySelectorAll('#lang-selector, .lang-selector-input');
        selectors.forEach(selector => {
            if (selector) {
                selector.value = currentLang;
            }
        });
    }

    // Obtener idioma actual
    function getCurrentLanguage() {
        return currentLang;
    }

    // Obtener idiomas soportados
    function getSupportedLanguages() {
        return [...SUPPORTED_LANGS];
    }

    // Verificar si está cargado
    function isReady() {
        return isLoaded;
    }

    // API pública
    return {
        init,
        t,
        setLanguage,
        translatePage,
        getCurrentLanguage,
        getSupportedLanguages,
        isReady,
        // Exponer currentLang como propiedad de solo lectura
        get currentLang() {
            return currentLang;
        }
    };
})();

// Exponer globalmente
window.I18n = I18n;
window.t = I18n.t; // Atajo para traducciones
