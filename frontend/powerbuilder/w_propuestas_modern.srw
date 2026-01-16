forward
global type w_propuestas_modern from window
end type
type dw_lineas_mem from datawindow within w_propuestas_modern
end type
type st_header from statictext within w_propuestas_modern
end type
type st_url_label from statictext within w_propuestas_modern
end type
type sle_url from singlelineedit within w_propuestas_modern
end type
type st_apikey_label from statictext within w_propuestas_modern
end type
type sle_apikey from singlelineedit within w_propuestas_modern
end type
type cb_cargar from commandbutton within w_propuestas_modern
end type
type cb_refresh from commandbutton within w_propuestas_modern
end type
type cb_marcar_procesada from commandbutton within w_propuestas_modern
end type
type cb_exportar from commandbutton within w_propuestas_modern
end type
type ln_separator from line within w_propuestas_modern
end type
type st_propuestas_title from statictext within w_propuestas_modern
end type
type st_total_propuestas from statictext within w_propuestas_modern
end type
type dw_propuestas from datawindow within w_propuestas_modern
end type
type st_lineas_title from statictext within w_propuestas_modern
end type
type st_total_lineas from statictext within w_propuestas_modern
end type
type dw_lineas from datawindow within w_propuestas_modern
end type
type st_status from statictext within w_propuestas_modern
end type
type st_propuesta_info from statictext within w_propuestas_modern
end type
type sle_filtro from singlelineedit within w_propuestas_modern
end type
type st_filtro_label from statictext within w_propuestas_modern
end type
type ddlb_estado from dropdownlistbox within w_propuestas_modern
end type
type st_estado_label from statictext within w_propuestas_modern
end type
end forward

global type w_propuestas_modern from window
integer width = 5600
integer height = 2800
boolean titlebar = true
string title = "Gestión de Propuestas - Sistema ERP"
boolean controlmenu = true
boolean minbox = true
boolean maxbox = true
boolean resizable = true
long backcolor = 16777215
string icon = "AppIcon!"
dw_lineas_mem dw_lineas_mem
st_header st_header
st_url_label st_url_label
sle_url sle_url
st_apikey_label st_apikey_label
sle_apikey sle_apikey
cb_cargar cb_cargar
cb_refresh cb_refresh
cb_marcar_procesada cb_marcar_procesada
cb_exportar cb_exportar
ln_separator ln_separator
st_propuestas_title st_propuestas_title
st_total_propuestas st_total_propuestas
dw_propuestas dw_propuestas
st_lineas_title st_lineas_title
st_total_lineas st_total_lineas
dw_lineas dw_lineas
st_status st_status
st_propuesta_info st_propuesta_info
sle_filtro sle_filtro
st_filtro_label st_filtro_label
ddlb_estado ddlb_estado
st_estado_label st_estado_label
end type
global w_propuestas_modern w_propuestas_modern

type variables
n_cst_api_rest in_api
Long il_propuesta_seleccionada
end variables

forward prototypes
public subroutine wf_cargar_todo ()
public function boolean wf_parse_propuestas_y_lineas_json (string as_json)
public function string wf_replace (string as_source, string as_old, string as_new)
public subroutine wf_actualizar_totales ()
public subroutine wf_marcar_como_procesada ()
public subroutine wf_aplicar_filtros ()
public subroutine wf_actualizar_info_propuesta ()
public subroutine wf_colorear_estados ()
end prototypes

public subroutine wf_cargar_todo ();String ls_response
Boolean lb_result

dw_propuestas.Reset()
dw_lineas.Reset()
dw_lineas_mem.Reset()

in_api.of_set_base_url(sle_url.Text)
in_api.of_set_api_key(sle_apikey.Text)

st_status.Text = "⏳ Cargando propuestas y líneas..."
st_status.BackColor = RGB(255,235,59)
st_status.TextColor = RGB(0,0,0)

ls_response = in_api.of_get_propuestas_pendientes(True)

