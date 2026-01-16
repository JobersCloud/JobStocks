#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Video tutorial del Sistema de Gestion de Stocks
con narracion de voz usando Google TTS

Autor: Jobers
"""

import os
import time
import subprocess
import webbrowser

import pyautogui
import mss
import cv2
import numpy as np
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

# Configuracion
BASE_URL = "http://localhost:5000"
EMPRESA_ID = "1"
USERNAME = "admin"
PASSWORD = "Desa2012"

OUTPUT_VIDEO = "tutorial_gestion_stocks.mp4"
TEMP_DIR = "video_temp"
FPS = 10


def setup():
    """Prepara el entorno"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    else:
        for f in os.listdir(TEMP_DIR):
            try:
                os.remove(os.path.join(TEMP_DIR, f))
            except:
                pass
    print(f"Directorio temporal: {os.path.abspath(TEMP_DIR)}")


def generate_audio(text, output_path):
    """Genera audio MP3 con Google TTS"""
    try:
        tts = gTTS(text=text, lang='es', slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"    Error generando audio: {e}")
        return False


def get_audio_duration(path):
    """Obtiene duracion del audio"""
    try:
        audio = AudioFileClip(path)
        dur = audio.duration
        audio.close()
        return dur
    except:
        return 5.0


def record_screen(duration, output_path):
    """Graba la pantalla"""
    frames = []
    num_frames = int(duration * FPS)
    print(f"    Grabando {num_frames} frames ({duration:.1f}s)...")

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        for i in range(num_frames):
            img = np.array(sct.grab(monitor))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            frames.append(img)
            time.sleep(1.0 / FPS)

    if frames:
        h, w = frames[0].shape[:2]
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'XVID'), FPS, (w, h))
        for frame in frames:
            out.write(frame)
        out.release()
        print(f"    Video guardado: {os.path.basename(output_path)}")

    return len(frames)


def open_chrome(url):
    """Abre Chrome maximizado"""
    subprocess.Popen([
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--new-window", "--start-maximized", url
    ])


def combine_all(segments, output):
    """Combina todos los segmentos con audio"""
    print("\nCombinando segmentos...")
    clips = []

    for i, (video_path, audio_path) in enumerate(segments):
        if not os.path.exists(video_path):
            print(f"  [!] Video no encontrado: {video_path}")
            continue

        print(f"  Procesando segmento {i+1}...")
        clip = VideoFileClip(video_path)

        if audio_path and os.path.exists(audio_path):
            try:
                audio = AudioFileClip(audio_path)
                # Si el video es mas corto que el audio, extenderlo
                if clip.duration < audio.duration:
                    clip = clip.with_duration(audio.duration)
                clip = clip.with_audio(audio)
            except Exception as e:
                print(f"    Error con audio: {e}")

        clips.append(clip)

    if not clips:
        print("[ERROR] No hay clips para combinar")
        return False

    print(f"\nConcatenando {len(clips)} clips...")
    final = concatenate_videoclips(clips, method="compose")

    print("Generando video final (esto puede tardar)...")
    final.write_videofile(
        output,
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        threads=4,
        verbose=False,
        logger=None
    )

    for c in clips:
        c.close()
    final.close()

    return True


