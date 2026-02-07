// ============================================================
//      ██╗ ██████╗ ██████╗ ███████╗██████╗ ███████╗
//      ██║██╔═══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝
//      ██║██║   ██║██████╔╝█████╗  ██████╔╝███████╗
// ██   ██║██║   ██║██╔══██╗██╔══╝  ██╔══██╗╚════██║
// ╚█████╔╝╚██████╔╝██████╔╝███████╗██║  ██║███████║
//  ╚════╝  ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝
//
//                ──  Jobers - Iaucejo  ──
//
// Autor : iaucejo
// Fecha : 2026-02-06
// ============================================================

// ============================================
// ARCHIVO: js/data-grid.js
// Descripcion: Componente DataGrid reutilizable para grids con sorting, filtros y estados
// Genera toda la estructura HTML, cabeceras con sort+filter, y gestiona estados
// ============================================

/**
 * DataGrid - Componente centralizado para grids de datos.
 *
 * Uso:
 *   const grid = new DataGrid({
 *       el: '#orders-grid',
 *       columns: [
 *           { key: 'pedido', label: '# Pedido', tipo: 'numero' },
 *           { key: 'fecha', label: 'Fecha', tipo: 'texto' },
 *           { key: '_actions', label: 'Acciones', sortable: false, filterable: false }
 *       ],
 *       renderCell(item, col) { return null; },  // null = texto plano item[col.key]
 *       renderCard(item) { return '<div>...</div>'; },
 *       defaultSort: { column: 'fecha', direction: 'DESC' },
 *       storageKey: 'filtros_pedidos',
 *       tableClass: 'proposals-table',
 *       emptyIcon: '📦',
 *       emptyText: 'No hay pedidos',
 *       loadingText: 'Cargando pedidos...'
 *   });
 */
class DataGrid {
    constructor(config) {
        this.el = typeof config.el === 'string' ? document.querySelector(config.el) : config.el;
        if (!this.el) throw new Error(`DataGrid: elemento '${config.el}' no encontrado`);

        this.columns = config.columns || [];
        this.renderCell = config.renderCell || (() => null);
        this.renderCard = config.renderCard || (() => '');
        this.tableClass = config.tableClass || 'proposals-table';
        this.emptyIcon = config.emptyIcon || '📦';
        this.emptyText = config.emptyText || 'No hay datos';
        this.loadingText = config.loadingText || 'Cargando...';
        this.storageKey = config.storageKey || 'filtrosGuardados';
        this.onSort = config.onSort || null;

        // Sort state
        this.ordenActual = {
            columna: config.defaultSort?.column || null,
            direccion: config.defaultSort?.direction || 'ASC'
        };

        // Data state
        this._allData = [];
        this._filteredData = [];

        // DOM refs (se crean en _buildDOM)
        this._refs = {};

        // GridFilters instance
        this._gridFilters = null;

        // Build
        this._buildDOM();
        this._initGridFilters();
        this._initEventListeners();
    }

    // ==================== DOM GENERATION ====================

    _buildDOM() {
        const sortIconSVG = '<svg class="sort-icon" viewBox="0 0 16 16" width="12" height="12" fill="currentColor"><path d="M8 2l4 5H4l4-5zm0 12L4 9h8l-4 5z"/></svg>';
        const filterIconSVG = '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 2h14l-5 6v5l-4 2v-7L1 2z"/></svg>';

        // Build thead
        const thCells = this.columns.map(col => {
            const sortable = col.sortable !== false;
            const filterable = col.filterable !== false;
            const alignClass = col.align === 'right' ? ' class="text-right"' : col.align === 'center' ? ' class="text-center"' : '';

            if (!sortable && !filterable) {
                return `<th${alignClass}>${col.label}</th>`;
            }

            let inner = '';
            if (sortable) {
                inner += `<span class="sortable-header" data-sort="${col.key}">${col.label} ${sortIconSVG}</span>`;
            } else {
                inner += `<span>${col.label}</span>`;
            }
            if (filterable) {
                inner += `<button class="column-filter-btn" data-columna="${col.key}" title="Filtrar">${filterIconSVG}</button>`;
            }

            return `<th data-column="${col.key}"${alignClass ? ' ' + alignClass.trim() : ''}><div class="column-header-wrapper">${inner}</div></th>`;
        }).join('');

        this.el.innerHTML = `
            <div class="proposals-container">
                <div class="proposals-content">
                    <div class="proposals-loading dg-loading">
                        <div class="spinner"></div>
                        <p>${this.loadingText}</p>
                    </div>
                    <div class="column-filters-chips dg-chips" id="dg-chips-${this.storageKey}" style="display:none;"></div>
                    <div class="proposals-empty dg-empty" style="display:none;">
                        <div class="proposals-empty-icon">${this.emptyIcon}</div>
                        <h3>${this.emptyText}</h3>
                    </div>
                    <div class="proposals-no-results dg-no-results" style="display:none;">
                        <div class="proposals-empty-icon">🔍</div>
                        <h3>No se encontraron resultados</h3>
                        <p>Prueba con otros criterios de busqueda</p>
                    </div>
                    <div class="proposals-table-wrapper dg-table-wrapper" style="display:none;">
                        <div class="table-scroll-container">
                            <table class="${this.tableClass}">
                                <thead><tr>${thCells}</tr></thead>
                                <tbody class="dg-tbody"></tbody>
                            </table>
                        </div>
                    </div>
                    <div class="proposals-cards dg-cards"></div>
                    <div class="grid-footer dg-footer"></div>
                </div>
            </div>
        `;

        // Cache refs
        this._refs.loading = this.el.querySelector('.dg-loading');
        this._refs.chips = this.el.querySelector('.dg-chips');
        this._refs.empty = this.el.querySelector('.dg-empty');
        this._refs.noResults = this.el.querySelector('.dg-no-results');
        this._refs.tableWrapper = this.el.querySelector('.dg-table-wrapper');
        this._refs.tbody = this.el.querySelector('.dg-tbody');
        this._refs.cards = this.el.querySelector('.dg-cards');
        this._refs.footer = this.el.querySelector('.dg-footer');
    }

