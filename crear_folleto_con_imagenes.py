#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador de folleto promocional - Version profesional
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.pdfgen import canvas
import os

# Colores corporativos
PRIMARY = colors.HexColor('#FF4338')
PRIMARY_DARK = colors.HexColor('#C62828')
ACCENT = colors.HexColor('#FF6B5B')
DARK = colors.HexColor('#1A202C')
GRAY = colors.HexColor('#4A5568')
LIGHT_GRAY = colors.HexColor('#EDF2F7')
WHITE = colors.white

SCREENSHOTS_DIR = "screenshots"
OUTPUT_FILE = "folleto_gestion_stocks.pdf"

class NumberedCanvas(canvas.Canvas):
    """Canvas con numero de pagina"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 8)
        self.setFillColor(GRAY)
        page = f"Pagina {self._pageNumber} de {page_count}"
        self.drawRightString(A4[0] - 1.5*cm, 1*cm, page)


def get_image(filename, max_width=None, max_height=None):
    """Obtiene imagen con dimensiones controladas"""
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  [!] No encontrada: {filename}")
        return None

    img = Image(filepath)
    orig_w = img.imageWidth
    orig_h = img.imageHeight
    aspect = orig_h / orig_w

    if max_width and max_height:
        # Ajustar a ambos limites manteniendo proporcion
        w = max_width
        h = w * aspect
        if h > max_height:
            h = max_height
            w = h / aspect
        img.drawWidth = w
        img.drawHeight = h
    elif max_width:
        img.drawWidth = max_width
        img.drawHeight = max_width * aspect

    return img


def crear_header_rojo(texto, width=17*cm):
    """Crea un bloque de titulo con fondo rojo"""
    data = [[texto]]
    t = Table(data, colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    return t


def crear_feature_box(titulo, descripcion, width=8*cm):
    """Crea una caja de caracteristica"""
    data = [
        [titulo],
        [descripcion]
    ]
    t = Table(data, colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (0, 0), PRIMARY),
        ('TEXTCOLOR', (0, 1), (0, 1), GRAY),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 11),
        ('FONTSIZE', (0, 1), (0, 1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


def generar_folleto():
    # Verificar capturas
    if not os.path.exists(SCREENSHOTS_DIR):
        print(f"ERROR: No existe '{SCREENSHOTS_DIR}'. Ejecuta primero capturar_pantallas.py")
        return

    capturas = sorted([f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith('.png')])
    print(f"Capturas encontradas: {len(capturas)}")
    for c in capturas:
        print(f"  - {c}")

    # Crear documento
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm
    )

    # Estilos
    s_titulo = ParagraphStyle('Titulo', fontSize=28, textColor=PRIMARY, alignment=TA_CENTER,
                               fontName='Helvetica-Bold', spaceAfter=5)
    s_subtitulo = ParagraphStyle('Subtitulo', fontSize=12, textColor=GRAY, alignment=TA_CENTER,
                                  fontName='Helvetica', spaceAfter=20, leading=16)
    s_seccion = ParagraphStyle('Seccion', fontSize=16, textColor=PRIMARY_DARK, alignment=TA_LEFT,
                                fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=10)
    s_texto = ParagraphStyle('Texto', fontSize=10, textColor=DARK, alignment=TA_JUSTIFY,
                              fontName='Helvetica', spaceAfter=10, leading=14)
    s_caption = ParagraphStyle('Caption', fontSize=8, textColor=GRAY, alignment=TA_CENTER,
                                fontName='Helvetica-Oblique', spaceBefore=5, spaceAfter=15)
    s_bullet = ParagraphStyle('Bullet', fontSize=10, textColor=DARK, alignment=TA_LEFT,
                               fontName='Helvetica', leftIndent=20, spaceAfter=5)

    elementos = []

    # ============ PAGINA 1: PORTADA ============
    elementos.append(Spacer(1, 2*cm))

    # Titulo principal
    elementos.append(Paragraph("SISTEMA DE GESTION", s_titulo))
    elementos.append(Paragraph("DE STOCKS", s_titulo))
    elementos.append(Spacer(1, 0.5*cm))

    # Linea decorativa
    d = Drawing(450, 4)
    d.add(Rect(0, 0, 450, 4, fillColor=PRIMARY, strokeColor=None))
    elementos.append(d)
    elementos.append(Spacer(1, 0.5*cm))

    elementos.append(Paragraph(
        "Plataforma web profesional para la gestion integral<br/>"
        "de inventario de azulejos y ceramica",
        s_subtitulo
    ))

    # Imagen principal
    img_main = get_image("02_listado_stocks.png", max_width=16*cm, max_height=10*cm)
    if img_main:
        # Centrar imagen en tabla
        t = Table([[img_main]], colWidths=[17*cm])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 1, LIGHT_GRAY),
        ]))
        elementos.append(t)
        elementos.append(Paragraph("Interfaz principal con listado completo de productos", s_caption))

    elementos.append(Spacer(1, 0.5*cm))

    # Caracteristicas destacadas
    features = [
        crear_feature_box("Multi-idioma", "ES / EN / FR"),
        crear_feature_box("Multi-empresa", "Config. independiente"),
        crear_feature_box("Responsive", "Desktop y movil"),
        crear_feature_box("API REST", "Documentacion Swagger"),
    ]
    t_feat = Table([features], colWidths=[4.25*cm] * 4)
    t_feat.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elementos.append(t_feat)

    elementos.append(PageBreak())

    # ============ PAGINA 2: FUNCIONALIDADES ============
    elementos.append(crear_header_rojo("FUNCIONALIDADES PRINCIPALES"))
    elementos.append(Spacer(1, 0.5*cm))

    # Busqueda y filtros
    elementos.append(Paragraph("Busqueda Avanzada y Filtros", s_seccion))
    elementos.append(Paragraph(
        "Encuentre cualquier producto en segundos. Filtros por descripcion, formato, serie, "
        "calidad, color, tono y calibre. Resultados en tiempo real mientras escribe. "
        "Vista en tabla o tarjetas segun preferencia.",
        s_texto
    ))

    # Detalle de producto - usar listado de stocks como referencia
    img_detail = get_image("02_listado_stocks.png", max_width=16*cm, max_height=8*cm)
    if img_detail:
        t = Table([[img_detail]], colWidths=[17*cm])
        t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('BOX', (0, 0), (-1, -1), 1, LIGHT_GRAY)]))
        elementos.append(t)
        elementos.append(Paragraph("Vista detallada con imagenes, especificaciones y ficha tecnica PDF", s_caption))

    elementos.append(Spacer(1, 0.3*cm))

    # Sistema de propuestas
    elementos.append(Paragraph("Sistema de Propuestas", s_seccion))
    elementos.append(Paragraph(
        "Los usuarios agregan productos al carrito con cantidades especificas. "
        "Al enviar, se genera un PDF profesional automaticamente, se envia por email "
        "y queda registrado en el sistema para seguimiento completo.",
        s_texto
    ))

    bullets = [
        "Carrito persistente durante la sesion",
        "Validacion de cantidades vs existencias",
        "PDF con detalle completo del pedido",
        "Historial de propuestas por usuario",
        "Estados: Enviada, Procesada, Cancelada"
    ]
    for b in bullets:
        elementos.append(Paragraph(f"<bullet>&bull;</bullet> {b}", s_bullet))

    elementos.append(PageBreak())

    # ============ PAGINA 3: DASHBOARD ============
    elementos.append(crear_header_rojo("PANEL DE CONTROL"))
    elementos.append(Spacer(1, 0.5*cm))

    elementos.append(Paragraph("Dashboard de Estadisticas", s_seccion))
    elementos.append(Paragraph(
        "Panel completo para administradores con metricas clave del negocio. "
        "Visualice tendencias, identifique productos populares y usuarios activos. "
        "Graficos interactivos con Chart.js.",
        s_texto
    ))

    # Dashboard
    img_dash = get_image("03_dashboard.png", max_width=16*cm, max_height=9*cm)
    if img_dash:
        t = Table([[img_dash]], colWidths=[17*cm])
        t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('BOX', (0, 0), (-1, -1), 1, LIGHT_GRAY)]))
        elementos.append(t)
        elementos.append(Paragraph("Dashboard con KPIs, graficos de tendencias y rankings", s_caption))

    elementos.append(Spacer(1, 0.3*cm))

    # Features del dashboard en tabla
    dash_features = [
        ["Total propuestas", "Propuestas pendientes", "Usuarios activos"],
        ["Grafico por dia/mes", "Distribucion por estado", "Top productos"],
    ]
    t_dash = Table(dash_features, colWidths=[5.5*cm] * 3)
    t_dash.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 1), (-1, 1), GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elementos.append(t_dash)

    elementos.append(PageBreak())

    # ============ PAGINA 4: ADMINISTRACION ============
    elementos.append(crear_header_rojo("ADMINISTRACION"))
    elementos.append(Spacer(1, 0.5*cm))

    # Gestion usuarios
    elementos.append(Paragraph("Gestion de Usuarios", s_seccion))
    elementos.append(Paragraph(
        "Control total sobre quienes acceden al sistema. Tres niveles de permisos, "
        "verificacion de email obligatoria y asociacion con clientes del ERP. "
        "Cree usuarios desde el panel o permita registro publico.",
        s_texto
    ))

    img_users = get_image("04_usuarios.png", max_width=16*cm, max_height=7*cm)
    if img_users:
        t = Table([[img_users]], colWidths=[17*cm])
        t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('BOX', (0, 0), (-1, -1), 1, LIGHT_GRAY)]))
        elementos.append(t)
        elementos.append(Paragraph("Panel de gestion de usuarios con roles y estados", s_caption))

    elementos.append(Spacer(1, 0.3*cm))

    # Config email y parametros - dos imagenes lado a lado
    elementos.append(Paragraph("Configuracion del Sistema", s_seccion))

    img_email = get_image("05_email_config.png", max_width=8*cm, max_height=5*cm)
    img_params = get_image("06_parametros.png", max_width=8*cm, max_height=5*cm)

    if img_email and img_params:
        t_config = Table([[img_email, img_params]], colWidths=[8.5*cm, 8.5*cm])
        t_config.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (0, 0), 1, LIGHT_GRAY),
            ('BOX', (1, 0), (1, 0), 1, LIGHT_GRAY),
        ]))
        elementos.append(t_config)
        elementos.append(Paragraph("Configuracion SMTP para emails y parametros del sistema", s_caption))

    elementos.append(PageBreak())

    # ============ PAGINA 5: PERSONALIZACION ============
    elementos.append(crear_header_rojo("PERSONALIZACION"))
    elementos.append(Spacer(1, 0.5*cm))

    elementos.append(Paragraph("Temas de Color y Marca", s_seccion))
    elementos.append(Paragraph(
        "Adapte la apariencia del sistema a su imagen corporativa. Elija entre 6 temas "
        "predefinidos, active el modo oscuro, suba su logo y favicon personalizados. "
        "Cada empresa puede tener su propia configuracion visual independiente.",
        s_texto
    ))

    img_temas = get_image("09_temas_color.png", max_width=16*cm, max_height=8*cm)
    if img_temas:
        t = Table([[img_temas]], colWidths=[17*cm])
        t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('BOX', (0, 0), (-1, -1), 1, LIGHT_GRAY)]))
        elementos.append(t)
        elementos.append(Paragraph("Selector de temas con vista previa en tiempo real", s_caption))

    elementos.append(Spacer(1, 0.3*cm))

    # Tabla de temas con colores
    temas_data = [
        [Paragraph("<b>Rubi</b>", ParagraphStyle('t', fontSize=10, textColor=colors.HexColor('#FF4338'), alignment=TA_CENTER)),
         Paragraph("<b>Zafiro</b>", ParagraphStyle('t', fontSize=10, textColor=colors.HexColor('#3182CE'), alignment=TA_CENTER)),
         Paragraph("<b>Esmeralda</b>", ParagraphStyle('t', fontSize=10, textColor=colors.HexColor('#38A169'), alignment=TA_CENTER))],
        [Paragraph("Rojo corporativo", ParagraphStyle('t', fontSize=8, textColor=GRAY, alignment=TA_CENTER)),
         Paragraph("Azul profesional", ParagraphStyle('t', fontSize=8, textColor=GRAY, alignment=TA_CENTER)),
         Paragraph("Verde natural", ParagraphStyle('t', fontSize=8, textColor=GRAY, alignment=TA_CENTER))],
        [Paragraph("<b>Amatista</b>", ParagraphStyle('t', fontSize=10, textColor=colors.HexColor('#805AD5'), alignment=TA_CENTER)),
         Paragraph("<b>Ambar</b>", ParagraphStyle('t', fontSize=10, textColor=colors.HexColor('#DD6B20'), alignment=TA_CENTER)),
         Paragraph("<b>Grafito</b>", ParagraphStyle('t', fontSize=10, textColor=colors.HexColor('#4A5568'), alignment=TA_CENTER))],
        [Paragraph("Morado elegante", ParagraphStyle('t', fontSize=8, textColor=GRAY, alignment=TA_CENTER)),
         Paragraph("Naranja calido", ParagraphStyle('t', fontSize=8, textColor=GRAY, alignment=TA_CENTER)),
         Paragraph("Gris sofisticado", ParagraphStyle('t', fontSize=8, textColor=GRAY, alignment=TA_CENTER))],
    ]
    t_temas = Table(temas_data, colWidths=[5.5*cm] * 3)
    t_temas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elementos.append(t_temas)

    elementos.append(PageBreak())

    # ============ PAGINA 6: ESPECIFICACIONES ============
    elementos.append(crear_header_rojo("ESPECIFICACIONES TECNICAS"))
    elementos.append(Spacer(1, 0.5*cm))

    # Requisitos
    elementos.append(Paragraph("Requisitos del Sistema", s_seccion))

    req_data = [
        ["Componente", "Requisito"],
        ["Servidor", "Linux (Debian/Ubuntu/CentOS) o Windows Server"],
        ["Base de Datos", "Microsoft SQL Server 2008 o superior"],
        ["Python", "Python 3.11 o superior"],
        ["Navegador", "Chrome, Firefox, Safari, Edge (versiones actuales)"],
        ["Despliegue", "Docker (incluido) o instalacion nativa"],
    ]
    t_req = Table(req_data, colWidths=[4*cm, 13*cm])
    t_req.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(t_req)

    elementos.append(Spacer(1, 0.5*cm))

    # Que incluye
    elementos.append(Paragraph("Incluido en la Licencia", s_seccion))

    inc_data = [
        ["Codigo fuente completo", "Scripts SQL para base de datos"],
        ["Documentacion tecnica", "Cliente PowerBuilder 2022"],
        ["Configuracion Docker", "Soporte tecnico por email"],
    ]
    t_inc = Table(inc_data, colWidths=[8.5*cm, 8.5*cm])
    t_inc.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
    ]))
    elementos.append(t_inc)

    elementos.append(Spacer(1, 1*cm))

    # Cierre
    d = Drawing(450, 3)
    d.add(Rect(0, 0, 450, 3, fillColor=PRIMARY, strokeColor=None))
    elementos.append(d)
    elementos.append(Spacer(1, 0.5*cm))

    s_cierre = ParagraphStyle('Cierre', fontSize=12, textColor=DARK, alignment=TA_CENTER, leading=18)
    elementos.append(Paragraph(
        "<b>Interesado en implementar esta solucion?</b><br/><br/>"
        "Solicite una demostracion personalizada y presupuesto<br/>"
        "adaptado a las necesidades de su empresa.",
        s_cierre
    ))

    elementos.append(Spacer(1, 0.5*cm))
    d2 = Drawing(450, 3)
    d2.add(Rect(0, 0, 450, 3, fillColor=PRIMARY, strokeColor=None))
    elementos.append(d2)

    # Generar
    doc.build(elementos, canvasmaker=NumberedCanvas)

    file_size = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n[OK] Folleto generado: {OUTPUT_FILE}")
    print(f"     Tamano: {file_size:.0f} KB")


if __name__ == '__main__':
    generar_folleto()
