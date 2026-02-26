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
// ARCHIVO: js/grid-filters.js
// Descripcion: Módulo reutilizable de filtros avanzados para grids
// Basado en el sistema de filtros de app.js (grid de stocks)
// ============================================

/**
 * GridFilters - Sistema de filtros avanzados reutilizable para grids.
 *
 * Uso:
 *   const gf = new GridFilters({
 *       columnasFiltrables: [
 *           { key: 'nombre', label: 'Nombre', tipo: 'texto' },
 *           { key: 'total', label: 'Total', tipo: 'numero' }
 *       ],
 *       getAllData: () => allData,
 *       onFilterApply: (datosFiltrados) => renderTable(datosFiltrados),
 *       chipsContainerId: 'column-filters-chips',
 *       storageKey: 'filtrosGuardados_miGrid'
 *   });
 */
class GridFilters {
    constructor(config) {
        this.columnasFiltrables = config.columnasFiltrables || [];
        this.getAllData = config.getAllData;          // función que retorna todos los datos
        this.onFilterApply = config.onFilterApply;    // callback con datos filtrados
        this.chipsContainerId = config.chipsContainerId || 'column-filters-chips';
        this.storageKey = config.storageKey || 'filtrosGuardados';

        // Estado interno
        this.filtrosColumna = [];
        this.popupFiltroAbierto = null;

        // Exponer a window ANTES de todo (para onclicks inline del popup)
        this._exposeToWindow();

        try {
            this.filtrosGuardados = JSON.parse(localStorage.getItem(this.storageKey) || '[]');
        } catch (e) {
            this.filtrosGuardados = [];
        }

        // Registrar event listeners globales (delegación de clicks)
        this._initEventListeners();
    }

    // ==================== CONSTANTES ====================

    static get operadoresTexto() {
        return [
            { key: 'contains', label: 'Contiene', negativo: false },
            { key: 'not_contains', label: 'No contiene', negativo: true },
            { key: 'eq', label: 'Igual a', negativo: false },
            { key: 'neq', label: 'No igual a', negativo: true },
            { key: 'starts', label: 'Empieza por', negativo: false },
            { key: 'not_starts', label: 'No empieza por', negativo: true },
            { key: 'ends', label: 'Termina en', negativo: false },
            { key: 'not_ends', label: 'No termina en', negativo: true }
        ];
    }

    static get operadoresNumero() {
        return [
            { key: 'eq', label: 'Igual a', negativo: false },
            { key: 'neq', label: 'Diferente de', negativo: true },
            { key: 'gt', label: 'Mayor que', negativo: false },
            { key: 'gte', label: 'Mayor o igual', negativo: false },
            { key: 'lt', label: 'Menor que', negativo: false },
            { key: 'lte', label: 'Menor o igual', negativo: false },
            { key: 'between', label: 'Entre', negativo: false, rango: true },
            { key: 'not_between', label: 'No entre', negativo: true, rango: true }
        ];
    }

    static get iconoFiltroSVG() {
        return `<svg viewBox="0 0 16 16" fill="currentColor" width="16" height="16"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>`;
    }

    // ==================== HELPERS ====================

    getOperadoresPorTipo(columna) {
        const col = this.columnasFiltrables.find(c => c.key === columna);
        return col?.tipo === 'numero' ? GridFilters.operadoresNumero : GridFilters.operadoresTexto;
    }

    getLabelOperador(operadorKey) {
        const op = [...GridFilters.operadoresTexto, ...GridFilters.operadoresNumero].find(o => o.key === operadorKey);
        return op?.label || operadorKey;
    }

    tieneFiltroColumna(columna) {
        return this.filtrosColumna.some(f => f.columna === columna);
    }

    // ==================== POPUP DE FILTRO ====================

