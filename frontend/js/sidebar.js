// sidebar.js - Control del sidebar colapsable

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
        if (!sidebar) return;

        sidebar.classList.toggle('mobile-open');
    }

    /**
     * Cerrar sidebar en móvil
     */
    function closeMobile() {
        if (!sidebar) return;

        sidebar.classList.remove('mobile-open');
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
