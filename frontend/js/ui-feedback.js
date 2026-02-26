// ============================================================
// ui-feedback.js - Sistema de notificaciones toast y modales confirm/alert
// Reemplaza alert() y confirm() nativos del navegador
// ============================================================

(function () {
    'use strict';

    // ==================== TOAST ====================
    let toastContainer = null;

    function ensureToastContainer() {
        if (!toastContainer || !document.body.contains(toastContainer)) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'ui-toast-container';
            document.body.appendChild(toastContainer);
        }
        return toastContainer;
    }

    const TOAST_ICONS = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };

    /**
     * Mostrar toast notification
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - 'success' | 'error' | 'warning' | 'info'
     * @param {number} duration - Duracion en ms (default 3000, errors 5000)
     */
    function toast(message, type, duration) {
        type = type || 'info';
        duration = duration || (type === 'error' ? 5000 : 3000);
        var container = ensureToastContainer();

        var el = document.createElement('div');
        el.className = 'ui-toast ui-toast-' + type;
        el.innerHTML =
            '<span class="ui-toast-icon">' + (TOAST_ICONS[type] || TOAST_ICONS.info) + '</span>' +
            '<span class="ui-toast-message">' + escapeHtml(message) + '</span>' +
            '<button class="ui-toast-close" aria-label="Cerrar">&times;</button>';

        el.querySelector('.ui-toast-close').addEventListener('click', function () {
            dismissToast(el);
        });

        container.appendChild(el);

        // Trigger entrance animation
        requestAnimationFrame(function () {
            el.classList.add('ui-toast-show');
        });

        // Auto dismiss
        var timer = setTimeout(function () { dismissToast(el); }, duration);
        el._timer = timer;

        return el;
    }

    function dismissToast(el) {
        if (el._dismissed) return;
        el._dismissed = true;
        clearTimeout(el._timer);
        el.classList.remove('ui-toast-show');
        el.classList.add('ui-toast-hide');
        el.addEventListener('animationend', function () {
            if (el.parentNode) el.parentNode.removeChild(el);
        });
        // Fallback removal
        setTimeout(function () {
            if (el.parentNode) el.parentNode.removeChild(el);
        }, 400);
    }

    // ==================== CONFIRM MODAL ====================

    /**
     * Mostrar modal de confirmacion (reemplaza confirm())
     * @param {Object} opts - Opciones
     * @param {string} opts.title - Titulo del modal
     * @param {string} opts.message - Mensaje
     * @param {string} opts.confirmText - Texto boton confirmar
     * @param {string} opts.cancelText - Texto boton cancelar
     * @param {string} opts.type - 'danger' | 'warning' | 'info'
     * @returns {Promise<boolean>}
     */
    function _t(key, fallback) {
        if (typeof t === 'function') {
            var val = t(key);
            if (val && val !== key) return val;
        }
        return fallback;
    }

    function confirm(opts) {
        opts = opts || {};
        var type = opts.type || 'warning';
        var title = opts.title || _t('uiFeedback.confirm', 'Confirmar');
        var message = opts.message || '';
        var confirmText = opts.confirmText || (type === 'danger' ? _t('uiFeedback.delete', 'Eliminar') : _t('uiFeedback.confirm', 'Confirmar'));
        var cancelText = opts.cancelText || _t('uiFeedback.cancel', 'Cancelar');

        return new Promise(function (resolve) {
            var overlay = createModalOverlay();
            var modal = document.createElement('div');
            modal.className = 'ui-modal ui-modal-' + type;
            modal.innerHTML =
                '<div class="ui-modal-header">' +
                    '<h3 class="ui-modal-title">' + escapeHtml(title) + '</h3>' +
                '</div>' +
                '<div class="ui-modal-body">' +
                    '<p>' + escapeHtml(message) + '</p>' +
                '</div>' +
                '<div class="ui-modal-footer">' +
                    '<button class="ui-modal-btn ui-modal-btn-cancel">' + escapeHtml(cancelText) + '</button>' +
                    '<button class="ui-modal-btn ui-modal-btn-confirm ui-modal-btn-' + type + '">' + escapeHtml(confirmText) + '</button>' +
                '</div>';

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            requestAnimationFrame(function () {
                overlay.classList.add('ui-modal-overlay-show');
                modal.classList.add('ui-modal-show');
            });

            var btnConfirm = modal.querySelector('.ui-modal-btn-confirm');
            var btnCancel = modal.querySelector('.ui-modal-btn-cancel');

            function close(result) {
                overlay.classList.remove('ui-modal-overlay-show');
                modal.classList.remove('ui-modal-show');
                setTimeout(function () {
                    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
                }, 200);
                resolve(result);
            }

            btnConfirm.addEventListener('click', function () { close(true); });
            btnCancel.addEventListener('click', function () { close(false); });
            overlay.addEventListener('click', function (e) {
                if (e.target === overlay) close(false);
            });

            // Escape key
            function onKey(e) {
                if (e.key === 'Escape') {
                    document.removeEventListener('keydown', onKey);
                    close(false);
                }
            }
            document.addEventListener('keydown', onKey);

            // Focus confirm button
            btnConfirm.focus();
        });
    }

    // ==================== ALERT MODAL ====================

    /**
     * Mostrar modal de alerta (reemplaza alert())
     * @param {Object|string} opts - Opciones o mensaje string
     * @param {string} opts.title - Titulo
     * @param {string} opts.message - Mensaje
     * @param {string} opts.type - 'success' | 'error' | 'warning' | 'info'
     * @returns {Promise<void>}
     */
    function alertModal(opts) {
        if (typeof opts === 'string') {
            opts = { message: opts, type: 'info' };
        }
        opts = opts || {};
        var type = opts.type || 'info';
        var title = opts.title || '';
        var message = opts.message || '';
        var acceptText = opts.acceptText || _t('uiFeedback.accept', 'Aceptar');

        return new Promise(function (resolve) {
            var overlay = createModalOverlay();
            var modal = document.createElement('div');
            modal.className = 'ui-modal ui-modal-alert ui-modal-' + type;
            modal.innerHTML =
                (title ? '<div class="ui-modal-header"><h3 class="ui-modal-title">' + escapeHtml(title) + '</h3></div>' : '') +
                '<div class="ui-modal-body">' +
                    '<p>' + escapeHtml(message) + '</p>' +
                '</div>' +
                '<div class="ui-modal-footer">' +
                    '<button class="ui-modal-btn ui-modal-btn-confirm ui-modal-btn-' + type + '">' + escapeHtml(acceptText) + '</button>' +
                '</div>';

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            requestAnimationFrame(function () {
                overlay.classList.add('ui-modal-overlay-show');
                modal.classList.add('ui-modal-show');
            });

            var btn = modal.querySelector('.ui-modal-btn-confirm');

            function close() {
                overlay.classList.remove('ui-modal-overlay-show');
                modal.classList.remove('ui-modal-show');
                setTimeout(function () {
                    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
                }, 200);
                resolve();
            }

            btn.addEventListener('click', close);
            overlay.addEventListener('click', function (e) {
                if (e.target === overlay) close();
            });

            function onKey(e) {
                if (e.key === 'Escape' || e.key === 'Enter') {
                    document.removeEventListener('keydown', onKey);
                    close();
                }
            }
            document.addEventListener('keydown', onKey);

            btn.focus();
        });
    }

    // ==================== HELPERS ====================

    function createModalOverlay() {
        var overlay = document.createElement('div');
        overlay.className = 'ui-modal-overlay';
        return overlay;
    }

    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ==================== API PUBLICA ====================
    window.UIFeedback = {
        toast: toast,
        confirm: confirm,
        alert: alertModal
    };

})();
