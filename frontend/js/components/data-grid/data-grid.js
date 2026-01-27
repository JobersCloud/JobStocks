/**
 * Data Grid Web Component
 * Componente reutilizable para grids con filtros, ordenación y paginación
 */

import { filterData, sortData, paginateData, formatDate, formatDateTime, formatNumber, generateId } from './data-grid-utils.js';
import { DataGridFilter } from './data-grid-filter.js';

export class DataGrid extends HTMLElement {
    constructor() {
        super();

        // Estado interno
        this._id = generateId();
        this._data = [];
        this._filteredData = [];
        this._displayData = [];
        this._columns = [];
        this._actions = [];
        this._filters = [];
        this._sort = { column: null, direction: 'asc' };
        this._pagination = { enabled: false, page: 1, pageSize: 20 };
        this._loading = false;
        this._mobileBreakpoint = 768;

        // Sub-componentes
        this._filterPopup = new DataGridFilter(this);
        this._filterPopup.onApply = (filter) => this._applyFilter(filter);
        this._filterPopup.onClear = (column) => this._clearFilter(column);

        // Bound methods para event listeners
        this._boundHandleResize = this._handleResize.bind(this);
    }

    // ==================== LIFECYCLE ====================

    connectedCallback() {
        this._render();
        window.addEventListener('resize', this._boundHandleResize);
    }

    disconnectedCallback() {
        window.removeEventListener('resize', this._boundHandleResize);
        this._filterPopup.close();
    }