    // ==================== GRID FILTERS ====================

    _initGridFilters() {
        const filterableCols = this.columns.filter(c => c.filterable !== false && c.sortable !== false);
        if (filterableCols.length === 0) return;

        try {
            this._gridFilters = new GridFilters({
                columnasFiltrables: filterableCols.map(c => ({
                    key: c.key,
                    label: c.label,
                    tipo: c.tipo || 'texto'
                })),
                getAllData: () => this._allData,
                onFilterApply: (datosFiltrados) => {
                    this._filteredData = this._sortData(datosFiltrados);
                    this._renderData(this._filteredData);
                },
                chipsContainerId: `dg-chips-${this.storageKey}`,
                storageKey: this.storageKey
            });
        } catch (e) {
            console.error('DataGrid: Error inicializando GridFilters:', e);
        }
    }

    // ==================== EVENT LISTENERS ====================

    _initEventListeners() {
        // Sort via event delegation on thead
        const thead = this.el.querySelector('thead');
        if (thead) {
            thead.addEventListener('click', (e) => {
                const sortableHeader = e.target.closest('.sortable-header');
                if (!sortableHeader) return;
                const column = sortableHeader.dataset.sort;
                if (!column) return;
                this._handleSort(column);
            });
        }
    }

    // ==================== SORTING ====================

    _handleSort(column) {
        if (this.ordenActual.columna === column) {
            this.ordenActual.direccion = this.ordenActual.direccion === 'ASC' ? 'DESC' : 'ASC';
        } else {
            this.ordenActual.columna = column;
            this.ordenActual.direccion = 'ASC';
        }
        this._updateSortIcons();
        this._applyFiltersAndSort();
    }

    _sortData(data) {
        if (!this.ordenActual.columna) return data;
        const sorted = [...data];
        const col = this.ordenActual.columna;
        const dir = this.ordenActual.direccion;

        sorted.sort((a, b) => {
            let valA = a[col];
            let valB = b[col];

            // Detect date strings
            if (typeof valA === 'string' && typeof valB === 'string') {
                const dateA = Date.parse(valA);
                const dateB = Date.parse(valB);
                if (!isNaN(dateA) && !isNaN(dateB) && valA.match(/\d{4}[-/]\d{2}[-/]\d{2}/)) {
                    valA = dateA;
                    valB = dateB;
                }
            }

            // Numeric comparison
            const numA = parseFloat(valA);
            const numB = parseFloat(valB);
            if (!isNaN(numA) && !isNaN(numB) && typeof valA !== 'boolean' && typeof valB !== 'boolean') {
                valA = numA;
                valB = numB;
            } else {
                // String comparison
                if (typeof valA === 'string') valA = valA.toLowerCase();
                if (typeof valB === 'string') valB = valB.toLowerCase();
            }

            // Handle nulls
            if (valA == null && valB == null) return 0;
            if (valA == null) return 1;
            if (valB == null) return -1;

            if (valA < valB) return dir === 'ASC' ? -1 : 1;
            if (valA > valB) return dir === 'ASC' ? 1 : -1;
            return 0;
        });

        return sorted;
    }

