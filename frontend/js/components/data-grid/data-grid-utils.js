/**
 * Data Grid Utilities
 * Funciones de filtrado, ordenación y utilidades para el componente data-grid
 */

// ==================== OPERADORES DE FILTRO ====================

export const TEXT_OPERATORS = [
    { key: 'contains', label: 'dataGrid.opContains', default: true },
    { key: 'not_contains', label: 'dataGrid.opNotContains' },
    { key: 'eq', label: 'dataGrid.opEquals' },
    { key: 'neq', label: 'dataGrid.opNotEquals' },
    { key: 'starts', label: 'dataGrid.opStartsWith' },
    { key: 'not_starts', label: 'dataGrid.opNotStartsWith' },
    { key: 'ends', label: 'dataGrid.opEndsWith' },
    { key: 'not_ends', label: 'dataGrid.opNotEndsWith' }
];

export const NUMBER_OPERATORS = [
    { key: 'eq', label: 'dataGrid.opEquals', default: true },
    { key: 'neq', label: 'dataGrid.opNotEquals' },
    { key: 'gt', label: 'dataGrid.opGreaterThan' },
    { key: 'gte', label: 'dataGrid.opGreaterOrEqual' },
    { key: 'lt', label: 'dataGrid.opLessThan' },
    { key: 'lte', label: 'dataGrid.opLessOrEqual' },
    { key: 'between', label: 'dataGrid.opBetween' },
    { key: 'not_between', label: 'dataGrid.opNotBetween' }
];

export const DATE_OPERATORS = [
    { key: 'eq', label: 'dataGrid.opEquals', default: true },
    { key: 'neq', label: 'dataGrid.opNotEquals' },
    { key: 'gt', label: 'dataGrid.opAfter' },
    { key: 'gte', label: 'dataGrid.opOnOrAfter' },
    { key: 'lt', label: 'dataGrid.opBefore' },
    { key: 'lte', label: 'dataGrid.opOnOrBefore' },
    { key: 'between', label: 'dataGrid.opBetween' },
    { key: 'not_between', label: 'dataGrid.opNotBetween' }
];

// ==================== FUNCIONES DE FILTRADO ====================

/**
 * Aplica un filtro a un valor según el operador
 * @param {*} value - Valor a evaluar
 * @param {string} operator - Operador de filtro
 * @param {*} filterValue - Valor del filtro
 * @param {*} filterValue2 - Segundo valor para operadores de rango
 * @param {string} type - Tipo de columna (text, number, date)
 * @returns {boolean} - Si el valor cumple el filtro
 */
export function applyFilter(value, operator, filterValue, filterValue2 = null, type = 'text') {
    if (value === null || value === undefined) {
        value = '';
    }

    // Normalizar valores según tipo
    if (type === 'number') {
        value = parseFloat(value) || 0;
        filterValue = parseFloat(filterValue) || 0;
        if (filterValue2 !== null) filterValue2 = parseFloat(filterValue2) || 0;
    } else if (type === 'date') {
        value = normalizeDate(value);
        filterValue = normalizeDate(filterValue);
        if (filterValue2 !== null) filterValue2 = normalizeDate(filterValue2);
    } else {
        value = String(value).toLowerCase();
        filterValue = String(filterValue).toLowerCase();
    }

    switch (operator) {
        // Operadores de texto
        case 'contains':
            return value.includes(filterValue);
        case 'not_contains':
            return !value.includes(filterValue);
        case 'starts':
            return value.startsWith(filterValue);
        case 'not_starts':
            return !value.startsWith(filterValue);
        case 'ends':
            return value.endsWith(filterValue);
        case 'not_ends':
            return !value.endsWith(filterValue);

        // Operadores de igualdad (todos los tipos)
        case 'eq':
            return value === filterValue || (type === 'text' && value == filterValue);
        case 'neq':
            return value !== filterValue && (type !== 'text' || value != filterValue);

        // Operadores numéricos/fecha
        case 'gt':
            return value > filterValue;
        case 'gte':
            return value >= filterValue;
        case 'lt':
            return value < filterValue;
        case 'lte':
            return value <= filterValue;

        // Operadores de rango
        case 'between':
            return value >= filterValue && value <= filterValue2;
        case 'not_between':
            return value < filterValue || value > filterValue2;

        default:
            return true;
    }
}

/**
 * Normaliza una fecha para comparación
 * @param {*} dateValue - Valor de fecha
 * @returns {number} - Timestamp normalizado
 */
function normalizeDate(dateValue) {
    if (!dateValue) return 0;
    const date = new Date(dateValue);
    return isNaN(date.getTime()) ? 0 : date.getTime();
}

