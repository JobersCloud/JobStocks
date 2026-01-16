# Guía de Migración - w_propuestas_main

## Problema Identificado

La ventana `w_propuestas_main` NO está cargando los datos porque **los nombres de los campos JSON que busca NO existen en la API**.

### Campos que la ventana buscaba (INCORRECTOS):
```
Cabecera:
❌ numero_propuesta
❌ cliente
❌ fecha_creacion
❌ usuario_creacion
❌ observaciones
❌ referencia
❌ numero_lineas

Líneas:
❌ codigo_articulo
❌ precio_unitario
❌ descuento
❌ total_linea
❌ linea
```

### Campos que la API REALMENTE devuelve:
```json
Cabecera (GET /api/propuestas/pendientes):
{
  "success": true,
  "total": 1,
  "propuestas": [
    {
      "id": 1,
      "user_id": 1,
      "fecha": "2024-01-15T10:30:00",
      "comentarios": "Urgente para cliente",
      "estado": "Enviada",
      "total_items": 3,
      "fecha_modificacion": "2024-01-15T10:30:00",
      "username": "admin",
      "full_name": "Administrador",
      "email": "admin@empresa.com"
    }
  ]
}

Líneas (GET /api/propuestas/{id}/lineas):
{
  "success": true,
  "propuesta_id": 1,
  "total": 3,
  "lineas": [
    {
      "id": 1,
      "propuesta_id": 1,
      "codigo": "ART001",
      "descripcion": "Azulejo 30x30",
      "formato": "30x30",
      "calidad": "1ª",
      "color": "Blanco",
      "tono": "T1",
      "calibre": "C1",
      "pallet": "1200",
      "caja": "60",
      "unidad": "M2",
      "existencias": 5000.00,
      "cantidad_solicitada": 100.00
    }
  ]
}
```

---

## Solución: Migración Paso a Paso

### PASO 1: Actualizar DataObjects

#### A) Modificar `d_propuestas_pendientes`

Abrir el DataObject en PowerBuilder y asegurarse que tenga estas columnas:

```
Columnas:
- id               (Number, formato: ####0)
- user_id          (Number, formato: ####0)
- fecha            (DateTime, formato: dd/mm/yyyy hh:mm:ss)
- fecha_modificacion (DateTime, formato: dd/mm/yyyy hh:mm:ss)
- estado           (Char(20))
- comentarios      (Char(500))
- total_items      (Number, formato: ##0)
- usuario          (Char(100)) - Computed o columna normal
- email            (Char(100))
```

**Display de columnas sugerido:**
- ID | Usuario | Email | Estado | Items | Fecha | Comentarios

#### B) Modificar `d_propuesta_lineas`

```
Columnas:
- id                   (Number, formato: ####0)
- propuesta_id         (Number, formato: ####0)
- codigo               (Char(30))
- descripcion          (Char(200))
- formato              (Char(20))
- calidad              (Char(10))
- color                (Char(30))
- tono                 (Char(10))
- calibre              (Char(10))
- pallet               (Char(20))
- caja                 (Char(20))
- unidad               (Char(10))
- existencias          (Decimal(2), formato: ###,##0.00)
- cantidad_solicitada  (Decimal(2), formato: ###,##0.00)
```

**Display de columnas sugerido:**
- Código | Descripción | Formato | Calidad | Color | Cantidad | Unidad

---

### PASO 2: Reemplazar Función `wf_parse_propuestas_json`

Abrir `w_propuestas_main` en PowerBuilder y reemplazar COMPLETAMENTE la función `wf_parse_propuestas_json`:

**ANTES (líneas 156-260):**
```powerscript
public function boolean wf_parse_propuestas_json(string as_json);
// ... código ANTIGUO que busca campos incorrectos
```