If in_api.of_get_last_http_code() = 200 Then
    lb_result = wf_parse_propuestas_y_lineas_json(ls_response)

    If lb_result Then
        wf_actualizar_totales()
        wf_colorear_estados()
        st_status.Text = "✓ Datos cargados correctamente"
        st_status.BackColor = RGB(76,175,80)
        st_status.TextColor = RGB(255,255,255)
    Else
        st_status.Text = "✗ Error al procesar datos"
        st_status.BackColor = RGB(244,67,54)
        st_status.TextColor = RGB(255,255,255)
        MessageBox("Error","No se pudo parsear la respuesta JSON")
    End If
Else
    st_status.Text = "✗ Error HTTP: " + String(in_api.of_get_last_http_code())
    st_status.BackColor = RGB(244,67,54)
    st_status.TextColor = RGB(255,255,255)
    MessageBox("Error","Error al obtener propuestas: "+in_api.of_get_last_error())
End If
end subroutine

public function boolean wf_parse_propuestas_y_lineas_json (string as_json);JsonParser lnv_parser
Long ll_root, ll_propuestas_array, ll_propuesta_obj, ll_lineas_array, ll_linea_obj
Long ll_count, ll_count_lineas, i, j
Long ll_row, ll_row_linea
Long ll_id, ll_user_id, ll_total_items
String ls_estado, ls_fecha, ls_fecha_mod, ls_comentarios, ls_email, ls_username, ls_fullname
DateTime ldt_fecha, ldt_fecha_mod
String ls_temp, ls_error
Long ll_dot

lnv_parser = Create JsonParser
ls_error = lnv_parser.LoadString(as_json)
If ls_error <> "" Then
    MessageBox("Error JSON","Error al parsear JSON: "+ls_error)
    Destroy lnv_parser
    Return False
End If

ll_root = lnv_parser.GetRootItem()

ll_propuestas_array = lnv_parser.GetItemArray(ll_root,"propuestas")
If ll_propuestas_array = 0 Then
    MessageBox("Error","No se encontró el array 'propuestas'")
    Destroy lnv_parser
    Return False
End If

ll_count = lnv_parser.GetChildCount(ll_propuestas_array)

