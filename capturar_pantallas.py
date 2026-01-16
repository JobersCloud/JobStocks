#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para capturar pantallas del sistema de gestion de stocks
Version automatica con delays - MEJORADA
"""

import pyautogui
import webbrowser
import time
import os
import subprocess

# Configuracion
BASE_URL = "http://192.168.63.51:5000"
EMPRESA_ID = "1"
USERNAME = "admin"
PASSWORD = "Desa2012"

# Carpeta para guardar capturas
SCREENSHOTS_DIR = "screenshots"

# Tiempo de espera entre acciones (segundos)
WAIT_PAGE_LOAD = 5
WAIT_SHORT = 2

def crear_carpeta():
    """Crea la carpeta de capturas si no existe"""
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)
    print(f"Carpeta: {os.path.abspath(SCREENSHOTS_DIR)}")

def capturar_pantalla(nombre):
    """Captura la pantalla actual"""
    filepath = os.path.join(SCREENSHOTS_DIR, f"{nombre}.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)
    print(f"  [OK] {nombre}.png")
    return filepath

def abrir_chrome(url):
    """Abre Chrome con una URL especifica"""
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    subprocess.Popen([chrome_path, "--new-window", f"--window-size=1920,1080", url])

def main():
    crear_carpeta()

    print("\n" + "=" * 50)
    print("CAPTURA AUTOMATICA DE PANTALLAS")
    print("=" * 50)
    print(f"URL: {BASE_URL}")
    print(f"Usuario: {USERNAME}")
    print("-" * 50)

    capturas = []

    # 1. Login
    print("\n[1/12] Pagina de login...")
    abrir_chrome(f"{BASE_URL}/login?empresa={EMPRESA_ID}")
    time.sleep(WAIT_PAGE_LOAD)
    capturas.append(capturar_pantalla("01_login"))

    # 2. Hacer login automatico
    print("\n[2/12] Haciendo login...")
    time.sleep(1)
    # Escribir usuario
    pyautogui.click(960, 400)  # Click aproximado en campo usuario
    time.sleep(0.5)
    pyautogui.typewrite(USERNAME, interval=0.05)
    pyautogui.press('tab')
    time.sleep(0.3)
    pyautogui.typewrite(PASSWORD, interval=0.05)
    pyautogui.press('enter')
    time.sleep(WAIT_PAGE_LOAD + 2)

    # 3. Listado de stocks
    print("\n[3/12] Listado de stocks...")
    capturas.append(capturar_pantalla("02_listado_stocks"))

    # 4. Click en un producto para ver detalle
    print("\n[4/12] Detalle de producto...")
    # Click en la primera fila de la tabla
    pyautogui.click(960, 450)  # Aproximadamente en la primera fila
    time.sleep(WAIT_SHORT)
    capturas.append(capturar_pantalla("03_detalle_producto"))
    # Cerrar modal con Escape
    pyautogui.press('escape')
    time.sleep(1)

    # 5. Agregar al carrito y ver carrito
    print("\n[5/12] Carrito de productos...")
    # Click en boton agregar de la primera fila
    pyautogui.click(1700, 450)  # Boton agregar aproximado
    time.sleep(1)
    # Aceptar cantidad
    pyautogui.press('enter')
    time.sleep(1)
    # Click en boton carrito flotante
    pyautogui.click(1850, 950)  # Boton carrito flotante
    time.sleep(WAIT_SHORT)
    capturas.append(capturar_pantalla("04_carrito"))
    # Cerrar modal carrito
    pyautogui.press('escape')
    time.sleep(1)

    # 6. Dashboard
    print("\n[6/12] Dashboard...")
    webbrowser.open(f"{BASE_URL}/dashboard.html?empresa={EMPRESA_ID}")
    time.sleep(WAIT_PAGE_LOAD)
    capturas.append(capturar_pantalla("05_dashboard"))

    # 7. Usuarios
    print("\n[7/12] Gestion de usuarios...")
    webbrowser.open(f"{BASE_URL}/usuarios.html?empresa={EMPRESA_ID}")
    time.sleep(WAIT_PAGE_LOAD)
    capturas.append(capturar_pantalla("06_usuarios"))

    # 8. Email config
    print("\n[8/12] Configuracion email...")
    webbrowser.open(f"{BASE_URL}/email-config.html?empresa={EMPRESA_ID}")
    time.sleep(WAIT_PAGE_LOAD)
    capturas.append(capturar_pantalla("07_email_config"))

    # 9. Parametros
    print("\n[9/12] Parametros...")
    webbrowser.open(f"{BASE_URL}/parametros.html?empresa={EMPRESA_ID}")
    time.sleep(WAIT_PAGE_LOAD)
    capturas.append(capturar_pantalla("08_parametros"))

    # 10. Propuestas
    print("\n[10/12] Propuestas...")
    webbrowser.open(f"{BASE_URL}/todas-propuestas.html?empresa={EMPRESA_ID}")
    time.sleep(WAIT_PAGE_LOAD)
    capturas.append(capturar_pantalla("09_propuestas"))

    # 11. Consultas
    print("\n[11/12] Consultas...")
    webbrowser.open(f"{BASE_URL}/todas-consultas.html?empresa={EMPRESA_ID}")
    time.sleep(WAIT_PAGE_LOAD)
    capturas.append(capturar_pantalla("10_consultas"))

    # 12. Temas de color
    print("\n[12/12] Temas de color...")
    webbrowser.open(f"{BASE_URL}/empresa-logo.html?empresa={EMPRESA_ID}")
    time.sleep(WAIT_PAGE_LOAD)
    capturas.append(capturar_pantalla("11_temas_color"))

    # Resumen
    print("\n" + "=" * 50)
    print("CAPTURAS COMPLETADAS")
    print("=" * 50)
    print(f"Total: {len(capturas)} capturas")
    print(f"Ubicacion: {os.path.abspath(SCREENSHOTS_DIR)}")

if __name__ == "__main__":
    main()
