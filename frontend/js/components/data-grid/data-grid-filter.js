/**
 * Data Grid Filter Popup
 * Componente para el popup de filtros por columna
 */

import { getOperatorsForType, getDefaultOperator } from './data-grid-utils.js';

export class DataGridFilter {
    constructor(grid) {
        this.grid = grid;
        this.popup = null;
        this.currentColumn = null;
        this.onApply = null;
        this.onClear = null;

        // Bind de eventos externos
        this._boundHandleClickOutside = this._handleClickOutside.bind(this);
        this._boundHandleKeydown = this._handleKeydown.bind(this);
        this._boundHandleScroll = this._handleScroll.bind(this);
    }

    /**
     * Abre el popup de filtro para una columna
     * @param {Object} column - Configuración de la columna
     * @param {HTMLElement} anchor - Elemento ancla para posicionar
     * @param {Object} currentFilter - Filtro actual si existe
     */
    open(column, anchor, currentFilter = null) {
        this.close(); // Cerrar cualquier popup previo
        this.currentColumn = column;

        const popup = this._createPopup(column, currentFilter);
        document.body.appendChild(popup);
        this.popup = popup;

        // Posicionar popup
        this._positionPopup(anchor);

        // Añadir event listeners
        setTimeout(() => {
            document.addEventListener('click', this._boundHandleClickOutside);
            document.addEventListener('keydown', this._boundHandleKeydown);
            window.addEventListener('scroll', this._boundHandleScroll, true);
        }, 10);

        // Focus en el input
        const input = popup.querySelector('.dg-filter-input');
        if (input) input.focus();
    }

    /**
     * Cierra el popup
     */
    close() {
        if (this.popup) {
            this.popup.remove();
            this.popup = null;
            this.currentColumn = null;

            document.removeEventListener('click', this._boundHandleClickOutside);
            document.removeEventListener('keydown', this._boundHandleKeydown);
            window.removeEventListener('scroll', this._boundHandleScroll, true);
        }
    }