**DESPUÉS:**
```powerscript
public function boolean wf_parse_propuestas_json(string as_json);
// Parsear JSON de propuestas y cargar en datawindow
Long ll_row, ll_index, ll_id, ll_user_id, ll_total_items
String ls_item, ls_estado, ls_fecha, ls_fecha_mod, ls_comentarios
String ls_username, ls_full_name, ls_email
DateTime ldt_fecha, ldt_fecha_mod
String ls_propuestas_json
Long ll_array_start, ll_array_end
Long ll_dot

// Buscar el array "propuestas" en el JSON
ll_array_start = Pos(as_json, '"propuestas":')

If ll_array_start > 0 Then
	ll_array_start = Pos(as_json, '[', ll_array_start)
	ll_array_end = Pos(as_json, ']', ll_array_start)
	ls_propuestas_json = Mid(as_json, ll_array_start, ll_array_end - ll_array_start + 1)
Else
	ls_propuestas_json = as_json
End If

ll_index = 1
Do While True
	ls_item = wf_get_json_array_item(ls_propuestas_json, ll_index)
	If Len(ls_item) = 0 Then Exit

	ll_row = dw_propuestas.InsertRow(0)

	// CAMPOS REALES DE LA API
	ll_id = Long(wf_get_json_value(ls_item, "id"))
	ll_user_id = Long(wf_get_json_value(ls_item, "user_id"))
	ls_estado = wf_get_json_value(ls_item, "estado")
	ls_fecha = wf_get_json_value(ls_item, "fecha")
	ls_fecha_mod = wf_get_json_value(ls_item, "fecha_modificacion")
	ls_comentarios = wf_get_json_value(ls_item, "comentarios")
	ll_total_items = Long(wf_get_json_value(ls_item, "total_items"))
	ls_username = wf_get_json_value(ls_item, "username")
	ls_full_name = wf_get_json_value(ls_item, "full_name")
	ls_email = wf_get_json_value(ls_item, "email")

	// Setear valores
	dw_propuestas.SetItem(ll_row, "id", ll_id)
	dw_propuestas.SetItem(ll_row, "user_id", ll_user_id)
	dw_propuestas.SetItem(ll_row, "estado", ls_estado)
	dw_propuestas.SetItem(ll_row, "total_items", ll_total_items)

	// Usuario (preferir nombre completo)
	If Len(ls_full_name) > 0 Then
		dw_propuestas.SetItem(ll_row, "usuario", ls_full_name)
	ElseIf Len(ls_username) > 0 Then
		dw_propuestas.SetItem(ll_row, "usuario", ls_username)
	End If

	If Len(ls_email) > 0 Then dw_propuestas.SetItem(ll_row, "email", ls_email)
	If Len(ls_comentarios) > 0 Then dw_propuestas.SetItem(ll_row, "comentarios", ls_comentarios)

	// Parsear fecha creación
	If Len(ls_fecha) > 0 Then
		ls_fecha = wf_replace(ls_fecha, 'T', ' ')
		ll_dot = Pos(ls_fecha, '.')
		If ll_dot > 0 Then ls_fecha = Left(ls_fecha, ll_dot - 1)

		If Len(ls_fecha) >= 19 Then
			ldt_fecha = DateTime(Date(Left(ls_fecha, 10)), Time(Mid(ls_fecha, 12)))
			dw_propuestas.SetItem(ll_row, "fecha", ldt_fecha)
		End If
	End If

	// Parsear fecha modificación
	If Len(ls_fecha_mod) > 0 Then
		ls_fecha_mod = wf_replace(ls_fecha_mod, 'T', ' ')
		ll_dot = Pos(ls_fecha_mod, '.')
		If ll_dot > 0 Then ls_fecha_mod = Left(ls_fecha_mod, ll_dot - 1)

		If Len(ls_fecha_mod) >= 19 Then
			ldt_fecha_mod = DateTime(Date(Left(ls_fecha_mod, 10)), Time(Mid(ls_fecha_mod, 12)))
			dw_propuestas.SetItem(ll_row, "fecha_modificacion", ldt_fecha_mod)
		End If
	End If

	ll_index = ll_index + 1
Loop

Return True
end function
```