For i = 1 To ll_count
    ll_propuesta_obj = lnv_parser.GetChildItem(ll_propuestas_array,i)
    If lnv_parser.GetItemType(ll_propuesta_obj) <> JsonObjectItem! Then Continue

    ll_row = dw_propuestas.InsertRow(0)

    ll_id = lnv_parser.GetItemNumber(ll_propuesta_obj,"id")
    dw_propuestas.SetItem(ll_row,"id",ll_id)

    ll_user_id = lnv_parser.GetItemNumber(ll_propuesta_obj,"user_id")
    dw_propuestas.SetItem(ll_row,"user_id",ll_user_id)

    ls_estado = lnv_parser.GetItemString(ll_propuesta_obj,"estado")
    dw_propuestas.SetItem(ll_row,"estado",ls_estado)

    ll_total_items = lnv_parser.GetItemNumber(ll_propuesta_obj,"total_items")
    dw_propuestas.SetItem(ll_row,"numero_lineas",ll_total_items)

    ls_email = lnv_parser.GetItemString(ll_propuesta_obj,"email")
    dw_propuestas.SetItem(ll_row,"email",ls_email)

    ls_fullname = lnv_parser.GetItemString(ll_propuesta_obj,"full_name")
    If Len(ls_fullname) > 0 Then
        dw_propuestas.SetItem(ll_row,"usuario",ls_fullname)
    Else
        ls_username = lnv_parser.GetItemString(ll_propuesta_obj,"username")
        dw_propuestas.SetItem(ll_row,"usuario",ls_username)
    End If

    ls_comentarios = lnv_parser.GetItemString(ll_propuesta_obj,"comentarios")
    dw_propuestas.SetItem(ll_row,"observaciones",ls_comentarios)

    ls_fecha = lnv_parser.GetItemString(ll_propuesta_obj,"fecha")
    If Len(ls_fecha)>0 Then
        ls_temp = wf_replace(ls_fecha,'T',' ')
        ll_dot = Pos(ls_temp,'.')
        If ll_dot>0 Then ls_temp = Left(ls_temp,ll_dot - 1)
        If Len(ls_temp) >= 19 Then
            ldt_fecha = DateTime(Date(Left(ls_temp,10)),Time(Mid(ls_temp,12)))
            dw_propuestas.SetItem(ll_row,"fecha_creacion",ldt_fecha)
        End If
    End If

    ls_fecha_mod = lnv_parser.GetItemString(ll_propuesta_obj,"fecha_modificacion")
    If Len(ls_fecha_mod)>0 And ls_fecha_mod<>"null" Then
        ls_temp = wf_replace(ls_fecha_mod,'T',' ')
        ll_dot = Pos(ls_temp,'.')
        If ll_dot>0 Then ls_temp = Left(ls_temp,ll_dot - 1)
        If Len(ls_temp) >= 19 Then
            ldt_fecha_mod = DateTime(Date(Left(ls_temp,10)),Time(Mid(ls_temp,12)))
            dw_propuestas.SetItem(ll_row,"fecha_modificacion",ldt_fecha_mod)
        End If
    End If

    ll_lineas_array = lnv_parser.GetItemArray(ll_propuesta_obj,"lineas")
    If ll_lineas_array>0 Then
        ll_count_lineas = lnv_parser.GetChildCount(ll_lineas_array)
        For j=1 To ll_count_lineas
            ll_linea_obj = lnv_parser.GetChildItem(ll_lineas_array,j)
            ll_row_linea = dw_lineas_mem.InsertRow(0)
            dw_lineas_mem.SetItem(ll_row_linea,"propuesta_id",ll_id)
            dw_lineas_mem.SetItem(ll_row_linea,"id",lnv_parser.GetItemNumber(ll_linea_obj,"id"))
            dw_lineas_mem.SetItem(ll_row_linea,"codigo_articulo",lnv_parser.GetItemString(ll_linea_obj,"codigo"))
            dw_lineas_mem.SetItem(ll_row_linea,"descripcion",lnv_parser.GetItemString(ll_linea_obj,"descripcion"))
            dw_lineas_mem.SetItem(ll_row_linea,"formato",lnv_parser.GetItemString(ll_linea_obj,"formato"))
            dw_lineas_mem.SetItem(ll_row_linea,"calidad",lnv_parser.GetItemString(ll_linea_obj,"calidad"))
            dw_lineas_mem.SetItem(ll_row_linea,"color",lnv_parser.GetItemString(ll_linea_obj,"color"))
            dw_lineas_mem.SetItem(ll_row_linea,"tono",lnv_parser.GetItemString(ll_linea_obj,"tono"))
            dw_lineas_mem.SetItem(ll_row_linea,"calibre",lnv_parser.GetItemString(ll_linea_obj,"calibre"))
            dw_lineas_mem.SetItem(ll_row_linea,"pallet",lnv_parser.GetItemString(ll_linea_obj,"pallet"))
            dw_lineas_mem.SetItem(ll_row_linea,"caja",lnv_parser.GetItemString(ll_linea_obj,"caja"))
            dw_lineas_mem.SetItem(ll_row_linea,"unidad",lnv_parser.GetItemString(ll_linea_obj,"unidad"))
            dw_lineas_mem.SetItem(ll_row_linea,"existencias",lnv_parser.GetItemDecimal(ll_linea_obj,"existencias"))
            dw_lineas_mem.SetItem(ll_row_linea,"cantidad",lnv_parser.GetItemDecimal(ll_linea_obj,"cantidad_solicitada"))
        Next
    End If
Next

Destroy lnv_parser
Return True
end function

public function string wf_replace (string as_source, string as_old, string as_new);String ls_result
Long ll_pos

ls_result = as_source
ll_pos = Pos(ls_result, as_old)

