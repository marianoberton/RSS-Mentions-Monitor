#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.matcher import find_keyword, normalize_text
import re

def test_keyword_matching():
    """Probar cómo funciona la detección de keywords."""
    
    # Texto de ejemplo que contiene menciones
    test_texts = [
        "El presidente Javier Milei anunció nuevas medidas económicas",
        "Milei presentó su propuesta en el Congreso",
        "Oscar Liberman criticó las políticas del gobierno",
        "El diputado Liberman votó en contra",
        "Andres de Leo participó en el debate",
        "de Leo expresó su posición sobre el tema"
    ]
    
    # Keywords que tenemos en la base de datos
    keywords_with_hits = ['Javier Milei', 'Oscar Liberman', 'Andres de Leo']
    keywords_without_hits = ['Milei', 'Liberman', 'de Leo']
    
    print("=== PRUEBA DE DETECCIÓN DE KEYWORDS ===")
    
    print("\n1. KEYWORDS QUE SÍ TIENEN MENCIONES:")
    for keyword in keywords_with_hits:
        print(f"\nKeyword: '{keyword}'")
        for text in test_texts:
            result = find_keyword(text, [keyword])
            status = "✅ ENCONTRADA" if result else "❌ NO ENCONTRADA"
            print(f"  Texto: '{text[:50]}...' → {status}")
    
    print("\n2. KEYWORDS QUE NO TIENEN MENCIONES:")
    for keyword in keywords_without_hits:
        print(f"\nKeyword: '{keyword}'")
        for text in test_texts:
            result = find_keyword(text, [keyword])
            status = "✅ ENCONTRADA" if result else "❌ NO ENCONTRADA"
            print(f"  Texto: '{text[:50]}...' → {status}")
    
    print("\n3. ANÁLISIS DEL PROBLEMA:")
    print("La función find_keyword usa word boundaries (\\b) que requieren coincidencias exactas.")
    print("Esto significa que:")
    print("  - 'Javier Milei' SÍ coincide con 'Javier Milei' (coincidencia exacta)")
    print("  - 'Milei' NO coincide con 'Javier Milei' (no es una palabra independiente)")
    print("  - 'Milei' SÍ coincidiría con 'Milei presentó...' (palabra independiente)")
    
    # Demostrar el problema con regex
    print("\n4. DEMOSTRACIÓN CON REGEX:")
    text = "El presidente Javier Milei anunció nuevas medidas"
    
    # Buscar 'Javier Milei' (funciona)
    pattern1 = r'\b' + re.escape(normalize_text('Javier Milei')) + r'\b'
    match1 = re.search(pattern1, normalize_text(text))
    print(f"Buscando 'Javier Milei' en '{text}': {'✅ ENCONTRADA' if match1 else '❌ NO ENCONTRADA'}")
    
    # Buscar 'Milei' (no funciona porque está dentro de 'Javier Milei')
    pattern2 = r'\b' + re.escape(normalize_text('Milei')) + r'\b'
    match2 = re.search(pattern2, normalize_text(text))
    print(f"Buscando 'Milei' en '{text}': {'✅ ENCONTRADA' if match2 else '❌ NO ENCONTRADA'}")
    
    # Probar con texto donde 'Milei' aparece solo
    text2 = "Milei presentó su propuesta en el Congreso"
    match3 = re.search(pattern2, normalize_text(text2))
    print(f"Buscando 'Milei' en '{text2}': {'✅ ENCONTRADA' if match3 else '❌ NO ENCONTRADA'}")

if __name__ == "__main__":
    test_keyword_matching()