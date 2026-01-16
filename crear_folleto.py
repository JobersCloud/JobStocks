#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para generar folleto promocional en PDF
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line
from reportlab.graphics import renderPDF
import os

# Colores corporativos
PRIMARY = colors.HexColor('#FF4338')
PRIMARY_DARK = colors.HexColor('#D32F2F')
DARK_GRAY = colors.HexColor('#2D3748')
LIGHT_GRAY = colors.HexColor('#F7FAFC')
WHITE = colors.white

def crear_linea_decorativa(width, color=PRIMARY):
    """Crea una línea decorativa"""
    d = Drawing(width, 3)
    d.add(Rect(0, 0, width, 3, fillColor=color, strokeColor=None))
    return d

def crear_icono_check():
    """Crea un icono de check"""
    d = Drawing(15, 15)
    d.add(Circle(7.5, 7.5, 7, fillColor=PRIMARY, strokeColor=None))
    return d

def generar_folleto():
    # Crear documento
    doc = SimpleDocTemplate(
        "folleto_gestion_stocks.pdf",
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    # Estilos
    styles = getSampleStyleSheet()

    # Estilos personalizados
    titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica'
    )

    seccion_titulo = ParagraphStyle(
        'SeccionTitulo',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=PRIMARY_DARK,
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    texto_normal = ParagraphStyle(
        'TextoNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14
    )

    feature_style = ParagraphStyle(
        'Feature',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        leftIndent=20,
        spaceAfter=6,
        bulletIndent=0
    )

    destacado = ParagraphStyle(
        'Destacado',
        parent=styles['Normal'],
        fontSize=11,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Contenido
    elementos = []

    # === PÁGINA 1: PORTADA ===
    elementos.append(Spacer(1, 2*cm))

    # Título principal
    elementos.append(Paragraph("SISTEMA DE GESTIÓN", titulo_principal))
    elementos.append(Paragraph("DE STOCKS", titulo_principal))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(crear_linea_decorativa(400))
    elementos.append(Spacer(1, 0.5*cm))

    # Subtítulo
    elementos.append(Paragraph(
        "Plataforma web profesional para la gestión integral<br/>de inventario de azulejos y cerámica",
        subtitulo
    ))

    elementos.append(Spacer(1, 1*cm))

    # Características destacadas en tabla
    datos_destacados = [
        ['🌐 Multi-idioma', '🏢 Multi-empresa', '📱 Responsive'],
        ['🔒 Seguro', '📊 Dashboard', '🎨 Personalizable'],
    ]

    tabla_destacados = Table(datos_destacados, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    tabla_destacados.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]))
    elementos.append(tabla_destacados)

    elementos.append(Spacer(1, 1.5*cm))

    # Caja de beneficios
    beneficios_texto = """
    <b>✓ Reduzca tiempos de consulta</b> con filtros avanzados<br/>
    <b>✓ Mejore la comunicación</b> con clientes mediante propuestas automatizadas<br/>
    <b>✓ Controle el acceso</b> con sistema de roles y permisos<br/>
    <b>✓ Analice datos</b> con dashboard de estadísticas en tiempo real<br/>
    <b>✓ Integre con su ERP</b> mediante API REST documentada
    """

    beneficios_style = ParagraphStyle(
        'Beneficios',
        parent=styles['Normal'],
        fontSize=11,
        textColor=DARK_GRAY,
        leading=18,
        leftIndent=10
    )

    elementos.append(Paragraph(beneficios_texto, beneficios_style))

    elementos.append(Spacer(1, 2*cm))

    # Pie de portada
    elementos.append(crear_linea_decorativa(400))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("Solución profesional • Soporte técnico • Actualizaciones incluidas", subtitulo))

    elementos.append(PageBreak())

    # === PÁGINA 2: FUNCIONALIDADES ===
    elementos.append(Paragraph("FUNCIONALIDADES PRINCIPALES", titulo_principal))
    elementos.append(crear_linea_decorativa(400))
    elementos.append(Spacer(1, 0.5*cm))

    # Gestión de Stocks
    elementos.append(Paragraph("📦 Gestión de Stocks", seccion_titulo))
    elementos.append(Paragraph(
        "Consulte su inventario en tiempo real con potentes filtros de búsqueda. "
        "Visualice información detallada de cada producto incluyendo formato, serie, calidad, "
        "tono, calibre y existencias. Acceda a imágenes y fichas técnicas en PDF.",
        texto_normal
    ))

    features_stocks = [
        "• Filtros avanzados por múltiples criterios",
        "• Vista detallada con galería de imágenes",
        "• Descarga de fichas técnicas en PDF",
        "• Código EAN-13 para cada producto",
        "• Búsqueda por existencias mínimas"
    ]
    for f in features_stocks:
        elementos.append(Paragraph(f, feature_style))

    # Sistema de Propuestas
    elementos.append(Paragraph("🛒 Sistema de Propuestas", seccion_titulo))
    elementos.append(Paragraph(
        "Permita a sus clientes crear solicitudes de productos con un carrito intuitivo. "
        "Las propuestas se envían automáticamente por email con PDF adjunto y se almacenan "
        "en base de datos para su seguimiento.",
        texto_normal
    ))

    features_propuestas = [
        "• Carrito de compras con detección de duplicados",
        "• Generación automática de PDF profesional",
        "• Envío por email al comercial asignado",
        "• Estados: Enviada, Procesada, Cancelada",
        "• Historial completo de propuestas"
    ]
    for f in features_propuestas:
        elementos.append(Paragraph(f, feature_style))

    # Gestión de Usuarios
    elementos.append(Paragraph("👥 Gestión de Usuarios", seccion_titulo))
    elementos.append(Paragraph(
        "Control total sobre quién accede al sistema y qué puede hacer. "
        "Tres niveles de permisos, verificación de email obligatoria y "
        "gestión completa desde el panel de administración.",
        texto_normal
    ))

    features_usuarios = [
        "• Roles: Usuario, Administrador, Superusuario",
        "• Registro público con verificación de email",
        "• Activación/desactivación de cuentas",
        "• Cambio de contraseña obligatorio",
        "• Asociación con clientes del ERP"
    ]
    for f in features_usuarios:
        elementos.append(Paragraph(f, feature_style))

    # Dashboard
    elementos.append(Paragraph("📊 Dashboard de Estadísticas", seccion_titulo))
    elementos.append(Paragraph(
        "Panel de control con métricas clave del negocio. Visualice propuestas, "
        "usuarios activos, productos más solicitados y tendencias temporales "
        "con gráficos interactivos.",
        texto_normal
    ))

    features_dashboard = [
        "• Tarjetas de resumen con KPIs principales",
        "• Gráfico de propuestas por día/mes",
        "• Top 10 productos más solicitados",
        "• Distribución por estado de propuestas",
        "• Usuarios más activos"
    ]
    for f in features_dashboard:
        elementos.append(Paragraph(f, feature_style))

    elementos.append(PageBreak())

    # === PÁGINA 3: CARACTERÍSTICAS TÉCNICAS ===
    elementos.append(Paragraph("CARACTERÍSTICAS TÉCNICAS", titulo_principal))
    elementos.append(crear_linea_decorativa(400))
    elementos.append(Spacer(1, 0.5*cm))

    # Multi-empresa
    elementos.append(Paragraph("🏢 Soporte Multi-Empresa", seccion_titulo))
    elementos.append(Paragraph(
        "Gestione múltiples empresas desde una única instalación. Cada empresa tiene "
        "su propia configuración de email, parámetros, logo y tema de colores. "
        "Los usuarios pueden trabajar con diferentes empresas simultáneamente.",
        texto_normal
    ))

    # API REST
    elementos.append(Paragraph("🔌 API REST Documentada", seccion_titulo))
    elementos.append(Paragraph(
        "Integre el sistema con su ERP o aplicaciones externas mediante nuestra API REST. "
        "Documentación completa con Swagger UI, autenticación por API Key y "
        "ejemplos de uso para PowerBuilder incluidos.",
        texto_normal
    ))

    features_api = [
        "• Swagger UI interactivo en /apidocs",
        "• Autenticación por sesión o API Key",
        "• Endpoints para stocks, propuestas, clientes",
        "• Cliente PowerBuilder 2022 incluido",
        "• Respuestas en formato JSON"
    ]
    for f in features_api:
        elementos.append(Paragraph(f, feature_style))

    # Personalización
    elementos.append(Paragraph("🎨 Personalización Visual", seccion_titulo))
    elementos.append(Paragraph(
        "Adapte la apariencia del sistema a su imagen corporativa. "
        "6 temas de colores predefinidos, modo oscuro, logo y favicon personalizables por empresa.",
        texto_normal
    ))

    # Tabla de temas
    datos_temas = [
        ['Tema', 'Color', 'Descripción'],
        ['Rubí', '🔴', 'Rojo corporativo (por defecto)'],
        ['Zafiro', '🔵', 'Azul profesional'],
        ['Esmeralda', '🟢', 'Verde natural'],
        ['Amatista', '🟣', 'Morado elegante'],
        ['Ámbar', '🟠', 'Naranja cálido'],
        ['Grafito', '⚫', 'Gris sofisticado'],
    ]

    tabla_temas = Table(datos_temas, colWidths=[3*cm, 2*cm, 10*cm])
    tabla_temas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
    ]))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(tabla_temas)

    # Internacionalización
    elementos.append(Paragraph("🌐 Multi-idioma", seccion_titulo))
    elementos.append(Paragraph(
        "Interfaz disponible en Español, Inglés y Francés. El sistema detecta "
        "automáticamente el idioma del navegador y permite cambiar en cualquier momento "
        "sin recargar la página. Fácilmente extensible a otros idiomas.",
        texto_normal
    ))

    # Seguridad
    elementos.append(Paragraph("🔒 Seguridad", seccion_titulo))
    features_seguridad = [
        "• Contraseñas hasheadas con Werkzeug",
        "• Sesiones seguras con Flask-Login",
        "• API Keys para integraciones externas",
        "• Verificación de email obligatoria",
        "• Control de acceso por roles",
        "• CORS configurado para APIs"
    ]
    for f in features_seguridad:
        elementos.append(Paragraph(f, feature_style))

    elementos.append(PageBreak())

    # === PÁGINA 4: REQUISITOS Y CONTACTO ===
    elementos.append(Paragraph("REQUISITOS TÉCNICOS", titulo_principal))
    elementos.append(crear_linea_decorativa(400))
    elementos.append(Spacer(1, 0.5*cm))

    # Tabla de requisitos
    datos_requisitos = [
        ['Componente', 'Requisito'],
        ['Servidor', 'Linux (Debian/Ubuntu/CentOS) o Windows Server'],
        ['Base de Datos', 'Microsoft SQL Server 2008 o superior'],
        ['Python', 'Python 3.11 o superior'],
        ['Navegador', 'Chrome, Firefox, Safari, Edge (versiones actuales)'],
        ['Red', 'Conexión a base de datos SQL Server'],
    ]

    tabla_requisitos = Table(datos_requisitos, colWidths=[4*cm, 13*cm])
    tabla_requisitos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    elementos.append(tabla_requisitos)

    elementos.append(Spacer(1, 1*cm))

    # Opciones de despliegue
    elementos.append(Paragraph("OPCIONES DE DESPLIEGUE", seccion_titulo))

    datos_despliegue = [
        ['Opción', 'Descripción', 'Ideal para'],
        ['Docker', 'Contenedor preconfigurado con Gunicorn', 'Producción escalable'],
        ['Systemd', 'Servicio nativo en Linux', 'Servidores dedicados'],
        ['Python directo', 'Ejecución con Flask', 'Desarrollo y pruebas'],
    ]

    tabla_despliegue = Table(datos_despliegue, colWidths=[3.5*cm, 7*cm, 6*cm])
    tabla_despliegue.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
    ]))
    elementos.append(tabla_despliegue)

    elementos.append(Spacer(1, 1.5*cm))

    # Incluye
    elementos.append(Paragraph("¿QUÉ INCLUYE?", seccion_titulo))

    incluye_items = [
        "✓ Código fuente completo del sistema",
        "✓ Scripts SQL para creación de tablas",
        "✓ Documentación técnica detallada",
        "✓ Cliente PowerBuilder 2022 para integración",
        "✓ Scripts de instalación para Linux",
        "✓ Configuración Docker lista para producción",
        "✓ Soporte técnico por email",
        "✓ Actualizaciones de seguridad"
    ]

    # Crear tabla de 2 columnas para los items
    items_col1 = incluye_items[:4]
    items_col2 = incluye_items[4:]

    datos_incluye = [[items_col1[i] if i < len(items_col1) else '',
                      items_col2[i] if i < len(items_col2) else '']
                     for i in range(max(len(items_col1), len(items_col2)))]

    tabla_incluye = Table(datos_incluye, colWidths=[8.5*cm, 8.5*cm])
    tabla_incluye.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_incluye)

    elementos.append(Spacer(1, 1.5*cm))

    # Caja de contacto
    elementos.append(crear_linea_decorativa(400))
    elementos.append(Spacer(1, 0.5*cm))

    contacto_style = ParagraphStyle(
        'Contacto',
        parent=styles['Normal'],
        fontSize=12,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        leading=18
    )

    elementos.append(Paragraph(
        "<b>¿Interesado en implementar esta solución?</b><br/><br/>"
        "Contacte con nosotros para una demostración personalizada<br/>"
        "y presupuesto adaptado a sus necesidades.",
        contacto_style
    ))

    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(crear_linea_decorativa(400))

    # Generar PDF
    doc.build(elementos)
    print("[OK] Folleto generado: folleto_gestion_stocks.pdf")

if __name__ == '__main__':
    generar_folleto()
