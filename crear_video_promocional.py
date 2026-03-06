#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Video promocional del Sistema de Gestion de Stocks
Flujo completo: Login > Catalogo > Filtro > Busqueda voz > Detalle > Carrito > Firmar > Enviar
             + Busqueda magica > Usuarios > Pedidos > Detalle pedido > Mapa

Datos sensibles (nombres clientes, precios, emails) se difuminan automaticamente.

Autor: Jóbers
Actualizado: 2026-03-03
"""

import os
import time
import asyncio
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

# Configuracion de voz
VOZ_ESPANOLA = "es-ES-AlvaroNeural"
VELOCIDAD_VOZ = "+0%"

# Configuracion
BASE_URL = "https://jobcloudstocks.jobers.es"
EMPRESA_ID = "10049"
USERNAME = "admin"
PASSWORD = "Desa2012."

DISPLAY_NAME = "Administrador"  # Nombre visible en el video (no el real del usuario)

OUTPUT_VIDEO = "video_promocional_stocks.mp4"
SCREENSHOTS_DIR = "screenshots_promo"
AUDIO_DIR = "audio_promo"
FPS = 24
TOTAL_SCENES = 12  # 1:Intro, 2:Login, 3:Catalogo, 4:Filtro, 5:Detalle, 6:Carrito, 7:Firma, 8:Enviado, 9:BusqMagica, 10:Usuarios, 11:Pedidos, 12:ERP


# ================================================================
# CSS para difuminar datos sensibles en capturas
# ================================================================
BLUR_CSS_USUARIOS = """
(function() {
    const style = document.createElement('style');
    style.id = 'promo-blur';
    style.textContent = `
        /* Difuminar nombre completo (col 2), email (col 3), nombre empresa (col 4) */
        .users-table td:nth-child(2),
        .users-table td:nth-child(3),
        .users-table td:nth-child(4) {
            filter: blur(5px) !important;
            user-select: none !important;
        }
        /* Difuminar en tarjetas movil */
        .user-card .grid-card-field span:last-child {
            filter: blur(5px) !important;
        }
        .user-card-name, .user-card-username {
            filter: blur(5px) !important;
        }
    `;
    document.head.appendChild(style);
})();
"""

BLUR_CSS_PEDIDOS = """
(function() {
    const style = document.createElement('style');
    style.id = 'promo-blur';
    style.textContent = `
        /* Difuminar cliente (col 3), referencia (col 4) y total (col 7) */
        #orders-grid table tbody td:nth-child(3),
        #orders-grid table tbody td:nth-child(4),
        #orders-grid table tbody td:nth-child(7) {
            filter: blur(5px) !important;
            user-select: none !important;
        }
        /* Difuminar en tarjetas movil */
        .grid-card .grid-card-field span:last-child {
            filter: blur(5px) !important;
        }
    `;
    document.head.appendChild(style);
})();
"""

BLUR_CSS_PEDIDO_DETALLE = """
(function() {
    const style = document.createElement('style');
    style.id = 'promo-blur-detail';
    style.textContent = `
        /* Difuminar nombre cliente, precios e importes en modal detalle */
        .proposal-info-item span {
            filter: blur(5px) !important;
        }
        /* Mantener visibles las etiquetas */
        .proposal-info-item label {
            filter: none !important;
        }
        /* Difuminar columnas de precio e importe en lineas */
        .order-lines-table td.text-right {
            filter: blur(5px) !important;
        }
        .order-lines-table th.text-right {
            filter: none !important;
        }
    `;
    document.head.appendChild(style);
})();
"""

BLUR_CSS_CATALOGO_PRECIOS = """
(function() {
    const style = document.createElement('style');
    style.id = 'promo-blur-prices';
    style.textContent = `
        /* Difuminar badges de precio en tarjetas del catalogo */
        .badge-price {
            filter: blur(5px) !important;
        }
        /* Difuminar precios en tabla */
        .stock-table td[data-col="precio"] {
            filter: blur(5px) !important;
        }
        /* Difuminar precio en modal de detalle */
        .detail-item:has(.detail-label) .detail-value strong[style*="color"] {
            filter: blur(5px) !important;
        }
    `;
    document.head.appendChild(style);
})();
"""


def setup_directories():
    """Crea directorios necesarios"""
    for dir_path in [SCREENSHOTS_DIR, AUDIO_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    print(f"Capturas: {SCREENSHOTS_DIR}")
    print(f"Audio: {AUDIO_DIR}")


def setup_browser():
    """Configura Chrome con Selenium en modo headless"""
    print("Iniciando navegador...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver


def fix_image_dimensions(filepath):
    """Corrige dimensiones para que sean divisibles por 2 (requisito video)"""
    img = Image.open(filepath)
    w, h = img.size
    new_w = w if w % 2 == 0 else w - 1
    new_h = h if h % 2 == 0 else h - 1
    if new_w != w or new_h != h:
        img = img.crop((0, 0, new_w, new_h))
        img.save(filepath)
    return filepath


def capture_screenshot(driver, name):
    """Captura screenshot del navegador"""
    filepath = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    driver.save_screenshot(filepath)
    fix_image_dimensions(filepath)
    img = Image.open(filepath)
    print(f"    Captura: {name}.png ({img.size[0]}x{img.size[1]})")
    return filepath


def generate_audio(text, name):
    """Genera audio con Edge TTS"""
    filepath = os.path.join(AUDIO_DIR, f"{name}.mp3")

    async def _generate():
        communicate = edge_tts.Communicate(
            text=text,
            voice=VOZ_ESPANOLA,
            rate=VELOCIDAD_VOZ
        )
        await communicate.save(filepath)

    asyncio.run(_generate())
    size_kb = os.path.getsize(filepath) / 1024
    print(f"    Audio: {name}.mp3 ({size_kb:.1f} KB)")
    return filepath


def get_audio_duration(path):
    """Obtiene duracion del audio"""
    audio = AudioFileClip(path)
    dur = audio.duration
    audio.close()
    return dur


def create_video_clip(image_path, audio_path, extra_time=0.5):
    """Crea clip con imagen estatica y audio"""
    audio_dur = get_audio_duration(audio_path)
    duration = audio_dur + extra_time
    img_clip = ImageClip(image_path).with_duration(duration)
    audio = AudioFileClip(audio_path)
    return img_clip.with_audio(audio)


def api_login(driver):
    """Login via API para obtener sesion y CSRF token"""
    print("    Haciendo login via API...")
    login_result = driver.execute_script(f"""
        try {{
            const resp = await fetch('{BASE_URL}/api/login', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                credentials: 'include',
                body: JSON.stringify({{
                    username: '{USERNAME}',
                    password: '{PASSWORD}',
                    empresa_cli_id: '{EMPRESA_ID}'
                }})
            }});
            const data = await resp.json();
            return JSON.stringify(data);
        }} catch(e) {{
            return JSON.stringify({{success: false, message: e.toString()}});
        }}
    """)
    result = json.loads(login_result)
    if result.get('success'):
        empresa_id = result.get('user', {}).get('empresa_id', EMPRESA_ID)
        driver.execute_script(f"""
            localStorage.setItem('connection', '{EMPRESA_ID}');
            localStorage.setItem('empresa_id', '{empresa_id}');
            localStorage.setItem('theme', 'light');
            if (arguments[0]) localStorage.setItem('csrf_token', arguments[0]);
        """, result.get('csrf_token', ''))
        print(f"    Login exitoso (empresa_id={empresa_id})")
        return True
    else:
        print(f"    Login fallido: {result.get('message')}")
        return False


def replace_display_name(driver):
    """Reemplaza el nombre del usuario en la UI por DISPLAY_NAME"""
    driver.execute_script(f"""
        document.querySelectorAll('#user-name-display, #menu-user-name, .user-name, .sidebar-user-name').forEach(el => {{
            if (el.textContent.trim()) el.textContent = '{DISPLAY_NAME}';
        }});
    """)


def force_load_thumbnails(driver, limit=30):
    """Fuerza la carga de los primeros N thumbnails visibles (await batch API)"""
    driver.set_script_timeout(60)
    try:
        result = driver.execute_async_script("""
            const done = arguments[arguments.length - 1];
            const limit = arguments[0];
            const allCodigos = [];
            const imgs = document.querySelectorAll('.stock-thumb[data-codigo]');
            for (let i = 0; i < Math.min(imgs.length, limit); i++) {
                const codigo = imgs[i].dataset.codigo.trim();
                if (codigo && !imgs[i].classList.contains('loaded')) {
                    allCodigos.push(codigo);
                }
            }

            if (allCodigos.length > 0 && typeof cargarThumbnailsBatch === 'function') {
                cargarThumbnailsBatch(allCodigos)
                    .then(() => done(allCodigos.length))
                    .catch(e => { console.error(e); done(-1); });
            } else {
                done(0);
            }
        """, limit)
        print(f"    Thumbnails procesados: {result}/{limit}")
        return result
    except Exception as e:
        print(f"    [!] Error cargando thumbnails: {e}")
        return -1


def inject_blur(driver, css_js):
    """Inyecta CSS de blur para ocultar datos sensibles"""
    # Eliminar blur previo si existe
    driver.execute_script("document.getElementById('promo-blur')?.remove();")
    driver.execute_script("document.getElementById('promo-blur-detail')?.remove();")
    driver.execute_script("document.getElementById('promo-blur-prices')?.remove();")
    driver.execute_script(css_js)


def create_intro_image():
    """Genera imagen de presentacion (1920x1080) con logo Jóbers y texto"""
    WIDTH, HEIGHT = 1920, 1080

    # Colores
    BG_COLOR = (13, 13, 26)
    RED = (255, 67, 56)
    WHITE = (255, 255, 255)
    LIGHT_GRAY = (190, 190, 205)
    SUBTLE = (120, 120, 145)

    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Resplandor rojo sutil en el centro (circulos concentricos con blend manual)
    for r in range(500, 0, -2):
        factor = 0.04 * (r / 500)
        blended = tuple(int(BG_COLOR[i] * (1 - factor) + RED[i] * factor * 0.3) for i in range(3))
        x0, y0 = WIDTH // 2 - r * 2, HEIGHT // 2 - r - 50
        x1, y1 = WIDTH // 2 + r * 2, HEIGHT // 2 + r - 50
        draw.ellipse([x0, y0, x1, y1], fill=blended)

    # Barra roja decorativa en la parte superior
    draw.rectangle([0, 0, WIDTH, 5], fill=RED)

    # Cargar y colocar logo
    logo_path = os.path.join(os.path.dirname(__file__), "frontend", "assets", "logojobers.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        # Escalar logo a ~280px de ancho
        logo_target_w = 280
        ratio = logo_target_w / logo.size[0]
        logo_h = int(logo.size[1] * ratio)
        logo = logo.resize((logo_target_w, logo_h), Image.LANCZOS)

        # Fondo blanco redondeado detras del logo
        pad = 25
        logo_x = (WIDTH - logo_target_w) // 2
        logo_y = 130
        draw.rounded_rectangle(
            [logo_x - pad, logo_y - pad,
             logo_x + logo_target_w + pad, logo_y + logo_h + pad],
            radius=18,
            fill=WHITE
        )

        # Pegar logo
        if logo.mode == 'RGBA':
            img.paste(logo, (logo_x, logo_y), logo)
        else:
            img.paste(logo, (logo_x, logo_y))
        text_start_y = logo_y + logo_h + 60
    else:
        text_start_y = 200

    # Fuentes
    try:
        font_title = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 96)
        font_sub = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuil.ttf", 34)
        font_feat = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 28)
        font_small = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuil.ttf", 20)
    except Exception:
        font_title = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 96)
        font_sub = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 34)
        font_feat = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 28)
        font_small = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 20)

    def center_text(text, font, y, color):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, y), text, fill=color, font=font)

    # Titulo "JobStocks"
    center_text("JobStocks", font_title, text_start_y, WHITE)

    # Linea roja decorativa
    line_y = text_start_y + 115
    line_w = 460
    draw.rounded_rectangle(
        [(WIDTH - line_w) // 2, line_y,
         (WIDTH + line_w) // 2, line_y + 4],
        radius=2, fill=RED
    )

    # Subtitulo
    sub_y = line_y + 28
    center_text("Plataforma integral para la externalización", font_sub, sub_y, LIGHT_GRAY)
    center_text("de stocks de fábrica", font_sub, sub_y + 46, LIGHT_GRAY)

    # Caracteristicas con viñetas rojas
    features = [
        "Catálogo de productos en tiempo real",
        "Propuestas de pedido con firma digital",
        "Búsqueda visual con inteligencia artificial",
        "Integración directa con su sistema ERP",
    ]
    feat_y = sub_y + 130
    for feat in features:
        full = f"▸  {feat}"
        bbox = draw.textbbox((0, 0), full, font=font_feat)
        tw = bbox[2] - bbox[0]
        fx = (WIDTH - tw) // 2
        # Viñeta en rojo
        draw.text((fx, feat_y), "▸", fill=RED, font=font_feat)
        bullet_w = draw.textbbox((0, 0), "▸  ", font=font_feat)[2]
        draw.text((fx + bullet_w, feat_y), feat, fill=WHITE, font=font_feat)
        feat_y += 46

    # Pie
    center_text("by Jóbers  ·  jobers.es", font_small, HEIGHT - 55, SUBTLE)

    # Guardar
    filepath = os.path.join(SCREENSHOTS_DIR, "00_intro.png")
    img.save(filepath, quality=95)
    fix_image_dimensions(filepath)
    print(f"    Intro generada: 00_intro.png ({WIDTH}x{HEIGHT})")
    return filepath


def main():
    print("\n" + "=" * 60)
    print("VIDEO PROMOCIONAL - FLUJO COMPLETO DE USUARIO")
    print("=" * 60)
    print(f"Servidor: {BASE_URL}")
    print(f"Salida: {OUTPUT_VIDEO}")
    print(f"Escenas: {TOTAL_SCENES}")
    print("-" * 60)

    setup_directories()

    driver = None
    try:
        driver = setup_browser()
        clips = []

        # ============================================================
        # ESCENA 1: PANTALLA DE PRESENTACION (INTRO)
        # ============================================================
        print(f"\n[1/{TOTAL_SCENES}] PANTALLA DE PRESENTACION...")

        intro_img = create_intro_image()
        intro_audio = generate_audio(
            "JobStocks, de Jóbers. "
            "Externalice el stock de su fábrica. "
            "Catálogo en tiempo real, propuestas con firma digital, "
            "búsqueda por inteligencia artificial "
            "y sincronización directa con su ERP.",
            "00_intro"
        )
        clips.append(create_video_clip(intro_img, intro_audio, extra_time=1.0))

        # ============================================================
        # ESCENA 2: PANTALLA DE LOGIN CON CREDENCIALES
        # ============================================================
        print(f"\n[2/{TOTAL_SCENES}] PANTALLA DE LOGIN...")

        for _attempt in range(3):
            try:
                driver.get(f"{BASE_URL}/login")
                break
            except Exception as e:
                print(f"    [!] Reintentando carga login ({_attempt+1}/3): {e}")
                time.sleep(5)
        time.sleep(3)
        driver.execute_script(f"localStorage.setItem('connection', '{EMPRESA_ID}'); localStorage.setItem('theme', 'light');")
        for _attempt in range(3):
            try:
                driver.get(f"{BASE_URL}/login")
                break
            except Exception as e:
                print(f"    [!] Reintentando carga login ({_attempt+1}/3): {e}")
                time.sleep(5)
        time.sleep(5)

        # Rellenar credenciales antes de capturar
        username_field = driver.find_element(By.ID, "username")
        username_field.clear()
        username_field.send_keys(USERNAME)
        time.sleep(0.3)
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        time.sleep(0.5)

        audio = generate_audio(
            "Acceda al sistema con sus credenciales de forma segura.",
            "01_login"
        )
        img = capture_screenshot(driver, "01_login")
        clips.append(create_video_clip(img, audio, extra_time=0.8))

        # Login real via API
        if not api_login(driver):
            print("[ERROR] No se pudo hacer login")
            return

        # ============================================================
        # ESCENA 3: CATALOGO DE PRODUCTOS CARGADO (con imagenes)
        # ============================================================
        print(f"\n[3/{TOTAL_SCENES}] CATALOGO DE PRODUCTOS...")

        driver.get(f"{BASE_URL}/index.html")
        time.sleep(2)

        # Esperar a que initApp() complete (muestra estado inicial "Buscar productos")
        print("    Esperando que initApp() complete...")
        for i in range(40):
            has_empty = driver.execute_script(
                "return document.querySelector('.empty-state') !== null"
            )
            if has_empty:
                print(f"    initApp() completo tras {(i+1)*0.5}s")
                break
            time.sleep(0.5)
        else:
            print("    [!] initApp() no completo tras 20s, continuando...")

        # Reemplazar nombre del usuario en la UI
        replace_display_name(driver)

        # Activar vista de tarjetas con imagenes (desactivada por defecto)
        driver.execute_script("gridConImagenes = true;")

        # Inyectar blur de precios en catalogo
        inject_blur(driver, BLUR_CSS_CATALOGO_PRECIOS)

        # Filtrar por color negro para mostrar imágenes oscuras
        driver.execute_script("""
            const colorInput = document.getElementById('filter-color');
            if (colorInput) {
                colorInput.value = 'NEGRO';
                colorInput.dispatchEvent(new Event('input'));
            }
        """)
        print("    Filtro color: NEGRO")

        # Lanzar busqueda (await async)
        print("    Ejecutando buscarStocks()...")
        driver.set_script_timeout(30)
        try:
            result = driver.execute_async_script("""
                const done = arguments[arguments.length - 1];
                buscarStocks()
                    .then(() => done('ok'))
                    .catch(e => done('error: ' + e.message));
            """)
            print(f"    buscarStocks: {result}")
        except Exception as e:
            print(f"    [!] Error buscarStocks: {e}")

        time.sleep(2)

        # Verificar que hay resultados
        card_count = driver.execute_script(
            "return document.querySelectorAll('.stock-image-card, table tbody tr').length"
        )
        print(f"    Productos en grid: {card_count}")

        if card_count == 0:
            print("    [!] Sin datos, reintentando...")
            try:
                driver.execute_async_script("""
                    const done = arguments[arguments.length - 1];
                    buscarStocks()
                        .then(() => done('ok'))
                        .catch(e => done('error: ' + e.message));
                """)
            except Exception:
                pass
            time.sleep(3)

        # Forzar carga de thumbnails (await batch API)
        force_load_thumbnails(driver)
        time.sleep(2)

        # Verificar cuantas se cargaron
        loaded_count = driver.execute_script(
            "return document.querySelectorAll('.stock-thumb.loaded').length"
        )
        total_count = driver.execute_script(
            "return document.querySelectorAll('.stock-thumb[data-codigo]').length"
        )
        print(f"    Thumbnails cargados: {loaded_count}/{total_count}")

        # Segunda pasada si quedaron pendientes
        if loaded_count < total_count:
            force_load_thumbnails(driver)
            loaded_count = driver.execute_script(
                "return document.querySelectorAll('.stock-thumb.loaded').length"
            )
            print(f"    Thumbnails cargados (2a pasada): {loaded_count}/{total_count}")

        # Forzar opacity 1 en todas las imagenes
        driver.execute_script("""
            document.querySelectorAll('.stock-thumb').forEach(img => {
                img.style.opacity = '1';
            });
        """)
        time.sleep(1)

        audio = generate_audio(
            "Catálogo con imágenes reales, "
            "actualizado en tiempo real desde su ERP.",
            "03_catalogo"
        )
        img = capture_screenshot(driver, "03_catalogo")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 4: FILTRAR POR FORMATO 25x40
        # ============================================================
        print(f"\n[4/{TOTAL_SCENES}] FILTRAR POR FORMATO 25x40...")

        # Añadir formato 25x40 al filtro de color negro ya activo
        driver.execute_script("""
            const select = document.getElementById('filter-formato');
            if (select) {
                // Buscar opcion que contenga 25x40
                for (const opt of select.options) {
                    if (opt.value.includes('25') && opt.value.includes('40')) {
                        select.value = opt.value;
                        break;
                    }
                }
            }
        """)
        print("    Filtro formato: 25x40")

        try:
            driver.execute_async_script("""
                const done = arguments[arguments.length - 1];
                buscarStocks().then(() => done('ok')).catch(e => done('error: ' + e.message));
            """)
        except Exception:
            pass
        time.sleep(2)

        force_load_thumbnails(driver)
        time.sleep(2)
        force_load_thumbnails(driver)
        driver.execute_script("""
            document.querySelectorAll('.stock-thumb').forEach(img => {
                img.style.opacity = '1';
            });
        """)

        narr_filtro = (
            "Filtros avanzados. Aquí filtramos por color negro y formato 25x40. "
            "También por modelo, calidad o existencias."
        )

        # Re-inyectar blur (se pierde al buscar porque se re-renderiza)
        inject_blur(driver, BLUR_CSS_CATALOGO_PRECIOS)
        time.sleep(0.3)

        audio = generate_audio(narr_filtro, "04_filtro")
        img = capture_screenshot(driver, "04_filtro")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 5: DETALLE DE PRODUCTO
        # ============================================================
        print(f"\n[5/{TOTAL_SCENES}] DETALLE DE PRODUCTO...")

        try:
            first_card = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".stock-image-card"))
            )
            first_card.click()
        except Exception:
            driver.execute_script("""
                const card = document.querySelector('.stock-image-card');
                if (card) card.click();
                else {
                    const row = document.querySelector('table tbody tr');
                    if (row) row.querySelector('td').click();
                }
            """)

        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script(
                    "const m = document.getElementById('detail-modal'); "
                    "return m && m.style.display !== 'none';"
                )
            )
        except Exception:
            pass

        # Esperar a que las imagenes de la galeria se carguen desde la API
        print("    Esperando carga de imagenes de galeria...")
        for i in range(20):
            img_count = driver.execute_script("""
                const imgs = document.querySelectorAll('#detail-imagenes img, .detail-gallery img');
                let loaded = 0;
                imgs.forEach(img => {
                    if (img.src && img.src.startsWith('data:image')) loaded++;
                });
                return loaded;
            """)
            if img_count > 0:
                print(f"    Imagenes de galeria cargadas: {img_count}")
                break
            time.sleep(0.5)
        else:
            print("    [!] Imagenes de galeria no cargaron")

        time.sleep(2)

        # Forzar visibilidad de imagenes del detalle
        driver.execute_script("""
            document.querySelectorAll('#detail-imagenes img, .detail-gallery img').forEach(img => {
                img.style.opacity = '1';
                img.classList.add('loaded');
            });
        """)
        time.sleep(1)

        # Blur de precios en detalle
        inject_blur(driver, BLUR_CSS_CATALOGO_PRECIOS)

        audio = generate_audio(
            "Ficha completa del producto: "
            "galería de imágenes, empaquetado, "
            "ficha técnica PDF y contacto directo.",
            "05_detalle"
        )
        img = capture_screenshot(driver, "05_detalle")
        clips.append(create_video_clip(img, audio))

        # Agregar producto al carrito (sin escena separada)
        print("    Agregando producto al carrito...")
        driver.execute_script("agregarAlCarritoDesdeDetalle()")
        time.sleep(2)
        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "quantity-modal-overlay"))
            )
        except Exception:
            pass
        driver.execute_script("""
            const btns = document.querySelectorAll('.quantity-package-btn-primary');
            if (btns.length > 0) btns[0].click();
        """)
        time.sleep(1)
        driver.execute_script("confirmarAgregarAlCarrito()")
        time.sleep(4)
        cart_count = driver.execute_script("return carrito.length")
        print(f"    Productos en carrito: {cart_count}")

        # ============================================================
        # ESCENA 6: VISTA DEL CARRITO
        # ============================================================
        print(f"\n[6/{TOTAL_SCENES}] VISTA DEL CARRITO...")

        if cart_count > 0:
            driver.execute_script("verCarrito()")
        else:
            driver.execute_script("""
                const btn = document.querySelector('.carrito-btn');
                if (btn) btn.click();
            """)
        time.sleep(2)

        audio = generate_audio(
            "Carrito de solicitudes. "
            "Revise cantidades y calidades antes del envío.",
            "07_carrito"
        )
        img = capture_screenshot(driver, "07_carrito")
        clips.append(create_video_clip(img, audio))

        # Rellenar formulario de envío (sin escena separada)
        driver.execute_script("mostrarFormularioEnvio()")
        time.sleep(2)
        driver.execute_script("""
            const ref = document.getElementById('referencia-envio');
            if (ref) {
                ref.value = 'REF-2026-001';
                ref.dispatchEvent(new Event('input'));
            }
            const com = document.getElementById('comentarios-envio');
            if (com) {
                com.value = 'Solicitud de muestra para showroom.';
                com.dispatchEvent(new Event('input'));
            }
        """)
        time.sleep(1)

        # ============================================================
        # ESCENA 7: FIRMA DIGITAL
        # ============================================================
        print(f"\n[7/{TOTAL_SCENES}] FIRMA DIGITAL...")

        has_firma = driver.execute_script("""
            const firmaCheck = document.getElementById('firmar-propuesta');
            if (firmaCheck) {
                firmaCheck.checked = true;
                togglePanelFirma(true);
                return true;
            }
            return false;
        """)
        time.sleep(1)

        if has_firma:
            driver.execute_script("""
                const canvas = document.getElementById('signature-canvas');
                if (canvas) {
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    ctx.beginPath();
                    ctx.strokeStyle = '#1a1a2e';
                    ctx.lineWidth = 2.5;
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                    ctx.moveTo(40, 140);
                    ctx.quadraticCurveTo(70, 70, 100, 130);
                    ctx.quadraticCurveTo(115, 165, 135, 105);
                    ctx.quadraticCurveTo(155, 55, 175, 125);
                    ctx.moveTo(200, 135);
                    ctx.quadraticCurveTo(230, 65, 260, 125);
                    ctx.quadraticCurveTo(280, 165, 300, 95);
                    ctx.quadraticCurveTo(320, 45, 345, 115);
                    ctx.quadraticCurveTo(365, 165, 390, 105);
                    ctx.moveTo(40, 180);
                    ctx.quadraticCurveTo(200, 205, 390, 170);
                    ctx.stroke();
                    hasSignature = true;
                }
            """)
            time.sleep(1)

            driver.execute_script("""
                const content = document.getElementById('carrito-content');
                if (content) content.scrollTop = content.scrollHeight;
            """)
            time.sleep(0.5)

            audio = generate_audio(
                "Firme digitalmente la propuesta para dar su conformidad. "
                "La firma se incluye en el PDF que se genera automáticamente.",
                "09_firma"
            )
        else:
            print("    [!] Panel de firma no disponible, capturando formulario...")
            audio = generate_audio(
                "Revise los datos del formulario. "
                "Todo listo para enviar la solicitud.",
                "09_firma"
            )

        img = capture_screenshot(driver, "09_firma")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 8: ENVIAR PROPUESTA
        # ============================================================
        print(f"\n[8/{TOTAL_SCENES}] ENVIANDO PROPUESTA...")

        driver.execute_script("""
            const content = document.getElementById('carrito-content');
            if (content) content.scrollTop = 0;
        """)
        time.sleep(0.5)

        driver.execute_script("enviarSolicitud()")
        time.sleep(8)

        audio = generate_audio(
            "Solicitud enviada. "
            "Se genera un PDF con imágenes y firma digital, "
            "y se envía por email automáticamente.",
            "10_enviado"
        )
        img = capture_screenshot(driver, "10_enviado")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 9: BUSQUEDA MAGICA
        # ============================================================
        print(f"\n[9/{TOTAL_SCENES}] BUSQUEDA MAGICA...")

        driver.get(f"{BASE_URL}/busqueda-magica.html")
        time.sleep(4)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "drop-zone"))
            )
        except Exception:
            pass
        time.sleep(2)
        replace_display_name(driver)

        # Subir imagen de prueba para mostrar resultados reales
        # prueba_catalogo.jpg es una imagen real del catálogo que garantiza resultados
        prueba_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "Recursos IA", "prueba_catalogo.jpg"))
        if not os.path.exists(prueba_img):
            prueba_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "Recursos IA", "prueba1.jpg"))
        if os.path.exists(prueba_img):
            print("    Subiendo imagen de prueba para busqueda visual...")
            file_input = driver.find_element(By.ID, "file-input")
            file_input.send_keys(prueba_img)
            time.sleep(2)
            # Clicar botón "Buscar productos similares"
            try:
                search_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btn-search"))
                )
                search_btn.click()
                print("    Botón 'Buscar' clicado, esperando resultados...")
            except Exception as e:
                print(f"    [!] No se pudo clicar botón de búsqueda: {e}")
            # Esperar a que aparezcan resultados (tarjetas .stock-image-card)
            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".stock-image-card"))
                )
                print("    Resultados encontrados!")
            except Exception:
                print("    [!] No se encontraron resultados de busqueda visual")
            time.sleep(3)
            replace_display_name(driver)
        else:
            print(f"    [!] No se encontro imagen: {prueba_img}")

        # Inyectar blur de precios en resultados
        inject_blur(driver, BLUR_CSS_CATALOGO_PRECIOS)
        time.sleep(0.3)

        audio = generate_audio(
            "Búsqueda mágica por imagen. "
            "Arrastre una foto y la inteligencia artificial "
            "encontrará los productos más similares de su catálogo.",
            "11_busqueda_magica"
        )
        img = capture_screenshot(driver, "11_busqueda_magica")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 10: GESTION DE USUARIOS (con blur)
        # ============================================================
        print(f"\n[10/{TOTAL_SCENES}] GESTION DE USUARIOS...")

        driver.get(f"{BASE_URL}/usuarios.html")
        time.sleep(4)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".users-table tbody tr, .user-card"))
            )
        except Exception:
            print("    [!] Esperando carga de usuarios...")
            time.sleep(5)
        time.sleep(3)

        # Difuminar emails y nombres reales
        inject_blur(driver, BLUR_CSS_USUARIOS)
        replace_display_name(driver)
        time.sleep(0.5)

        audio = generate_audio(
            "Administración de usuarios. "
            "Gestione cuentas, roles y permisos "
            "con filtros avanzados por columna.",
            "12_usuarios"
        )
        img = capture_screenshot(driver, "12_usuarios")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 11: PEDIDOS DE VENTA - LISTA (con blur)
        # ============================================================
        print(f"\n[11/{TOTAL_SCENES}] PEDIDOS DE VENTA...")

        driver.get(f"{BASE_URL}/todos-pedidos.html")
        time.sleep(4)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#orders-grid table tbody tr, #orders-grid .proposal-card"))
            )
        except Exception:
            print("    [!] Esperando carga de pedidos...")
            time.sleep(5)
        time.sleep(3)

        # Difuminar nombres de clientes y totales
        inject_blur(driver, BLUR_CSS_PEDIDOS)
        replace_display_name(driver)
        time.sleep(0.5)

        audio = generate_audio(
            "Pedidos de venta sincronizados con su ERP. "
            "Filtre por año, país o cliente.",
            "13_pedidos"
        )
        img = capture_screenshot(driver, "13_pedidos")
        clips.append(create_video_clip(img, audio))

        # Cerrar navegador
        driver.quit()
        driver = None

        # ============================================================
        # ESCENA 12: INTEGRADOR ERP (imagen estática)
        # ============================================================
        print(f"\n[{TOTAL_SCENES}/{TOTAL_SCENES}] INTEGRADOR ERP...")

        erp_img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "Recursos IA", "integrador.png"))
        if os.path.exists(erp_img_path):
            audio = generate_audio(
                "Integración directa con su ERP. "
                "Las propuestas se importan automáticamente como pedidos de venta. "
                "Todo conectado mediante API REST segura.",
                "17_integrador_erp"
            )
            audio_dur = get_audio_duration(os.path.join(AUDIO_DIR, "17_integrador_erp.mp3"))
            erp_clip = ImageClip(erp_img_path).with_duration(audio_dur + 1.5)
            erp_audio = AudioFileClip(os.path.join(AUDIO_DIR, "17_integrador_erp.mp3"))
            clips.append(erp_clip.with_audio(erp_audio))
        else:
            print(f"    [!] No se encontro imagen: {erp_img_path}")

        # ============================================================
        # COMBINAR VIDEO
        # ============================================================
        print("\n" + "-" * 60)
        print(f"Combinando {len(clips)} clips...")

        final = concatenate_videoclips(clips, method="compose")

        print("Generando video final...")
        final.write_videofile(
            OUTPUT_VIDEO,
            fps=FPS,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium',
            ffmpeg_params=['-pix_fmt', 'yuv420p']
        )

        for c in clips:
            c.close()
        final.close()

        size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)

        print("\n" + "=" * 60)
        print(f"[OK] Video generado: {OUTPUT_VIDEO}")
        print(f"     Tamano: {size:.1f} MB")
        print(f"     Escenas: {TOTAL_SCENES}")
        print("=" * 60)
        print("\nPara anadir musica de fondo ejecuta:")
        print("  python añadir_musica_video.py")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
