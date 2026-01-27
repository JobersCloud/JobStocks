/**
 * Data Grid Component - Entry Point
 *
 * Uso:
 * <script type="module" src="js/components/data-grid/index.js"></script>
 *
 * <data-grid id="my-grid" data-pagination="true" data-page-size="20"></data-grid>
 *
 * <script>
 * const grid = document.getElementById('my-grid');
 * grid.columns = [...];
 * grid.actions = [...];
 * grid.data = [...];
 * </script>
 */

// Importar y registrar el componente
export { DataGrid } from './data-grid.js';
export { DataGridFilter } from './data-grid-filter.js';
export * from './data-grid-utils.js';

// El componente se registra automáticamente al importar data-grid.js