Do While ll_pos > 0
   ls_result = Left(ls_result, ll_pos - 1) + as_new + Mid(ls_result, ll_pos + Len(as_old))
   ll_pos = Pos(ls_result, as_old, ll_pos + Len(as_new))
Loop

Return ls_result
end function

public subroutine wf_actualizar_totales ();Long ll_total_prop, ll_total_lin

ll_total_prop = dw_propuestas.RowCount()
ll_total_lin = dw_lineas.RowCount()

st_total_propuestas.Text = "Total: " + String(ll_total_prop) + " propuesta(s)"
st_total_lineas.Text = "Total: " + String(ll_total_lin) + " línea(s)"
end subroutine

public subroutine wf_marcar_como_procesada ();Long ll_row
String ls_response

ll_row = dw_propuestas.GetRow()

If ll_row <= 0 Then
    MessageBox("Aviso", "Seleccione una propuesta primero")
    Return
End If

If MessageBox("Confirmar", "¿Marcar propuesta " + String(il_propuesta_seleccionada) + " como Procesada?", Question!, YesNo!) = 2 Then
    Return
End If

in_api.of_set_base_url(sle_url.Text)
in_api.of_set_api_key(sle_apikey.Text)

st_status.Text = "⏳ Actualizando estado..."
st_status.BackColor = RGB(255,235,59)
st_status.TextColor = RGB(0,0,0)

ls_response = in_api.of_actualizar_estado_propuesta(il_propuesta_seleccionada, "Procesada")

If in_api.of_get_last_http_code() = 200 Then
    st_status.Text = "✓ Estado actualizado correctamente"
    st_status.BackColor = RGB(76,175,80)
    st_status.TextColor = RGB(255,255,255)
    dw_propuestas.SetItem(ll_row, "estado", "Procesada")
    wf_colorear_estados()
    MessageBox("Éxito", "Propuesta marcada como Procesada")
Else
    st_status.Text = "✗ Error al actualizar estado"
    st_status.BackColor = RGB(244,67,54)
    st_status.TextColor = RGB(255,255,255)
    MessageBox("Error", "Error al actualizar estado: " + in_api.of_get_last_error())
End If
end subroutine

public subroutine wf_aplicar_filtros ();String ls_filtro, ls_estado
ls_filtro = Trim(sle_filtro.Text)
ls_estado = ddlb_estado.Text

dw_propuestas.SetRedraw(False)

If ls_filtro = "" And ls_estado = "Todos" Then
    dw_propuestas.SetFilter("")
Else
    String ls_condicion
    ls_condicion = ""

    If ls_filtro <> "" Then
        ls_condicion = "usuario like '%" + ls_filtro + "%' or email like '%" + ls_filtro + "%' or observaciones like '%" + ls_filtro + "%'"
    End If

    If ls_estado <> "Todos" Then
        If ls_condicion <> "" Then ls_condicion = ls_condicion + " and "
        ls_condicion = ls_condicion + "estado = '" + ls_estado + "'"
    End If

    dw_propuestas.SetFilter(ls_condicion)
End If

dw_propuestas.Filter()
dw_propuestas.SetRedraw(True)
wf_actualizar_totales()
end subroutine

public subroutine wf_actualizar_info_propuesta ();Long ll_row, ll_items
String ls_usuario, ls_estado, ls_fecha

ll_row = dw_propuestas.GetRow()

If ll_row > 0 Then
    ll_items = dw_propuestas.GetItemNumber(ll_row, "numero_lineas")
    ls_usuario = dw_propuestas.GetItemString(ll_row, "usuario")
    ls_estado = dw_propuestas.GetItemString(ll_row, "estado")

    st_propuesta_info.Text = "📋 Propuesta #" + String(il_propuesta_seleccionada) + " | " + ls_usuario + " | Estado: " + ls_estado + " | Artículos: " + String(ll_items)
Else
    st_propuesta_info.Text = "Seleccione una propuesta para ver sus líneas"
