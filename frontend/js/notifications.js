/**
 * Notifications Module
 * Sistema de notificaciones con polling adaptativo.
 * - Empieza en 30s, sube a 60s/120s si no hay cambios
 * - Pausa cuando la pestaña no está visible
 * - Fetch inmediato al volver a ser visible
 * Expone window.Notifications.
 */
(function() {
    'use strict';

    let pollInterval = null;
    let lastCount = 0;
    let csrfToken = null;
    let currentDelay = 30000;       // Empieza en 30s
    let unchangedCycles = 0;        // Ciclos sin cambios

    const MIN_DELAY = 30000;        // 30s mínimo
    const MAX_DELAY = 120000;       // 2min máximo
    const BACKOFF_AFTER = 3;        // Tras 3 ciclos sin cambios, aumentar

    function getApiUrl() {
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return `${protocol}//${hostname}:5000`;
        }
        return `${protocol}//${hostname}${port ? ':' + port : ''}`;
    }

    /**
     * Inicializar sistema de notificaciones.
     * Fetch inmediato + polling adaptativo + visibilitychange.
     */
    function init() {
        csrfToken = localStorage.getItem('csrf_token');
        fetchCount();
        scheduleNext();

        // Pausar/reanudar según visibilidad de pestaña
        document.addEventListener('visibilitychange', onVisibilityChange);
    }

    function onVisibilityChange() {
        if (document.hidden) {
            // Pestaña oculta: parar polling
            clearTimeout(pollInterval);
            pollInterval = null;
        } else {
            // Pestaña visible: fetch inmediato y reanudar con delay mínimo
            currentDelay = MIN_DELAY;
            unchangedCycles = 0;
            fetchCount();
            scheduleNext();
        }
    }

    function scheduleNext() {
        clearTimeout(pollInterval);
        pollInterval = setTimeout(function pollTick() {
            fetchCount();
            pollInterval = setTimeout(pollTick, currentDelay);
        }, currentDelay);
    }

    /**
     * Obtener conteo de notificaciones no leídas.
     */
    async function fetchCount() {
        try {
            const response = await fetch(`${getApiUrl()}/api/notifications/unread-count`, {
                credentials: 'include'
            });

            if (!response.ok) return;

            const data = await response.json();
            if (!data.success) return;

            const newCount = data.count || 0;
            updateBadges(newCount);

            // Si el conteo aumentó, mostrar toast y resetear backoff
            if (newCount > lastCount && lastCount >= 0) {
                const diff = newCount - lastCount;
                if (lastCount > 0) {
                    showToast(diff);
                }
                // Hay actividad: volver a intervalo mínimo
                currentDelay = MIN_DELAY;
                unchangedCycles = 0;
            } else {
                // Sin cambios: incrementar backoff
                unchangedCycles++;
                if (unchangedCycles >= BACKOFF_AFTER && currentDelay < MAX_DELAY) {
                    currentDelay = Math.min(currentDelay * 2, MAX_DELAY);
                }
            }

            lastCount = newCount;
        } catch (e) {
            // Silenciar errores de polling; aumentar delay para no saturar
            unchangedCycles++;
            if (currentDelay < MAX_DELAY) {
                currentDelay = Math.min(currentDelay * 2, MAX_DELAY);
            }
        }
    }

    /**
     * Actualizar todos los badges de campana en la página.
     */
    function updateBadges(count) {
        const badges = document.querySelectorAll('.notification-badge');
        badges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        });
    }

    /**
     * Mostrar toast flotante de nuevas notificaciones.
     */
    function showToast(count) {
        // Eliminar toast previo si existe
        const existing = document.querySelector('.notification-toast');
        if (existing) existing.remove();

        const t = window.t || (k => k);
        const msg = count === 1
            ? (t('notifications.newNotification') || 'Nueva notificacion')
            : `${count} ${t('notifications.newNotifications') || 'nuevas notificaciones'}`;

        const toast = document.createElement('div');
        toast.className = 'notification-toast';
        toast.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span>${msg}</span>
        `;
        document.body.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('notification-toast-show');
        });

        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            toast.classList.remove('notification-toast-show');
            toast.classList.add('notification-toast-hide');
            setTimeout(() => toast.remove(), 400);
        }, 5000);
    }

    /**
     * Obtener lista completa de notificaciones y mostrar dropdown.
     */
    async function showDropdown() {
        try {
            const response = await fetch(`${getApiUrl()}/api/notifications`, {
                credentials: 'include'
            });

            if (!response.ok) return;

            const data = await response.json();
            if (!data.success) return;

            renderDropdown(data.notifications || []);
        } catch (e) {
            console.error('Error fetching notifications:', e);
        }
    }

    /**
     * Renderizar dropdown de notificaciones.
     */
    function renderDropdown(notifications) {
        // Eliminar dropdown previo
        const existing = document.querySelector('.notification-dropdown');
        if (existing) {
            existing.remove();
            return; // Toggle: si ya estaba abierto, lo cierra
        }

        const t = window.t || (k => k);
        const bellBtn = document.querySelector('.bell-btn');
        if (!bellBtn) return;

        const dropdown = document.createElement('div');
        dropdown.className = 'notification-dropdown';

        let html = `<div class="notification-dropdown-header">
            <span>${t('notifications.title') || 'Notificaciones'}</span>`;
        if (notifications.length > 0) {
            html += `<button class="notification-mark-all" onclick="Notifications.markAllAsRead()">${t('notifications.markAllRead') || 'Marcar todas como leidas'}</button>`;
        }
        html += `</div><div class="notification-dropdown-body">`;

        if (notifications.length === 0) {
            html += `<div class="notification-empty">${t('notifications.noNotifications') || 'Sin notificaciones'}</div>`;
        } else {
            notifications.forEach(n => {
                const timeAgo = formatTimeAgo(n.fecha_creacion);
                const icon = getNotificationIcon(n.tipo);
                html += `<div class="notification-item" data-id="${n.id}" onclick="Notifications.markAsRead(${n.id}, this)">
                    <div class="notification-item-icon">${icon}</div>
                    <div class="notification-item-content">
                        <div class="notification-item-title">${escapeHtml(n.titulo)}</div>
                        ${n.mensaje ? `<div class="notification-item-message">${escapeHtml(n.mensaje)}</div>` : ''}
                        <div class="notification-item-time">${timeAgo}</div>
                    </div>
                </div>`;
            });
        }

        html += `</div>`;
        dropdown.innerHTML = html;
        bellBtn.parentElement.appendChild(dropdown);

        // Cerrar al hacer clic fuera
        setTimeout(() => {
            document.addEventListener('click', closeDropdownOutside);
        }, 100);
    }

    function closeDropdownOutside(e) {
        const dropdown = document.querySelector('.notification-dropdown');
        const bellBtn = document.querySelector('.bell-btn');
        if (dropdown && !dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
            dropdown.remove();
            document.removeEventListener('click', closeDropdownOutside);
        }
    }

    function getNotificationIcon(tipo) {
        switch (tipo) {
            case 'propuesta_cambio_estado': return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>';
            case 'consulta_respondida': return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
            case 'nueva_propuesta': return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FF9800" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>';
            default: return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
        }
    }

    function formatTimeAgo(isoDate) {
        if (!isoDate) return '';
        const date = new Date(isoDate);
        const now = new Date();
        const diffMs = now - date;
        const diffMin = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMin < 1) return 'Ahora';
        if (diffMin < 60) return `${diffMin}m`;
        if (diffHours < 24) return `${diffHours}h`;
        return `${diffDays}d`;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Marcar una notificación como leída.
     */
    async function markAsRead(id, element) {
        try {
            csrfToken = csrfToken || localStorage.getItem('csrf_token');
            const response = await fetch(`${getApiUrl()}/api/notifications/${id}/read`, {
                method: 'PUT',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken || ''
                }
            });

            if (response.ok) {
                if (element) {
                    element.style.opacity = '0.5';
                    setTimeout(() => element.remove(), 300);
                }
                fetchCount();
            }
        } catch (e) {
            console.error('Error marking notification as read:', e);
        }
    }

    /**
     * Marcar todas como leídas.
     */
    async function markAllAsRead() {
        try {
            csrfToken = csrfToken || localStorage.getItem('csrf_token');
            const response = await fetch(`${getApiUrl()}/api/notifications/read-all`, {
                method: 'PUT',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken || ''
                }
            });

            if (response.ok) {
                const dropdown = document.querySelector('.notification-dropdown');
                if (dropdown) dropdown.remove();
                fetchCount();
            }
        } catch (e) {
            console.error('Error marking all as read:', e);
        }
    }

    /**
     * Detener polling y limpiar listeners.
     */
    function stopPolling() {
        if (pollInterval) {
            clearTimeout(pollInterval);
            pollInterval = null;
        }
        document.removeEventListener('visibilitychange', onVisibilityChange);
    }

    // Exponer API pública
    window.Notifications = {
        init,
        fetchCount,
        showDropdown,
        markAsRead,
        markAllAsRead,
        stopPolling
    };
})();
