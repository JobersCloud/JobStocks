#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Añade música de fondo al video promocional
Mezcla la narración existente con música corporativa

Autor: Jobers
"""

import os
import urllib.request
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

# Configuración
VIDEO_INPUT = "video_promocional_stocks.mp4"
VIDEO_OUTPUT = "video_promocional_stocks_con_musica.mp4"
MUSIC_FILE = "musica_fondo.mp3"

# Volumen de la música de fondo (0.0 a 1.0)
# 0.15 = 15% del volumen original para no tapar la narración
VOLUMEN_MUSICA = 0.12

# URL de música corporativa libre de derechos
# Música "Corporate Ambient" - Free Music Archive (CC0)
MUSIC_URL = "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Shipping_Lanes.mp3"


def descargar_musica():
    """Descarga la música de fondo si no existe"""
    if os.path.exists(MUSIC_FILE):
        print(f"[OK] Música encontrada: {MUSIC_FILE}")
        return True

    print(f"Descargando música de fondo...")
    try:
        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(MUSIC_URL, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as response:
            with open(MUSIC_FILE, 'wb') as f:
                f.write(response.read())

        size_mb = os.path.getsize(MUSIC_FILE) / (1024 * 1024)
        print(f"[OK] Música descargada: {MUSIC_FILE} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo descargar la música: {e}")
        print("Por favor, descarga manualmente una música y guárdala como 'musica_fondo.mp3'")
        return False


def añadir_musica():
    """Añade música de fondo al video"""
    print("\n" + "=" * 60)
    print("AÑADIENDO MÚSICA DE FONDO AL VIDEO")
    print("=" * 60)

    # Verificar que existe el video
    if not os.path.exists(VIDEO_INPUT):
        print(f"[ERROR] No se encontró el video: {VIDEO_INPUT}")
        print("Primero ejecuta: python crear_video_promocional.py")
        return

    # Descargar música si no existe
    if not descargar_musica():
        return

    print(f"\nProcesando video: {VIDEO_INPUT}")
    print(f"Volumen música: {int(VOLUMEN_MUSICA * 100)}%")

    # Cargar video con su audio original (narración)
    video = VideoFileClip(VIDEO_INPUT)
    duracion_video = video.duration
    print(f"Duración del video: {duracion_video:.1f} segundos")

    # Cargar música de fondo
    musica = AudioFileClip(MUSIC_FILE)
    duracion_musica = musica.duration
    print(f"Duración de la música: {duracion_musica:.1f} segundos")

    # Si la música es más corta que el video, hacer loop
    if duracion_musica < duracion_video:
        print("La música es más corta que el video, aplicando loop...")
        # Crear loop de la música
        repeticiones = int(duracion_video / duracion_musica) + 1
        from moviepy import concatenate_audioclips
        musica_loop = concatenate_audioclips([musica] * repeticiones)
        musica = musica_loop.with_duration(duracion_video)
    else:
        # Recortar música a la duración del video
        musica = musica.with_duration(duracion_video)

    # Ajustar volumen de la música
    musica = musica.with_volume_scaled(VOLUMEN_MUSICA)

    # Obtener audio original del video (narración)
    audio_original = video.audio

    # Combinar narración + música de fondo
    print("Mezclando narración con música de fondo...")
    audio_combinado = CompositeAudioClip([audio_original, musica])

    # Crear video final con audio combinado
    video_final = video.with_audio(audio_combinado)

    # Exportar video
    print(f"\nGenerando video final: {VIDEO_OUTPUT}")
    video_final.write_videofile(
        VIDEO_OUTPUT,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        threads=4,
        preset='medium',
        ffmpeg_params=['-pix_fmt', 'yuv420p']
    )

    # Limpiar
    video.close()
    musica.close()
    video_final.close()

    size_mb = os.path.getsize(VIDEO_OUTPUT) / (1024 * 1024)

    print("\n" + "=" * 60)
    print(f"[OK] Video generado: {VIDEO_OUTPUT}")
    print(f"     Tamaño: {size_mb:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    añadir_musica()