---

### PASO 3: Reemplazar Función `wf_parse_lineas_json`

**ANTES (líneas 262-325):**
```powerscript
public function boolean wf_parse_lineas_json(string as_json);
// ... código ANTIGUO que busca codigo_articulo, precio_unitario, etc.
```

**DESPUÉS:**
```powerscript
public function boolean wf_parse_lineas_json(string as_json);
// Parsear JSON de líneas
Long ll_row, ll_index, ll_id, ll_propuesta_id
String ls_item, ls_codigo, ls_descripcion
String ls_formato, ls_calidad, ls_color, ls_tono, ls_calibre, ls_pallet, ls_caja, ls_unidad
String ls_existencias, ls_cantidad
Decimal ldec_existencias, ldec_cantidad
String ls_lineas_json
Long ll_array_start, ll_array_end

// Buscar array "lineas"
ll_array_start = Pos(as_json, '"lineas":')

If ll_array_start > 0 Then
	ll_array_start = Pos(as_json, '[', ll_array_start)
	ll_array_end = Pos(as_json, ']', ll_array_start)
	ls_lineas_json = Mid(as_json, ll_array_start, ll_array_end - ll_array_start + 1)
Else
	ls_lineas_json = as_json
End If

ll_index = 1
Do While True
	ls_item = wf_get_json_array_item(ls_lineas_json, ll_index)
	If Len(ls_item) = 0 Then Exit

	ll_row = dw_lineas.InsertRow(0)

	// CAMPOS REALES DE LA API
	ll_id = Long(wf_get_json_value(ls_item, "id"))
	ll_propuesta_id = Long(wf_get_json_value(ls_item, "propuesta_id"))
	ls_codigo = wf_get_json_value(ls_item, "codigo")  // NO "codigo_articulo"
	ls_descripcion = wf_get_json_value(ls_item, "descripcion")
	ls_formato = wf_get_json_value(ls_item, "formato")
	ls_calidad = wf_get_json_value(ls_item, "calidad")
	ls_color = wf_get_json_value(ls_item, "color")
	ls_tono = wf_get_json_value(ls_item, "tono")
	ls_calibre = wf_get_json_value(ls_item, "calibre")
	ls_pallet = wf_get_json_value(ls_item, "pallet")
	ls_caja = wf_get_json_value(ls_item, "caja")
	ls_unidad = wf_get_json_value(ls_item, "unidad")
	ls_existencias = wf_get_json_value(ls_item, "existencias")
	ls_cantidad = wf_get_json_value(ls_item, "cantidad_solicitada")

	// Convertir numéricos
	If Len(ls_existencias) > 0 Then ldec_existencias = Dec(ls_existencias) Else ldec_existencias = 0
	If Len(ls_cantidad) > 0 Then ldec_cantidad = Dec(ls_cantidad) Else ldec_cantidad = 0

	// Setear valores
	dw_lineas.SetItem(ll_row, "id", ll_id)
	dw_lineas.SetItem(ll_row, "propuesta_id", ll_propuesta_id)
	dw_lineas.SetItem(ll_row, "codigo", ls_codigo)
	dw_lineas.SetItem(ll_row, "descripcion", ls_descripcion)
	dw_lineas.SetItem(ll_row, "formato", ls_formato)
	dw_lineas.SetItem(ll_row, "calidad", ls_calidad)
	dw_lineas.SetItem(ll_row, "color", ls_color)
	dw_lineas.SetItem(ll_row, "tono", ls_tono)
	dw_lineas.SetItem(ll_row, "calibre", ls_calibre)
	dw_lineas.SetItem(ll_row, "pallet", ls_pallet)
	dw_lineas.SetItem(ll_row, "caja", ls_caja)
	dw_lineas.SetItem(ll_row, "unidad", ls_unidad)
	dw_lineas.SetItem(ll_row, "existencias", ldec_existencias)
	dw_lineas.SetItem(ll_row, "cantidad_solicitada", ldec_cantidad)

	ll_index = ll_index + 1
Loop

Return True
end function
```

