#!/usr/bin/env python
"""
Script para instalar Playwright y sus dependencias necesarias.

Este script instala el paquete de Playwright y los navegadores requeridos.
Ejecución: python install_playwright.py
"""

import subprocess
import sys
import os

def main():
    print("Instalando Playwright y sus dependencias...")
    
    # Instalar el paquete de Playwright
    print("\n1. Instalando el paquete de Playwright...")
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    
    # Instalar los navegadores necesarios (solo Chromium para ahorrar espacio)
    print("\n2. Instalando el navegador Chromium...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    
    print("\n✅ Instalación completada con éxito!")
    print("Ahora puedes usar Playwright para la extracción avanzada de contenido.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error durante la instalación: {e}")
        sys.exit(1)