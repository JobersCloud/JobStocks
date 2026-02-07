// sidebar.js - Control del sidebar colapsable

// Función global para toggle móvil (disponible inmediatamente)
window.toggleSidebarMobile = function() {
    var sidebar = document.querySelector('.sidebar');
    var overlay = document.querySelector('.sidebar-overlay');
    var mobileMenu = document.getElementById('mobile-menu-panel');

    if (!sidebar) return;

    // Verificar si está abierto por la existencia del panel
    var isOpen = mobileMenu !== null;

    if (isOpen) {
        // Cerrar
        mobileMenu.remove();
        if (overlay) overlay.style.display = '';
    } else {
        // Cerrar menú de usuario si está abierto
        var userDropdown = document.getElementById('menu-dropdown');
        if (userDropdown) userDropdown.classList.remove('show');
        // Abrir - crear menú móvil clonando el sidebar
        mobileMenu = sidebar.cloneNode(true);
        mobileMenu.id = 'mobile-menu-panel';
        mobileMenu.className = 'sidebar mobile-open';
        mobileMenu.style.cssText = 'position: fixed !important; left: 0 !important; top: 70px !important; bottom: 0 !important; width: 240px !important; min-width: 240px !important; z-index: 99999 !important; display: flex !important; flex-direction: column !important; transform: none !important; visibility: visible !important; opacity: 1 !important;';

        // Mostrar todos los textos y secciones
        var allTexts = mobileMenu.querySelectorAll('.sidebar-item-text, .sidebar-section-title, .sidebar-accordion-title span, .sidebar-accordion-arrow');
        allTexts.forEach(function(el) {
            el.style.cssText = 'opacity: 1 !important; width: auto !important; display: inline !important; overflow: visible !important;';
        });

        var allItems = mobileMenu.querySelectorAll('.sidebar-item');
        allItems.forEach(function(el) {
            el.style.cssText = 'justify-content: flex-start !important; padding: 12px 14px !important;';
        });

        // Mostrar secciones de admin si estaban visibles
        var adminSections = mobileMenu.querySelectorAll('.sidebar-accordion, .sidebar-section');
        adminSections.forEach(function(el) {
            if (el.style.display !== 'none') {
                el.style.display = 'block';
            }
        });

        // Ocultar el toggle (no se necesita en móvil)
        var toggleContainer = mobileMenu.querySelector('.sidebar-toggle-container');
        if (toggleContainer) toggleContainer.style.display = 'none';

        document.body.appendChild(mobileMenu);
        if (overlay) {
            overlay.style.display = 'block';
            overlay.onclick = function() { toggleSidebarMobile(); };
        }
    }
};

// Limpiar estilos móviles al cambiar a desktop
window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
        var sidebar = document.querySelector('.sidebar');
        var overlay = document.querySelector('.sidebar-overlay');
        if (sidebar) {
            sidebar.classList.remove('mobile-open');
            sidebar.style.cssText = '';
        }
        if (overlay) overlay.style.display = '';
    }
});

(function() {
    'use strict';

    // Configuración
    const STORAGE_KEY = 'sidebar_collapsed';

    // Elementos del DOM
    let sidebar = null;
    let toggleBtn = null;
    let overlay = null;
    let mobileMenuBtn = null;

    /**
     * Inicializa el sidebar
     */
    function init() {
        sidebar = document.querySelector('.sidebar');
        toggleBtn = document.querySelector('.sidebar-toggle');
        overlay = document.querySelector('.sidebar-overlay');
        mobileMenuBtn = document.querySelector('.mobile-menu-btn');

        if (!sidebar) return;

        // Restaurar estado guardado
        restoreState();

        // Event listeners
        if (toggleBtn) {
            toggleBtn.addEventListener('click', toggle);
        }

        if (overlay) {
            overlay.addEventListener('click', closeMobile);
        }

        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', toggleMobile);
        }

        // Marcar página activa
        markActivePage();

        // Keyboard shortcut: Ctrl+B para toggle
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                toggle();
            }
        });

        // Limpiar estilos móviles al cambiar tamaño de ventana
        window.addEventListener('resize', handleResize);
    }

    /**
     * Toggle del sidebar (expandir/colapsar)
     */
    function toggle() {
        if (!sidebar) return;

        sidebar.classList.toggle('collapsed');
        saveState();
    }

    /**
     * Toggle para móvil
     */
    function toggleMobile() {
        if (!sidebar) {
            sidebar = document.querySelector('.sidebar');
        }
        if (!overlay) {
            overlay = document.querySelector('.sidebar-overlay');
        }
        if (!sidebar) return;

        // Solo funciona en móvil
        if (window.innerWidth > 768) return;

        const isOpen = sidebar.classList.contains('mobile-open');

        if (isOpen) {
            sidebar.classList.remove('mobile-open');
            sidebar.style.transform = '';
            sidebar.style.zIndex = '';
            if (overlay) overlay.style.display = '';
        } else {
            sidebar.classList.add('mobile-open');
            sidebar.style.transform = 'translateX(0)';
            sidebar.style.zIndex = '9999';
            if (overlay) overlay.style.display = 'block';
        }
    }

    /**
     * Cerrar sidebar en móvil
     */
    function closeMobile() {
        if (!sidebar) {
            sidebar = document.querySelector('.sidebar');
        }
        if (!overlay) {
            overlay = document.querySelector('.sidebar-overlay');
        }
        if (!sidebar) return;

        sidebar.classList.remove('mobile-open');
        sidebar.style.transform = '';
        sidebar.style.zIndex = '';
        if (overlay) overlay.style.display = '';
    }

    /**
     * Limpiar estilos móviles al cambiar a desktop
     */
    function handleResize() {
        if (window.innerWidth > 768 && sidebar) {
            sidebar.classList.remove('mobile-open');
            sidebar.style.transform = '';
            sidebar.style.zIndex = '';
            if (overlay) overlay.style.display = '';
        }
    }

    /**
     * Guardar estado en localStorage
     */
    function saveState() {
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem(STORAGE_KEY, isCollapsed ? 'true' : 'false');
    }

    /**
     * Restaurar estado desde localStorage
     */
    function restoreState() {
        const savedState = localStorage.getItem(STORAGE_KEY);

        // Solo restaurar en desktop
        if (window.innerWidth > 1024) {
            if (savedState === 'true') {
                sidebar.classList.add('collapsed');
            } else {
                sidebar.classList.remove('collapsed');
            }
        }
    }

    /**
     * Marcar la página actual como activa en el menú
     */
    function markActivePage() {
        const currentPath = window.location.pathname;
        const currentPage = currentPath.split('/').pop() || 'index.html';

        const menuItems = document.querySelectorAll('.sidebar-item[data-page]');

        menuItems.forEach(item => {
            const page = item.getAttribute('data-page');
            if (page === currentPage || (currentPage === '' && page === 'index.html')) {
                item.classList.add('active');
                // Expandir el acordeón padre si existe
                const accordion = item.closest('.sidebar-accordion');
                if (accordion) {
                    accordion.classList.add('expanded');
                }
            } else {
                item.classList.remove('active');
            }
        });
    }

    /**
     * Navegar a una página manteniendo empresa_id
     */
    function navigateTo(page) {
        const empresaId = localStorage.getItem('empresa_id');
        let url = page;

        if (empresaId && !page.includes('login')) {
            url = `${page}?empresa=${empresaId}`;
        }

        window.location.href = url;
    }

    // Exponer funciones globales
    window.SidebarNav = {
        init: init,
        toggle: toggle,
        toggleMobile: toggleMobile,
        closeMobile: closeMobile,
        navigateTo: navigateTo
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