def main():
    print("\n" + "=" * 60)
    print("VIDEO TUTORIAL - GESTION DE STOCKS")
    print("=" * 60)
    print(f"Servidor: {BASE_URL}")
    print(f"Salida: {OUTPUT_VIDEO}")
    print("-" * 60)
    print("\nIMPORTANTE:")
    print("  - NO toques el raton ni el teclado durante la grabacion")
    print("  - El proceso tardara unos 2-3 minutos")
    print("\nIniciando en 3 segundos...")
    time.sleep(3)

    setup()
    segments = []

    # Definir escenas
    scenes = [
        {
            "name": "01_intro",
            "text": "Bienvenido al tutorial del Sistema de Gestion de Stocks. Esta aplicacion web permite gestionar inventarios de ceramica de forma profesional.",
            "before": lambda: (open_chrome(f"{BASE_URL}/login?empresa={EMPRESA_ID}"), time.sleep(4))[1],
            "extra_time": 2
        },
        {
            "name": "02_login",
            "text": "Introducimos el usuario y la contrasena proporcionados por el administrador para acceder al sistema.",
            "before": lambda: (
                pyautogui.click(960, 430),
                time.sleep(0.5),
                pyautogui.typewrite(USERNAME, interval=0.08),
                pyautogui.press('tab'),
                time.sleep(0.3),
                pyautogui.typewrite(PASSWORD, interval=0.08)
            ),
            "after": lambda: (pyautogui.press('enter'), time.sleep(5)),
            "extra_time": 2
        },
        {
            "name": "03_listado",
            "text": "Esta es la pantalla principal. Muestra todos los productos con su codigo, descripcion, formato, calidad, tono, calibre y existencias disponibles.",
            "extra_time": 3
        },
        {
            "name": "04_detalle",
            "text": "Al hacer clic en cualquier producto se abre el detalle con imagenes y especificaciones tecnicas completas.",
            "before": lambda: (pyautogui.click(600, 450), time.sleep(2)),
            "after": lambda: (pyautogui.press('escape'), time.sleep(1)),
            "extra_time": 3
        },
        {
            "name": "05_dashboard",
            "text": "El dashboard muestra estadisticas del sistema: propuestas enviadas, usuarios activos, graficos de tendencias y productos mas solicitados.",
            "before": lambda: (webbrowser.open(f"{BASE_URL}/dashboard.html?empresa={EMPRESA_ID}"), time.sleep(4)),
            "extra_time": 3
        },
        {
            "name": "06_usuarios",
            "text": "En gestion de usuarios controlamos el acceso al sistema con tres niveles de permisos: usuario, administrador y superusuario.",
            "before": lambda: (webbrowser.open(f"{BASE_URL}/usuarios.html?empresa={EMPRESA_ID}"), time.sleep(4)),
            "extra_time": 3
        },
        {
            "name": "07_temas",
            "text": "El sistema permite personalizar la apariencia eligiendo entre seis temas de color y subiendo el logo de la empresa.",
            "before": lambda: (webbrowser.open(f"{BASE_URL}/empresa-logo.html?empresa={EMPRESA_ID}"), time.sleep(4)),
            "extra_time": 3
        },
        {
            "name": "08_cierre",
            "text": "Esto concluye el tutorial. El sistema incluye carrito de propuestas, envio de emails, documentacion Swagger y soporte multi idioma. Gracias por su atencion.",
            "extra_time": 3
        }
    ]

    # Ejecutar escenas
    total = len(scenes)
    for i, scene in enumerate(scenes):
        name = scene["name"]
        text = scene["text"]
        extra = scene.get("extra_time", 2)

        print(f"\n[{i+1}/{total}] {name}")

        # Ejecutar accion previa
        if "before" in scene:
            scene["before"]()

        # Generar audio
        audio_path = os.path.join(TEMP_DIR, f"{name}.mp3")
        print(f"    Generando audio...")
        if generate_audio(text, audio_path):
            duration = get_audio_duration(audio_path) + extra
        else:
            duration = 8
            audio_path = None

        # Grabar video
        video_path = os.path.join(TEMP_DIR, f"{name}.avi")
        record_screen(duration, video_path)

        # Ejecutar accion posterior
        if "after" in scene:
            scene["after"]()

        segments.append((video_path, audio_path))

    # Combinar todo
    print("\n" + "-" * 60)
    if combine_all(segments, OUTPUT_VIDEO):
        size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
        print("\n" + "=" * 60)
        print(f"[OK] Video generado: {OUTPUT_VIDEO}")
        print(f"     Tamano: {size:.1f} MB")
        print("=" * 60)
    else:
        print("\n[ERROR] No se pudo generar el video")


if __name__ == "__main__":
    main()