End If

wf_actualizar_totales()
end subroutine

public subroutine wf_colorear_estados ();Long ll_row
String ls_estado

For ll_row = 1 To dw_propuestas.RowCount()
    ls_estado = dw_propuestas.GetItemString(ll_row, "estado")

    Choose Case ls_estado
        Case "Enviada"
            dw_propuestas.SetItem(ll_row, "color_fondo", RGB(255,249,196))
        Case "Procesada"
            dw_propuestas.SetItem(ll_row, "color_fondo", RGB(200,230,201))
        Case "Cancelada"
            dw_propuestas.SetItem(ll_row, "color_fondo", RGB(255,205,210))
        Case Else
            dw_propuestas.SetItem(ll_row, "color_fondo", RGB(255,255,255))
    End Choose
Next
end subroutine

on w_propuestas_modern.create
this.dw_lineas_mem=create dw_lineas_mem
this.st_header=create st_header
this.st_url_label=create st_url_label
this.sle_url=create sle_url
this.st_apikey_label=create st_apikey_label
this.sle_apikey=create sle_apikey
this.cb_cargar=create cb_cargar
this.cb_refresh=create cb_refresh
this.cb_marcar_procesada=create cb_marcar_procesada
this.cb_exportar=create cb_exportar
this.ln_separator=create ln_separator
this.st_propuestas_title=create st_propuestas_title
this.st_total_propuestas=create st_total_propuestas
this.dw_propuestas=create dw_propuestas
this.st_lineas_title=create st_lineas_title
this.st_total_lineas=create st_total_lineas
this.dw_lineas=create dw_lineas
this.st_status=create st_status
this.st_propuesta_info=create st_propuesta_info
this.sle_filtro=create sle_filtro
this.st_filtro_label=create st_filtro_label
this.ddlb_estado=create ddlb_estado
this.st_estado_label=create st_estado_label
this.Control[]={this.dw_lineas_mem,&
this.st_header,&
this.st_url_label,&
this.sle_url,&
this.st_apikey_label,&
this.sle_apikey,&
this.cb_cargar,&
this.cb_refresh,&
this.cb_marcar_procesada,&
this.cb_exportar,&
this.ln_separator,&
this.st_propuestas_title,&
this.st_total_propuestas,&
this.dw_propuestas,&
this.st_lineas_title,&
this.st_total_lineas,&
this.dw_lineas,&
this.st_status,&
this.st_propuesta_info,&
this.sle_filtro,&
this.st_filtro_label,&
this.ddlb_estado,&
this.st_estado_label}
end on

on w_propuestas_modern.destroy
destroy(this.dw_lineas_mem)
destroy(this.st_header)
destroy(this.st_url_label)
destroy(this.sle_url)
destroy(this.st_apikey_label)
destroy(this.sle_apikey)
destroy(this.cb_cargar)
destroy(this.cb_refresh)
destroy(this.cb_marcar_procesada)
destroy(this.cb_exportar)
destroy(this.ln_separator)
destroy(this.st_propuestas_title)
destroy(this.st_total_propuestas)
destroy(this.dw_propuestas)
destroy(this.st_lineas_title)
destroy(this.st_total_lineas)
destroy(this.dw_lineas)
destroy(this.st_status)
destroy(this.st_propuesta_info)
destroy(this.sle_filtro)
destroy(this.st_filtro_label)
destroy(this.ddlb_estado)
destroy(this.st_estado_label)
end on

event open;sle_url.Text = "http://localhost:5000"
sle_apikey.Text = "720656659a558a47a95269ae7cab14e10d488583a2d6116476beaf24739fe870"

dw_propuestas.DataObject = "d_propuestas_pendientes"
dw_lineas.DataObject = "d_propuesta_lineas"
dw_lineas_mem.DataObject = "d_propuesta_lineas"

