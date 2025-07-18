import threading
import time
import subprocess
import os
import signal
import sys
import logging
from dotenv import load_dotenv
from func.response_listener import ResponseListener

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fall_detection_system.log')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Variables globales
stop_detection_event = threading.Event()
ffmpeg_processes = {"monitor": None, "alerta": None}
streaming_threads = {}
threads_lock = threading.Lock()

def signal_handler(signum, frame):
    """Maneja la señal de interrupción de forma segura"""
    logger.info(f"Señal {signum} recibida. Iniciando shutdown...")
    stop_detection_event.set()

def cleanup_processes():
    """Limpia todos los procesos FFmpeg de forma segura"""
    with threads_lock:
        for stream_type in list(ffmpeg_processes.keys()):
            stop_streaming(stream_type)

def validate_dependencies():
    """Valida que las dependencias estén disponibles"""
    try:
        # Verificar FFmpeg
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            timeout=5
        )
        if result.returncode != 0:
            logger.error("FFmpeg no está disponible")
            return False
        
        # Verificar variables de entorno críticas
        required_vars = [
            "INGEST_URL_Monitor", "STREAM_KEY_Monitor",
            "INGEST_URL_Alerta", "STREAM_KEY_Alerta"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {missing_vars}")
            return False
            
        return True
        
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"Error validando dependencias: {e}")
        return False

def detection_worker():
    """Worker para la detección de caídas con auto-recovery"""
    consecutive_failures = 0
    max_consecutive_failures = 3
    
    try:
        logger.info("Iniciando detección de caídas...")
        
        # Verificar que el archivo existe
        detector_path = "./func/fall_detector.py"
        if not os.path.exists(detector_path):
            logger.error(f"Archivo no encontrado: {detector_path}")
            return
        
        # Monitorear el proceso de detección
        while not stop_detection_event.is_set():
            try:
                result = subprocess.run(
                    [sys.executable, detector_path],
                    check=False,
                    capture_output=False,
                    timeout=None
                )
                
                if result.returncode == 0:
                    consecutive_failures = 0  # Reset en éxito
                    logger.info("Detección de caídas terminó normalmente")
                else:
                    consecutive_failures += 1
                    logger.warning(f"Detección de caídas terminó con código: {result.returncode} "
                                 f"(Fallos consecutivos: {consecutive_failures})")
                    
                    # Si hay muchos fallos consecutivos, esperar más tiempo
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("Demasiados fallos consecutivos. Esperando 30 segundos...")
                        if not stop_detection_event.wait(30):  # Wait with interrupt check
                            consecutive_failures = 0  # Reset después del break largo
                        continue
                    
                # Si el proceso termina y no es por shutdown, reiniciar
                if not stop_detection_event.is_set():
                    sleep_time = min(5 + consecutive_failures * 2, 15)  # Progressive backoff
                    logger.info(f"Reiniciando detección de caídas en {sleep_time} segundos...")
                    if stop_detection_event.wait(sleep_time):  # Interruptible sleep
                        break
                    
            except subprocess.TimeoutExpired:
                logger.warning("Proceso de detección tomó demasiado tiempo")
                consecutive_failures += 1
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Error en detección de caídas: {e}")
                if not stop_detection_event.wait(5):
                    continue
            
    except Exception as e:
        logger.error(f"Error crítico en detection_worker: {e}")
    finally:
        logger.info("Worker de detección finalizado")

