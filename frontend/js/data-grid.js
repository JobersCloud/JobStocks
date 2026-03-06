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
 *       loadingText: 'Cargando pedidos...',
 *       onPageChange: (page) => loadOrders(page)  // Server-side pagination callback
 *   });
 */
class DataGrid {
    constructor(config) {
        this.el = typeof config.el === 'string' ? document.querySelector(config.el) : config.el;
        if (!this.el) throw new Error(`DataGrid: elemento '${config.el}' no encontrado`);

        this.columns = config.columns || [];
        this._originalColumns = [...this.columns];
        this.renderCell = config.renderCell || (() => null);
        this.renderCard = config.renderCard || (() => '');
        this.tableClass = config.tableClass || 'proposals-table';
        this.emptyIcon = config.emptyIcon || '📦';
        this.emptyText = config.emptyText || 'No hay datos';
        this.loadingText = config.loadingText || 'Cargando...';
        this.storageKey = config.storageKey || 'filtrosGuardados';
        this.onSort = config.onSort || null;
        this.onPageChange = config.onPageChange || null;

        // Sort state
        this.ordenActual = {
            columna: config.defaultSort?.column || null,
            direccion: config.defaultSort?.direction || 'ASC'
        };

        // Data state
        this._allData = [];
        this._filteredData = [];

        // Server-side pagination metadata
        this._paginationMeta = null;

        // DOM refs (se crean en _buildDOM)
        this._refs = {};

        // GridFilters instance
        this._gridFilters = null;

        // Ensure host element participates in flex layout
        this.el.style.flex = '1';
        this.el.style.minHeight = '0';
        this.el.style.display = 'flex';
        this.el.style.flexDirection = 'column';

        // Lock the parent .main-content-area to viewport height
        this._lockParentHeight();

        // Restore saved column order
        this._loadColumnOrder();

        // Build
        this._buildDOM();
        this._initGridFilters();
        this._initEventListeners();
        this._initColumnResize();
        this._initColumnReorder();

        // Resize handler for viewport fitting
        this._resizeHandler = () => this._fitToViewport();
        window.addEventListener('resize', this._resizeHandler);
    }

    // ==================== LAYOUT ====================

    _lockParentHeight() {
        // Solo bloquear altura en desktop - en movil necesitamos scroll natural
        if (window.innerWidth <= 768) return;
        const mca = this.el.closest('.main-content-area');
        if (mca) {
            mca.style.height = '100vh';
            mca.style.minHeight = 'unset';
            mca.style.overflow = 'hidden';
            mca.style.overflowY = 'hidden';
        }
    }

    _fitToViewport() {
        // Directly calculate and set max-height on scroll container
        // so thead stays sticky at top, footer stays fixed at bottom
        const sc = this._refs?.tableWrapper?.querySelector('.table-scroll-container');
        if (!sc || this._refs.tableWrapper.style.display === 'none') return;

        const scRect = sc.getBoundingClientRect();
        const footerH = this._refs.footer?.offsetHeight || 40;
        const padding = 25;
        const available = window.innerHeight - scRect.top - footerH - padding;

        if (available > 100) {
            sc.style.maxHeight = available + 'px';
            sc.style.overflowY = 'auto';
        }
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
            const widthStyle = col.width ? ` style="width:${col.width};max-width:${col.width};"` : '';

            const resizeHandle = '<div class="dg-resize-handle"></div>';

            if (!sortable && !filterable) {
                return `<th${alignClass}${widthStyle} data-column="${col.key}">${col.label}${resizeHandle}</th>`;
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

            return `<th data-column="${col.key}"${alignClass ? ' ' + alignClass.trim() : ''}${widthStyle}><div class="column-header-wrapper">${inner}</div>${resizeHandle}</th>`;
        }).join('');

