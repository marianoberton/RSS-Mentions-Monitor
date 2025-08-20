#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para RSS Mentions Monitor en VPS
Uso: python diagnostico_vps.py
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta
import json

def check_environment():
    """Verificar variables de entorno"""
    print("=== VERIFICACIÓN DE VARIABLES DE ENTORNO ===")
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID', 
        'LOG_LEVEL',
        'SQLITE_PATH',
        'TZ'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'TELEGRAM_BOT_TOKEN':
                print(f"✅ {var}: {value[:10]}...{value[-5:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NO CONFIGURADA")
    print()

def check_database():
    """Verificar estado de la base de datos"""
    print("=== VERIFICACIÓN DE BASE DE DATOS ===")
    db_path = os.getenv('SQLITE_PATH', 'data/mentions.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar integridad
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if integrity == 'ok':
            print(f"✅ Integridad de BD: OK")
        else:
            print(f"❌ Integridad de BD: {integrity}")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM hits")
        total_hits = cursor.fetchone()[0]
        print(f"📊 Total de hits: {total_hits}")
        
        # Hits recientes (últimas 24 horas)
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute("SELECT COUNT(*) FROM hits WHERE created_at > ?", (yesterday.isoformat(),))
        recent_hits = cursor.fetchone()[0]
        print(f"📊 Hits últimas 24h: {recent_hits}")
        
        # Verificar duplicados
        cursor.execute("""
            SELECT url, COUNT(*) as count 
            FROM hits 
            GROUP BY url 
            HAVING COUNT(*) > 1 
            LIMIT 5
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"⚠️  Duplicados encontrados: {len(duplicates)} URLs")
            for url, count in duplicates:
                print(f"   - {url}: {count} veces")
        else:
            print("✅ Sin duplicados detectados")
        
        # Menciones por keyword
        cursor.execute("""
            SELECT keyword, COUNT(*) as count 
            FROM hits 
            GROUP BY keyword 
            ORDER BY count DESC
        """)
        keywords = cursor.fetchall()
        print("📊 Menciones por keyword:")
        for keyword, count in keywords:
            print(f"   - {keyword}: {count}")
        
        conn.close()
        
    except sqlite3.DatabaseError as e:
        print(f"❌ Error de base de datos: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    print()

def check_logs():
    """Verificar logs recientes"""
    print("=== VERIFICACIÓN DE LOGS ===")
    log_paths = ['logs/app.log', 'logs/error.log']
    
    for log_path in log_paths:
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"✅ {log_path}: {len(lines)} líneas")
                    
                    # Últimas 5 líneas
                    if lines:
                        print(f"   Últimas entradas:")
                        for line in lines[-3:]:
                            print(f"   {line.strip()[:100]}...")
            except Exception as e:
                print(f"❌ Error leyendo {log_path}: {e}")
        else:
            print(f"⚠️  Log no encontrado: {log_path}")
    print()

def check_config():
    """Verificar configuración"""
    print("=== VERIFICACIÓN DE CONFIGURACIÓN ===")
    config_files = ['config.yml', 'config.production.yml']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ Encontrado: {config_file}")
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    print(f"   Keywords: {len(config.get('keywords', []))}")
                    print(f"   Feeds: {len(config.get('feeds', []))}")
            except Exception as e:
                print(f"   ⚠️  Error leyendo config: {e}")
        else:
            print(f"❌ No encontrado: {config_file}")
    print()

def check_processes():
    """Verificar procesos en ejecución"""
    print("=== VERIFICACIÓN DE PROCESOS ===")
    try:
        import psutil
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'main.py' in cmdline or 'web_app.py' in cmdline:
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'cmd': cmdline
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if python_processes:
            print("✅ Procesos Python encontrados:")
            for proc in python_processes:
                print(f"   PID {proc['pid']}: {proc['cmd'][:80]}...")
        else:
            print("⚠️  No se encontraron procesos Python del monitor")
    except ImportError:
        print("⚠️  psutil no disponible, no se pueden verificar procesos")
    except Exception as e:
        print(f"❌ Error verificando procesos: {e}")
    print()

def generate_report():
    """Generar reporte completo"""
    print("\n" + "="*60)
    print("REPORTE DE DIAGNÓSTICO RSS MENTIONS MONITOR")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    check_environment()
    check_database()
    check_logs()
    check_config()
    check_processes()
    
    print("=== RECOMENDACIONES ===")
    print("1. Si hay errores de BD corrupta, ejecutar: sqlite3 data/mentions.db '.recover' > backup.sql")
    print("2. Para reiniciar servicios: docker-compose restart")
    print("3. Para ver logs en tiempo real: docker-compose logs -f")
    print("4. Para verificar salud: curl http://localhost:5000/health")
    print()

if __name__ == "__main__":
    generate_report()