---

### PASO 4: Agregar Botón "Marcar como Procesada" (OPCIONAL)

1. Abrir la ventana `w_propuestas_main` en el diseñador
2. Agregar un CommandButton:
   - Nombre: `cb_marcar_procesada`
   - Texto: "Marcar como Procesada"
   - Posición: Junto al botón "Actualizar"

3. Agregar el siguiente código al evento `clicked`:

```powerscript
event cb_marcar_procesada::clicked;
Long ll_row, ll_propuesta_id
String ls_response

ll_row = dw_propuestas.GetRow()

If ll_row <= 0 Then
	MessageBox("Aviso", "Seleccione una propuesta primero")
	Return
End If

ll_propuesta_id = dw_propuestas.GetItemNumber(ll_row, "id")

If MessageBox("Confirmar", "¿Marcar propuesta " + String(ll_propuesta_id) + " como Procesada?", Question!, YesNo!) = 2 Then
	Return
End If

// Configurar API
in_api.of_set_base_url(sle_url.Text)
in_api.of_set_api_key(sle_apikey.Text)

// Mostrar estado
st_status.Text = "Actualizando estado..."
st_status.BackColor = RGB(255, 255, 0)

// Llamar API
ls_response = in_api.of_actualizar_estado_propuesta(ll_propuesta_id, "Procesada")

// Verificar respuesta
If in_api.of_get_last_http_code() = 200 Then
	st_status.Text = "Estado actualizado correctamente"
	st_status.BackColor = RGB(0, 255, 0)
	dw_propuestas.SetItem(ll_row, "estado", "Procesada")
	MessageBox("Éxito", "Propuesta marcada como Procesada")
Else
	st_status.Text = "Error HTTP: " + String(in_api.of_get_last_http_code())
	st_status.BackColor = RGB(255, 0, 0)
	MessageBox("Error", "Error al actualizar estado: " + in_api.of_get_last_error())
End If
end event
```

---

## Verificación Post-Migración

### Checklist:

1. ☐ DataObjects actualizados con columnas correctas
2. ☐ Función `wf_parse_propuestas_json` reemplazada
3. ☐ Función `wf_parse_lineas_json` reemplazada
4. ☐ Compilado sin errores
5. ☐ Probado con API en ejecución

### Pruebas:

1. **Cargar propuestas pendientes:**
   - Click en botón "Cargar Datos"
   - Verificar que aparezcan propuestas en el grid superior
   - Verificar estado: "Propuestas cargadas: X"

2. **Ver líneas de propuesta:**
   - Click en una propuesta del grid superior
   - Verificar que aparezcan líneas en el grid inferior
   - Verificar estado: "Líneas cargadas: X"

3. **Cambiar estado (si agregaste el botón):**
   - Seleccionar una propuesta
   - Click en "Marcar como Procesada"
   - Verificar que el estado cambie a "Procesada"

---

## Problemas Comunes

### Error: "Column 'usuario' not found"
**Solución:** Agregar la columna `usuario` (string/char) al DataObject `d_propuestas_pendientes`

### Error: "Column 'cantidad_solicitada' not found"
**Solución:** Agregar la columna `cantidad_solicitada` (decimal) al DataObject `d_propuesta_lineas`

### Las fechas salen vacías
**Solución:** Verificar que las columnas `fecha` y `fecha_modificacion` sean de tipo DateTime

### HTTP 401 - No autenticado
**Solución:** Verificar que el API Key sea correcto y esté vigente

### HTTP 500 - Error del servidor
**Solución:** Verificar que el backend Flask esté en ejecución en el puerto 5000

---

## Contacto

Si tienes problemas con la migración, revisa:
1. El archivo `w_propuestas_main_mejorado.txt` con el código completo
2. La documentación Swagger en `http://localhost:5000/apidocs/`
3. Los logs del servidor Flask en la consola
