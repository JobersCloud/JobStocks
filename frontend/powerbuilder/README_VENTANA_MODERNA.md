# Ventana Moderna de Propuestas - w_propuestas_modern

## 🎨 Características del Diseño Moderno

### Mejoras Visuales

#### 1. **Paleta de Colores Contemporánea**
- **Header azul Material Design**: RGB(0, 128, 255) con texto blanco
- **Fondo blanco limpio**: RGB(255, 255, 255)
- **Botones con colores semánticos**:
  - Cargar Datos: Azul suave RGB(33, 150, 243)
  - Marcar Procesada: Verde RGB(76, 175, 80)
  - Exportar: Gris neutro
- **Barra de estado con colores dinámicos**:
  - Cargando: Amarillo RGB(255, 235, 59)
  - Éxito: Verde RGB(76, 175, 80)
  - Error: Rojo Material RGB(244, 67, 54)
  - Listo: Gris RGB(189, 189, 189)

#### 2. **Iconos Emoji para Mejor UX**
- 📊 Gestión de Propuestas (título)
- 📋 Propuestas Pendientes
- 📦 Líneas de Propuesta
- 🔄 Cargar Datos
- 🔃 Actualizar
- ✓ Marcar Procesada
- 📥 Exportar
- 🔍 Filtrar
- ⏳ Cargando...
- ✓ Éxito
- ✗ Error
- 💡 Listo

#### 3. **Tipografía Moderna**
- **Fuente**: Segoe UI (Windows 10/11 native)
- **Código fuente monoespaciada**: Consolas para API Key
- **Tamaños jerárquicos**:
  - Header: -14 bold
  - Títulos: -11 bold
  - Labels: -9 normal
  - Botones: -9 bold

#### 4. **Coloreo Automático de Estados**
Función `wf_colorear_estados()` que aplica colores de fondo según estado:
- **Enviada**: Amarillo claro RGB(255, 249, 196)
- **Procesada**: Verde claro RGB(200, 230, 201)
- **Cancelada**: Rojo claro RGB(255, 205, 210)

### Funcionalidades Nuevas

#### 1. **Sistema de Filtros Avanzado**
- **Filtro de texto** (`sle_filtro`): Busca en usuario, email y observaciones
- **Filtro por estado** (`ddlb_estado`): Dropdown con opciones:
  - Todos
  - Enviada
  - Procesada
  - Cancelada
- Aplicación automática al modificar (evento `modified` y `selectionchanged`)

#### 2. **Información Contextual de Propuesta**
StaticText `st_propuesta_info` muestra:
```
📋 Propuesta #123 | Israel Aucejo | Estado: Enviada | Artículos: 5
```

#### 3. **Totalizadores Dinámicos**
- `st_total_propuestas`: "Total: X propuesta(s)"
- `st_total_lineas`: "Total: X línea(s)"
- Actualización automática con función `wf_actualizar_totales()`

#### 4. **Botón "Marcar como Procesada"**
- Integrado en el header junto a los botones principales
- Color verde semántico
- Confirmación antes de ejecutar
- Actualización automática del estado en el grid
- Llamada a API `PUT /api/propuestas/{id}/estado`

#### 5. **Botón Exportar** (Placeholder)
- Preparado para futuras funcionalidades
- Actualmente deshabilitado con mensaje informativo

#### 6. **Barra de Estado Inteligente**
Mensajes descriptivos con iconos:
- "💡 Listo para cargar datos"
- "⏳ Cargando propuestas y líneas..."
- "✓ Datos cargados correctamente"
- "✗ Error HTTP: 401"
- "✓ Estado actualizado correctamente"

### Arquitectura del Código

#### Variables de Instancia
```powerscript
n_cst_api_rest in_api
Long il_propuesta_seleccionada  // Almacena ID de propuesta actual
```

#### Funciones Principales

**`wf_cargar_todo()`**
- Carga propuestas y líneas en una sola llamada API
- Incluye líneas: `of_get_propuestas_pendientes(True)`
- Actualiza totales y aplica coloreo de estados

**`wf_parse_propuestas_y_lineas_json(as_json)`**
- Parseo con JSONParser (sintaxis correcta PB 2022)
- Carga propuestas en `dw_propuestas`
- Carga todas las líneas en `dw_lineas_mem` (invisible)
- Retorna Boolean (éxito/fallo)

**`wf_actualizar_totales()`**
- Cuenta filas en ambos DataWindows
- Actualiza StaticTexts de totales

**`wf_marcar_como_procesada()`**
- Valida selección de propuesta
- Confirmación con MessageBox
- Llamada API para cambiar estado
- Actualización visual del grid

**`wf_aplicar_filtros()`**
- Construye condición de filtro dinámica
- Aplica `SetFilter()` y `Filter()` en DataWindow
- Actualiza totales después de filtrar

**`wf_actualizar_info_propuesta()`**
- Extrae datos de la propuesta seleccionada
- Formatea texto informativo
- Actualiza `st_propuesta_info`

**`wf_colorear_estados()`**
- Itera filas del DataWindow de propuestas
- Aplica color de fondo según estado
- Mejora visual y legibilidad

**`wf_replace(as_source, as_old, as_new)`**
- Función auxiliar para parseo de fechas
- Reemplaza 'T' por espacio en timestamps

#### Eventos Importantes

**`dw_propuestas.clicked`**
```powerscript
// Al hacer clic en una propuesta:
1. Guarda ID en il_propuesta_seleccionada
2. Filtra dw_lineas_mem por propuesta_id
3. Copia datos filtrados a dw_lineas visible
4. Actualiza información contextual
```

**`sle_filtro.modified`**
```powerscript
// Al escribir en el filtro de texto:
- Aplica filtros automáticamente
```

