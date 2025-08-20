import subprocess
import sys

def install_dependencies():
    print("Instalando dependencias necesarias...")
    dependencies = [
        "beautifulsoup4",  # Para extraer contenido de artículos
        "requests",       # Para hacer peticiones HTTP
        "feedparser",     # Para procesar feeds RSS
        "tenacity",       # Para reintentos
        "unidecode",      # Para normalizar texto
        "apscheduler",    # Para programar tareas
        "python-telegram-bot"  # Para notificaciones
    ]
    
    for dependency in dependencies:
        print(f"Instalando {dependency}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])
            print(f"{dependency} instalado correctamente.")
        except subprocess.CalledProcessError as e:
            print(f"Error al instalar {dependency}: {e}")
            return False
    
    print("Todas las dependencias han sido instaladas correctamente.")
    return True

if __name__ == "__main__":
    install_dependencies()