    static get observedAttributes() {
        return ['data-endpoint', 'data-page-size', 'data-pagination', 'data-row-key'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;

        switch (name) {
            case 'data-page-size':
                this._pagination.pageSize = parseInt(newValue) || 20;
                this._processData();
                break;
            case 'data-pagination':
                this._pagination.enabled = newValue === 'true';
                this._processData();
                break;
        }
    }

    // ==================== PUBLIC API ====================

    /**
     * Configuración de columnas
     * @param {Array} columns - [{key, label, type, sortable, filterable, width, renderer}]
     */
    set columns(columns) {
        this._columns = columns || [];
        this._render();
    }

    get columns() {
        return this._columns;
    }

    /**
     * Configuración de acciones
     * @param {Array} actions - [{key, label, icon, className, visible}]
     */
    set actions(actions) {
        this._actions = actions || [];
        this._render();
    }

    get actions() {
        return this._actions;
    }

    /**
     * Datos del grid
     * @param {Array} data
     */
    set data(data) {
        this._data = data || [];
        this._pagination.page = 1;
        this._processData();
    }

    get data() {
        return this._data;
    }

    /**
     * Obtiene los datos filtrados actuales
     */
    get filteredData() {
        return this._filteredData;
    }

    /**
     * Establece el estado de carga
     */
    set loading(value) {
        this._loading = !!value;
        this._renderLoading();
    }

    get loading() {
        return this._loading;
    }

    /**
     * Obtiene los filtros activos
     */
    get filters() {
        return [...this._filters];
    }

    /**
     * Obtiene el estado de ordenación
     */
    get sort() {
        return { ...this._sort };
    }

    /**
     * Establece el breakpoint móvil
     */
    set mobileBreakpoint(value) {
        this._mobileBreakpoint = parseInt(value) || 768;
        this._render();
    }

    /**
     * Limpia todos los filtros
     */
    clearFilters() {
        this._filters = [];
        this._pagination.page = 1;
        this._processData();
        this._dispatchEvent('filter-change', { filters: [] });
    }

    /**
     * Establece la página actual
     */
    setPage(page) {
        this._pagination.page = page;
        this._processData();
        this._dispatchEvent('page-change', { page });
    }

    /**
     * Refresca el renderizado
     */
    refresh() {
        this._render();
    }

    // ==================== DATA PROCESSING ====================

    _processData() {
        // Aplicar filtros
        this._filteredData = filterData(this._data, this._filters);

        // Aplicar ordenación
        if (this._sort.column) {
            const column = this._columns.find(c => c.key === this._sort.column);
            const type = column?.type || 'text';
            this._filteredData = sortData(this._filteredData, this._sort.column, this._sort.direction, type);
        }

        // Aplicar paginación
        if (this._pagination.enabled) {
            const result = paginateData(this._filteredData, this._pagination.page, this._pagination.pageSize);
            this._displayData = result.data;
            this._paginationInfo = result;
        } else {
            this._displayData = this._filteredData;
            this._paginationInfo = null;
        }

        this._render();
    }

    // ==================== FILTERING ====================

    _applyFilter(filter) {
        // Reemplazar filtro existente para la misma columna
        const index = this._filters.findIndex(f => f.column === filter.column);
        if (index >= 0) {
            this._filters[index] = filter;
        } else {
            this._filters.push(filter);
        }

        this._pagination.page = 1;
        this._processData();
        this._dispatchEvent('filter-change', { filters: this.filters });
    }

    _clearFilter(column) {
        this._filters = this._filters.filter(f => f.column !== column);
        this._pagination.page = 1;
        this._processData();
        this._dispatchEvent('filter-change', { filters: this.filters });
    }

    _openFilterPopup(column, e) {
        const anchor = e.currentTarget;
        const currentFilter = this._filters.find(f => f.column === column.key);
        this._filterPopup.open(column, anchor, currentFilter);
    }

    // ==================== SORTING ====================

    _toggleSort(column) {
        if (!column.sortable) return;

        if (this._sort.column === column.key) {
            this._sort.direction = this._sort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this._sort.column = column.key;
            this._sort.direction = 'asc';
        }

        this._processData();
        this._dispatchEvent('sort-change', { column: this._sort.column, direction: this._sort.direction });
    }

    // ==================== RENDERING ====================

    _render() {
        const isMobile = window.innerWidth < this._mobileBreakpoint;
        const t = window.t || ((key) => key);

        this.innerHTML = `
            <div class="dg-container">
                ${this._renderFilterChips()}
                <div class="dg-content">
                    ${this._loading ? this._renderLoadingContent() : ''}
                    ${!this._loading && this._displayData.length === 0 ? this._renderEmpty() : ''}
                    ${!this._loading && this._displayData.length > 0 ? (
                        isMobile ? this._renderCards() : this._renderTable()
                    ) : ''}
                </div>
                ${this._renderFooter()}
            </div>
        `;

        this._attachEventListeners();
    }

    _renderLoadingContent() {
        const t = window.t || ((key) => key);
        return `
            <div class="dg-loading">
                <div class="dg-spinner"></div>
                <p>${t('dataGrid.loading')}</p>
            </div>
        `;
    }

    _renderLoading() {
        const loadingEl = this.querySelector('.dg-loading');
        const contentEl = this.querySelector('.dg-content');

        if (this._loading) {
            if (!loadingEl && contentEl) {
                contentEl.innerHTML = this._renderLoadingContent();
            }
        } else {
            this._render();
        }
    }

    _renderEmpty() {
        const t = window.t || ((key) => key);
        const hasFilters = this._filters.length > 0;

        return `
            <div class="dg-empty">
                <div class="dg-empty-icon">${hasFilters ? '🔍' : '📋'}</div>
                <h3>${hasFilters ? t('dataGrid.noResults') : t('dataGrid.noData')}</h3>
                ${hasFilters ? `<p>${t('dataGrid.tryDifferentFilters')}</p>` : ''}
            </div>
        `;
    }

    _renderFilterChips() {
        if (this._filters.length === 0) return '';

        const t = window.t || ((key) => key);
        const operatorLabels = {
            contains: t('dataGrid.opContains'),
            not_contains: t('dataGrid.opNotContains'),
            eq: '=',
            neq: '≠',
            gt: '>',
            gte: '≥',
            lt: '<',
            lte: '≤',
            starts: t('dataGrid.opStartsWith'),
            not_starts: t('dataGrid.opNotStartsWith'),
            ends: t('dataGrid.opEndsWith'),
            not_ends: t('dataGrid.opNotEndsWith'),
            between: t('dataGrid.opBetween'),
            not_between: t('dataGrid.opNotBetween')
        };

        const chips = this._filters.map(filter => {
            const opLabel = operatorLabels[filter.operator] || filter.operator;
            let valueDisplay = filter.value;
            if (filter.value2) {
                valueDisplay = `${filter.value} - ${filter.value2}`;
            }

            return `
                <span class="dg-filter-chip" data-column="${filter.column}">
                    <strong>${filter.columnLabel}:</strong>
                    <span class="dg-chip-operator">${opLabel}</span>
                    "${valueDisplay}"
                    <button class="dg-chip-remove" data-column="${filter.column}">&times;</button>
                </span>
            `;
        }).join('');

        return `
            <div class="dg-filter-chips">
                ${chips}
                <button class="dg-clear-all-filters">${t('dataGrid.clearAll')}</button>
            </div>
        `;
    }

    _renderTable() {
        const t = window.t || ((key) => key);
        const rowKey = this.getAttribute('data-row-key') || 'id';

        const thead = `
            <thead>
                <tr>
                    ${this._columns.map(col => this._renderTableHeader(col)).join('')}
                    ${this._actions.length > 0 ? `<th class="dg-actions-header">${t('dataGrid.actions')}</th>` : ''}
                </tr>
            </thead>
        `;

        const tbody = `
            <tbody>
                ${this._displayData.map((row, index) => `
                    <tr data-row-index="${index}" data-row-key="${row[rowKey] || index}">
                        ${this._columns.map(col => this._renderTableCell(row, col)).join('')}
                        ${this._actions.length > 0 ? this._renderTableActions(row) : ''}
                    </tr>
                `).join('')}
            </tbody>
        `;

        return `
            <div class="dg-table-wrapper">
                <table class="dg-table">
                    ${thead}
                    ${tbody}
                </table>
            </div>
        `;
    }

    _renderTableHeader(column) {
        const t = window.t || ((key) => key);
        const isSorted = this._sort.column === column.key;
        const sortDir = isSorted ? this._sort.direction : null;
        const hasFilter = this._filters.some(f => f.column === column.key);
        const label = column.label.startsWith('dataGrid.') ? t(column.label) : column.label;

        let sortIcon = '';
        if (column.sortable) {
            if (sortDir === 'asc') {
                sortIcon = `<svg class="dg-sort-icon active" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M7 14l5-5 5 5z"/></svg>`;
            } else if (sortDir === 'desc') {
                sortIcon = `<svg class="dg-sort-icon active" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M7 10l5 5 5-5z"/></svg>`;
            } else {
                sortIcon = `<svg class="dg-sort-icon" width="12" height="12" viewBox="0 0 24 24" fill="currentColor" opacity="0.3"><path d="M7 10l5-5 5 5M7 14l5 5 5-5"/></svg>`;
            }
        }

        let filterIcon = '';
        if (column.filterable) {
            filterIcon = `
                <button class="dg-filter-btn ${hasFilter ? 'active' : ''}" data-column="${column.key}" title="${t('dataGrid.filter')}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                    </svg>
                </button>
            `;
        }

        const style = column.width ? `style="width: ${column.width}"` : '';

        return `
            <th class="dg-th ${column.sortable ? 'sortable' : ''}" data-column="${column.key}" ${style}>
                <div class="dg-th-content">
                    <span class="dg-th-label ${column.sortable ? 'clickable' : ''}" data-column="${column.key}">
                        ${label}
                        ${sortIcon}
                    </span>
                    ${filterIcon}
                </div>
            </th>
        `;
    }

    _renderTableCell(row, column) {
        let value = row[column.key];

        // Aplicar renderer personalizado
        if (column.renderer) {
            value = column.renderer(value, row);
        } else {
            // Formateo por defecto según tipo
            switch (column.type) {
                case 'date':
                    value = formatDate(value);
                    break;
                case 'datetime':
                    value = formatDateTime(value);
                    break;
                case 'number':
                    value = formatNumber(value, column.decimals || 0);
                    break;
                default:
                    value = value ?? '-';
            }
        }

        const style = column.width ? `style="width: ${column.width}"` : '';
        return `<td class="dg-td" ${style}>${value}</td>`;
    }

    _renderTableActions(row) {
        const visibleActions = this._actions.filter(action => {
            if (typeof action.visible === 'function') {
                return action.visible(row);
            }
            return action.visible !== false;
        });

        if (visibleActions.length === 0) {
            return '<td class="dg-td dg-actions-cell"></td>';
        }

        const buttons = visibleActions.map(action => `
            <button class="dg-action-btn ${action.className || ''}" data-action="${action.key}"
                title="${action.label}">
                ${action.icon || ''}
                <span class="dg-action-label">${action.label}</span>
            </button>
        `).join('');

        return `<td class="dg-td dg-actions-cell">${buttons}</td>`;
    }

    _renderCards() {
        const t = window.t || ((key) => key);
        const rowKey = this.getAttribute('data-row-key') || 'id';

        return `
            <div class="dg-cards">
                ${this._displayData.map((row, index) => this._renderCard(row, index, rowKey)).join('')}
            </div>
        `;
    }

    _renderCard(row, index, rowKey) {
        const t = window.t || ((key) => key);

        // Primera columna como título
        const titleColumn = this._columns[0];
        let title = row[titleColumn?.key] || `#${index + 1}`;
        if (titleColumn?.renderer) {
            title = titleColumn.renderer(row[titleColumn.key], row);
        }

        // Resto de columnas como contenido
        const fields = this._columns.slice(1).map(col => {
            let value = row[col.key];
            if (col.renderer) {
                value = col.renderer(value, row);
            } else {
                switch (col.type) {
                    case 'date':
                        value = formatDate(value);
                        break;
                    case 'datetime':
                        value = formatDateTime(value);
                        break;
                    case 'number':
                        value = formatNumber(value, col.decimals || 0);
                        break;
                    default:
                        value = value ?? '-';
                }
            }
            const label = col.label.startsWith('dataGrid.') ? t(col.label) : col.label;
            return `<div class="dg-card-field"><span class="dg-card-label">${label}:</span> <span class="dg-card-value">${value}</span></div>`;
        }).join('');

        // Acciones
        const visibleActions = this._actions.filter(action => {
            if (typeof action.visible === 'function') {
                return action.visible(row);
            }
            return action.visible !== false;
        });

        const actions = visibleActions.map(action => `
            <button class="dg-action-btn ${action.className || ''}" data-action="${action.key}">
                ${action.icon || ''} ${action.label}
            </button>
        `).join('');

        return `
            <div class="dg-card" data-row-index="${index}" data-row-key="${row[rowKey] || index}">
                <div class="dg-card-header">
                    <span class="dg-card-title">${title}</span>
                </div>
                <div class="dg-card-body">
                    ${fields}
                </div>
                ${visibleActions.length > 0 ? `<div class="dg-card-actions">${actions}</div>` : ''}
            </div>
        `;
    }

    _renderFooter() {
        // No mostrar footer si está cargando o no hay datos
        if (this._loading || this._data.length === 0) return '';

        const t = window.t || ((key) => key);
        const totalFiltered = this._filteredData.length;
        const totalOriginal = this._data.length;
        const hasFilters = this._filters.length > 0;

        // Información de registros
        let recordsInfo = '';
        if (this._pagination.enabled && this._paginationInfo) {
            const { startIndex, endIndex, totalItems } = this._paginationInfo;
            recordsInfo = `${t('dataGrid.showing')} ${startIndex + 1}-${endIndex} ${t('dataGrid.of')} ${totalItems} ${t('dataGrid.records')}`;
        } else {
            if (hasFilters && totalFiltered !== totalOriginal) {
                recordsInfo = `${totalFiltered} ${t('dataGrid.records')} (${t('dataGrid.filteredFrom')} ${totalOriginal})`;
            } else {
                recordsInfo = `${totalFiltered} ${t('dataGrid.records')}`;
            }
        }

        // Controles de paginación
        const paginationControls = this._pagination.enabled && this._paginationInfo
            ? this._renderPaginationControls()
            : '';

        return `
            <div class="dg-footer">
                <div class="dg-footer-info">${recordsInfo}</div>
                ${paginationControls}
            </div>
        `;
    }

    _renderPaginationControls() {
        if (!this._paginationInfo) return '';

        const { currentPage, totalPages } = this._paginationInfo;

        // Generar botones de página
        let pageButtons = '';
        const maxVisiblePages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        if (endPage - startPage < maxVisiblePages - 1) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        if (startPage > 1) {
            pageButtons += `<button class="dg-page-btn" data-page="1">1</button>`;
            if (startPage > 2) {
                pageButtons += `<span class="dg-page-ellipsis">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            pageButtons += `<button class="dg-page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                pageButtons += `<span class="dg-page-ellipsis">...</span>`;
            }
            pageButtons += `<button class="dg-page-btn" data-page="${totalPages}">${totalPages}</button>`;
        }

        return `
            <div class="dg-footer-pagination">
                <button class="dg-page-btn dg-page-prev" data-page="${currentPage - 1}" ${currentPage <= 1 ? 'disabled' : ''}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
                </button>
                ${pageButtons}
                <button class="dg-page-btn dg-page-next" data-page="${currentPage + 1}" ${currentPage >= totalPages ? 'disabled' : ''}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
            </div>
        `;
    }

    // ==================== EVENT HANDLING ====================

    _attachEventListeners() {
        // Sorting
        this.querySelectorAll('.dg-th-label.clickable').forEach(label => {
            label.addEventListener('click', (e) => {
                const columnKey = e.currentTarget.dataset.column;
                const column = this._columns.find(c => c.key === columnKey);
                if (column) this._toggleSort(column);
            });
        });

        // Filter buttons
        this.querySelectorAll('.dg-filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const columnKey = e.currentTarget.dataset.column;
                const column = this._columns.find(c => c.key === columnKey);
                if (column) this._openFilterPopup(column, e);
            });
        });

        // Filter chip remove
        this.querySelectorAll('.dg-chip-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const column = e.currentTarget.dataset.column;
                this._clearFilter(column);
            });
        });

        // Clear all filters
        const clearAllBtn = this.querySelector('.dg-clear-all-filters');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearFilters());
        }

        // Pagination
        this.querySelectorAll('.dg-page-btn:not([disabled])').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt(e.currentTarget.dataset.page);
                if (page) this.setPage(page);
            });
        });

        // Action buttons
        this.querySelectorAll('.dg-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const actionKey = e.currentTarget.dataset.action;
                const rowEl = e.currentTarget.closest('[data-row-index]');
                const rowIndex = parseInt(rowEl.dataset.rowIndex);
                const row = this._displayData[rowIndex];

                this._dispatchEvent('action', { action: actionKey, row, rowIndex });
            });
        });

        // Row click
        this.querySelectorAll('[data-row-index]').forEach(rowEl => {
            rowEl.addEventListener('click', (e) => {
                // Ignorar si se hizo clic en un botón de acción
                if (e.target.closest('.dg-action-btn') || e.target.closest('.dg-filter-btn')) return;

                const rowIndex = parseInt(rowEl.dataset.rowIndex);
                const row = this._displayData[rowIndex];
                this._dispatchEvent('row-click', { row, rowIndex });
            });
        });
    }

    _handleResize() {
        this._render();
    }

    _dispatchEvent(name, detail) {
        this.dispatchEvent(new CustomEvent(name, {
            detail,
            bubbles: true,
            composed: true
        }));
    }
}

// Registrar el custom element
customElements.define('data-grid', DataGrid);
