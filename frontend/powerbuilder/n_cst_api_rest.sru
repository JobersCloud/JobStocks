HA$PBExportHeader$n_cst_api_rest.sru
forward
global type n_cst_api_rest from nonvisualobject
end type
end forward

global type n_cst_api_rest from nonvisualobject autoinstantiate
end type

type variables
// URL base de la API
Protected String is_base_url = "http://localhost:5000"

// API Key para autenticacion
Protected String is_api_key = ""

// Connection ID (empresa_cli_id) para multi-empresa
Protected String is_connection = ""

// Ultimo error
Protected String is_last_error = ""

// Ultimo codigo HTTP
Protected Integer ii_last_http_code = 0

// HTTPClient para las peticiones
Protected HTTPClient ihc_client
end variables

forward prototypes
public function string of_get_last_error ()
public function integer of_get_last_http_code ()
public subroutine of_set_base_url (string as_url)
public subroutine of_set_api_key (string as_key)
public subroutine of_set_connection (string as_connection)
protected function string of_append_connection (string as_endpoint)
protected function string of_http_get (string as_endpoint)
protected function string of_http_post (string as_endpoint, string as_body)
protected function string of_http_put (string as_endpoint, string as_body)
protected function string of_http_delete (string as_endpoint)
public function string of_login (string as_username, string as_password)
public function string of_get_stocks ()
public function string of_search_stocks (string as_formato, string as_serie, string as_calidad, string as_color, decimal adec_existencias_min)
public function string of_get_stock_detail (string as_codigo)
public function string of_get_propuestas_pendientes (boolean ab_incluir_lineas)
public function string of_get_propuesta (long al_id)
public function string of_get_propuesta_lineas (long al_propuesta_id)
public function string of_actualizar_estado_propuesta (long al_id, string as_estado)
end prototypes

public function string of_get_last_error ();
// Retorna el ultimo error
Return is_last_error
end function

public function integer of_get_last_http_code ();
// Retorna el ultimo codigo HTTP
Return ii_last_http_code
end function

public subroutine of_set_base_url (string as_url);
// Establece la URL base de la API
is_base_url = as_url

// Quitar barra final si existe
If Right(is_base_url, 1) = "/" Then
   is_base_url = Left(is_base_url, Len(is_base_url) - 1)
End If
end subroutine

public subroutine of_set_api_key (string as_key);
// Establece la API Key para autenticacion
is_api_key = as_key
end subroutine

public subroutine of_set_connection (string as_connection);
// Establece el ID de conexion (empresa_cli_id) para multi-empresa
is_connection = Trim(as_connection)
end subroutine

protected function string of_append_connection (string as_endpoint);
// Agrega el parametro connection al endpoint si esta configurado
String ls_result

ls_result = as_endpoint

If Len(is_connection) > 0 Then
   If Pos(ls_result, "?") > 0 Then
      ls_result = ls_result + "&connection=" + is_connection
   Else
      ls_result = ls_result + "?connection=" + is_connection
   End If
End If

Return ls_result
end function

protected function string of_http_get (string as_endpoint);
// Realiza una peticion GET
String ls_url, ls_response
Integer li_rc

is_last_error = ""
ii_last_http_code = 0

// Crear cliente HTTP
ihc_client = Create HTTPClient

// Configurar headers
ihc_client.SetRequestHeader("Content-Type", "application/json")
ihc_client.SetRequestHeader("Accept", "application/json")

// Agregar API Key si existe
If Len(is_api_key) > 0 Then
   ihc_client.SetRequestHeader("X-API-Key", is_api_key)
End If

// Construir URL (con connection si aplica)
ls_url = is_base_url + of_append_connection(as_endpoint)

// Realizar peticion
li_rc = ihc_client.SendRequest("GET", ls_url)

If li_rc = 1 Then
   ii_last_http_code = ihc_client.GetResponseStatusCode()
   ihc_client.GetResponseBody(ls_response)
Else
   is_last_error = "Error de conexion: " + String(li_rc)
   ls_response = '{"success": false, "error": "' + is_last_error + '"}'
End If

Destroy ihc_client

Return ls_response
end function

protected function string of_http_post (string as_endpoint, string as_body);
// Realiza una peticion POST
String ls_url, ls_response
Integer li_rc

is_last_error = ""
ii_last_http_code = 0

// Crear cliente HTTP
ihc_client = Create HTTPClient

// Configurar headers
ihc_client.SetRequestHeader("Content-Type", "application/json")
ihc_client.SetRequestHeader("Accept", "application/json")

// Agregar API Key si existe
If Len(is_api_key) > 0 Then
   ihc_client.SetRequestHeader("X-API-Key", is_api_key)
End If

// Construir URL (con connection si aplica)
ls_url = is_base_url + of_append_connection(as_endpoint)

// Realizar peticion
li_rc = ihc_client.SendRequest("POST", ls_url, as_body)

If li_rc = 1 Then
   ii_last_http_code = ihc_client.GetResponseStatusCode()
   ihc_client.GetResponseBody(ls_response)
Else
   is_last_error = "Error de conexion: " + String(li_rc)
   ls_response = '{"success": false, "error": "' + is_last_error + '"}'