ddlb_estado.AddItem("Todos")
ddlb_estado.AddItem("Enviada")
ddlb_estado.AddItem("Procesada")
ddlb_estado.AddItem("Cancelada")
ddlb_estado.SelectItem(1)

st_status.Text = "💡 Listo para cargar datos"
st_status.BackColor = RGB(189,189,189)
st_status.TextColor = RGB(255,255,255)

st_propuesta_info.Text = "Seleccione una propuesta para ver sus líneas"
il_propuesta_seleccionada = 0
end event

type dw_lineas_mem from datawindow within w_propuestas_modern
boolean visible = false
integer x = 37
integer y = 2400
integer width = 4384
integer height = 300
string dataobject = "d_propuesta_lineas"
boolean border = false
end type

type st_header from statictext within w_propuestas_modern
integer width = 5600
integer height = 120
integer textsize = -14
integer weight = 700
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 16777215
long backcolor = 33023
string text = "  📊 GESTIÓN DE PROPUESTAS - SISTEMA ERP"
alignment alignment = left!
boolean focusrectangle = false
end type

type st_url_label from statictext within w_propuestas_modern
integer x = 50
integer y = 160
integer width = 250
integer height = 64
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 8421504
long backcolor = 16777215
string text = "URL Base:"
boolean focusrectangle = false
end type

type sle_url from singlelineedit within w_propuestas_modern
integer x = 310
integer y = 150
integer width = 850
integer height = 88
integer taborder = 10
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 33554432
long backcolor = 16777215
borderstyle borderstyle = stylelowered!
end type

type st_apikey_label from statictext within w_propuestas_modern
integer x = 1220
integer y = 160
integer width = 250
integer height = 64
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 8421504
long backcolor = 16777215
string text = "API Key:"
boolean focusrectangle = false
end type

type sle_apikey from singlelineedit within w_propuestas_modern
integer x = 1480
integer y = 150
integer width = 1900
integer height = 88
integer taborder = 20
integer textsize = -8
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Consolas"
long textcolor = 8421504
long backcolor = 16777215
borderstyle borderstyle = stylelowered!
end type

type cb_cargar from commandbutton within w_propuestas_modern
integer x = 3450
integer y = 144
integer width = 450
integer height = 100
integer taborder = 30
integer textsize = -9
integer weight = 700
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long backcolor = 12615808
string text = "🔄 Cargar Datos"
end type

event clicked;wf_cargar_todo()
end event

type cb_refresh from commandbutton within w_propuestas_modern
integer x = 3950
integer y = 144
integer width = 380
integer height = 100
integer taborder = 40
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
string text = "🔃 Actualizar"
end type

event clicked;wf_cargar_todo()
end event

type cb_marcar_procesada from commandbutton within w_propuestas_modern
integer x = 4380
integer y = 144
integer width = 530
integer height = 100
integer taborder = 50
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long backcolor = 5296995
string text = "✓ Marcar Procesada"
end type

event clicked;Parent.wf_marcar_como_procesada()
end event

type cb_exportar from commandbutton within w_propuestas_modern
integer x = 4960
integer y = 144
integer width = 400
integer height = 100
integer taborder = 60
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
string text = "📥 Exportar"
boolean enabled = false
end type

event clicked;MessageBox("Exportar", "Funcionalidad de exportación en desarrollo...")
end event

type ln_separator from line within w_propuestas_modern
long linecolor = 12632256
integer linethickness = 4
integer beginx = 50
integer beginy = 280
integer endx = 5550
integer endy = 280
end type

type st_propuestas_title from statictext within w_propuestas_modern
integer x = 50
integer y = 320
integer width = 600
integer height = 72
integer textsize = -11
integer weight = 700
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 33023
long backcolor = 16777215
string text = "📋 Propuestas Pendientes"
boolean focusrectangle = false
end type

type st_total_propuestas from statictext within w_propuestas_modern
integer x = 660
integer y = 328
integer width = 550
integer height = 64
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 8421504
long backcolor = 16777215
string text = "Total: 0 propuesta(s)"
boolean focusrectangle = false
end type

