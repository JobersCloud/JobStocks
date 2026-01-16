#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Regenera el video desde screenshots y audio existentes
"""

import os
from PIL import Image
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

SCREENSHOTS_DIR = "screenshots_promo"
AUDIO_DIR = "audio_promo"
OUTPUT_VIDEO = "video_promocional_stocks.mp4"
FPS = 24

# Orden de las escenas
SCENES = [
    "00_intro",
    "listado",
    "dashboard",
    "usuarios",
    "propuestas",
    "personalizacion",
    "99_outro"
]

def fix_image_dimensions(image_path):
    """Asegura que las dimensiones sean divisibles por 2 (requisito de libx264)"""
    img = Image.open(image_path)
    w, h = img.size

    # Redondear a número par
    new_w = w if w % 2 == 0 else w - 1
    new_h = h if h % 2 == 0 else h - 1

    if new_w != w or new_h != h:
        img = img.crop((0, 0, new_w, new_h))
        img.save(image_path)
        print(f"    Ajustado: {w}x{h} -> {new_w}x{new_h}")

    return image_path

def get_audio_duration(path):
    """Obtiene duracion del audio"""
    audio = AudioFileClip(path)
    dur = audio.duration
    audio.close()
    return dur

def create_video_clip(image_path, audio_path, extra_time=2):
    """Crea clip con imagen y audio"""
    # Corregir dimensiones primero
    fix_image_dimensions(image_path)

    audio_dur = get_audio_duration(audio_path)
    duration = audio_dur + extra_time

    img_clip = ImageClip(image_path).with_duration(duration)
    audio = AudioFileClip(audio_path)

    return img_clip.with_audio(audio)

def main():
    print("=" * 60)
    print("REGENERANDO VIDEO PROMOCIONAL")
    print("=" * 60)

    clips = []

    for name in SCENES:
        img_path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
        audio_path = os.path.join(AUDIO_DIR, f"{name}.mp3")

        if not os.path.exists(img_path):
            print(f"[!] No existe: {img_path}")
            continue
        if not os.path.exists(audio_path):
            print(f"[!] No existe: {audio_path}")
            continue

        print(f"  Procesando: {name}")
        clip = create_video_clip(img_path, audio_path, extra_time=2)
        clips.append(clip)

    if not clips:
        print("[ERROR] No hay clips para combinar")
        return

    print(f"\nCombinando {len(clips)} clips...")
    final = concatenate_videoclips(clips, method="compose")

    print("Generando video...")
    final.write_videofile(
        OUTPUT_VIDEO,
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        ffmpeg_params=['-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    )

    for c in clips:
        c.close()
    final.close()

    size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print("=" * 60)
    print(f"[OK] Video: {OUTPUT_VIDEO} ({size:.1f} MB)")
    print("=" * 60)

if __name__ == "__main__":
    main()