/**
 * Filtra un array de datos según los filtros activos
 * @param {Array} data - Datos a filtrar
 * @param {Array} filters - Array de filtros activos [{column, operator, value, value2, type}]
 * @returns {Array} - Datos filtrados
 */
export function filterData(data, filters) {
    if (!filters || filters.length === 0) {
        return data;
    }

    return data.filter(row => {
        return filters.every(filter => {
            const value = row[filter.column];
            return applyFilter(value, filter.operator, filter.value, filter.value2, filter.type);
        });
    });
}

// ==================== FUNCIONES DE ORDENACIÓN ====================

/**
 * Ordena un array de datos por una columna
 * @param {Array} data - Datos a ordenar
 * @param {string} column - Nombre de la columna
 * @param {string} direction - 'asc' o 'desc'
 * @param {string} type - Tipo de columna (text, number, date)
 * @returns {Array} - Datos ordenados
 */
export function sortData(data, column, direction = 'asc', type = 'text') {
    if (!column) return data;

    return [...data].sort((a, b) => {
        let valA = a[column];
        let valB = b[column];

        // Manejar nulos
        if (valA === null || valA === undefined) valA = '';
        if (valB === null || valB === undefined) valB = '';

        // Convertir según tipo
        if (type === 'number') {
            valA = parseFloat(valA) || 0;
            valB = parseFloat(valB) || 0;
        } else if (type === 'date') {
            valA = new Date(valA).getTime() || 0;
            valB = new Date(valB).getTime() || 0;
        } else {
            valA = String(valA).toLowerCase();
            valB = String(valB).toLowerCase();
        }

        let result = 0;
        if (valA < valB) result = -1;
        else if (valA > valB) result = 1;

        return direction === 'desc' ? -result : result;
    });
}

// ==================== FUNCIONES DE PAGINACIÓN ====================

/**
 * Pagina un array de datos
 * @param {Array} data - Datos a paginar
 * @param {number} page - Página actual (1-indexed)
 * @param {number} pageSize - Elementos por página
 * @returns {Object} - {data: Array, totalPages: number, totalItems: number}
 */
export function paginateData(data, page, pageSize) {
    const totalItems = data.length;
    const totalPages = Math.ceil(totalItems / pageSize);
    const currentPage = Math.max(1, Math.min(page, totalPages || 1));
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;

    return {
        data: data.slice(startIndex, endIndex),
        currentPage,
        totalPages,
        totalItems,
        startIndex,
        endIndex: Math.min(endIndex, totalItems)
    };
}

// ==================== FUNCIONES DE FORMATO ====================

/**
 * Formatea una fecha para mostrar
 * @param {*} dateValue - Valor de fecha
 * @param {string} locale - Locale para formato
 * @returns {string} - Fecha formateada
 */
export function formatDate(dateValue, locale = 'es-ES') {
    if (!dateValue) return '-';
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return dateValue;

    return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

/**
 * Formatea fecha y hora para mostrar
 * @param {*} dateValue - Valor de fecha
 * @param {string} locale - Locale para formato
 * @returns {string} - Fecha y hora formateadas
 */
export function formatDateTime(dateValue, locale = 'es-ES') {
    if (!dateValue) return '-';
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return dateValue;

    return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Formatea un número para mostrar
 * @param {*} value - Valor numérico
 * @param {number} decimals - Decimales
 * @param {string} locale - Locale para formato
 * @returns {string} - Número formateado
 */
export function formatNumber(value, decimals = 0, locale = 'es-ES') {
    if (value === null || value === undefined || value === '') return '-';
    const num = parseFloat(value);
    if (isNaN(num)) return value;

    return num.toLocaleString(locale, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// ==================== UTILIDADES ====================

/**
 * Obtiene los operadores según el tipo de columna
 * @param {string} type - Tipo de columna
 * @returns {Array} - Array de operadores
 */
export function getOperatorsForType(type) {
    switch (type) {
        case 'number':
            return NUMBER_OPERATORS;
        case 'date':
            return DATE_OPERATORS;
        default:
            return TEXT_OPERATORS;
    }
}

/**
 * Obtiene el operador por defecto para un tipo
 * @param {string} type - Tipo de columna
 * @returns {string} - Key del operador por defecto
 */
export function getDefaultOperator(type) {
    const operators = getOperatorsForType(type);
    const defaultOp = operators.find(op => op.default);
    return defaultOp ? defaultOp.key : operators[0].key;
}

/**
 * Debounce para funciones
 * @param {Function} func - Función a ejecutar
 * @param {number} wait - Tiempo de espera en ms
 * @returns {Function} - Función con debounce
 */
export function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Genera un ID único
 * @returns {string} - ID único
 */
export function generateId() {
    return 'dg_' + Math.random().toString(36).substr(2, 9);
}