type st_filtro_label from statictext within w_propuestas_modern
integer x = 2900
integer y = 328
integer width = 200
integer height = 64
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 8421504
long backcolor = 16777215
string text = "🔍 Filtrar:"
alignment alignment = right!
boolean focusrectangle = false
end type

type sle_filtro from singlelineedit within w_propuestas_modern
integer x = 3120
integer y = 316
integer width = 750
integer height = 80
integer taborder = 70
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 33554432
long backcolor = 16777215
borderstyle borderstyle = stylelowered!
end type

event modified;Parent.wf_aplicar_filtros()
end event

type st_estado_label from statictext within w_propuestas_modern
integer x = 3920
integer y = 328
integer width = 200
integer height = 64
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 8421504
long backcolor = 16777215
string text = "Estado:"
alignment alignment = right!
boolean focusrectangle = false
end type

type ddlb_estado from dropdownlistbox within w_propuestas_modern
integer x = 4140
integer y = 312
integer width = 450
integer height = 400
integer taborder = 80
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 33554432
long backcolor = 16777215
boolean vscrollbar = true
borderstyle borderstyle = stylelowered!
end type

event selectionchanged;Parent.wf_aplicar_filtros()
end event

type dw_propuestas from datawindow within w_propuestas_modern
integer x = 50
integer y = 420
integer width = 5500
integer height = 920
integer taborder = 90
string dataobject = "d_propuestas_pendientes"
boolean hscrollbar = true
boolean vscrollbar = true
boolean hsplitscroll = true
boolean livescroll = true
borderstyle borderstyle = stylelowered!
end type

event clicked;Long ll_row

ll_row = row
If ll_row > 0 Then
    il_propuesta_seleccionada = This.GetItemNumber(ll_row,"id")

    dw_lineas.SetRedraw(False)
    dw_lineas_mem.SetFilter("propuesta_id = " + String(il_propuesta_seleccionada))
    dw_lineas_mem.Filter()
    dw_lineas.DataObject = dw_lineas_mem.DataObject
    dw_lineas_mem.RowsCopy(1, dw_lineas_mem.RowCount(), Primary!, dw_lineas, 1, Primary!)
    dw_lineas.SetRedraw(True)

    Parent.wf_actualizar_info_propuesta()
End If
end event

type st_lineas_title from statictext within w_propuestas_modern
integer x = 50
integer y = 1420
integer width = 500
integer height = 72
integer textsize = -11
integer weight = 700
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 33023
long backcolor = 16777215
string text = "📦 Líneas de Propuesta"
boolean focusrectangle = false
end type

type st_total_lineas from statictext within w_propuestas_modern
integer x = 560
integer y = 1428
integer width = 450
integer height = 64
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 8421504
long backcolor = 16777215
string text = "Total: 0 línea(s)"
boolean focusrectangle = false
end type

type st_propuesta_info from statictext within w_propuestas_modern
integer x = 50
integer y = 1360
integer width = 5500
integer height = 60
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 8421504
long backcolor = 16771796
string text = "Seleccione una propuesta para ver sus líneas"
alignment alignment = center!
boolean border = true
borderstyle borderstyle = styleraised!
boolean focusrectangle = false
end type

type dw_lineas from datawindow within w_propuestas_modern
integer x = 50
integer y = 1520
integer width = 5500
integer height = 1120
integer taborder = 100
string dataobject = "d_propuesta_lineas"
boolean hscrollbar = true
boolean vscrollbar = true
boolean hsplitscroll = true
boolean livescroll = true
borderstyle borderstyle = stylelowered!
end type

type st_status from statictext within w_propuestas_modern
integer x = 50
integer y = 2680
integer width = 5500
integer height = 80
integer textsize = -9
integer weight = 700
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Segoe UI"
long textcolor = 16777215
long backcolor = 12632256
alignment alignment = center!
boolean border = true
borderstyle borderstyle = styleraised!
boolean focusrectangle = false
end type
