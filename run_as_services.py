import os
import sys
import time
import logging
import subprocess
import signal
import atexit

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("services.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Procesos
processes = []

def signal_handler(sig, frame):
    """Manejador de señales para detener los procesos correctamente."""
    logger.info("Recibida señal de terminación. Deteniendo servicios...")
    stop_services()
    sys.exit(0)

def stop_services():
    """Detiene todos los servicios en ejecución."""
    for process in processes:
        if process.poll() is None:  # Si el proceso sigue en ejecución
            logger.info(f"Deteniendo proceso: {process.args}")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"El proceso no se detuvo correctamente. Forzando cierre: {process.args}")
                process.kill()

def start_service(command, name):
    """Inicia un servicio como proceso en segundo plano."""
    try:
        logger.info(f"Iniciando servicio {name}: {command}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        processes.append(process)
        logger.info(f"Servicio {name} iniciado con PID: {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Error al iniciar el servicio {name}: {e}")
        return None

def monitor_services():
    """Monitorea los servicios y los reinicia si se detienen."""
    while True:
        for i, process in enumerate(processes[:]):
            name = "RSS Monitor" if i == 0 else "Background Processor"
            if process.poll() is not None:  # Si el proceso ha terminado
                logger.warning(f"El servicio {name} se ha detenido. Código de salida: {process.returncode}")
                # Leer la salida del proceso para diagnóstico
                output, _ = process.communicate()
                logger.info(f"Salida del servicio {name}:\n{output}")
                
                # Reiniciar el servicio
                logger.info(f"Reiniciando el servicio {name}...")
                command = process.args
                processes.remove(process)
                new_process = start_service(command, name)
                if new_process is None:
                    logger.error(f"No se pudo reiniciar el servicio {name}")
        
        # Verificar cada 10 segundos
        time.sleep(10)

def run_services():
    """Ejecuta los servicios del monitor RSS y el procesador en segundo plano."""
    # Registrar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Registrar función para detener servicios al salir
    atexit.register(stop_services)
    
    # Iniciar servicios
    rss_monitor = start_service([sys.executable, "main.py"], "RSS Monitor")
    background_processor = start_service([sys.executable, "background_processor.py"], "Background Processor")
    
    if rss_monitor is None or background_processor is None:
        logger.error("No se pudieron iniciar todos los servicios. Abortando.")
        stop_services()
        return
    
    logger.info("Todos los servicios iniciados correctamente. Iniciando monitoreo...")
    
    try:
        # Monitorear servicios y reiniciarlos si es necesario
        monitor_services()
    except KeyboardInterrupt:
        logger.info("Interrupción de teclado recibida. Deteniendo servicios...")
    finally:
        stop_services()

if __name__ == "__main__":
    logger.info("=== INICIANDO SERVICIOS DEL MONITOR RSS Y PROCESADOR EN SEGUNDO PLANO ===")
    run_services()