End If

Destroy ihc_client

Return ls_response
end function

protected function string of_http_put (string as_endpoint, string as_body);
// Realiza una peticion PUT
String ls_url, ls_response
Integer li_rc

is_last_error = ""
ii_last_http_code = 0

// Crear cliente HTTP
ihc_client = Create HTTPClient

// Configurar headers
ihc_client.SetRequestHeader("Content-Type", "application/json")
ihc_client.SetRequestHeader("Accept", "application/json")

// Agregar API Key si existe
If Len(is_api_key) > 0 Then
   ihc_client.SetRequestHeader("X-API-Key", is_api_key)
End If

// Construir URL (con connection si aplica)
ls_url = is_base_url + of_append_connection(as_endpoint)

// Realizar peticion
li_rc = ihc_client.SendRequest("PUT", ls_url, as_body)

If li_rc = 1 Then
   ii_last_http_code = ihc_client.GetResponseStatusCode()
   ihc_client.GetResponseBody(ls_response)
Else
   is_last_error = "Error de conexion: " + String(li_rc)
   ls_response = '{"success": false, "error": "' + is_last_error + '"}'
End If

Destroy ihc_client

Return ls_response
end function

protected function string of_http_delete (string as_endpoint);
// Realiza una peticion DELETE
String ls_url, ls_response
Integer li_rc

is_last_error = ""
ii_last_http_code = 0

// Crear cliente HTTP
ihc_client = Create HTTPClient

// Configurar headers
ihc_client.SetRequestHeader("Content-Type", "application/json")
ihc_client.SetRequestHeader("Accept", "application/json")

// Agregar API Key si existe
If Len(is_api_key) > 0 Then
   ihc_client.SetRequestHeader("X-API-Key", is_api_key)
End If

// Construir URL (con connection si aplica)
ls_url = is_base_url + of_append_connection(as_endpoint)

// Realizar peticion
li_rc = ihc_client.SendRequest("DELETE", ls_url)

If li_rc = 1 Then
   ii_last_http_code = ihc_client.GetResponseStatusCode()
   ihc_client.GetResponseBody(ls_response)
Else
   is_last_error = "Error de conexion: " + String(li_rc)
   ls_response = '{"success": false, "error": "' + is_last_error + '"}'
End If

Destroy ihc_client

Return ls_response
end function

public function string of_login (string as_username, string as_password);
// Iniciar sesion y obtener cookie de sesion
String ls_body, ls_response

ls_body = '{"username": "' + as_username + '", "password": "' + as_password + '"}'
ls_response = of_http_post("/api/login", ls_body)

Return ls_response
end function

public function string of_get_stocks ();
// Obtener todos los stocks
Return of_http_get("/api/stocks")
end function

public function string of_search_stocks (string as_formato, string as_serie, string as_calidad, string as_color, decimal adec_existencias_min);
// Buscar stocks con filtros
String ls_endpoint, ls_params

ls_endpoint = "/api/stocks/search?"
ls_params = ""

If Len(Trim(as_formato)) > 0 Then
   ls_params += "formato=" + as_formato + "&"
End If

If Len(Trim(as_serie)) > 0 Then
   ls_params += "serie=" + as_serie + "&"
End If

If Len(Trim(as_calidad)) > 0 Then
   ls_params += "calidad=" + as_calidad + "&"
End If

If Len(Trim(as_color)) > 0 Then
   ls_params += "color=" + as_color + "&"
End If

If adec_existencias_min > 0 Then
   ls_params += "existencias_min=" + String(adec_existencias_min) + "&"
End If

// Quitar ultimo &
If Right(ls_params, 1) = "&" Then
   ls_params = Left(ls_params, Len(ls_params) - 1)
End If

Return of_http_get(ls_endpoint + ls_params)
end function

public function string of_get_stock_detail (string as_codigo);
// Obtener detalle de un stock
Return of_http_get("/api/stocks/" + as_codigo)
end function

public function string of_get_propuestas_pendientes (boolean ab_incluir_lineas);
// Obtener propuestas pendientes de procesar
String ls_endpoint

ls_endpoint = "/api/propuestas/pendientes"

If ab_incluir_lineas Then
   ls_endpoint += "?incluir_lineas=true"
End If

Return of_http_get(ls_endpoint)
end function

public function string of_get_propuesta (long al_id);
// Obtener detalle de una propuesta
Return of_http_get("/api/propuestas/" + String(al_id))
end function

public function string of_get_propuesta_lineas (long al_propuesta_id);
// Obtener lineas de propuesta
String ls_endpoint

ls_endpoint = "/api/propuestas/lineas"

If al_propuesta_id > 0 Then
   ls_endpoint += "?propuesta_id=" + String(al_propuesta_id)
End If

Return of_http_get(ls_endpoint)
end function

public function string of_actualizar_estado_propuesta (long al_id, string as_estado);
// Actualizar estado de una propuesta
String ls_body

ls_body = '{"estado": "' + as_estado + '"}'

Return of_http_put("/api/propuestas/" + String(al_id) + "/estado", ls_body)
end function

on n_cst_api_rest.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_cst_api_rest.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
