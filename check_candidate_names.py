#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
import html
import json

def check_candidate_names():
    print("=== Verificación de Nombres de Candidatos ===")
    
    conn = get_db_connection()
    cursor = conn.execute("SELECT id, name FROM candidates WHERE is_active = 1 ORDER BY id")
    candidates = cursor.fetchall()
    conn.close()
    
    if not candidates:
        print("❌ No hay candidatos activos")
        return
    
    print(f"\n👥 Candidatos activos encontrados: {len(candidates)}")
    
    for candidate in candidates:
        candidate_id = candidate[0]
        candidate_name = candidate[1]
        
        print(f"\n🔍 Analizando: ID {candidate_id} - '{candidate_name}'")
        
        # Verificar caracteres problemáticos
        has_single_quote = "'" in candidate_name
        has_double_quote = '"' in candidate_name
        has_backslash = "\\" in candidate_name
        has_newline = "\n" in candidate_name
        has_special_chars = any(ord(c) > 127 for c in candidate_name)
        
        print(f"  📝 Nombre original: '{candidate_name}'")
        print(f"  📏 Longitud: {len(candidate_name)}")
        print(f"  🔤 Caracteres especiales:")
        print(f"    - Comilla simple ('): {'✅' if has_single_quote else '❌'}")
        print(f"    - Comilla doble (\"): {'✅' if has_double_quote else '❌'}")
        print(f"    - Barra invertida (\\): {'✅' if has_backslash else '❌'}")
        print(f"    - Salto de línea: {'✅' if has_newline else '❌'}")
        print(f"    - Caracteres Unicode: {'✅' if has_special_chars else '❌'}")
        
        # Mostrar escape de Jinja2
        jinja_escaped = candidate_name.replace("'", "\\'").replace('"', '\\"')
        print(f"  🔧 Escape Jinja2: '{jinja_escaped}'")
        
        # Mostrar escape HTML
        html_escaped = html.escape(candidate_name)
        print(f"  🌐 Escape HTML: '{html_escaped}'")
        
        # Mostrar escape JSON
        json_escaped = json.dumps(candidate_name)
        print(f"  📄 Escape JSON: {json_escaped}")
        
        # Generar JavaScript de prueba
        js_call = f"confirmDelete({candidate_id}, '{jinja_escaped}')"
        print(f"  🔧 Llamada JS: {js_call}")
        
        # Verificar si hay caracteres que podrían causar problemas
        problematic_chars = []
        for char in candidate_name:
            if char in ["'", '"', '\\', '\n', '\r', '\t']:
                problematic_chars.append(f"'{char}' (ord: {ord(char)})")
        
        if problematic_chars:
            print(f"  ⚠️ Caracteres problemáticos: {', '.join(problematic_chars)}")
        else:
            print(f"  ✅ No se detectaron caracteres problemáticos")

if __name__ == "__main__":
    check_candidate_names()