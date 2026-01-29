// ========== MASTERPAGE COMPONENT ==========
// Sistema unificado de sidebar y header para todas las páginas

const MasterPage = {
    // Configuración por defecto
    config: {
        title: 'JobStocks',
        subtitle: 'Stock a tiempo real',
        showBackButton: false
    },

    // HTML del Header
    getHeaderHTML: function() {
        return `
        <header class="master-header">
            <div class="header-left">
                <button class="hamburger-btn" onclick="openSidebar()" title="Abrir menú">☰</button>
                <button class="sidebar-toggle-btn" onclick="toggleSidebar()" title="Toggle menú">☰</button>
                <img src="" alt="Logo" class="header-logo logo" id="header-logo">
                <div class="header-titles">
                    <h1 class="header-title">JobStocks</h1>
                    <span class="header-subtitle">Stock a tiempo real</span>
                </div>
            </div>
            <div class="header-right">
                <span class="header-company" id="header-company-name"></span>
            </div>
        </header>`;
    },

    // HTML del Sidebar
    getSidebarHTML: function() {
        return `
    <aside class="master-sidebar" id="master-sidebar">
        <div class="sidebar-user">
            <div class="sidebar-user-name" id="sidebar-user-name">Usuario</div>
            <div class="sidebar-user-role" id="sidebar-user-role">usuario</div>
        </div>

        <nav class="sidebar-nav">
            <!-- Grupo: Productos -->
            <div class="accordion-group expanded" data-accordion="products">
                <button class="accordion-header" onclick="toggleAccordion(this)">
                    <span class="accordion-icon">📦</span>
                    <span class="accordion-title" data-i18n="sidebar.products">Productos</span>
                    <span class="accordion-arrow">▼</span>
                </button>
                <div class="accordion-content">
                    <a href="index.html" class="sidebar-link" data-page="index"><span class="link-icon">📊</span> <span data-i18n="sidebar.stocks">Stocks</span></a>
                </div>
            </div>

            <!-- Grupo: Propuestas -->
            <div class="accordion-group" data-accordion="proposals">
                <button class="accordion-header" onclick="toggleAccordion(this)">
                    <span class="accordion-icon">📋</span>
                    <span class="accordion-title" data-i18n="sidebar.proposals">Propuestas</span>
                    <span class="accordion-arrow">▼</span>
                </button>
                <div class="accordion-content">
                    <a href="mis-propuestas.html" class="sidebar-link" data-page="mis-propuestas"><span class="link-icon">📝</span> <span data-i18n="sidebar.myProposals">Mis Propuestas</span></a>
                </div>
            </div>

            <!-- Grupo: Administración (solo admin) -->
            <div class="accordion-group" data-accordion="admin" id="sidebar-admin-section" style="display: none;">
                <button class="accordion-header" onclick="toggleAccordion(this)">
                    <span class="accordion-icon">⚙️</span>
                    <span class="accordion-title" data-i18n="sidebar.admin">Administración</span>
                    <span class="accordion-arrow">▼</span>
                </button>
                <div class="accordion-content">
                    <a href="dashboard.html" class="sidebar-link" data-page="dashboard"><span class="link-icon">📈</span> <span data-i18n="sidebar.dashboard">Dashboard</span></a>
                    <a href="todas-propuestas.html" class="sidebar-link" data-page="todas-propuestas"><span class="link-icon">📑</span> <span data-i18n="sidebar.allProposals">Todas las Propuestas</span></a>
                    <a href="todas-consultas.html" class="sidebar-link" data-page="todas-consultas"><span class="link-icon">💬</span> <span data-i18n="sidebar.inquiries">Consultas</span></a>
                    <a href="usuarios.html" class="sidebar-link" data-page="usuarios"><span class="link-icon">👥</span> <span data-i18n="sidebar.users">Usuarios</span></a>
                    <a href="email-config.html" class="sidebar-link" data-page="email-config"><span class="link-icon">📧</span> <span data-i18n="sidebar.emailConfig">Configuración Email</span></a>
                    <a href="parametros.html" class="sidebar-link" data-page="parametros"><span class="link-icon">🔧</span> <span data-i18n="sidebar.parameters">Parámetros</span></a>
                    <a href="empresa-logo.html" class="sidebar-link" data-page="empresa-logo"><span class="link-icon">🏢</span> <span data-i18n="sidebar.companyLogo">Logo Empresa</span></a>
                </div>
            </div>

            <!-- Grupo: Apariencia -->
            <div class="accordion-group" data-accordion="appearance">
                <button class="accordion-header" onclick="toggleAccordion(this)">
                    <span class="accordion-icon">🎨</span>
                    <span class="accordion-title" data-i18n="sidebar.appearance">Apariencia</span>
                    <span class="accordion-arrow">▼</span>
                </button>
                <div class="accordion-content">
                    <div class="sidebar-setting">
                        <span data-i18n="sidebar.darkMode">Modo Oscuro</span>
                        <label class="switch">
                            <input type="checkbox" id="sidebar-theme-switch" onchange="toggleTheme()">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="sidebar-setting">
                        <span data-i18n="sidebar.language">Idioma</span>
                        <select id="sidebar-lang-selector" onchange="I18n.setLanguage(this.value)">
                            <option value="es">ES</option>
                            <option value="en">EN</option>
                            <option value="fr">FR</option>
                        </select>
                    </div>
                </div>
            </div>
        </nav>

        <div class="sidebar-footer">
            <button class="sidebar-logout" onclick="logout()">
                <span>🚪</span>
                <span data-i18n="sidebar.logout">Cerrar Sesión</span>
            </button>
        </div>
    </aside>

    <!-- Overlay móvil -->
    <div class="sidebar-overlay" id="sidebar-overlay" onclick="closeSidebar()"></div>`;
    },

    // Inicializar masterpage
    init: function(pageId) {
        // Buscar el contenedor del masterpage
        const container = document.getElementById('masterpage-container');
        if (!container) {
            console.error('MasterPage: No se encontró #masterpage-container');
            return;
        }

        // Obtener el contenido original de la página
        const pageContent = container.innerHTML;

        // Construir la estructura completa
        container.innerHTML = `
            ${this.getSidebarHTML()}
            <div class="master-main" id="master-main">
                ${this.getHeaderHTML()}
                <main class="master-content">
                    ${pageContent}
                </main>
            </div>
        `;

        // Marcar el link activo en el sidebar
        if (pageId) {
            const activeLink = document.querySelector(`[data-page="${pageId}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
                // Expandir el grupo del acordeón padre
                const accordionGroup = activeLink.closest('.accordion-group');
                if (accordionGroup) {
                    accordionGroup.classList.add('expanded');
                }
            }
        }

        // Inicializar estado del sidebar desde localStorage
        this.initSidebarState();
    },

    // Inicializar estado del sidebar
    initSidebarState: function() {
        const sidebarVisible = localStorage.getItem('sidebarVisible');
        if (sidebarVisible === 'false' && window.innerWidth > 768) {
            const sidebar = document.getElementById('master-sidebar');
            const main = document.getElementById('master-main');
            if (sidebar) sidebar.classList.add('hidden');
            if (main) main.classList.add('sidebar-hidden');
        }
    }
};

// ========== FUNCIONES GLOBALES DEL SIDEBAR ==========

function toggleAccordion(element) {
    var group = element;
    while (group && !group.classList.contains('accordion-group')) {
        group = group.parentElement;
    }
    if (group) {
        group.classList.toggle('expanded');
    }
}

function toggleSidebar() {
    var sidebar = document.getElementById('master-sidebar');
    var main = document.getElementById('master-main');
    if (!sidebar || !main) return;

    if (window.innerWidth <= 768) {
        closeSidebar();
        return;
    }

    if (sidebar.classList.contains('hidden')) {
        sidebar.classList.remove('hidden');
        main.classList.remove('sidebar-hidden');
        localStorage.setItem('sidebarVisible', 'true');
    } else {
        sidebar.classList.add('hidden');
        main.classList.add('sidebar-hidden');
        localStorage.setItem('sidebarVisible', 'false');
    }
}

function openSidebar() {
    var sidebar = document.getElementById('master-sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.add('mobile-open');
    if (overlay) overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeSidebar() {
    var sidebar = document.getElementById('master-sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    if (sidebar) {
        sidebar.classList.remove('mobile-open');
        sidebar.classList.remove('hidden');
    }
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
}

// Exponer MasterPage globalmente
window.MasterPage = MasterPage;
window.toggleAccordion = toggleAccordion;
window.toggleSidebar = toggleSidebar;
window.openSidebar = openSidebar;
window.closeSidebar = closeSidebar;
