import subprocess
import sys
import os
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='background_processor_service.log',
                   filemode='a')
logger = logging.getLogger(__name__)

# También mostrar logs en consola
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def run_background_processor():
    """Ejecuta el procesador en segundo plano y lo reinicia si se detiene."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processor_script = os.path.join(script_dir, 'background_processor.py')
    
    logger.info(f"Iniciando el procesador en segundo plano desde {processor_script}")
    
    while True:
        try:
            # Ejecutar el procesador en un proceso separado
            logger.info("Iniciando proceso de background_processor.py")
            process = subprocess.Popen(
                [sys.executable, processor_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Esperar a que el proceso termine
            stdout, stderr = process.communicate()
            
            # Verificar si el proceso terminó con error
            if process.returncode != 0:
                logger.error(f"El procesador terminó con código de error {process.returncode}")
                logger.error(f"Salida estándar: {stdout}")
                logger.error(f"Salida de error: {stderr}")
            else:
                logger.info("El procesador terminó normalmente")
                logger.info(f"Salida estándar: {stdout}")
            
            # Esperar antes de reiniciar
            logger.info("Esperando 10 segundos antes de reiniciar el procesador...")
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error al ejecutar el procesador: {e}")
            logger.info("Esperando 30 segundos antes de reintentar...")
            time.sleep(30)

if __name__ == "__main__":
    logger.info("Iniciando servicio de procesamiento en segundo plano")
    run_background_processor()