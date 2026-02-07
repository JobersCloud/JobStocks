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
            modal.style.cssText = 'display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.6); z-index:10000; justify-content:center; align-items:center;';
            modal.innerHTML = `
                <div style="width: 96vw; height: 96vh; max-width: 96vw; border-radius: 12px; display: flex; flex-direction: column; background: var(--bg-primary, white); overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                    <div class="modal-header" style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px;">
                        <div style="display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink: 0;">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                                <circle cx="12" cy="10" r="3"></circle>
                            </svg>
                            <h2 id="${this.modalId}-title" style="font-size: 1rem; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"></h2>
                        </div>
                        <button onclick="document.getElementById('${this.modalId}').style.display='none'" style="background: none; border: none; cursor: pointer; padding: 6px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; opacity: 0.8; transition: opacity 0.2s;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.8'">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
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
