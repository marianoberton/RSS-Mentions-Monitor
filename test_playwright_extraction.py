#!/usr/bin/env python
"""
Script para probar la extracción de contenido con Playwright.

Este script permite probar la extracción de contenido de una URL específica
utilizando tanto el método tradicional como el método con Playwright.

Ejecución: python test_playwright_extraction.py <url>
"""

import sys
import logging
import asyncio
from app.improved_extractor import extract_article_content_improved, extract_with_playwright, playwright_available

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    if len(sys.argv) < 2:
        print("Uso: python test_playwright_extraction.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"\nProbando extracción de contenido para: {url}\n")
    
    # Probar método tradicional
    print("1. Extracción con método tradicional (BeautifulSoup):")
    traditional_content = extract_article_content_improved(url)
    print(f"Longitud del contenido: {len(traditional_content)} caracteres")
    if traditional_content:
        print(f"Primeros 200 caracteres: {traditional_content[:200]}...")
    else:
        print("No se pudo extraer contenido con el método tradicional.")
    
    # Probar método con Playwright si está disponible
    if playwright_available:
        print("\n2. Extracción con Playwright:")
        playwright_content = await extract_with_playwright(url)
        print(f"Longitud del contenido: {len(playwright_content)} caracteres")
        if playwright_content:
            print(f"Primeros 200 caracteres: {playwright_content[:200]}...")
        else:
            print("No se pudo extraer contenido con Playwright.")
    else:
        print("\n2. Playwright no está disponible. Instálalo con: python install_playwright.py")

if __name__ == "__main__":
    asyncio.run(main())