**`ddlb_estado.selectionchanged`**
```powerscript
// Al cambiar el estado en dropdown:
- Aplica filtros automáticamente
```

**`open`**
```powerscript
// Inicialización de la ventana:
- Valores por defecto (URL, API Key)
- Asignación de DataObjects
- Población del dropdown de estados
- Estado inicial "Listo"
```

### Layout de Controles

#### Zona Superior (Header)
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 GESTIÓN DE PROPUESTAS - SISTEMA ERP                      │
├─────────────────────────────────────────────────────────────┤
│ URL Base: [localhost:5000] API Key: [xxx...]                │
│ [🔄 Cargar] [🔃 Actualizar] [✓ Procesada] [📥 Exportar]    │
├─────────────────────────────────────────────────────────────┤
```

#### Zona de Propuestas
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Propuestas Pendientes  Total: X   🔍 Filtrar: [___] Estado: [▼] │
├─────────────────────────────────────────────────────────────┤
│ DataWindow: Propuestas (920px altura)                       │
│ - Coloreo por estado (Enviada/Procesada/Cancelada)         │
└─────────────────────────────────────────────────────────────┘
```

#### Zona de Líneas
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Propuesta #123 | Usuario | Estado | Artículos           │
├─────────────────────────────────────────────────────────────┤
│ 📦 Líneas de Propuesta  Total: X                            │
├─────────────────────────────────────────────────────────────┤
│ DataWindow: Líneas (1120px altura)                          │
└─────────────────────────────────────────────────────────────┘
```

#### Zona Inferior (Status)
```
┌─────────────────────────────────────────────────────────────┐
│ 💡 Listo para cargar datos                                  │
└─────────────────────────────────────────────────────────────┘
```

### Tamaño de la Ventana
- **Ancho**: 5600 units (~1400px)
- **Alto**: 2800 units (~700px)
- **Resizable**: Sí
- **Min/Max boxes**: Sí

### Comparación con Ventana Anterior

| Característica | w_propuestas_main | w_propuestas_modern |
|----------------|-------------------|---------------------|
| Esquema de colores | Gris/básico | Material Design |
| Iconos | No | Sí (emoji) |
| Filtros | No | Sí (texto + estado) |
| Totalizadores | No | Sí |
| Info contextual | No | Sí |
| Coloreo estados | No | Sí (automático) |
| Marcar procesada | No | Sí |
| Fuente | Arial | Segoe UI |
| Barra estado | Simple | Inteligente con iconos |
| Tamaño | 5120x2400 | 5600x2800 |

## 📋 Requisitos

### DataObjects Necesarios

#### `d_propuestas_pendientes`
Debe tener estas columnas:
- `id` (Number)
- `user_id` (Number)
- `estado` (String)
- `numero_lineas` (Number)
- `usuario` (String)
- `email` (String)
- `observaciones` (String)
- `fecha_creacion` (DateTime)
- `fecha_modificacion` (DateTime)
- `color_fondo` (Number) - Para coloreo de estados

#### `d_propuesta_lineas`
Debe tener estas columnas:
- `id` (Number)
- `propuesta_id` (Number)
- `codigo_articulo` (String)
- `descripcion` (String)
- `formato` (String)
- `calidad` (String)
- `color` (String)
- `tono` (String)
- `calibre` (String)
- `pallet` (String)
- `caja` (String)
- `unidad` (String)
- `existencias` (Decimal)
- `cantidad` (Decimal)

### Objeto API
Requiere `n_cst_api_rest` con estos métodos:
- `of_set_base_url(string)`
- `of_set_api_key(string)`
- `of_get_propuestas_pendientes(boolean)` - boolean indica si incluir líneas
- `of_actualizar_estado_propuesta(long, string)`
- `of_get_last_http_code()` - Retorna Long
- `of_get_last_error()` - Retorna String

## 🚀 Uso

1. **Importar la ventana** en PowerBuilder:
   ```
   File > Import > PowerBuilder Object
   Seleccionar: w_propuestas_modern.srw
   ```

2. **Configurar DataObjects**:
   - Crear o modificar `d_propuestas_pendientes`
   - Crear o modificar `d_propuesta_lineas`
   - Añadir columna `color_fondo` a propuestas

3. **Abrir la ventana**:
   ```powerscript
   Open(w_propuestas_modern)
   ```

4. **Flujo de trabajo**:
   - Ingresar URL y API Key (valores por defecto cargados)
   - Click en "🔄 Cargar Datos"
   - Las propuestas aparecen coloreadas por estado
   - Click en una propuesta para ver sus líneas
   - Usar filtros para buscar propuestas específicas
   - Click en "✓ Marcar Procesada" para cambiar estado

## 🎯 Funcionalidades Futuras

- [ ] Exportar a Excel/PDF
- [ ] Impresión de propuestas
- [ ] Edición inline de líneas
- [ ] Gráficos/dashboards
- [ ] Notificaciones push
- [ ] Historial de cambios
- [ ] Comentarios colaborativos
- [ ] Adjuntos/documentos

## 🐛 Troubleshooting

**Error: "Column 'color_fondo' not found"**
- Agregar columna computed `color_fondo` tipo Number al DataObject

**Los colores no se aplican**
- Verificar que el DataObject tenga propiedad de color de fondo configurada
- Modificar la expresión de color de fondo: `color_fondo`

**Filtros no funcionan**
- Verificar nombres de columnas en DataObject
- Revisar sintaxis de SetFilter()

**API Key inválido**
- Generar nuevo API Key desde el frontend web
- Copiar key completa sin espacios

---

**Creado**: 2025-12-29
**Versión**: 1.0
**Autor**: Claude Code
**Licencia**: Proyecto ApiRestExternos
