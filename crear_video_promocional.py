#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Video promocional del Sistema de Gestion de Stocks
Usa Selenium para capturar pantallas con animaciones + Edge TTS (voz natural)

Autor: Jobers
"""

import os
import time
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image

# Configuracion de voz
VOZ_ESPANOLA = "es-ES-AlvaroNeural"
VELOCIDAD_VOZ = "+0%"

# Configuracion
BASE_URL = "http://localhost:5000"
EMPRESA_ID = "1"
USERNAME = "admin"
PASSWORD = "Desa2012"

OUTPUT_VIDEO = "video_promocional_stocks.mp4"
SCREENSHOTS_DIR = "screenshots_promo"
AUDIO_DIR = "audio_promo"
FPS = 24

# Frames por segundo para animaciones de scroll
SCROLL_FPS = 10


def setup_directories():
    """Crea directorios necesarios"""
    for dir_path in [SCREENSHOTS_DIR, AUDIO_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    print(f"Capturas: {SCREENSHOTS_DIR}")
    print(f"Audio: {AUDIO_DIR}")


def setup_browser():
    """Configura Chrome con Selenium"""
    print("Iniciando navegador...")
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    return driver


def login(driver):
    """Hace login en el sistema"""
    print("Haciendo login...")
    driver.get(f"{BASE_URL}/login?empresa={EMPRESA_ID}")
    time.sleep(2)

    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field.send_keys(USERNAME)

        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(PASSWORD)

        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_btn.click()

        time.sleep(3)
        print("Login exitoso")
        return True
    except Exception as e:
        print(f"Error en login: {e}")
        return False


def fix_image_dimensions(filepath):
    """Corrige dimensiones para que sean divisibles por 2"""
    img = Image.open(filepath)
    w, h = img.size
    new_w = w if w % 2 == 0 else w - 1
    new_h = h if h % 2 == 0 else h - 1
    if new_w != w or new_h != h:
        img = img.crop((0, 0, new_w, new_h))
        img.save(filepath)
    return filepath


def capture_screenshot(driver, name, silent=False):
    """Captura screenshot del navegador"""
    filepath = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    driver.save_screenshot(filepath)
    fix_image_dimensions(filepath)
    if not silent:
        img = Image.open(filepath)
        print(f"    Captura: {name}.png ({img.size[0]}x{img.size[1]})")
    return filepath


def capture_scroll_animation(driver, name, scroll_amount=500, duration=2.0):
    """Captura múltiples frames mientras hace scroll suave"""
    frames = []
    num_frames = int(duration * SCROLL_FPS)
    scroll_per_frame = scroll_amount / num_frames

    print(f"    Capturando {num_frames} frames con scroll...")

    for i in range(num_frames):
        frame_path = os.path.join(SCREENSHOTS_DIR, f"{name}_frame_{i:03d}.png")
        driver.save_screenshot(frame_path)
        fix_image_dimensions(frame_path)
        frames.append(frame_path)

        # Scroll suave
        driver.execute_script(f"window.scrollBy(0, {scroll_per_frame});")
        time.sleep(1.0 / SCROLL_FPS)

    return frames


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


def create_video_clip(image_path, audio_path, extra_time=2):
    """Crea clip con imagen estatica y audio"""
    audio_dur = get_audio_duration(audio_path)
    duration = audio_dur + extra_time

    img_clip = ImageClip(image_path).with_duration(duration)
    audio = AudioFileClip(audio_path)

    return img_clip.with_audio(audio)


def create_animated_clip(frame_paths, audio_path, extra_time=1):
    """Crea clip animado con múltiples frames y audio"""
    audio_dur = get_audio_duration(audio_path)
    total_duration = audio_dur + extra_time

    # Duración de cada frame
    frame_duration = total_duration / len(frame_paths)

    clips = []
    for frame_path in frame_paths:
        clip = ImageClip(frame_path).with_duration(frame_duration)
        clips.append(clip)

    # Concatenar frames
    video = concatenate_videoclips(clips, method="compose")

    # Añadir audio
    audio = AudioFileClip(audio_path)
    return video.with_audio(audio)


def main():
    print("\n" + "=" * 60)
    print("VIDEO PROMOCIONAL - GESTION DE STOCKS")
    print("=" * 60)
    print(f"Servidor: {BASE_URL}")
    print(f"Salida: {OUTPUT_VIDEO}")
    print("-" * 60)

    setup_directories()

    driver = None
    try:
        driver = setup_browser()

        if not login(driver):
            print("[ERROR] No se pudo hacer login")
            return

        time.sleep(2)

        clips = []

        # ============================================================
        # INTRO - Vista inicial del catálogo
        # ============================================================
        print("\n[INTRO] Creando introduccion...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
            )
            time.sleep(2)
        except:
            time.sleep(3)

        intro_audio = generate_audio(
            "Sistema de Gestión de Stocks. "
            "Plataforma web profesional para empresas cerámicas.",
            "00_intro"
        )
        intro_img = capture_screenshot(driver, "00_intro")
        clips.append(create_video_clip(intro_img, intro_audio, extra_time=1))

        # ============================================================
        # ESCENA 1: CATÁLOGO con scroll
        # ============================================================
        print("\n[1/6] CATALOGO DE PRODUCTOS con scroll...")

        # Primero captura estática
        listado_audio = generate_audio(
            "Consulte su catálogo completo en tiempo real. "
            "Filtros avanzados por formato, calidad, tono y calibre. "
            "Búsqueda instantánea mientras escribe.",
            "listado"
        )

        # Scroll hacia abajo para mostrar más productos
        frames = capture_scroll_animation(driver, "listado", scroll_amount=400, duration=2.5)
        clips.append(create_animated_clip(frames, listado_audio, extra_time=1))

        # ============================================================
        # ESCENA 2: MODAL AÑADIR AL CARRITO
        # ============================================================
        print("\n[2/6] MODAL AÑADIR AL CARRITO...")

        # Volver arriba
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        # Buscar botón de añadir al carrito en la primera fila
        try:
            add_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "table tbody tr:first-child .btn-add-cart, table tbody tr:first-child button[onclick*='agregar']"))
            )
            add_btn.click()
            time.sleep(1.5)

            carrito_audio = generate_audio(
                "Añada productos al carrito con un solo clic. "
                "Seleccione la cantidad deseada y confirme su pedido.",
                "carrito_modal"
            )
            carrito_img = capture_screenshot(driver, "carrito_modal")
            clips.append(create_video_clip(carrito_img, carrito_audio, extra_time=1))

            # Cerrar modal
            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, ".modal-close, .quantity-btn-cancel, [onclick*='cerrar']")
                close_btn.click()
            except:
                driver.execute_script("document.querySelector('.modal, .quantity-modal').style.display='none';")
            time.sleep(1)

        except Exception as e:
            print(f"    [!] No se pudo abrir modal del carrito: {e}")
            # Crear clip de fallback
            carrito_audio = generate_audio(
                "Añada productos al carrito con un solo clic. "
                "Seleccione la cantidad deseada y confirme su pedido.",
                "carrito_modal"
            )
            carrito_img = capture_screenshot(driver, "carrito_modal")
            clips.append(create_video_clip(carrito_img, carrito_audio, extra_time=1))

        # ============================================================
        # ESCENA 3: DASHBOARD con scroll
        # ============================================================
        print("\n[3/6] DASHBOARD con scroll...")

        driver.get(f"{BASE_URL}/dashboard.html?empresa={EMPRESA_ID}")
        time.sleep(2)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
            )
            time.sleep(3)
        except:
            time.sleep(5)

        dashboard_audio = generate_audio(
            "Panel de control con métricas clave de su negocio. "
            "Gráficos de tendencias, productos populares y usuarios más activos.",
            "dashboard"
        )

        # Capturar con scroll para mostrar todo el dashboard
        frames = capture_scroll_animation(driver, "dashboard", scroll_amount=600, duration=3.0)
        clips.append(create_animated_clip(frames, dashboard_audio, extra_time=1))

        # ============================================================
        # ESCENA 4: GESTIÓN DE USUARIOS
        # ============================================================
        print("\n[4/6] GESTION DE USUARIOS...")

        driver.get(f"{BASE_URL}/usuarios.html?empresa={EMPRESA_ID}")
        time.sleep(2)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".users-table tbody tr, .user-card"))
            )
            time.sleep(2)
        except:
            time.sleep(3)

        usuarios_audio = generate_audio(
            "Control total de accesos con tres niveles de permisos. "
            "Usuarios, administradores y superusuarios.",
            "usuarios"
        )

        # Scroll suave
        frames = capture_scroll_animation(driver, "usuarios", scroll_amount=300, duration=2.0)
        clips.append(create_animated_clip(frames, usuarios_audio, extra_time=1))

        # ============================================================
        # ESCENA 5: PROPUESTAS
        # ============================================================
        print("\n[5/6] PROPUESTAS...")

        driver.get(f"{BASE_URL}/todas-propuestas.html?empresa={EMPRESA_ID}")
        time.sleep(2)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".proposals-table tbody tr, .proposal-card"))
            )
            time.sleep(2)
        except:
            time.sleep(3)

        propuestas_audio = generate_audio(
            "Sus clientes seleccionan productos y envían propuestas. "
            "PDF automático enviado por correo electrónico.",
            "propuestas"
        )
        propuestas_img = capture_screenshot(driver, "propuestas")
        clips.append(create_video_clip(propuestas_img, propuestas_audio, extra_time=2))

        # ============================================================
        # ESCENA 6: PERSONALIZACIÓN con scroll
        # ============================================================
        print("\n[6/6] PERSONALIZACION...")

        driver.get(f"{BASE_URL}/empresa-logo.html?empresa={EMPRESA_ID}")
        time.sleep(2)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".theme-option, .logo-preview, .theme-grid"))
            )
            time.sleep(2)
        except:
            time.sleep(3)

        personalizacion_audio = generate_audio(
            "Adapte el sistema a su marca. "
            "Seis temas de color, logo personalizado y modo oscuro.",
            "personalizacion"
        )

        # Scroll para mostrar todos los temas
        frames = capture_scroll_animation(driver, "personalizacion", scroll_amount=400, duration=2.5)
        clips.append(create_animated_clip(frames, personalizacion_audio, extra_time=1))

        # ============================================================
        # OUTRO
        # ============================================================
        print("\n[OUTRO] Creando cierre...")

        # Volver a la página principal para el cierre
        driver.get(f"{BASE_URL}/?empresa={EMPRESA_ID}")
        time.sleep(2)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
            )
            time.sleep(1)
        except:
            pass

        outro_audio = generate_audio(
            "Solicite una demostración personalizada. "
            "Documentación completa, formación y soporte técnico incluidos.",
            "99_outro"
        )
        outro_img = capture_screenshot(driver, "99_outro")
        clips.append(create_video_clip(outro_img, outro_audio, extra_time=2))

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
        print(f"     Tamaño: {size:.1f} MB")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
