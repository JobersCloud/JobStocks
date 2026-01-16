# PowerBuilder 2022 - Cliente API REST

Cliente PowerBuilder para consumir la API REST de Gestión de Stocks.

## Archivos Incluidos

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `n_cst_api_rest.sru` | Non-Visual Object | Objeto para consumir la API REST |
| `w_test_api.srw` | Window | Ventana de pruebas interactiva |

## Instrucciones de Importación

### 1. Crear Workspace y Target

1. Abrir PowerBuilder 2022
2. **File > New > Workspace** - Crear workspace `api_rest_stocks.pbw`
3. **File > New > Target** - Crear target Application tipo **PowerBuilder Application**
4. Nombre: `api_rest_test`
5. Crear una nueva librería (PBL): `api_rest_test.pbl`

### 2. Importar Objetos

1. Click derecho en la librería `api_rest_test.pbl`
2. **Import...**
3. Seleccionar `n_cst_api_rest.sru` y `w_test_api.srw`
4. Click **Open**

### 3. Configurar Aplicación

1. Abrir el objeto Application (`api_rest_test`)
2. En el evento **Open**, agregar:

```powerscript
Open(w_test_api)
```

### 4. Compilar y Ejecutar

1. **Run > Full Rebuild** (Ctrl+Shift+F7)
2. **Run > Run** (Ctrl+R)

## Uso del Objeto n_cst_api_rest

### Crear Instancia

```powerscript
n_cst_api_rest ln_api
ln_api = Create n_cst_api_rest
```

### Configurar

```powerscript
// URL del servidor
ln_api.of_set_base_url("http://localhost:5000")

// API Key para autenticación
ln_api.of_set_api_key("tu-api-key-aqui")
```

### Métodos Disponibles

#### Stocks

```powerscript
// Obtener todos los stocks
String ls_json
ls_json = ln_api.of_get_stocks()

// Buscar con filtros
ls_json = ln_api.of_search_stocks(as_formato, as_serie, as_calidad, as_color, adec_existencias_min)

// Detalle de un producto
ls_json = ln_api.of_get_stock_detail("CODIGO123")
```

#### Propuestas (ERP)

```powerscript
// Propuestas pendientes
ls_json = ln_api.of_get_propuestas_pendientes(False)  // Sin líneas
ls_json = ln_api.of_get_propuestas_pendientes(True)   // Con líneas

// Detalle de propuesta
ls_json = ln_api.of_get_propuesta(123)

// Líneas de propuesta
ls_json = ln_api.of_get_propuesta_lineas(123)  // De una propuesta
ls_json = ln_api.of_get_propuesta_lineas(0)    // Todas las líneas

// Cambiar estado
ls_json = ln_api.of_actualizar_estado_propuesta(123, "Procesada")
// Estados: "Enviada", "Procesada", "Cancelada"
```

### Manejo de Errores

```powerscript
String ls_json, ls_error
Integer li_http_code

ls_json = ln_api.of_get_stocks()

// Verificar código HTTP
li_http_code = ln_api.of_get_last_http_code()

If li_http_code <> 200 Then
   ls_error = ln_api.of_get_last_error()
   MessageBox("Error", ls_error)
End If
```

### Parsear JSON (PowerBuilder 2022)

```powerscript
JsonParser ljp
String ls_json, ls_value
Long ll_count, ll_i

ls_json = ln_api.of_get_propuestas_pendientes(False)

ljp = Create JsonParser
If ljp.LoadString(ls_json) = JsonParseError! Then
   MessageBox("Error", "JSON inválido")
   Return
End If

// Leer valores
If ljp.GetItemBoolean("/success") Then
   ll_count = ljp.GetItemNumber("/total")

   For ll_i = 1 To ll_count
      ls_value = ljp.GetItemString("/propuestas[" + String(ll_i) + "]/id")
      // Procesar...
   Next
End If

Destroy ljp
```

## Requisitos

- PowerBuilder 2022 o superior
- .NET Framework 4.x (para HTTPClient)
- Conexión de red al servidor API

## Endpoints Soportados

| Método | Función | Endpoint |
|--------|---------|----------|
| GET | of_get_stocks | /api/stocks |
| GET | of_search_stocks | /api/stocks/search |
| GET | of_get_stock_detail | /api/stocks/{codigo} |
| GET | of_get_propuestas_pendientes | /api/propuestas/pendientes |
| GET | of_get_propuesta | /api/propuestas/{id} |
| GET | of_get_propuesta_lineas | /api/propuestas/lineas |
| PUT | of_actualizar_estado_propuesta | /api/propuestas/{id}/estado |