    mostrarPopupFiltro(columna, elemento) {
        this.cerrarPopupFiltro();

        const col = this.columnasFiltrables.find(c => c.key === columna);
        if (!col) return;

        const operadores = this.getOperadoresPorTipo(columna);
        const filtroExistente = this.filtrosColumna.find(f => f.columna === columna);
        const valoresSeleccionados = filtroExistente?.valores || [];
        const tieneValoresSeleccionados = valoresSeleccionados.length > 0;
        const tieneCondicion = filtroExistente?.valor && !tieneValoresSeleccionados;

        // Obtener valores únicos de los datos FILTRADOS (excluyendo filtro de esta columna)
        let datosFiltrados = [...(this.getAllData() || [])];

        this.filtrosColumna.forEach(filtro => {
            if (filtro.columna !== columna) {
                datosFiltrados = this._filtrarDatos(datosFiltrados, filtro);
            }
        });

        const valores = datosFiltrados
            .map(item => item[columna])
            .filter(v => v !== null && v !== undefined && v !== '');
        const valoresUnicos = [...new Set(valores)].sort((a, b) =>
            String(a).localeCompare(String(b), 'es', { numeric: true })
        ).slice(0, 100);

        // Crear el popup
        const popup = document.createElement('div');
        popup.className = 'filter-popup';
        popup.id = `filter-popup-${columna}`;

        popup.innerHTML = `
            <div class="filter-popup-header">
                <span class="filter-popup-icon">${GridFilters.iconoFiltroSVG}</span>
                <span class="filter-popup-title">${col.label}</span>
                <button class="filter-popup-close" onclick="gridFilters.cerrarPopupFiltro()" title="Cerrar">×</button>
            </div>
            <div class="filter-popup-tabs">
                <button class="filter-tab ${!tieneCondicion ? 'active' : ''}" id="filter-tab-valores-${columna}"
                        onclick="gridFilters.cambiarTabFiltro('${columna}', 'valores')">
                    <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/><path d="M10.97 4.97a.75.75 0 0 1 1.071 1.05l-3.992 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.235.235 0 0 1 .02-.022z"/></svg>
                    Valores
                </button>
                <button class="filter-tab ${tieneCondicion ? 'active' : ''}" id="filter-tab-condicion-${columna}"
                        onclick="gridFilters.cambiarTabFiltro('${columna}', 'condicion')">
                    <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/></svg>
                    Condición
                </button>
            </div>
            <div class="filter-popup-body">
                <!-- Contenido pestaña VALORES -->
                <div class="filter-tab-content" id="filter-content-valores-${columna}" style="display: ${!tieneCondicion ? 'block' : 'none'};">
                    <div class="filter-search-box">
                        <input type="text" class="filter-search-input" id="filter-search-${columna}"
                               placeholder="Buscar..." oninput="gridFilters.filtrarValoresPopup('${columna}')">
                    </div>
                    ${valoresUnicos.length > 0 ? `
                    <div class="filter-popup-values" id="filter-values-list-${columna}">
                        <label class="filter-value-item filter-value-select-all">
                            <input type="checkbox" class="filter-value-checkbox"
                                   onchange="gridFilters.toggleSelectAllValores('${columna}', this.checked)">
                            <span class="filter-value-text">(Seleccionar todo)</span>
                        </label>
                        ${valoresUnicos.map(v => `
                            <label class="filter-value-item" data-valor="${String(v).toLowerCase()}">
                                <input type="checkbox" class="filter-value-checkbox" value="${v}"
                                       ${valoresSeleccionados.includes(String(v)) ? 'checked' : ''}>
                                <span class="filter-value-text">${v}</span>
                            </label>
                        `).join('')}
                    </div>
                    ` : '<p class="filter-no-values">No hay valores disponibles</p>'}
                </div>
                <!-- Contenido pestaña CONDICIÓN -->
                <div class="filter-tab-content" id="filter-content-condicion-${columna}" style="display: ${tieneCondicion ? 'block' : 'none'};">
                    <div class="filter-condition-operators">
                        ${operadores.map((op, idx) => `
                            <label class="filter-condition-option ${op.negativo ? 'negativo' : ''} ${op.rango ? 'rango' : ''}">
                                <input type="radio" name="op-${columna}" value="${op.key}"
                                       ${(filtroExistente?.operador === op.key || (!filtroExistente && idx === 0)) ? 'checked' : ''}
                                       onchange="gridFilters.toggleRangoInputs('${columna}', '${op.key}')">
                                <span class="filter-radio-dot"></span>
                                <span>${op.label}</span>
                            </label>
                        `).join('')}
                    </div>
                    <div class="filter-inputs-container">
                        <input type="text" class="filter-condition-input" id="filter-value-${columna}"
                               placeholder="Escribir valor..." value="${filtroExistente?.valor || ''}"
                               onkeypress="if(event.key==='Enter') gridFilters.aplicarFiltroColumna('${columna}')">
                        <div class="filter-range-inputs" id="filter-range-${columna}" style="display: none;">
                            <input type="number" class="filter-condition-input filter-range-from" id="filter-from-${columna}"
                                   placeholder="Desde" value="${filtroExistente?.valorDesde || ''}">
                            <span class="filter-range-separator">y</span>
                            <input type="number" class="filter-condition-input filter-range-to" id="filter-to-${columna}"
                                   placeholder="Hasta" value="${filtroExistente?.valorHasta || ''}"
                                   onkeypress="if(event.key==='Enter') gridFilters.aplicarFiltroColumna('${columna}')">
                        </div>
                    </div>
                </div>
                <!-- Filtros guardados -->
                <div class="filter-saved-section" id="filter-saved-${columna}">
                    ${this.filtrosGuardados.length > 0 ? `
                    <div class="filter-saved-header">
                        <span class="filter-saved-title">Filtros guardados</span>
                    </div>
                    <div class="filter-saved-list">
                        ${this.filtrosGuardados.map((fg, idx) => `
                            <div class="filter-saved-item" onclick="gridFilters.cargarFiltroGuardado(${idx})">
                                <span class="filter-saved-name">${fg.nombre}</span>
                                <span class="filter-saved-count">${fg.filtros.length} filtros</span>
                                <button class="filter-saved-delete" onclick="event.stopPropagation(); gridFilters.eliminarFiltroGuardado(${idx})" title="Eliminar">×</button>
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
            </div>
            <div class="filter-popup-footer">
                <button class="btn-filter-clear" onclick="gridFilters.limpiarFiltroColumna('${columna}')" title="Limpiar">
                    <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                </button>
                ${this.filtrosColumna.length > 0 ? `
                <button class="btn-filter-save" onclick="gridFilters.guardarFiltrosActuales()" title="Guardar filtros actuales">
                    <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><path d="M2 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H9.5a1 1 0 0 0-1 1v7.293l2.646-2.647a.5.5 0 0 1 .708.708l-3.5 3.5a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L7.5 9.293V2a2 2 0 0 1 2-2H14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h2.5a.5.5 0 0 1 0 1H2z"/></svg>
                </button>
                ` : ''}
                <button class="btn-filter-apply" onclick="gridFilters.aplicarFiltroColumna('${columna}')" title="Aplicar">
                    <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg>
                </button>
            </div>
        `;

        // Posicionar el popup - primero añadir al DOM para medir
        popup.style.position = 'fixed';
        popup.style.zIndex = '1000';
        popup.style.visibility = 'hidden';
        document.body.appendChild(popup);

        const rect = elemento.getBoundingClientRect();
        const popupRect = popup.getBoundingClientRect();
        const viewportH = window.innerHeight;
        const viewportW = window.innerWidth;
        const popupW = Math.max(popupRect.width, 260);
        const popupH = popupRect.height;

        // Horizontal: no salir por la derecha
        let left = rect.left;
        if (left + popupW > viewportW - 10) {
            left = viewportW - popupW - 10;
        }
        if (left < 10) left = 10;

        // Vertical: si no cabe abajo, poner arriba
        let top;
        const spaceBelow = viewportH - rect.bottom - 10;
        const spaceAbove = rect.top - 10;
        if (spaceBelow >= popupH || spaceBelow >= spaceAbove) {
            top = rect.bottom + 5;
        } else {
            top = rect.top - popupH - 5;
        }

        // Asegurar que no se salga por arriba ni por abajo
        const maxH = viewportH - 20;
        if (popupH > maxH) {
            popup.style.maxHeight = maxH + 'px';
            popup.style.overflowY = 'auto';
            top = 10;
        } else if (top < 10) {
            top = 10;
        } else if (top + popupH > viewportH - 10) {
            top = viewportH - popupH - 10;
        }

        popup.style.top = `${top}px`;
        popup.style.left = `${left}px`;
        popup.style.visibility = 'visible';
        this.popupFiltroAbierto = popup;

        // Si tiene un filtro de rango existente, mostrar los inputs de rango
        if (filtroExistente && (filtroExistente.operador === 'between' || filtroExistente.operador === 'not_between')) {
            this.toggleRangoInputs(columna, filtroExistente.operador);
        }
    }

    cerrarPopupFiltro() {
        if (this.popupFiltroAbierto) {
            this.popupFiltroAbierto.remove();
            this.popupFiltroAbierto = null;
        }
        document.querySelectorAll('.filter-popup').forEach(p => p.remove());
    }

    // ==================== TABS ====================

    cambiarTabFiltro(columna, tab) {
        const tabValores = document.getElementById(`filter-tab-valores-${columna}`);
        const tabCondicion = document.getElementById(`filter-tab-condicion-${columna}`);
        const contentValores = document.getElementById(`filter-content-valores-${columna}`);
        const contentCondicion = document.getElementById(`filter-content-condicion-${columna}`);

        if (tab === 'valores') {
            tabValores.classList.add('active');
            tabCondicion.classList.remove('active');
            contentValores.style.display = 'block';
            contentCondicion.style.display = 'none';
            const inputCondicion = document.getElementById(`filter-value-${columna}`);
            if (inputCondicion) inputCondicion.value = '';
        } else {
            tabCondicion.classList.add('active');
            tabValores.classList.remove('active');
            contentCondicion.style.display = 'block';
            contentValores.style.display = 'none';
            const checkboxes = document.querySelectorAll(`#filter-values-list-${columna} input[type="checkbox"]`);
            checkboxes.forEach(cb => cb.checked = false);
            setTimeout(() => document.getElementById(`filter-value-${columna}`)?.focus(), 50);
        }
    }

    // ==================== VALORES POPUP ====================

    filtrarValoresPopup(columna) {
        const busqueda = document.getElementById(`filter-search-${columna}`)?.value.toLowerCase() || '';
        const items = document.querySelectorAll(`#filter-values-list-${columna} .filter-value-item:not(.filter-value-select-all)`);
        let visibles = 0;
        items.forEach(item => {
            const texto = item.dataset.valor?.toLowerCase() || '';
            const visible = texto.includes(busqueda);
            item.style.display = visible ? 'flex' : 'none';
            if (visible) visibles++;
        });
        const selectAll = document.querySelector(`#filter-values-list-${columna} .filter-value-select-all`);
        if (selectAll) selectAll.style.display = visibles > 0 ? 'flex' : 'none';
    }

    toggleSelectAllValores(columna, checked) {
        const checkboxes = document.querySelectorAll(`#filter-values-list-${columna} input[type="checkbox"]`);
        checkboxes.forEach(cb => {
            if (cb.closest('.filter-value-item').style.display !== 'none') {
                cb.checked = checked;
            }
        });
    }

    toggleRangoInputs(columna, operador) {
        const rangeContainer = document.getElementById(`filter-range-${columna}`);
        const valueInput = document.getElementById(`filter-value-${columna}`);
        const esRango = operador === 'between' || operador === 'not_between';

        if (rangeContainer && valueInput) {
            rangeContainer.style.display = esRango ? 'flex' : 'none';
            valueInput.style.display = esRango ? 'none' : 'block';
        }
    }

    // ==================== APLICAR / LIMPIAR FILTROS ====================

    aplicarFiltroColumna(columna) {
        // Capturar valores ANTES de cerrar el popup
        const inputValor = document.getElementById(`filter-value-${columna}`);
        const radioSeleccionado = document.querySelector(`input[name="op-${columna}"]:checked`);
        const inputFrom = document.getElementById(`filter-from-${columna}`);
        const inputTo = document.getElementById(`filter-to-${columna}`);

        const valorInput = inputValor?.value.trim() || '';
        const operador = radioSeleccionado?.value || 'contains';
        const esRango = operador === 'between' || operador === 'not_between';
        const valorDesde = inputFrom?.value.trim() || '';
        const valorHasta = inputTo?.value.trim() || '';

        // Obtener valores seleccionados de checkboxes
        const todosCheckboxes = document.querySelectorAll(`#filter-values-list-${columna} .filter-value-item:not(.filter-value-select-all) input[type="checkbox"]`);
        const checkboxesMarcados = document.querySelectorAll(`#filter-values-list-${columna} .filter-value-item:not(.filter-value-select-all) input[type="checkbox"]:checked`);
        const valoresSeleccionados = Array.from(checkboxesMarcados).map(cb => cb.value);
        const todosSeleccionados = todosCheckboxes.length > 0 && todosCheckboxes.length === checkboxesMarcados.length;

        // Cerrar popup
        this.cerrarPopupFiltro();

        // Procesar filtro
        if (esRango) {
            if (!valorDesde && !valorHasta) {
                this.limpiarFiltroColumna(columna);
                return;
            }
            this.filtrosColumna = this.filtrosColumna.filter(f => f.columna !== columna);
            this.filtrosColumna.push({ columna, operador, valorDesde: valorDesde || null, valorHasta: valorHasta || null });
        } else if (todosSeleccionados) {
            this.limpiarFiltroColumna(columna);
            return;
        } else if (valoresSeleccionados.length > 0) {
            this.filtrosColumna = this.filtrosColumna.filter(f => f.columna !== columna);
            this.filtrosColumna.push({ columna, operador: 'in', valores: valoresSeleccionados });
        } else if (valorInput) {
            this.filtrosColumna = this.filtrosColumna.filter(f => f.columna !== columna);
            this.filtrosColumna.push({ columna, operador, valor: valorInput });
        } else {
            this.limpiarFiltroColumna(columna);
            return;
        }

        this._notifyFilterChange();
    }

    limpiarFiltroColumna(columna) {
        this.filtrosColumna = this.filtrosColumna.filter(f => f.columna !== columna);
        this.cerrarPopupFiltro();
        this._notifyFilterChange();
    }

    quitarFiltroColumna(index) {
        this.filtrosColumna.splice(index, 1);
        this._notifyFilterChange();
    }

    limpiarTodosFiltrosColumna() {
        this.filtrosColumna = [];
        this._notifyFilterChange();
    }

    // ==================== FILTROS GUARDADOS ====================

    guardarFiltrosActuales() {
        if (this.filtrosColumna.length === 0) {
            UIFeedback.toast('No hay filtros para guardar', 'warning');
            return;
        }
        const nombre = prompt('Nombre para guardar los filtros:');
        if (!nombre || !nombre.trim()) return;

        this.filtrosGuardados.push({
            nombre: nombre.trim(),
            filtros: [...this.filtrosColumna],
            fecha: new Date().toISOString()
        });
        localStorage.setItem(this.storageKey, JSON.stringify(this.filtrosGuardados));
        this.cerrarPopupFiltro();
        UIFeedback.toast(`Filtros guardados como "${nombre}"`, 'success');
    }

    cargarFiltroGuardado(index) {
        const filtroGuardado = this.filtrosGuardados[index];
        if (!filtroGuardado) return;

        this.filtrosColumna = [...filtroGuardado.filtros];
        this.cerrarPopupFiltro();
        this._notifyFilterChange();
    }

    async eliminarFiltroGuardado(index) {
        if (!await UIFeedback.confirm({ message: '¿Eliminar este filtro guardado?', type: 'danger' })) return;
        this.filtrosGuardados.splice(index, 1);
        localStorage.setItem(this.storageKey, JSON.stringify(this.filtrosGuardados));
        this.cerrarPopupFiltro();
    }

    // ==================== APLICAR FILTROS A DATOS ====================

    aplicarFiltrosADatos(datos) {
        let resultado = [...datos];
        this.filtrosColumna.forEach(filtro => {
            resultado = this._filtrarDatos(resultado, filtro);
        });
        return resultado;
    }

    _filtrarDatos(datos, filtro) {
        return datos.filter(item => {
            const valorItem = (item[filtro.columna] || '').toString();
            const valorItemLower = valorItem.toLowerCase();
            const valorNumerico = parseFloat(valorItem);

            // Operador 'in' para multi-selección
            if (filtro.operador === 'in' && filtro.valores) {
                return filtro.valores.some(v => valorItemLower === v.toLowerCase());
            }

            // Operadores de rango
            if (filtro.operador === 'between' || filtro.operador === 'not_between') {
                const desde = filtro.valorDesde ? parseFloat(filtro.valorDesde) : -Infinity;
                const hasta = filtro.valorHasta ? parseFloat(filtro.valorHasta) : Infinity;
                const dentroRango = valorNumerico >= desde && valorNumerico <= hasta;
                return filtro.operador === 'between' ? dentroRango : !dentroRango;
            }

            const valorBuscar = (filtro.valor || '').toLowerCase();

            switch (filtro.operador) {
                case 'eq': return valorItemLower === valorBuscar;
                case 'contains': return valorItemLower.includes(valorBuscar);
                case 'starts': return valorItemLower.startsWith(valorBuscar);
                case 'ends': return valorItemLower.endsWith(valorBuscar);
                case 'neq': return valorItemLower !== valorBuscar;
                case 'not_contains': return !valorItemLower.includes(valorBuscar);
                case 'not_starts': return !valorItemLower.startsWith(valorBuscar);
                case 'not_ends': return !valorItemLower.endsWith(valorBuscar);
                case 'gt': return valorNumerico > parseFloat(filtro.valor);
                case 'gte': return valorNumerico >= parseFloat(filtro.valor);
                case 'lt': return valorNumerico < parseFloat(filtro.valor);
                case 'lte': return valorNumerico <= parseFloat(filtro.valor);
                default: return valorItemLower.includes(valorBuscar);
            }
        });
    }

    // ==================== ICONOS DE FILTRO ====================

    actualizarIconosFiltro() {
        this.columnasFiltrables.forEach(col => {
            const icono = document.querySelector(`.column-filter-btn[data-columna="${col.key}"]`);
            if (icono) {
                if (this.tieneFiltroColumna(col.key)) {
                    icono.classList.add('active');
                } else {
                    icono.classList.remove('active');
                }
            }
        });
    }

    // ==================== CHIPS DE FILTROS ====================

    renderizarChipsFiltrosColumna() {
        const container = document.getElementById(this.chipsContainerId);
        if (!container) return;

        if (this.filtrosColumna.length === 0) {
            container.innerHTML = '';
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex';

        const chipsHTML = this.filtrosColumna.map((filtro, idx) => {
            const labelColumna = this.columnasFiltrables.find(c => c.key === filtro.columna)?.label || filtro.columna;
            const esNegativo = filtro.operador?.startsWith('not_') || filtro.operador === 'neq';
            const chipClass = esNegativo ? 'filter-chip filter-chip-negative' : 'filter-chip';

            if (filtro.operador === 'in' && filtro.valores) {
                const count = filtro.valores.length;
                const valorMostrar = count <= 2
                    ? filtro.valores.join(', ')
                    : `${filtro.valores[0]}, ${filtro.valores[1]}... (+${count - 2})`;
                return `
                    <span class="filter-chip filter-chip-multi">
                        <span class="filter-chip-column">${labelColumna}:</span>
                        <span class="filter-chip-operator">es uno de</span>
                        <span class="filter-chip-value" title="${filtro.valores.join(', ')}">${valorMostrar}</span>
                        <span class="filter-chip-remove" onclick="gridFilters.quitarFiltroColumna(${idx})">✕</span>
                    </span>
                `;
            } else if (filtro.operador === 'between' || filtro.operador === 'not_between') {
                const desde = filtro.valorDesde || '∞';
                const hasta = filtro.valorHasta || '∞';
                const labelOperador = filtro.operador === 'between' ? 'entre' : 'no entre';
                return `
                    <span class="${chipClass}">
                        <span class="filter-chip-column">${labelColumna}:</span>
                        <span class="filter-chip-operator">${labelOperador}</span>
                        <span class="filter-chip-value">${desde} y ${hasta}</span>
                        <span class="filter-chip-remove" onclick="gridFilters.quitarFiltroColumna(${idx})">✕</span>
                    </span>
                `;
            } else {
                const labelOperador = this.getLabelOperador(filtro.operador);
                return `
                    <span class="${chipClass}">
                        <span class="filter-chip-column">${labelColumna}:</span>
                        <span class="filter-chip-operator">${labelOperador.toLowerCase()}</span>
                        <span class="filter-chip-value" title="${filtro.valor}">"${filtro.valor}"</span>
                        <span class="filter-chip-remove" onclick="gridFilters.quitarFiltroColumna(${idx})">✕</span>
                    </span>
                `;
            }
        }).join('');

        container.innerHTML = chipsHTML + `
            <button class="btn-icon btn-icon-ghost btn-icon-sm" onclick="gridFilters.limpiarTodosFiltrosColumna()" title="Limpiar todo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
        `;
    }

    // ==================== INTERNAL ====================

    _notifyFilterChange() {
        this.renderizarChipsFiltrosColumna();
        this.actualizarIconosFiltro();

        if (this.onFilterApply) {
            const datos = this.getAllData ? this.getAllData() : [];
            const filtrados = this.aplicarFiltrosADatos(datos);
            this.onFilterApply(filtrados);
        }
    }

    _initEventListeners() {
        const self = this;

        // FASE CAPTURA: interceptar clics en botones de filtro ANTES de cualquier onclick inline
        document.addEventListener('click', (e) => {
            const filterBtn = e.target.closest('.column-filter-btn');
            if (filterBtn) {
                e.stopPropagation();
                e.preventDefault();
                const columna = filterBtn.dataset.columna || filterBtn.getAttribute('data-columna');
                if (columna) {
                    self.mostrarPopupFiltro(columna, filterBtn);
                }
                return;
            }
        }, true); // true = capture phase

        // FASE BURBUJA: cerrar popup al clic fuera
        document.addEventListener('click', (e) => {
            if (self.popupFiltroAbierto) {
                if (!self.popupFiltroAbierto.contains(e.target)) {
                    self.cerrarPopupFiltro();
                }
            }
        });

        // Cerrar con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && self.popupFiltroAbierto) {
                self.cerrarPopupFiltro();
            }
        });

        // Cerrar al scroll de la pagina (no del contenedor de tabla)
        window.addEventListener('scroll', (e) => {
            if (self.popupFiltroAbierto) {
                if (e.target === document || e.target === document.documentElement) {
                    self.cerrarPopupFiltro();
                }
            }
        }, true);
    }

    _exposeToWindow() {
        // Exponer la instancia como `gridFilters` en window para onclick inline
        window.gridFilters = this;
    }
}
