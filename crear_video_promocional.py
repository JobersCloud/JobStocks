#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Video promocional del Sistema de Gestion de Stocks
Flujo completo: Login > Catalogo > Filtro > Busqueda voz > Detalle > Carrito > Firmar > Enviar
             + Busqueda magica > Usuarios > Pedidos > Detalle pedido > Mapa

Datos sensibles (nombres clientes, precios, emails) se difuminan automaticamente.

Autor: Jobers
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
from PIL import Image

# Configuracion de voz
VOZ_ESPANOLA = "es-ES-AlvaroNeural"
VELOCIDAD_VOZ = "+0%"

# Configuracion
BASE_URL = "http://localhost:5000"
EMPRESA_ID = "10049"
USERNAME = "admin"
PASSWORD = "Desa2012."

OUTPUT_VIDEO = "video_promocional_stocks.mp4"
SCREENSHOTS_DIR = "screenshots_promo"
AUDIO_DIR = "audio_promo"
FPS = 24
TOTAL_SCENES = 16


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
    driver.set_page_load_timeout(30)
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


def create_video_clip(image_path, audio_path, extra_time=1.5):
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
            if (arguments[0]) localStorage.setItem('csrf_token', arguments[0]);
        """, result.get('csrf_token', ''))
        print(f"    Login exitoso (empresa_id={empresa_id})")
        return True
    else:
        print(f"    Login fallido: {result.get('message')}")
        return False


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
        # ESCENA 1: PANTALLA DE LOGIN
        # ============================================================
        print(f"\n[1/{TOTAL_SCENES}] PANTALLA DE LOGIN...")

        driver.get(f"{BASE_URL}/login")
        time.sleep(3)
        driver.execute_script(f"localStorage.setItem('connection', '{EMPRESA_ID}');")
        driver.get(f"{BASE_URL}/login")
        time.sleep(5)

        audio = generate_audio(
            "Bienvenido al Sistema de Gestión de Stocks. "
            "Plataforma profesional para la gestión de inventario cerámico. "
            "Acceda con sus credenciales para comenzar.",
            "01_login"
        )
        img = capture_screenshot(driver, "01_login")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 2: CREDENCIALES INTRODUCIDAS
        # ============================================================
        print(f"\n[2/{TOTAL_SCENES}] INTRODUCIENDO CREDENCIALES...")

        username_field = driver.find_element(By.ID, "username")
        username_field.clear()
        username_field.send_keys(USERNAME)
        time.sleep(0.3)

        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        time.sleep(0.5)

        audio = generate_audio(
            "Introduzca su usuario y contraseña. "
            "El sistema valida su identidad con cifrado seguro "
            "y protección contra intentos no autorizados.",
            "02_credenciales"
        )
        img = capture_screenshot(driver, "02_credenciales")
        clips.append(create_video_clip(img, audio))

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

        # Activar vista de tarjetas con imagenes (desactivada por defecto)
        driver.execute_script("gridConImagenes = true;")

        # Inyectar blur de precios en catalogo
        inject_blur(driver, BLUR_CSS_CATALOGO_PRECIOS)

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
            "El catálogo muestra todas las referencias de su inventario "
            "con imágenes reales de los productos, "
            "actualizadas en tiempo real desde su sistema ERP.",
            "03_catalogo"
        )
        img = capture_screenshot(driver, "03_catalogo")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 4: FILTRAR POR FORMATO
        # ============================================================
        print(f"\n[4/{TOTAL_SCENES}] FILTRAR POR FORMATO...")

        formats = driver.execute_script("""
            const select = document.getElementById('filter-formato');
            if (!select) return [];
            return Array.from(select.options).map(o => ({value: o.value, text: o.text})).filter(o => o.value !== '');
        """)
        print(f"    Formatos disponibles: {len(formats)}")

        target_format = ""
        narr_formato = ""
        if formats:
            fmt60 = next((f for f in formats if '60' in f['value']), None)
            if fmt60:
                target_format = fmt60['value']
                narr_formato = fmt60['text']
            else:
                target_format = formats[0]['value']
                narr_formato = formats[0]['text']

            print(f"    Seleccionando formato: {target_format}")
            driver.execute_script(f"""
                document.getElementById('filter-formato').value = '{target_format}';
            """)
            try:
                driver.execute_async_script("""
                    const done = arguments[arguments.length - 1];
                    buscarStocks().then(() => done('ok')).catch(e => done('error: ' + e.message));
                """)
            except Exception:
                pass
            time.sleep(2)

            # Forzar carga de thumbnails tras nuevo filtrado
            force_load_thumbnails(driver)
            time.sleep(2)
            # Segunda pasada
            force_load_thumbnails(driver)
            # Forzar opacity
            driver.execute_script("""
                document.querySelectorAll('.stock-thumb').forEach(img => {
                    img.style.opacity = '1';
                });
            """)

            has_results = driver.execute_script(
                "return document.querySelectorAll('.stock-image-card, table tbody tr').length > 0"
            )
            if not has_results:
                print("    [!] Sin resultados, probando otro formato...")
                if len(formats) > 1:
                    target_format = formats[1]['value']
                    narr_formato = formats[1]['text']
                    driver.execute_script(f"""
                        document.getElementById('filter-formato').value = '{target_format}';
                    """)
                    try:
                        driver.execute_async_script("""
                            const done = arguments[arguments.length - 1];
                            buscarStocks().then(() => done('ok')).catch(e => done('error: ' + e.message));
                        """)
                    except Exception:
                        pass
                    time.sleep(2)
                    force_load_thumbnails(driver)
                    driver.execute_script("""
                        document.querySelectorAll('.stock-thumb').forEach(img => {
                            img.style.opacity = '1';
                        });
                    """)

        if target_format:
            narr_filtro = (
                f"Utilice los filtros del panel de búsqueda para encontrar productos. "
                f"Aquí filtramos por formato {narr_formato}. "
                f"También puede filtrar por modelo, color, calidad o existencias mínimas."
            )
        else:
            narr_filtro = (
                "Explore todo el catálogo o filtre por formato, modelo, calidad o color "
                "para encontrar exactamente lo que necesita."
            )

        # Re-inyectar blur (se pierde al buscar porque se re-renderiza)
        inject_blur(driver, BLUR_CSS_CATALOGO_PRECIOS)
        time.sleep(0.3)

        audio = generate_audio(narr_filtro, "04_filtro")
        img = capture_screenshot(driver, "04_filtro")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 5: BUSQUEDA POR VOZ
        # ============================================================
        print(f"\n[5/{TOTAL_SCENES}] BUSQUEDA POR VOZ...")

        # Asegurar que estamos en la pagina del catalogo
        # Simular visualmente el estado "escuchando" del boton de voz
        driver.execute_script("""
            // Mostrar el boton de voz (forzar visible)
            const wrapper = document.getElementById('voice-search-wrapper');
            if (wrapper) wrapper.style.display = '';

            // Activar estado visual "escuchando" (pulso rojo)
            const btn = document.getElementById('btn-voice-search');
            if (btn) btn.classList.add('listening');

            // Mostrar tooltip de ayuda
            const tooltip = document.getElementById('voice-help-tooltip');
            if (tooltip) {
                tooltip.style.display = 'block';
                tooltip.innerHTML = '<strong>🎤 Escuchando...</strong><br>Diga el nombre del producto';
            }
        """)
        time.sleep(2)

        # Re-inyectar blur de precios
        inject_blur(driver, BLUR_CSS_CATALOGO_PRECIOS)
        time.sleep(0.3)

        audio = generate_audio(
            "Búsqueda por voz. "
            "Pulse el micrófono y diga el nombre del producto que busca. "
            "El sistema reconoce su voz y filtra el catálogo automáticamente. "
            "Compatible con español, inglés y francés.",
            "05_busqueda_voz"
        )
        img = capture_screenshot(driver, "05_busqueda_voz")
        clips.append(create_video_clip(img, audio))

        # Desactivar estado de escucha
        driver.execute_script("""
            const btn = document.getElementById('btn-voice-search');
            if (btn) btn.classList.remove('listening');
            const tooltip = document.getElementById('voice-help-tooltip');
            if (tooltip) tooltip.style.display = 'none';
        """)
        time.sleep(0.5)

        # ============================================================
        # ESCENA 6: DETALLE DE PRODUCTO
        # ============================================================
        print(f"\n[6/{TOTAL_SCENES}] DETALLE DE PRODUCTO...")

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
            "Haga clic en cualquier producto para ver su ficha completa. "
            "Galería de imágenes, datos de empaquetado, "
            "ficha técnica en PDF y contacto directo por email o WhatsApp.",
            "05_detalle"
        )
        img = capture_screenshot(driver, "05_detalle")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 7: MODAL DE CANTIDAD - ANADIR 1 CAJA
        # ============================================================
        print(f"\n[7/{TOTAL_SCENES}] ANADIR CAJA AL CARRITO...")

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

        audio = generate_audio(
            "Seleccione la cantidad deseada. "
            "Añada productos por caja o por pallet directamente con un solo clic. "
            "El sistema controla que no supere las existencias disponibles.",
            "06_cantidad"
        )
        img = capture_screenshot(driver, "06_cantidad")
        clips.append(create_video_clip(img, audio))

        # Confirmar agregar al carrito
        print("    Confirmando agregar al carrito...")
        driver.execute_script("confirmarAgregarAlCarrito()")
        time.sleep(4)

        cart_count = driver.execute_script("return carrito.length")
        print(f"    Productos en carrito: {cart_count}")

        # ============================================================
        # ESCENA 8: VISTA DEL CARRITO
        # ============================================================
        print(f"\n[8/{TOTAL_SCENES}] VISTA DEL CARRITO...")

        if cart_count > 0:
            driver.execute_script("verCarrito()")
        else:
            driver.execute_script("""
                const btn = document.querySelector('.carrito-btn');
                if (btn) btn.click();
            """)
        time.sleep(2)

        audio = generate_audio(
            "Revise los productos de su solicitud en el carrito. "
            "Verifique cantidades, formatos y calidades antes de continuar con el envío.",
            "07_carrito"
        )
        img = capture_screenshot(driver, "07_carrito")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 9: FORMULARIO DE ENVIO
        # ============================================================
        print(f"\n[9/{TOTAL_SCENES}] FORMULARIO DE ENVIO...")

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
                com.value = 'Solicitud de muestra para showroom. Entregar en horario de mañana, de 9:00 a 13:00.';
                com.dispatchEvent(new Event('input'));
            }
        """)
        time.sleep(1)

        audio = generate_audio(
            "Complete los datos del envío. "
            "Añada una referencia comercial y comentarios para su propuesta.",
            "08_formulario"
        )
        img = capture_screenshot(driver, "08_formulario")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 10: FIRMA DIGITAL
        # ============================================================
        print(f"\n[10/{TOTAL_SCENES}] FIRMA DIGITAL...")

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
        # ESCENA 11: ENVIAR PROPUESTA
        # ============================================================
        print(f"\n[11/{TOTAL_SCENES}] ENVIANDO PROPUESTA...")

        driver.execute_script("""
            const content = document.getElementById('carrito-content');
            if (content) content.scrollTop = 0;
        """)
        time.sleep(0.5)

        driver.execute_script("enviarSolicitud()")
        time.sleep(8)

        audio = generate_audio(
            "La solicitud ha sido enviada. "
            "El sistema genera un PDF profesional con las imágenes de los productos "
            "y la firma digital, y lo envía automáticamente por correo electrónico. "
            "La propuesta queda registrada en el historial para su seguimiento.",
            "10_enviado"
        )
        img = capture_screenshot(driver, "10_enviado")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 12: BUSQUEDA MAGICA
        # ============================================================
        print(f"\n[12/{TOTAL_SCENES}] BUSQUEDA MAGICA...")

        driver.get(f"{BASE_URL}/busqueda-magica.html")
        time.sleep(4)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "drop-zone"))
            )
        except Exception:
            pass
        time.sleep(2)

        audio = generate_audio(
            "Búsqueda mágica por imagen. "
            "Arrastre una fotografía de cualquier producto cerámico "
            "y el sistema encontrará las referencias más similares de su catálogo "
            "utilizando inteligencia artificial y reconocimiento visual. "
            "Cada resultado muestra un porcentaje de similitud.",
            "11_busqueda_magica"
        )
        img = capture_screenshot(driver, "11_busqueda_magica")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 13: GESTION DE USUARIOS (con blur)
        # ============================================================
        print(f"\n[13/{TOTAL_SCENES}] GESTION DE USUARIOS...")

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
        time.sleep(0.5)

        audio = generate_audio(
            "Panel de administración de usuarios. "
            "Gestione las cuentas de acceso, active o desactive usuarios, "
            "asigne roles y permisos, y controle quién accede al sistema. "
            "Filtros avanzados por columna para encontrar cualquier usuario rápidamente.",
            "12_usuarios"
        )
        img = capture_screenshot(driver, "12_usuarios")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 14: PEDIDOS DE VENTA - LISTA (con blur)
        # ============================================================
        print(f"\n[14/{TOTAL_SCENES}] PEDIDOS DE VENTA...")

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
        time.sleep(0.5)

        audio = generate_audio(
            "Consulte todos los pedidos de venta sincronizados con su ERP. "
            "Filtre por año, país, provincia o cliente para localizar cualquier pedido. "
            "Información en tiempo real del estado de cada operación.",
            "13_pedidos"
        )
        img = capture_screenshot(driver, "13_pedidos")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 15: DETALLE DE PEDIDO CON IMAGENES (con blur)
        # ============================================================
        print(f"\n[15/{TOTAL_SCENES}] DETALLE DE PEDIDO...")

        driver.execute_script("""
            const btn = document.querySelector('#orders-grid .btn-icon-primary');
            if (btn) btn.click();
        """)
        time.sleep(2)

        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script(
                    "const m = document.getElementById('order-detail-modal'); "
                    "return m && getComputedStyle(m).display === 'flex';"
                )
            )
        except Exception:
            pass
        time.sleep(4)

        # Difuminar datos del cliente y precios en el detalle
        inject_blur(driver, BLUR_CSS_PEDIDO_DETALLE)
        time.sleep(0.5)

        has_thumbs = driver.execute_script(
            "return document.querySelectorAll('.order-line-thumb').length > 0"
        )
        print(f"    Thumbnails en lineas: {has_thumbs}")

        audio = generate_audio(
            "El detalle del pedido muestra todas las líneas con las imágenes reales "
            "de cada producto, cantidades y referencias. "
            "Información completa para verificar cualquier operación comercial.",
            "14_detalle_pedido"
        )
        img = capture_screenshot(driver, "14_detalle_pedido")
        clips.append(create_video_clip(img, audio))

        # ============================================================
        # ESCENA 16: UBICACION DEL CLIENTE (MAPA)
        # ============================================================
        print(f"\n[16/{TOTAL_SCENES}] UBICACION DEL CLIENTE (MAPA)...")

        # Cerrar modal de detalle
        driver.execute_script("""
            const modal = document.getElementById('order-detail-modal');
            if (modal) modal.style.display = 'none';
        """)
        time.sleep(1)

        # Click en boton de ubicacion
        driver.execute_script("""
            const btns = document.querySelectorAll('#orders-grid button[title]');
            let mapBtn = null;
            for (const btn of btns) {
                const title = btn.getAttribute('title') || '';
                if (title.toLowerCase().includes('ubicaci') || title.toLowerCase().includes('location')) {
                    mapBtn = btn;
                    break;
                }
            }
            if (mapBtn) mapBtn.click();
        """)
        time.sleep(3)

        # Esperar mapa + marcador
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".leaflet-container"))
            )
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".leaflet-marker-icon"))
            )
        except Exception:
            print("    [!] Mapa o marcador no encontrado, esperando...")
            time.sleep(5)
        time.sleep(3)

        # Difuminar datos del cliente en el mapa (titulo, direccion, popup)
        driver.execute_script("""
            // Titulo del modal (nombre del cliente)
            document.querySelectorAll('[id^="map-modal-"] h2').forEach(h2 => {
                h2.style.filter = 'blur(5px)';
            });
            // Direccion debajo del titulo
            document.querySelectorAll('[id$="-address"]').forEach(el => {
                if (el.id.startsWith('map-modal-')) {
                    el.style.filter = 'blur(5px)';
                }
            });
            // Popup del marcador en el mapa (nombre + direccion)
            document.querySelectorAll('.leaflet-popup-content').forEach(el => {
                el.style.filter = 'blur(5px)';
            });
        """)
        time.sleep(0.3)

        audio = generate_audio(
            "Visualice la ubicación de sus clientes en el mapa. "
            "El sistema geocodifica la dirección del cliente "
            "y muestra su ubicación exacta sobre el mapa interactivo. "
            "Una forma rápida de localizar dónde se encuentra cada cliente.",
            "15_mapa_cliente"
        )
        img = capture_screenshot(driver, "15_mapa_cliente")
        clips.append(create_video_clip(img, audio))

        # Cerrar navegador
        driver.quit()
        driver = None

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