    /**
     * Crea el elemento popup
     */
    _createPopup(column, currentFilter) {
        const popup = document.createElement('div');
        popup.className = 'dg-filter-popup';

        const operators = getOperatorsForType(column.type || 'text');
        const currentOperator = currentFilter?.operator || getDefaultOperator(column.type || 'text');
        const currentValue = currentFilter?.value || '';
        const currentValue2 = currentFilter?.value2 || '';
        const isRangeOperator = ['between', 'not_between'].includes(currentOperator);

        const t = window.t || ((key) => key);

        popup.innerHTML = `
            <div class="dg-filter-header">
                <span class="dg-filter-title">${t('dataGrid.filterBy')} ${column.label || column.key}</span>
                <button class="dg-filter-close" type="button">&times;</button>
            </div>
            <div class="dg-filter-body">
                <div class="dg-filter-tabs">
                    ${this._renderOperatorTabs(operators, currentOperator)}
                </div>
                <div class="dg-filter-inputs">
                    ${this._renderInputs(column, currentValue, currentValue2, isRangeOperator)}
                </div>
            </div>
            <div class="dg-filter-footer">
                <button class="dg-filter-btn dg-filter-btn-clear" type="button">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                    </svg>
                    ${t('dataGrid.clear')}
                </button>
                <button class="dg-filter-btn dg-filter-btn-apply" type="button">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    ${t('dataGrid.apply')}
                </button>
            </div>
        `;

        // Event listeners internos
        popup.querySelector('.dg-filter-close').addEventListener('click', () => this.close());
        popup.querySelector('.dg-filter-btn-clear').addEventListener('click', () => this._handleClear());
        popup.querySelector('.dg-filter-btn-apply').addEventListener('click', () => this._handleApply());

        // Cambio de operador
        popup.querySelectorAll('.dg-filter-operator').forEach(radio => {
            radio.addEventListener('change', (e) => this._handleOperatorChange(e, column));
        });

        // Enter en input aplica filtro
        popup.querySelectorAll('.dg-filter-input').forEach(input => {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this._handleApply();
                }
            });
        });

        return popup;
    }

    /**
     * Renderiza los radio buttons de operadores
     */
    _renderOperatorTabs(operators, currentOperator) {
        const t = window.t || ((key) => key);

        return operators.map(op => `
            <label class="dg-filter-operator-label ${op.key === currentOperator ? 'active' : ''}">
                <input type="radio" name="dg-operator" value="${op.key}"
                    class="dg-filter-operator" ${op.key === currentOperator ? 'checked' : ''}>
                <span>${t(op.label)}</span>
            </label>
        `).join('');
    }

    /**
     * Renderiza los inputs según el tipo de columna
     */
    _renderInputs(column, value, value2, isRange) {
        const t = window.t || ((key) => key);
        const type = column.type || 'text';
        let inputType = 'text';

        if (type === 'number') inputType = 'number';
        else if (type === 'date') inputType = 'date';

        const input1 = `<input type="${inputType}" class="dg-filter-input" value="${this._escapeHtml(value)}"
            placeholder="${t('dataGrid.enterValue')}">`;

        const input2 = `<input type="${inputType}" class="dg-filter-input dg-filter-input-2"
            value="${this._escapeHtml(value2)}" placeholder="${t('dataGrid.enterValue2')}"
            style="display: ${isRange ? 'block' : 'none'};">`;

        const rangeLabel = `<span class="dg-filter-range-label" style="display: ${isRange ? 'block' : 'none'};">
            ${t('dataGrid.and')}
        </span>`;

        return input1 + rangeLabel + input2;
    }

    /**
     * Maneja el cambio de operador
     */
    _handleOperatorChange(e, column) {
        const operator = e.target.value;
        const isRange = ['between', 'not_between'].includes(operator);

        // Actualizar clases activas
        this.popup.querySelectorAll('.dg-filter-operator-label').forEach(label => {
            label.classList.toggle('active', label.querySelector('input').value === operator);
        });

        // Mostrar/ocultar segundo input para rangos
        const input2 = this.popup.querySelector('.dg-filter-input-2');
        const rangeLabel = this.popup.querySelector('.dg-filter-range-label');
        if (input2) input2.style.display = isRange ? 'block' : 'none';
        if (rangeLabel) rangeLabel.style.display = isRange ? 'block' : 'none';
    }

    /**
     * Maneja aplicar filtro
     */
    _handleApply() {
        if (!this.currentColumn) return;

        const operator = this.popup.querySelector('.dg-filter-operator:checked')?.value;
        const value = this.popup.querySelector('.dg-filter-input')?.value?.trim();
        const value2 = this.popup.querySelector('.dg-filter-input-2')?.value?.trim();

        if (!value) {
            this._handleClear();
            return;
        }

        const filter = {
            column: this.currentColumn.key,
            columnLabel: this.currentColumn.label || this.currentColumn.key,
            operator,
            value,
            value2: ['between', 'not_between'].includes(operator) ? value2 : null,
            type: this.currentColumn.type || 'text'
        };

        if (this.onApply) {
            this.onApply(filter);
        }

        this.close();
    }

    /**
     * Maneja limpiar filtro
     */
    _handleClear() {
        if (this.onClear && this.currentColumn) {
            this.onClear(this.currentColumn.key);
        }
        this.close();
    }

    /**
     * Posiciona el popup relativo al ancla
     */
    _positionPopup(anchor) {
        if (!this.popup || !anchor) return;

        const rect = anchor.getBoundingClientRect();
        const popupRect = this.popup.getBoundingClientRect();

        let top = rect.bottom + 5;
        let left = rect.left;

        // Ajustar si se sale por la derecha
        if (left + popupRect.width > window.innerWidth - 10) {
            left = window.innerWidth - popupRect.width - 10;
        }

        // Ajustar si se sale por abajo
        if (top + popupRect.height > window.innerHeight - 10) {
            top = rect.top - popupRect.height - 5;
        }

        this.popup.style.top = `${top}px`;
        this.popup.style.left = `${Math.max(10, left)}px`;
    }

    /**
     * Maneja clic fuera del popup
     */
    _handleClickOutside(e) {
        if (this.popup && !this.popup.contains(e.target)) {
            this.close();
        }
    }

    /**
     * Maneja tecla Escape
     */
    _handleKeydown(e) {
        if (e.key === 'Escape') {
            this.close();
        }
    }

    /**
     * Maneja scroll
     */
    _handleScroll() {
        this.close();
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
