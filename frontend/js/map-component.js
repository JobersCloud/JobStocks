// ============================================================
// map-component.js - Componente de mapa reutilizable
// Usa Leaflet + OpenStreetMap + Nominatim para geocoding
// ============================================================

(function() {
    'use strict';

    /**
     * MapComponent - Muestra un mapa con un marcador en una direccion
     *
     * Uso:
     *   const map = new MapComponent({ el: '#map-container' });
     *   map.showAddress('Calle Mayor 1, Castellon, Espana');
     *   map.showModal('Calle Mayor 1, Castellon', 'Cliente ABC');
     */
    class MapComponent {
        constructor(config = {}) {
            this.el = config.el || null;
            this.map = null;
            this.marker = null;
            this.defaultZoom = config.zoom || 15;
            this.defaultCenter = config.center || [39.98, -0.05]; // Castellon por defecto
            this.modalId = 'map-modal-' + Date.now();
            this._createModal();
        }

        /**
         * Crea el modal para mostrar el mapa
         */
        _createModal() {
            if (document.getElementById(this.modalId)) return;

            const modal = document.createElement('div');
            modal.id = this.modalId;
            modal.className = 'modal-overlay';
            modal.style.display = 'none';
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 700px; height: 80vh; display: flex; flex-direction: column;">
                    <div class="modal-header">
                        <h2 id="${this.modalId}-title" style="font-size: 1rem; margin: 0;"></h2>
                        <button class="modal-close" onclick="document.getElementById('${this.modalId}').style.display='none'">&times;</button>
                    </div>
                    <div id="${this.modalId}-address" style="padding: 8px 16px; font-size: 0.85rem; color: var(--text-secondary, #666); border-bottom: 1px solid var(--border-color, #eee);"></div>
                    <div id="${this.modalId}-map" style="flex: 1; min-height: 300px;"></div>
                    <div id="${this.modalId}-error" style="display: none; padding: 20px; text-align: center; color: var(--text-secondary, #999);">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 10px;">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                            <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                        <p id="${this.modalId}-error-text"></p>
                    </div>
                </div>
            `;

            // Cerrar al hacer clic fuera
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.hideModal();
            });

            document.body.appendChild(modal);
        }

        /**
         * Muestra el modal con el mapa de una direccion
         * @param {string} address - Direccion a geocodificar
         * @param {string} title - Titulo del modal
         */
        async showModal(address, title) {
            const modal = document.getElementById(this.modalId);
            const titleEl = document.getElementById(this.modalId + '-title');
            const addressEl = document.getElementById(this.modalId + '-address');
            const mapEl = document.getElementById(this.modalId + '-map');
            const errorEl = document.getElementById(this.modalId + '-error');

            titleEl.textContent = title || 'Ubicacion';
            addressEl.textContent = address;
            mapEl.style.display = 'block';
            errorEl.style.display = 'none';
            modal.style.display = 'flex';

            // Inicializar mapa tras mostrar modal (Leaflet requiere contenedor visible)
            await this._delay(100);

            if (!this.map) {
                this.map = L.map(mapEl).setView(this.defaultCenter, this.defaultZoom);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                    maxZoom: 19
                }).addTo(this.map);
            }

            this.map.invalidateSize();

            // Geocodificar la direccion
            try {
                const coords = await this._geocode(address);
                if (coords) {
                    this.map.setView(coords, this.defaultZoom);
                    if (this.marker) this.map.removeLayer(this.marker);
                    this.marker = L.marker(coords).addTo(this.map);
                    this.marker.bindPopup(`<strong>${title || ''}</strong><br>${address}`).openPopup();
                } else {
                    mapEl.style.display = 'none';
                    errorEl.style.display = 'block';
                    document.getElementById(this.modalId + '-error-text').textContent =
                        'No se pudo encontrar la ubicacion para esta direccion';
                }
            } catch (e) {
                mapEl.style.display = 'none';
                errorEl.style.display = 'block';
                document.getElementById(this.modalId + '-error-text').textContent =
                    'Error al buscar la ubicacion';
            }
        }

        /**
         * Oculta el modal
         */
        hideModal() {
            const modal = document.getElementById(this.modalId);
            if (modal) modal.style.display = 'none';
        }

        /**
         * Geocodifica una direccion usando Nominatim (OpenStreetMap)
         * @param {string} address - Direccion a geocodificar
         * @returns {Promise<[number, number]|null>} - Coordenadas [lat, lng] o null
         */
        async _geocode(address) {
            if (!address || !address.trim()) return null;

            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`;
            const response = await fetch(url, {
                headers: { 'Accept-Language': 'es' }
            });

            if (!response.ok) return null;
            const results = await response.json();

            if (results.length > 0) {
                return [parseFloat(results[0].lat), parseFloat(results[0].lon)];
            }
            return null;
        }

        /**
         * Destruye el componente y limpia recursos
         */
        destroy() {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
            const modal = document.getElementById(this.modalId);
            if (modal) modal.remove();
        }

        _delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
    }

    // Exponer globalmente
    window.MapComponent = MapComponent;
})();