def streaming_worker():
    """Worker para manejar las solicitudes de streaming"""
    try:
        listener = ResponseListener()
        logger.info("Escuchando respuestas para streaming...")

        while not stop_detection_event.is_set():
            try:
                # Verificación defensiva de atributos
                if (hasattr(listener, 'response_received') and 
                    getattr(listener, 'response_received', False)):
                    
                    stream_type = getattr(listener, 'stream_type', None)
                    action = getattr(listener, 'action', None)
                    
                    if action and stream_type:
                        if action == "start":
                            logger.info(f"Solicitud de inicio para {stream_type} recibida")
                            start_streaming_async(stream_type)
                        elif action == "stop":
                            logger.info(f"Solicitud de detención para {stream_type} recibida")
                            stop_streaming(stream_type)
                        else:
                            logger.warning(f"Acción desconocida: {action}")
                    
                    # Reset listener state de forma segura
                    try:
                        listener.response_received = False
                        listener.action = None
                        listener.stream_type = None
                    except AttributeError:
                        logger.warning("No se pudieron resetear atributos del listener")
                    
            except Exception as e:
                logger.error(f"Error en el hilo de streaming: {e}")
            
            # Sleep interruptible
            if stop_detection_event.wait(0.5):
                break
        
        logger.info("Hilo de streaming detenido")
        
    except Exception as e:
        logger.error(f"Error crítico en streaming worker: {e}")

def start_streaming_async(stream_type):
    """Inicia streaming de forma asíncrona"""
    if not stream_type or stream_type not in ["monitor", "alerta"]:
        logger.error(f"Tipo de stream inválido: {stream_type}")
        return
        
    with threads_lock:
        # Detener streaming existente si hay uno
        current_thread = streaming_threads.get(stream_type)
        if current_thread and current_thread.is_alive():
            logger.info(f"Deteniendo streaming existente para {stream_type}")
            stop_streaming(stream_type)
            
            # Esperar a que termine el hilo anterior
            current_thread.join(timeout=3)
            if current_thread.is_alive():
                logger.warning(f"Hilo anterior de {stream_type} no terminó a tiempo")
        
        # Crear nuevo hilo para streaming
        thread = threading.Thread(
            target=start_streaming,
            args=(stream_type,),
            daemon=True,
            name=f"Streaming-{stream_type}"
        )
        streaming_threads[stream_type] = thread
        thread.start()
        logger.info(f"Hilo de streaming iniciado para {stream_type}")

def stop_streaming(stream_type):
    """Detiene el proceso de streaming FFmpeg"""
    global ffmpeg_processes, streaming_threads
    
    proc = ffmpeg_processes.get(stream_type)
    if proc and proc.poll() is None:
        try:
            logger.info(f"Deteniendo FFmpeg ({stream_type})...")
            
            # Intentar terminación graceful primero
            proc.terminate()
            
            try:
                proc.wait(timeout=5)
                logger.info(f"FFmpeg ({stream_type}) detenido correctamente")
            except subprocess.TimeoutExpired:
                logger.warning(f"FFmpeg ({stream_type}) no respondió, forzando terminación...")
                proc.kill()
                try:
                    proc.wait(timeout=3)
                    logger.info(f"FFmpeg ({stream_type}) terminado forzosamente")
                except subprocess.TimeoutExpired:
                    logger.error(f"No se pudo terminar FFmpeg ({stream_type}) - proceso zombie")
            
        except ProcessLookupError:
            logger.info(f"FFmpeg ({stream_type}) ya había terminado")
        except Exception as e:
            logger.error(f"Error al detener FFmpeg ({stream_type}): {e}")
        finally:
            ffmpeg_processes[stream_type] = None
    
    # Limpiar hilo de streaming
    if stream_type in streaming_threads:
        streaming_threads[stream_type] = None

def validate_env_vars(stream_type):
    """Valida que las variables de entorno estén configuradas"""
    env_mapping = {
        "monitor": ("INGEST_URL_Monitor", "STREAM_KEY_Monitor"),
        "alerta": ("INGEST_URL_Alerta", "STREAM_KEY_Alerta")
    }
    
    if stream_type not in env_mapping:
        logger.error(f"Tipo de stream no válido: {stream_type}")
        return None, None
    
    url_var, key_var = env_mapping[stream_type]
    ingest_url = os.getenv(url_var)
    stream_key = os.getenv(key_var)
    
    if not ingest_url or not stream_key:
        logger.error(f"Variables de entorno faltantes para {stream_type}: {url_var}, {key_var}")
        return None, None
    
    return ingest_url, stream_key

