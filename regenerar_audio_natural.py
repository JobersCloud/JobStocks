#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Regenera los audios del video promocional con voz natural española
Usa Edge TTS (Microsoft) con voces neuronales de España

Autor: Jobers
"""

import os
import asyncio
import edge_tts

# Configuracion
AUDIO_DIR = "audio_promo"

# Voz española de España - opciones:
# es-ES-AlvaroNeural (masculina, profesional)
# es-ES-ElviraNeural (femenina, profesional)
VOZ = "es-ES-AlvaroNeural"

# Velocidad de habla: -50% a +50% (ej: "+10%" mas rapido, "-10%" mas lento)
VELOCIDAD = "+0%"

# Textos de narracion (con tildes y puntuacion correcta para mejor entonacion)
NARRACIONES = {
    "00_intro": (
        "Sistema de Gestión de Stocks. "
        "Plataforma web profesional para empresas cerámicas."
    ),
    "listado": (
        "Consulte su catálogo completo en tiempo real. "
        "Filtros avanzados por formato, calidad, tono y calibre. "
        "Búsqueda instantánea mientras escribe."
    ),
    "dashboard": (
        "Panel de control con métricas clave de su negocio. "
        "Gráficos de tendencias, productos populares y usuarios activos."
    ),
    "usuarios": (
        "Control total de accesos con tres niveles de permisos. "
        "Usuarios, administradores y superusuarios."
    ),
    "propuestas": (
        "Sus clientes seleccionan productos y envían propuestas. "
        "PDF automático enviado por correo electrónico."
    ),
    "personalizacion": (
        "Adapte el sistema a su marca. "
        "Seis temas de color, logo personalizado y modo oscuro."
    ),
    "99_outro": (
        "Solicite una demostración personalizada. "
        "Incluye código fuente, documentación completa y soporte técnico."
    ),
}


async def generar_audio(nombre, texto):
    """Genera audio con Edge TTS"""
    filepath = os.path.join(AUDIO_DIR, f"{nombre}.mp3")

    # Crear comunicador con la voz seleccionada
    communicate = edge_tts.Communicate(
        text=texto,
        voice=VOZ,
        rate=VELOCIDAD
    )

    # Guardar audio
    await communicate.save(filepath)

    # Obtener tamano
    size_kb = os.path.getsize(filepath) / 1024
    print(f"  [OK] {nombre}.mp3 ({size_kb:.1f} KB)")


async def main():
    print("=" * 60)
    print("REGENERANDO AUDIOS CON VOZ NATURAL ESPANOLA")
    print("=" * 60)
    print(f"Voz: {VOZ}")
    print(f"Velocidad: {VELOCIDAD}")
    print(f"Directorio: {AUDIO_DIR}")
    print("-" * 60)

    # Crear directorio si no existe
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    # Generar todos los audios
    for nombre, texto in NARRACIONES.items():
        print(f"\nGenerando: {nombre}")
        print(f"  Texto: {texto[:50]}...")
        await generar_audio(nombre, texto)

    print("\n" + "=" * 60)
    print("[OK] Audios regenerados con exito")
    print("=" * 60)
    print("\nAhora ejecuta: python regenerar_video.py")
    print("para crear el video con los nuevos audios.")


if __name__ == "__main__":
    asyncio.run(main())