    _updateSortIcons() {
        const headers = this.el.querySelectorAll('.sortable-header');
        headers.forEach(header => {
            const col = header.dataset.sort;
            const icon = header.querySelector('.sort-icon');
            if (!icon) return;

            if (col === this.ordenActual.columna) {
                icon.style.opacity = '1';
                if (this.ordenActual.direccion === 'ASC') {
                    icon.innerHTML = '<path d="M8 2l4 5H4l4-5z" opacity="1"/><path d="M8 14L4 9h8l-4 5z" opacity="0.3"/>';
                } else {
                    icon.innerHTML = '<path d="M8 2l4 5H4l4-5z" opacity="0.3"/><path d="M8 14L4 9h8l-4 5z" opacity="1"/>';
                }
            } else {
                icon.style.opacity = '0.4';
                icon.innerHTML = '<path d="M8 2l4 5H4l4-5zm0 12L4 9h8l-4 5z"/>';
            }
        });
    }

    // ==================== RENDERING ====================

    _applyFiltersAndSort() {
        let data = [...this._allData];
        if (this._gridFilters) {
            data = this._gridFilters.aplicarFiltrosADatos(data);
        }
        data = this._sortData(data);
        this._filteredData = data;
        this._renderData(data);
        if (this._gridFilters) {
            this._gridFilters.renderizarChipsFiltrosColumna();
            this._gridFilters.actualizarIconosFiltro();
        }
    }

    _renderData(data) {
        const hasFilters = this._gridFilters && this._gridFilters.filtrosColumna.length > 0;

        // Hide loading
        this._refs.loading.style.display = 'none';

        if (this._allData.length === 0) {
            // No data at all
            this._refs.empty.style.display = 'block';
            this._refs.noResults.style.display = 'none';
            this._refs.tableWrapper.style.display = 'none';
            this._refs.cards.innerHTML = '';
            this._refs.footer.innerHTML = '';
            return;
        }

        if (data.length === 0 && hasFilters) {
            // Filters active but no results
            this._refs.empty.style.display = 'none';
            this._refs.noResults.style.display = 'block';
            this._refs.tableWrapper.style.display = 'none';
            this._refs.cards.innerHTML = '';
            this._updateFooter(0);
            return;
        }

        // Has data
        this._refs.empty.style.display = 'none';
        this._refs.noResults.style.display = 'none';
        this._refs.tableWrapper.style.display = 'block';

        // Render table rows
        this._refs.tbody.innerHTML = data.map(item => {
            const cells = this.columns.map(col => {
                const alignClass = col.align === 'right' ? ' class="text-right"' : col.align === 'center' ? ' class="text-center"' : '';
                const content = this.renderCell(item, col);
                const cellContent = content !== null && content !== undefined ? content : this._escapeHtml(item[col.key]);
                return `<td${alignClass}>${cellContent}</td>`;
            }).join('');
            return `<tr>${cells}</tr>`;
        }).join('');

        // Render cards
        this._refs.cards.innerHTML = data.map(item => this.renderCard(item)).join('');

        // Update footer
        this._updateFooter(data.length);
    }

    _updateFooter(count) {
        const total = this._allData.length;
        const hasFilters = this._gridFilters && this._gridFilters.filtrosColumna.length > 0;
        if (hasFilters && count !== total) {
            this._refs.footer.innerHTML = `${count} registros (filtrados de ${total})`;
        } else {
            this._refs.footer.innerHTML = `${count} registros`;
        }
    }

    _escapeHtml(value) {
        if (value === null || value === undefined) return '';
        const str = String(value);
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ==================== PUBLIC API ====================

    /**
     * Load data into the grid. Applies filters and sort, then renders.
     * @param {Array} data - Array of data objects
     */
    setData(data) {
        this._allData = data || [];
        this._applyFiltersAndSort();
        this._updateSortIcons();
    }

    /**
     * Returns the original unfiltered data.
     */
    getData() {
        return this._allData;
    }

    /**
     * Returns the currently filtered and sorted data.
     */
    getFilteredData() {
        return this._filteredData;
    }

    /**
     * Shows the loading spinner. Call before fetching data.
     */
    showLoading() {
        this._refs.loading.style.display = 'flex';
        this._refs.empty.style.display = 'none';
        this._refs.noResults.style.display = 'none';
        this._refs.tableWrapper.style.display = 'none';
        this._refs.cards.innerHTML = '';
        this._refs.footer.innerHTML = '';
    }

    /**
     * Re-applies filters and sort, re-renders.
     */
    refresh() {
        this._applyFiltersAndSort();
    }

    /**
     * Returns the internal GridFilters instance.
     */
    getFilters() {
        return this._gridFilters;
    }

    /**
     * Cleans up event listeners and DOM.
     */
    destroy() {
        if (this._gridFilters) {
            this._gridFilters.cerrarPopupFiltro();
        }
        this.el.innerHTML = '';
        this._allData = [];
        this._filteredData = [];
    }
}