def start_streaming(stream_type):
    """Inicia el proceso de streaming FFmpeg"""
    global ffmpeg_processes
    
    # Validar variables de entorno
    ingest_url, stream_key = validate_env_vars(stream_type)
    if not ingest_url or not stream_key:
        return
    
    # Detener proceso existente si hay uno
    if ffmpeg_processes.get(stream_type):
        stop_streaming(stream_type)

    ffmpeg_command = [
        "ffmpeg",
        "-y",  # Sobrescribir sin preguntar
        "-f", "x11grab",
        "-video_size", "1280x720",
        "-framerate", "24",
        "-i", ":0.0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-b:v", "800k",
        "-maxrate", "800k",
        "-bufsize", "1200k",
        "-reconnect", "1",  # Auto-reconnect
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-f", "flv",
        f"{ingest_url}{stream_key}"
    ]

    logger.info(f"Iniciando streaming ({stream_type})...")
    try:
        proc = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Crear nuevo grupo de procesos
        )
        ffmpeg_processes[stream_type] = proc
        logger.info(f"FFmpeg proceso iniciado para {stream_type} (PID: {proc.pid})")
        
        # Monitorear proceso
        while not stop_detection_event.is_set():
            poll_result = proc.poll()
            if poll_result is not None:
                if poll_result != 0:
                    try:
                        stderr_output = proc.stderr.read().decode('utf-8', errors='ignore')
                        logger.error(f"FFmpeg ({stream_type}) error {poll_result}: {stderr_output[:300]}...")
                    except Exception:
                        logger.error(f"FFmpeg ({stream_type}) terminó con error {poll_result}")
                else:
                    logger.info(f"FFmpeg ({stream_type}) terminó normalmente")
                break
            
            # Check más frecuente para mejor responsividad
            if stop_detection_event.wait(0.5):
                break
            
    except Exception as e:
        logger.error(f"Error durante el streaming ({stream_type}): {e}")
    finally:
        if stream_type in ffmpeg_processes:
            ffmpeg_processes[stream_type] = None
        logger.info(f"Streaming ({stream_type}) finalizado")

def main():
    """Función principal del sistema"""
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=== INICIANDO SISTEMA DE DETECCIÓN DE CAÍDAS ===")
    
    # Validar dependencias
    if not validate_dependencies():
        logger.error("Falló la validación de dependencias")
        return 1

    # Crear hilos principales
    detection_thread = threading.Thread(
        target=detection_worker,
        daemon=False,
        name="Detection-Worker"
    )
    streaming_thread = threading.Thread(
        target=streaming_worker,
        daemon=False,
        name="Streaming-Worker"
    )

    # Iniciar hilos
    logger.info("Iniciando hilos del sistema...")
    detection_thread.start()
    streaming_thread.start()

    try:
        # Mantener programa vivo con monitoreo
        health_check_interval = 30  # Segundos
        last_health_check = time.time()
        
        while not stop_detection_event.is_set():
            current_time = time.time()
            
            # Health check periódico
            if current_time - last_health_check >= health_check_interval:
                if not detection_thread.is_alive():
                    logger.error("❌ Hilo de detección se detuvo inesperadamente")
                if not streaming_thread.is_alive():
                    logger.error("❌ Hilo de streaming se detuvo inesperadamente")
                else:
                    logger.info("✅ Sistema funcionando correctamente")
                
                last_health_check = current_time
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupción recibida. Finalizando sistema...")
        stop_detection_event.set()
    finally:
        # Limpieza ordenada
        logger.info("=== INICIANDO SHUTDOWN DEL SISTEMA ===")
        cleanup_processes()
        
        # Esperar finalización de hilos con timeout progresivo
        logger.info("Esperando finalización de hilos...")
        
        detection_thread.join(timeout=10)
        if detection_thread.is_alive():
            logger.warning("⚠️  Hilo de detección no terminó en 10s")
            
        streaming_thread.join(timeout=10)
        if streaming_thread.is_alive():
            logger.warning("⚠️  Hilo de streaming no terminó en 10s")
        
        logger.info("=== SISTEMA FINALIZADO CORRECTAMENTE ===")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
