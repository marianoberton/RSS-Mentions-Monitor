#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import yaml
import requests
from datetime import datetime

print("=== VERIFICACIÓN PARA DESPLIEGUE EN EASYPANEL ===")
print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

# Lista de archivos requeridos
required_files = [
    'Dockerfile',
    'docker-compose.yml',
    'start.sh',
    'requirements.txt',
    'config.yml',
    'config.production.yml',
    '.env.example',
    '.dockerignore',
    'DEPLOY.md',
    'main.py',
    'web_app.py'
]

print("📁 VERIFICANDO ARCHIVOS REQUERIDOS:")
all_files_present = True
for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - FALTANTE")
        all_files_present = False

print(f"\n📋 RESULTADO: {'✅ Todos los archivos presentes' if all_files_present else '❌ Faltan archivos'}")

# Verificar estructura de directorios
print("\n📂 VERIFICANDO ESTRUCTURA DE DIRECTORIOS:")
required_dirs = ['app', 'templates', 'static']
for dir_name in required_dirs:
    if os.path.exists(dir_name) and os.path.isdir(dir_name):
        print(f"✅ {dir_name}/")
    else:
        print(f"❌ {dir_name}/ - FALTANTE")

# Verificar configuración
print("\n⚙️ VERIFICANDO CONFIGURACIÓN:")
try:
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Verificar keywords
    if 'keywords' in config and len(config['keywords']) > 0:
        print(f"✅ Keywords configuradas: {len(config['keywords'])}")
        for keyword in config['keywords']:
            print(f"   • {keyword}")
    else:
        print("❌ No hay keywords configuradas")
    
    # Verificar feeds
    if 'feeds' in config and len(config['feeds']) > 0:
        enabled_feeds = [f for f in config['feeds'] if f.get('enabled', True)]
        print(f"✅ Feeds configurados: {len(config['feeds'])} (habilitados: {len(enabled_feeds)})")
        for feed in enabled_feeds[:5]:  # Mostrar solo los primeros 5
            print(f"   • {feed['name']}: {feed['url']}")
        if len(enabled_feeds) > 5:
            print(f"   ... y {len(enabled_feeds) - 5} más")
    else:
        print("❌ No hay feeds configurados")
        
except Exception as e:
    print(f"❌ Error al leer config.yml: {e}")

# Verificar variables de entorno de ejemplo
print("\n🔐 VERIFICANDO VARIABLES DE ENTORNO:")
try:
    with open('.env.example', 'r') as f:
        env_content = f.read()
    
    required_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    for var in required_vars:
        if var in env_content:
            print(f"✅ {var} documentado en .env.example")
        else:
            print(f"❌ {var} no documentado")
except Exception as e:
    print(f"❌ Error al leer .env.example: {e}")

# Verificar Dockerfile
print("\n🐳 VERIFICANDO DOCKERFILE:")
try:
    with open('Dockerfile', 'r') as f:
        dockerfile_content = f.read()
    
    checks = [
        ('FROM python:', 'Imagen base de Python'),
        ('COPY requirements.txt', 'Copia de requirements.txt'),
        ('RUN pip install', 'Instalación de dependencias'),
        ('EXPOSE 5000', 'Puerto expuesto'),
        ('CMD', 'Comando de inicio')
    ]
    
    for check, description in checks:
        if check in dockerfile_content:
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - No encontrado")
except Exception as e:
    print(f"❌ Error al leer Dockerfile: {e}")

# Verificar requirements.txt
print("\n📦 VERIFICANDO DEPENDENCIAS:")
try:
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    essential_packages = ['flask', 'requests', 'feedparser', 'apscheduler', 'pyyaml']
    for package in essential_packages:
        if package.lower() in requirements.lower():
            print(f"✅ {package}")
        else:
            print(f"❌ {package} - No encontrado")
except Exception as e:
    print(f"❌ Error al leer requirements.txt: {e}")

# Verificar permisos de start.sh
print("\n🚀 VERIFICANDO SCRIPT DE INICIO:")
if os.path.exists('start.sh'):
    # En Windows, no podemos verificar permisos de ejecución de la misma manera
    print("✅ start.sh existe")
    try:
        with open('start.sh', 'r') as f:
            start_content = f.read()
        if 'python main.py' in start_content and 'flask' in start_content:
            print("✅ Script contiene comandos de inicio")
        else:
            print("❌ Script no contiene comandos esperados")
    except Exception as e:
        print(f"❌ Error al leer start.sh: {e}")
else:
    print("❌ start.sh no existe")

# Resumen final
print("\n" + "="*50)
print("📊 RESUMEN DE VERIFICACIÓN")
print("="*50)

if all_files_present:
    print("✅ LISTO PARA DESPLIEGUE")
    print("\n🎯 PRÓXIMOS PASOS:")
    print("1. Subir código a repositorio Git")
    print("2. Configurar aplicación en EasyPanel")
    print("3. Configurar variables de entorno")
    print("4. Desplegar y verificar funcionamiento")
    print("\n📖 Consulta DEPLOY.md para instrucciones detalladas")
else:
    print("❌ FALTAN ARCHIVOS REQUERIDOS")
    print("\n🔧 ACCIONES REQUERIDAS:")
    print("1. Crear/verificar archivos faltantes")
    print("2. Ejecutar nuevamente esta verificación")
    print("3. Proceder con el despliegue una vez completo")

print("\n=== VERIFICACIÓN COMPLETADA ===")