# Sistema Multi-Empresa

## 📋 Descripción

El sistema ApiRestExternos soporta **múltiples empresas** mediante un sistema de filtrado por empresa. Un mismo usuario puede acceder a datos de diferentes empresas simplemente cambiando el parámetro de empresa en la URL.

## 🚀 Funcionalidad

### Concepto

- **NO vinculado al usuario**: El `empresa_id` no se almacena en la tabla `users`
- **Parámetro OBLIGATORIO**: El parámetro `empresa` en la URL es **OBLIGATORIO** en el primer acceso
- **Multi-sesión**: Permite abrir múltiples navegadores/pestañas con empresas diferentes simultáneamente
- **Persistencia local**: El `empresa_id` se guarda en `localStorage` del navegador
- **Validación estricta**: Si no hay `empresa` en URL ni en localStorage, se muestra error crítico

### Flujo de Trabajo

1. **Usuario DEBE acceder al login con parámetro empresa** (OBLIGATORIO):
   ```
   http://localhost:5000/login.html?empresa=1   ✅ CORRECTO
   http://localhost:5000/login.html?empresa=2   ✅ CORRECTO
   http://localhost:5000/login.html              ❌ ERROR (sin parámetro)
   ```

2. **El sistema valida y guarda el empresa_id**:
   - Verifica que exista `?empresa=X` en la URL o en localStorage
   - Si no existe, muestra **pantalla de error crítico** y detiene la inicialización
   - Se almacena en `localStorage.setItem('empresa_id', 'X')`
   - Persiste entre recargas de página

3. **Todas las peticiones incluyen el empresa_id**:
   ```javascript
   GET /api/stocks?empresa=1
   GET /api/stocks/search?empresa=1&calidad=Primera
   GET /api/stocks/PROD001?empresa=1
   ```

4. **El backend filtra los datos por empresa**:
   ```sql
   SELECT * FROM view_externos_stock WHERE empresa LIKE '%1%'
   ```

## 📁 Archivos Modificados

### Frontend

#### `frontend/js/login.js`
```javascript
// Capturar empresa_id de la URL (OBLIGATORIO)
function getEmpresaFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const empresa = urlParams.get('empresa');

    if (empresa) {
        // Guardar en localStorage
        localStorage.setItem('empresa_id', empresa);
        console.log(`Empresa seleccionada: ${empresa}`);
        return empresa;
    } else {
        // Si no viene en URL, verificar si hay una guardada
        const empresaGuardada = localStorage.getItem('empresa_id');
        if (empresaGuardada) {
            console.log(`Usando empresa guardada: ${empresaGuardada}`);
            return empresaGuardada;
        } else {
            // ERROR: No hay empresa en URL ni en localStorage
            return null;
        }
    }
}

// Mostrar error crítico cuando falta el parámetro empresa
function showCriticalError() {
    // Reemplaza todo el contenido de la página con pantalla de error
    document.body.innerHTML = `
        <div style="...">
            <h1>Parámetro Obligatorio Faltante</h1>
            <p>Esta aplicación requiere el parámetro <strong>empresa</strong> en la URL.</p>
            <div>${window.location.origin}${window.location.pathname}<strong>?empresa=1</strong></div>
        </div>
    `;
}

// En initLogin() se valida empresa_id
async function initLogin() {
    await I18n.init();
    const empresaId = getEmpresaFromURL();

    if (!empresaId) {
        // ERROR CRÍTICO: detener inicialización
        console.error('ERROR: Parámetro empresa obligatorio no encontrado');
        showCriticalError();
        return;
    }

    // Continuar con la inicialización normal...
}
```

#### `frontend/js/app.js`
```javascript
// Obtener empresa_id del localStorage (OBLIGATORIO)
function getEmpresaId() {
    const empresaId = localStorage.getItem('empresa_id');
    if (!empresaId) {
        console.error('ERROR: No hay empresa_id en localStorage');
        return null;
    }
    console.log(`📍 Empresa actual: ${empresaId}`);
    return empresaId;
}

// Agregar empresa_id a los parámetros de búsqueda
function addEmpresaToParams(params) {
    const empresaId = getEmpresaId();
    if (empresaId) {
        params.append('empresa', empresaId);
    }
    return params;
}

// En window.onload se valida empresa_id
window.onload = async function() {
    console.log('🚀 Iniciando aplicación...');

    // VALIDAR EMPRESA_ID OBLIGATORIO
    const empresaId = getEmpresaId();
    if (!empresaId) {
        console.error('❌ ERROR CRÍTICO: No hay empresa_id en localStorage');
        showCriticalError();
        return; // Detener la inicialización
    }

    // Continuar con la inicialización normal...
};
```

