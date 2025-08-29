#!/usr/bin/env python3
"""
Script de prueba completa del flujo de trabajo:
1. Verificar migración de BD
2. Probar APIs de candidatos
3. Simular adición de candidato
4. Probar búsqueda de keywords
5. Verificar sistema de notificaciones
"""

import sqlite3
import requests
import json
from app.config import config
from app.storage import get_db_connection

def test_database_migration():
    """Verificar que todas las tablas estén creadas correctamente"""
    print("=== VERIFICACIÓN DE MIGRACIÓN DE BD ===")
    
    required_tables = [
        'articles', 'hits', 'feed_state', 'persons', 'person_keywords',
        'articles_fts', 'candidates', 'candidate_keywords', 
        'electoral_alliances', 'notifications', 'political_positions', 
        'electoral_sections'
    ]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        all_tables_exist = True
        for table in required_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} registros")
            except sqlite3.Error as e:
                print(f"❌ {table}: ERROR - {e}")
                all_tables_exist = False
        
        conn.close()
        return all_tables_exist
        
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False

def test_candidate_apis():
    """Probar que todas las APIs de candidatos funcionen"""
    print("\n=== VERIFICACIÓN DE APIs DE CANDIDATOS ===")
    
    base_url = "http://localhost:5000"
    apis = [
        ('/api/political-positions', 'positions'),
        ('/api/electoral-sections', 'sections'),
        ('/api/alliances', 'alliances'),
        ('/api/candidates', 'data')
    ]
    
    all_apis_working = True
    api_data = {}
    
    for endpoint, data_key in apis:
        try:
            response = requests.get(base_url + endpoint, timeout=5)
            if response.status_code == 200:
                data = response.json()
                count = len(data.get(data_key, []))
                print(f"✅ {endpoint}: {count} elementos")
                api_data[endpoint] = data
            else:
                print(f"❌ {endpoint}: Error {response.status_code}")
                all_apis_working = False
        except Exception as e:
            print(f"❌ {endpoint}: Error {e}")
            all_apis_working = False
    
    return all_apis_working, api_data

def test_candidate_creation():
    """Simular la creación de un candidato de prueba"""
    print("\n=== SIMULACIÓN DE CREACIÓN DE CANDIDATO ===")
    
    try:
        conn = get_db_connection()
        
        # Verificar si ya existe un candidato de prueba
        cursor = conn.execute("""
            SELECT id FROM candidates WHERE name = 'Candidato Test'
        """)
        existing = cursor.fetchone()
        
        if existing:
            print("✅ Candidato de prueba ya existe")
            candidate_id = existing[0]
        else:
            # Crear candidato de prueba
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            
            cursor = conn.execute("""
                INSERT INTO candidates (
                    name, full_name, description, political_party,
                    electoral_section, legislative_position, district,
                    list_number, list_position, importance_level, is_active,
                    created_utc, updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'Candidato Test',
                'Candidato de Prueba Completo',
                'Candidato creado para pruebas del sistema',
                'Partido Test',
                1,  # electoral_section debe ser un número entre 1 y 8
                'Diputado Provincial',
                'Distrito Test',
                1, 1, 2, 1, now, now
            ))
            
            candidate_id = cursor.lastrowid
            
            # Agregar keywords de prueba
            test_keywords = ['Candidato Test', 'Prueba Sistema']
            for keyword in test_keywords:
                cursor.execute("""
                    INSERT INTO candidate_keywords (candidate_id, keyword, is_active, created_utc)
                    VALUES (?, ?, 1, ?)
                """, (candidate_id, keyword, now))
            
            conn.commit()
            print(f"✅ Candidato de prueba creado con ID: {candidate_id}")
        
        conn.close()
        return candidate_id
        
    except Exception as e:
        print(f"❌ Error creando candidato de prueba: {e}")
        return None

def test_keyword_search(candidate_id):
    """Probar el sistema de búsqueda de keywords"""
    print("\n=== VERIFICACIÓN DE BÚSQUEDA DE KEYWORDS ===")
    
    try:
        conn = get_db_connection()
        
        # Obtener keywords del candidato
        cursor = conn.execute("""
            SELECT keyword FROM candidate_keywords 
            WHERE candidate_id = ? AND is_active = 1
        """, (candidate_id,))
        keywords = [row[0] for row in cursor.fetchall()]
        
        print(f"✅ Keywords del candidato: {keywords}")
        
        # Verificar si hay artículos que contengan estas keywords
        total_matches = 0
        for keyword in keywords:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE title LIKE ? OR full_content LIKE ?
            """, (f'%{keyword}%', f'%{keyword}%'))
            matches = cursor.fetchone()[0]
            total_matches += matches
            print(f"  - '{keyword}': {matches} coincidencias")
        
        print(f"✅ Total de coincidencias encontradas: {total_matches}")
        
        conn.close()
        return total_matches > 0
        
    except Exception as e:
        print(f"❌ Error en búsqueda de keywords: {e}")
        return False

def test_notification_system():
    """Verificar que el sistema de notificaciones esté configurado"""
    print("\n=== VERIFICACIÓN DE SISTEMA DE NOTIFICACIONES ===")
    
    try:
        conn = get_db_connection()
        
        # Verificar tabla de notificaciones
        cursor = conn.execute("SELECT COUNT(*) FROM notifications")
        notification_count = cursor.fetchone()[0]
        print(f"✅ Notificaciones en BD: {notification_count}")
        
        # Verificar configuración de Telegram
        from app.config import config
        telegram_config = {
            'bot_token': config.get('TELEGRAM_BOT_TOKEN'),
            'chat_id': config.get('TELEGRAM_CHAT_ID')
        }
        
        if telegram_config['bot_token']:
            print("✅ Token de Telegram configurado")
        else:
            print("⚠️ Token de Telegram NO configurado")
            
        if telegram_config['chat_id']:
            print("✅ Chat ID de Telegram configurado")
        else:
            print("⚠️ Chat ID de Telegram NO configurado")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando sistema de notificaciones: {e}")
        return False

def test_web_interface():
    """Probar que la interfaz web esté funcionando"""
    print("\n=== VERIFICACIÓN DE INTERFAZ WEB ===")
    
    base_url = "http://localhost:5000"
    pages = [
        '/candidates',
        '/candidates/manage'
    ]
    
    all_pages_working = True
    
    for page in pages:
        try:
            response = requests.get(base_url + page, timeout=5)
            if response.status_code == 200:
                print(f"✅ {page}: Página carga correctamente")
            else:
                print(f"❌ {page}: Error {response.status_code}")
                all_pages_working = False
        except Exception as e:
            print(f"❌ {page}: Error {e}")
            all_pages_working = False
    
    return all_pages_working

def main():
    print("🧪 PRUEBA COMPLETA DEL FLUJO DE TRABAJO")
    print("=" * 60)
    
    # Ejecutar todas las pruebas
    results = {
        'database_migration': test_database_migration(),
        'candidate_apis': test_candidate_apis()[0],
        'web_interface': test_web_interface(),
        'notification_system': test_notification_system()
    }
    
    # Pruebas que requieren candidato
    candidate_id = test_candidate_creation()
    if candidate_id:
        results['candidate_creation'] = True
        results['keyword_search'] = test_keyword_search(candidate_id)
    else:
        results['candidate_creation'] = False
        results['keyword_search'] = False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TODAS LAS PRUEBAS PASARON - SISTEMA LISTO PARA DESPLIEGUE")
    else:
        print("⚠️ ALGUNAS PRUEBAS FALLARON - REVISAR ANTES DEL DESPLIEGUE")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    main()