        this.el.innerHTML = `
            <div class="proposals-container">
                <div class="proposals-content">
                    <div class="proposals-loading dg-loading">
                        <div class="spinner"></div>
                        <p>${this.loadingText}</p>
                    </div>
                    <div class="dg-mobile-toolbar">${this._buildMobileToolbarHTML()}</div>
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

        // Mobile toolbar refs
        this._refs.mobileToolbar = this.el.querySelector('.dg-mobile-toolbar');
        this._refs.mobileSortSelect = this.el.querySelector('.dg-mobile-sort-select');
        this._refs.mobileSortDir = this.el.querySelector('.dg-mobile-sort-dir');
        this._refs.mobileFilterBtn = this.el.querySelector('.dg-mobile-filter-btn');
        this._refs.mobileFilterCount = this.el.querySelector('.dg-mobile-filter-count');
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

        // Mobile toolbar events
        if (this._refs.mobileSortSelect) {
            this._refs.mobileSortSelect.addEventListener('change', (e) => {
                const col = e.target.value;
                if (!col) return;
                this.ordenActual.columna = col;
                this.ordenActual.direccion = 'ASC';
                this._updateSortIcons();
                this._applyFiltersAndSort();
                this._updateMobileSortUI();
            });
        }

        if (this._refs.mobileSortDir) {
            this._refs.mobileSortDir.addEventListener('click', () => {
                if (!this.ordenActual.columna) return;
                this.ordenActual.direccion = this.ordenActual.direccion === 'ASC' ? 'DESC' : 'ASC';
                this._updateSortIcons();
                this._applyFiltersAndSort();
                this._updateMobileSortUI();
            });
        }

        if (this._refs.mobileFilterBtn) {
            this._refs.mobileFilterBtn.addEventListener('click', () => {
                this._showMobileFilterPicker();
            });
        }
    }

    // ==================== COLUMN RESIZE ====================

    _initColumnResize() {
        const handles = this.el.querySelectorAll('.dg-resize-handle');
        handles.forEach(handle => {
            handle.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const th = handle.parentElement;
                const colIndex = Array.from(th.parentElement.children).indexOf(th);
                const startX = e.pageX;
                const startWidth = th.offsetWidth;

                const onMouseMove = (ev) => {
                    const newWidth = Math.max(30, startWidth + (ev.pageX - startX));
                    th.style.width = newWidth + 'px';
                    th.style.maxWidth = newWidth + 'px';
                };

                const onMouseUp = () => {
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                };

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });
        });
    }

    // ==================== COLUMN REORDER (DRAG & DROP) ====================

    _loadColumnOrder() {
        try {
            const saved = localStorage.getItem(`${this.storageKey}_colOrder`);
            if (!saved) return;
            const order = JSON.parse(saved);
            const currentKeys = this.columns.map(c => c.key);
            // Validate saved order matches current columns
            if (order.length !== currentKeys.length || !order.every(k => currentKeys.includes(k))) return;
            const colMap = {};
            this.columns.forEach(c => colMap[c.key] = c);
            this.columns = order.map(k => colMap[k]);
        } catch (e) { /* ignore corrupt data */ }
    }

    _saveColumnOrder() {
        try {
            localStorage.setItem(`${this.storageKey}_colOrder`, JSON.stringify(this.columns.map(c => c.key)));
        } catch (e) { /* ignore */ }
    }

    _initColumnReorder() {
        const thead = this.el.querySelector('thead');
        if (!thead) return;
        const ths = thead.querySelectorAll('th');
        this._dragColIndex = null;

        ths.forEach((th, idx) => {
            th.setAttribute('draggable', 'true');

            th.addEventListener('dragstart', (e) => {
                // Don't start drag from resize handle
                if (e.target.closest('.dg-resize-handle')) {
                    e.preventDefault();
                    return;
                }
                this._dragColIndex = idx;
                th.classList.add('dg-dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', idx.toString());
            });

            th.addEventListener('dragover', (e) => {
                if (this._dragColIndex === null) return;
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                // Visual indicator
                ths.forEach(t => t.classList.remove('dg-drag-over-left', 'dg-drag-over-right'));
                const rect = th.getBoundingClientRect();
                const midX = rect.left + rect.width / 2;
                if (e.clientX < midX) {
                    th.classList.add('dg-drag-over-left');
                } else {
                    th.classList.add('dg-drag-over-right');
                }
            });

            th.addEventListener('dragleave', () => {
                th.classList.remove('dg-drag-over-left', 'dg-drag-over-right');
            });

            th.addEventListener('drop', (e) => {
                e.preventDefault();
                ths.forEach(t => t.classList.remove('dg-drag-over-left', 'dg-drag-over-right', 'dg-dragging'));
                const fromIdx = this._dragColIndex;
                if (fromIdx === null || fromIdx === idx) return;

                // Reorder columns array
                const [moved] = this.columns.splice(fromIdx, 1);
                this.columns.splice(idx, 0, moved);

                this._saveColumnOrder();
                this._rebuildAfterReorder();
            });

            th.addEventListener('dragend', () => {
                this._dragColIndex = null;
                ths.forEach(t => t.classList.remove('dg-dragging', 'dg-drag-over-left', 'dg-drag-over-right'));
            });
        });
    }

    _rebuildAfterReorder() {
        // Rebuild thead with new column order
        const sortIconSVG = '<svg class="sort-icon" viewBox="0 0 16 16" width="12" height="12" fill="currentColor"><path d="M8 2l4 5H4l4-5zm0 12L4 9h8l-4 5z"/></svg>';
        const filterIconSVG = '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 2h14l-5 6v5l-4 2v-7L1 2z"/></svg>';

        const thead = this.el.querySelector('thead tr');
        thead.innerHTML = this.columns.map(col => {
            const sortable = col.sortable !== false;
            const filterable = col.filterable !== false;
            const alignClass = col.align === 'right' ? ' class="text-right"' : col.align === 'center' ? ' class="text-center"' : '';
            const widthStyle = col.width ? ` style="width:${col.width};max-width:${col.width};"` : '';
            const resizeHandle = '<div class="dg-resize-handle"></div>';

            if (!sortable && !filterable) {
                return `<th${alignClass}${widthStyle} data-column="${col.key}">${col.label}${resizeHandle}</th>`;
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

            return `<th data-column="${col.key}"${alignClass ? ' ' + alignClass.trim() : ''}${widthStyle}><div class="column-header-wrapper">${inner}</div>${resizeHandle}</th>`;
        }).join('');

        // Reorder existing tbody cells
        const rows = this._refs.tbody.querySelectorAll('tr');
        const keyToNewIdx = {};
        this.columns.forEach((col, i) => keyToNewIdx[col.key] = i);

        // Get old column order from _originalColumns or fallback
        rows.forEach(tr => {
            const tds = Array.from(tr.querySelectorAll('td'));
            if (tds.length !== this.columns.length) return;
            // We need to figure out current order - rebuild from data instead
        });

        // Simplest: re-render data rows with new column order
        if (this._filteredData.length > 0 || this._allData.length > 0) {
            const data = this._filteredData.length > 0 ? this._filteredData : this._allData;
            this._refs.tbody.innerHTML = data.map(item => {
                const cells = this.columns.map(col => {
                    const alignClass = col.align === 'right' ? ' class="text-right"' : col.align === 'center' ? ' class="text-center"' : '';
                    const content = this.renderCell(item, col);
                    const cellContent = content !== null && content !== undefined ? content : this._escapeHtml(item[col.key]);
                    return `<td data-column="${col.key}"${alignClass}>${cellContent}</td>`;
                }).join('');
                const rowId = item.id != null ? ` data-id="${item.id}"` : '';
                return `<tr${rowId}>${cells}</tr>`;
            }).join('');
        }

        // Re-init resize handles and column reorder
        this._initColumnResize();
        this._initColumnReorder();
        this._updateSortIcons();

        // Re-init GridFilters filter button events
        if (this._gridFilters) {
            this._gridFilters.actualizarIconosFiltro();
        }

        // Rebuild mobile sort options with new column order
        this._rebuildMobileSortOptions();
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
        this._updateMobileSortUI();
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

    // ==================== MOBILE TOOLBAR ====================

    _buildMobileToolbarHTML() {
        const t = window.t || (k => k);
        const sortableCols = this.columns.filter(c => c.sortable !== false);
        const filterableCols = this.columns.filter(c => c.filterable !== false && c.sortable !== false);

        const sortOptions = sortableCols.map(col =>
            `<option value="${col.key}">${col.label}</option>`
        ).join('');

        const filterCount = filterableCols.length > 0
            ? `<span class="dg-mobile-filter-count" style="display:none;">0</span>`
            : '';

        return `
            <div class="dg-mobile-sort">
                <span class="dg-mobile-sort-icon">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 5h10M11 9h7M11 13h4M3 17l4 4 4-4M7 3v18"/></svg>
                </span>
                <select class="dg-mobile-sort-select">
                    <option value="">${t('common.mobileSortPlaceholder') || '-- Ordenar por --'}</option>
                    <optgroup label="${t('common.mobileSortBy') || 'Ordenar por'}">
                        ${sortOptions}
                    </optgroup>
                </select>
                <button class="dg-mobile-sort-dir" title="ASC/DESC">
                    <span class="dg-sort-arrow-down">&#9660;</span><span class="dg-sort-arrow-up" style="display:none;">&#9650;</span>
                </button>
            </div>
            ${filterableCols.length > 0 ? `
            <button class="dg-mobile-filter-btn" title="${t('common.mobileFilterBtn') || 'Filtrar'}">
                <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 2h14l-5 6v5l-4 2v-7L1 2z"/></svg>
                ${filterCount}
            </button>` : ''}
        `;
    }

    _updateMobileSortUI() {
        if (!this._refs.mobileSortSelect) return;
        this._refs.mobileSortSelect.value = this.ordenActual.columna || '';

        if (this._refs.mobileSortDir) {
            const arrowDown = this._refs.mobileSortDir.querySelector('.dg-sort-arrow-down');
            const arrowUp = this._refs.mobileSortDir.querySelector('.dg-sort-arrow-up');
            if (arrowDown && arrowUp) {
                if (this.ordenActual.direccion === 'ASC') {
                    arrowDown.style.display = 'none';
                    arrowUp.style.display = '';
                } else {
                    arrowDown.style.display = '';
                    arrowUp.style.display = 'none';
                }
            }
        }
    }

    _updateMobileFilterCount() {
        if (!this._refs.mobileFilterCount) {
            this._refs.mobileFilterCount = this.el.querySelector('.dg-mobile-filter-count');
        }
        if (!this._refs.mobileFilterCount) return;
        const count = this._gridFilters ? this._gridFilters.filtrosColumna.length : 0;
        if (count > 0) {
            this._refs.mobileFilterCount.textContent = count;
            this._refs.mobileFilterCount.style.display = 'inline-flex';
        } else {
            this._refs.mobileFilterCount.style.display = 'none';
        }
    }

    _showMobileFilterPicker() {
        // Remove existing picker
        const existing = document.querySelector('.dg-mobile-filter-picker-overlay');
        if (existing) { existing.remove(); return; }

        const t = window.t || (k => k);
        const filterableCols = this.columns.filter(c => c.filterable !== false && c.sortable !== false);
        if (filterableCols.length === 0) return;

        const overlay = document.createElement('div');
        overlay.className = 'dg-mobile-filter-picker-overlay';

        const activeFilters = this._gridFilters ? this._gridFilters.filtrosColumna.map(f => f.columna) : [];

        const items = filterableCols.map(col => {
            const isActive = activeFilters.includes(col.key);
            return `<button class="dg-mobile-filter-picker-item${isActive ? ' active' : ''}" data-col="${col.key}">
                <span class="dg-mobile-filter-picker-label">${col.label}</span>
                ${isActive ? '<span class="dg-mobile-filter-picker-dot"></span>' : ''}
            </button>`;
        }).join('');

        overlay.innerHTML = `
            <div class="dg-mobile-filter-picker">
                <div class="dg-mobile-filter-picker-header">
                    <span>${t('common.mobileFilterTitle') || 'Filtrar por columna'}</span>
                    <button class="dg-mobile-filter-picker-close">&times;</button>
                </div>
                <div class="dg-mobile-filter-picker-body">
                    ${items}
                </div>
                ${activeFilters.length > 0 ? `
                <div class="dg-mobile-filter-picker-footer">
                    <button class="dg-mobile-filter-picker-clear">
                        <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 2l12 12M14 2L2 14"/></svg>
                        ${t('common.mobileClearFilters') || 'Limpiar todos'}
                    </button>
                </div>` : ''}
            </div>
        `;

        document.body.appendChild(overlay);

        // Trigger slide-up animation
        requestAnimationFrame(() => {
            overlay.classList.add('visible');
        });

        // Event: close overlay
        const closeOverlay = () => {
            overlay.classList.remove('visible');
            setTimeout(() => overlay.remove(), 300);
        };

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeOverlay();
        });

        overlay.querySelector('.dg-mobile-filter-picker-close').addEventListener('click', closeOverlay);

        // Event: column item click → open filter popup for that column
        overlay.querySelectorAll('.dg-mobile-filter-picker-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const colKey = btn.dataset.col;
                closeOverlay();
                // Small delay to allow sheet to close before popup opens
                setTimeout(() => {
                    if (this._gridFilters) {
                        this._gridFilters.mostrarPopupFiltro(colKey, this._refs.mobileFilterBtn || this.el);
                    }
                }, 350);
            });
        });

        // Event: clear all filters
        const clearBtn = overlay.querySelector('.dg-mobile-filter-picker-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (this._gridFilters) {
                    this._gridFilters.limpiarTodosFiltrosColumna();
                }
                closeOverlay();
            });
        }
    }

    _rebuildMobileSortOptions() {
        if (!this._refs.mobileSortSelect) return;
        const t = window.t || (k => k);
        const sortableCols = this.columns.filter(c => c.sortable !== false);
        this._refs.mobileSortSelect.innerHTML = `
            <option value="">${t('common.mobileSortPlaceholder') || '-- Ordenar --'}</option>
            ${sortableCols.map(col => `<option value="${col.key}">${col.label}</option>`).join('')}
        `;
        this._updateMobileSortUI();
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
        this._updateMobileFilterCount();
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
        this._refs.tableWrapper.style.display = 'flex';

        // Render table rows
        this._refs.tbody.innerHTML = data.map(item => {
            const cells = this.columns.map(col => {
                const alignClass = col.align === 'right' ? ' class="text-right"' : col.align === 'center' ? ' class="text-center"' : '';
                const content = this.renderCell(item, col);
                const cellContent = content !== null && content !== undefined ? content : this._escapeHtml(item[col.key]);
                return `<td data-column="${col.key}"${alignClass}>${cellContent}</td>`;
            }).join('');
            const rowId = item.id != null ? ` data-id="${item.id}"` : '';
            return `<tr${rowId}>${cells}</tr>`;
        }).join('');

        // Render cards always (CSS handles visibility via media queries)
        this._refs.cards.innerHTML = data.map(item => this.renderCard(item)).join('');

        // Update footer
        this._updateFooter(data.length);

        // Adjust scroll container height to fit viewport
        requestAnimationFrame(() => this._fitToViewport());
    }

    _updateFooter(count) {
        // Server-side pagination mode
        if (this._paginationMeta) {
            this._renderPaginationFooter(count);
            return;
        }
        // Client-side mode
        const total = this._allData.length;
        const hasFilters = this._gridFilters && this._gridFilters.filtrosColumna.length > 0;
        const infoText = hasFilters && count !== total
            ? `${count} registros (filtrados de ${total})`
            : `${count} registros`;

        this._refs.footer.innerHTML = `
            <div class="dg-footer-row">
                <span>${infoText}</span>
                ${count > 0 ? this._exportButtonHtml() : ''}
            </div>
        `;
        this._attachExportHandler();
    }

    _renderPaginationFooter(filteredCount) {
        const meta = this._paginationMeta;
        if (!meta) return;

        const { page, total_pages, total, page_size } = meta;
        const start = Math.min((page - 1) * page_size + 1, total);
        const end = Math.min(page * page_size, total);

        const hasFilters = this._gridFilters && this._gridFilters.filtrosColumna.length > 0;
        let filterInfo = '';
        if (hasFilters && filteredCount < this._allData.length) {
            filterInfo = ` | ${filteredCount} filtrados en pagina`;
        }

        this._refs.footer.innerHTML = `
            <div class="dg-pagination">
                <div class="dg-pagination-info">
                    ${start}-${end} de ${total} registros${filterInfo}
                    ${this._allData.length > 0 ? this._exportButtonHtml() : ''}
                </div>
                <div class="dg-pagination-controls">
                    <button class="dg-page-btn" data-page="1" ${page <= 1 ? 'disabled' : ''} title="Primera">&laquo;</button>
                    <button class="dg-page-btn" data-page="${page - 1}" ${page <= 1 ? 'disabled' : ''} title="Anterior">&lsaquo;</button>
                    <span class="dg-page-current">Pag. ${page} / ${total_pages}</span>
                    <button class="dg-page-btn" data-page="${page + 1}" ${page >= total_pages ? 'disabled' : ''} title="Siguiente">&rsaquo;</button>
                    <button class="dg-page-btn" data-page="${total_pages}" ${page >= total_pages ? 'disabled' : ''} title="Ultima">&raquo;</button>
                </div>
            </div>
        `;
        this._attachExportHandler();

        // Attach click handlers for pagination buttons
        this._refs.footer.querySelectorAll('.dg-page-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const newPage = parseInt(btn.dataset.page);
                if (newPage >= 1 && newPage <= total_pages && newPage !== page && this.onPageChange) {
                    this.onPageChange(newPage);
                }
            });
        });
    }

    _escapeHtml(value) {
        if (value === null || value === undefined) return '';
        return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // ==================== EXPORT ====================

    _exportButtonHtml() {
        return `<button class="dg-export-btn" title="Exportar a Excel">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M23 1.5q.41 0 .7.3.3.29.3.7v19q0 .41-.3.7-.29.3-.7.3H7q-.41 0-.7-.3-.3-.29-.3-.7V18H1q-.41 0-.7-.3-.3-.29-.3-.7V7q0-.41.3-.7Q.58 6 1 6h5V2.5q0-.41.3-.7.29-.3.7-.3zM1 16.5h5v-9H1zm6-13.5v3h2.5L8 9.25 6 6h1V2.5H7zM14.35 7l-1.9 3.15L14.5 13.4h-2.1l-1.2-2.4-1.2 2.4H7.85l2.05-3.25L8 7h2.1l1.1 2.25L12.3 7zM23 16.5V18h-9v3.5h9zM23 2.5h-9V6h9zM23 7h-9v8h9z"/>
            </svg>
        </button>`;
    }

    _attachExportHandler() {
        const btn = this._refs.footer.querySelector('.dg-export-btn');
        if (btn) btn.addEventListener('click', () => this.exportToExcel());
    }

    /**
     * Exports current data (filtered if filters active) to Excel-compatible CSV.
     * @param {string} filename - Optional filename (default: 'export.csv')
     */
    exportToExcel(filename) {
        const data = this._filteredData.length > 0 || (this._gridFilters && this._gridFilters.filtrosColumna.length > 0)
            ? this._filteredData
            : this._allData;

        if (data.length === 0) return;

        // Use only visible data columns (exclude _actions and similar)
        const exportCols = this.columns.filter(c => !c.key.startsWith('_') && c.exportable !== false);

        // Header row
        const header = exportCols.map(c => `"${c.label.replace(/"/g, '""')}"`).join(';');

        // Data rows
        const rows = data.map(item => {
            return exportCols.map(col => {
                let val = item[col.key];
                if (val === null || val === undefined) val = '';
                val = String(val).replace(/"/g, '""');
                return `"${val}"`;
            }).join(';');
        });

        // BOM + CSV content (semicolon separator for es-ES Excel)
        const csvContent = '\uFEFF' + header + '\n' + rows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });

        // Download
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || `export_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    // ==================== PUBLIC API ====================

    /**
     * Load data into the grid (client-side mode). Applies filters and sort, then renders.
     * @param {Array} data - Array of data objects
     */
    setData(data) {
        this._allData = data || [];
        this._paginationMeta = null;
        this._applyFiltersAndSort();
        this._updateSortIcons();
        this._updateMobileSortUI();
    }

    /**
     * Load paginated data from server. Renders data with pagination controls.
     * @param {Array} data - Array of data objects for current page
     * @param {Object} meta - Pagination metadata: { page, page_size, total, total_pages }
     */
    setPaginatedData(data, meta) {
        this._allData = data || [];
        this._paginationMeta = meta || null;
        this._applyFiltersAndSort();
        this._updateSortIcons();
        this._updateMobileSortUI();
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
        if (this._resizeHandler) {
            window.removeEventListener('resize', this._resizeHandler);
        }
        if (this._gridFilters) {
            this._gridFilters.cerrarPopupFiltro();
        }
        // Clean up mobile filter picker if open
        const picker = document.querySelector('.dg-mobile-filter-picker-overlay');
        if (picker) picker.remove();
        this.el.innerHTML = '';
        this._allData = [];
        this._filteredData = [];
    }
}