### Backend

#### `backend/controllers/stock_controller.py`
```python
@staticmethod
def get_all():
    """Obtener todos los stocks (con filtro opcional por empresa)"""
    try:
        empresa = request.args.get('empresa')

        if empresa:
            filtros = {'empresa': empresa}
            stocks = StockModel.search(filtros)
        else:
            stocks = StockModel.get_all()

        return jsonify(stocks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### `backend/models/stock_model.py`
```python
@staticmethod
def get_by_codigo_and_empresa(codigo, empresa):
    """Obtiene un stock por código y empresa"""
    conn = Database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
               formato, serie, unidad, pallet, caja, existencias
        FROM view_externos_stock
        WHERE codigo = ? AND empresa LIKE ?
    """, (codigo, f"%{empresa}%"))
    # ...
```

## 🎯 Endpoints Afectados

### Stocks

Todos los endpoints de stocks ahora soportan el parámetro `empresa`:

| Endpoint | Parámetro | Ejemplo |
|----------|-----------|---------|
| `GET /api/stocks` | `?empresa=1` | `/api/stocks?empresa=1` |
| `GET /api/stocks/search` | `?empresa=1` | `/api/stocks/search?empresa=1&calidad=Primera` |
| `GET /api/stocks/<codigo>` | `?empresa=1` | `/api/stocks/PROD001?empresa=1` |
| `GET /api/stocks/<codigo>/imagenes` | `?empresa=1` | `/api/stocks/PROD001/imagenes?empresa=1` |
| `GET /api/stocks/resumen` | `?empresa=1` | `/api/stocks/resumen?empresa=1` |

### Propuestas

Los endpoints de propuestas también filtran por empresa:

| Endpoint | Parámetro | Ejemplo |
|----------|-----------|---------|
| `GET /api/propuestas/pendientes` | `?empresa=1` | `/api/propuestas/pendientes?empresa=1` |
| `POST /api/carrito/enviar` | Body: `empresa_id` | `{"comentarios": "...", "empresa_id": "1"}` |

## 🔍 Ejemplo de Uso

### Escenario: Usuario con acceso a 2 empresas

**Navegador 1 - Chrome (Empresa 1)**:
```
1. Acceder a: http://localhost:5000/login.html?empresa=1
2. Login con credenciales
3. Ver stocks de Empresa 1
```

**Navegador 2 - Firefox (Empresa 2)**:
```
1. Acceder a: http://localhost:5000/login.html?empresa=2
2. Login con las MISMAS credenciales
3. Ver stocks de Empresa 2
```

Ambas sesiones funcionan simultáneamente sin conflictos.

## 📊 Base de Datos

### Vista: `view_externos_stock`

La vista ya contiene el campo `empresa`:

```sql
SELECT
    empresa,      -- Campo que identifica la empresa
    codigo,
    descripcion,
    formato,
    serie,
    calidad,
    color,
    tono,
    calibre,
    unidad,
    pallet,
    caja,
    existencias
FROM view_externos_stock
WHERE empresa LIKE '%1%'  -- Filtrado por empresa
```

### Tabla: `propuestas`

La tabla de propuestas incluye el campo `empresa_id`:

```sql
CREATE TABLE propuestas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    empresa_id VARCHAR(5) NOT NULL DEFAULT '1',  -- 🔑 Campo multi-empresa (obligatorio)
    fecha DATETIME DEFAULT GETDATE(),
    comentarios VARCHAR(MAX),
    estado VARCHAR(20) DEFAULT 'Enviada',
    total_items INT,
    fecha_modificacion DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT DF_propuestas_empresa_id DEFAULT '1' FOR empresa_id
);

CREATE INDEX IX_propuestas_empresa_id ON propuestas(empresa_id);
```

**Importante**:
- `empresa_id` es **NOT NULL** con valor por defecto `'1'`
- Las propuestas existentes se actualizan automáticamente con `empresa_id = '1'`
- Las nuevas propuestas **siempre** tienen un `empresa_id` asignado
- Permite filtrar propuestas por empresa: `WHERE empresa_id = '1'`

## ⚙️ Configuración

### Parámetro Obligatorio

⚠️ **IMPORTANTE**: El parámetro `empresa` en la URL es **OBLIGATORIO** en el primer acceso. No existe valor por defecto.

Si intentas acceder sin el parámetro, verás una **pantalla de error crítico**:

```
❌ http://localhost:5000/login.html              → ERROR
✅ http://localhost:5000/login.html?empresa=1    → CORRECTO
```

### Persistencia entre Sesiones

Una vez que accedes con `?empresa=X`, el valor se guarda en `localStorage` y **persiste** entre:
- Recargas de página
- Cierre y apertura del navegador (mismo perfil)
- Navegación entre páginas de la aplicación

### Cambiar de Empresa

Para cambiar de empresa en una sesión activa:

1. **Opción 1**: Acceder nuevamente al login con nuevo parámetro:
   ```
   http://localhost:5000/login.html?empresa=3
   ```

2. **Opción 2**: Modificar localStorage manualmente (consola del navegador):
   ```javascript
   localStorage.setItem('empresa_id', '3');
   location.reload();
   ```

3. **Opción 3**: Limpiar localStorage y volver a entrar:
   ```javascript
   localStorage.removeItem('empresa_id');
   location.href = '/login?empresa=3';
   ```

## 🛠️ Desarrollo Futuro

### Mejoras Propuestas

1. **Selector de Empresa en UI**:
   - Dropdown en el header para cambiar empresa sin recargar
   - `<select id="empresa-selector">...</select>`

2. **Gestión de Empresas**:
   - Tabla `empresas` con configuración
   - Endpoint `/api/empresas` para listar empresas disponibles

3. **Permisos por Empresa**:
   - Tabla `user_empresas` vinculando usuarios con empresas permitidas
   - Validación en backend de acceso por empresa

4. **Indicador Visual**:
   - Mostrar nombre de empresa actual en header
   - Color diferente por empresa para distinguir visualmente

## 🐛 Troubleshooting

### Problema: Pantalla de error "Parámetro Obligatorio Faltante"

**Causa**: Intentaste acceder a la aplicación sin el parámetro `?empresa=X` en la URL y no hay valor guardado en localStorage.

**Solución**:
1. Accede siempre con la URL correcta: `http://localhost:5000/login?empresa=1`
2. No uses marcadores/favoritos sin el parámetro empresa
3. Si guardas la URL en marcadores, incluye el parámetro: `?empresa=1`

### Problema: No se filtran los datos por empresa

**Solución**:
1. Verificar que `localStorage.getItem('empresa_id')` tenga valor (consola del navegador)
2. Revisar en Network tab (F12) que las peticiones incluyan `?empresa=X`
3. Comprobar que la vista `view_externos_stock` tenga el campo `empresa`
4. Verificar logs en consola del navegador

### Problema: Datos de otra empresa aparecen mezclados

**Solución**:
1. Limpiar caché del navegador
2. Borrar localStorage: `localStorage.clear()` (en consola)
3. Reiniciar sesión con URL correcta: `/login?empresa=X`

### Problema: Al abrir nueva pestaña no mantiene la empresa

**Solución**:
Esto es comportamiento esperado. localStorage es compartido entre pestañas del mismo origen. Si quieres empresas diferentes:
- Usa navegadores diferentes (Chrome vs Firefox)
- Usa modo incógnito en otro navegador
- Usa perfiles de Chrome diferentes

### Problema: "Sesión Inválida" al acceder a la aplicación principal

**Causa**: Accediste directamente a `http://localhost:5000/` sin haber pasado por el login con parámetro empresa.

**Solución**:
1. Cierra la pestaña
2. Accede primero al login: `http://localhost:5000/login?empresa=1`
3. Inicia sesión normalmente
4. El empresa_id se guardará y podrás navegar libremente

## 📝 Notas Técnicas

- **Almacenamiento**: `localStorage` (persistente, específico por dominio)
- **Filtrado SQL**: Usa `LIKE '%empresa%'` para buscar en campo de texto
- **Sin autenticación extra**: No requiere API keys diferentes por empresa
- **Compatible**: Funciona con autenticación por sesión y por API Key

---

**Implementado**: 2025-12-29
**Versión**: 1.0
**Autor**: Claude Code
