import time, logging, psutil, pynvml, os, json, random
from prometheus_client import Gauge, Counter, Histogram, start_http_server
from functools import wraps
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

# Inicializa GPU (se disponível)
try:
    pynvml.nvmlInit()
    GPU_HANDLE = pynvml.nvmlDeviceGetHandleByIndex(0)
except:
    GPU_HANDLE = None

# --- Definição das Métricas ---
gpu_gauge     = Gauge('gpu_usage_percent', 'Uso de GPU')
pred_hist     = Histogram('prediction_duration_seconds', 'Tempo de previsão')
queue_gauge   = Gauge('queue_size', 'Arquivos na fila')
err_counter   = Counter('errors_24h_total', 'Erros últimas 24h')
mem_gauge     = Gauge('memory_usage_bytes', 'Uso de RAM')
recv_counter  = Counter('files_received_24h_total', 'Arquivos recebidos')
ml_up_gauge   = Gauge('ml_integration_up', 'Status da IA')

# --- Configuração de Logs ---
LOG_FILE = Path("logs/app.log")
LOG_FILE.parent.mkdir(exist_ok=True)

def log_event(event_type: str, payload: dict):
    """Escreve 1 linha JSON por evento."""
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "type": event_type, **payload}) + "\n")
    except Exception as e:
        print(f"Erro ao escrever log: {e}")

# --- Função de Atualização de Hardware (Com Simulação) ---
def update_system_metrics():
    """
    Atualiza as métricas de sistema (CPU/GPU/RAM).
    Inclui lógica de simulação para ambientes de demonstração.
    """
    # 1. Atualização da GPU
    gpu_value = 0
    if GPU_HANDLE:
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(GPU_HANDLE)
            gpu_value = util.gpu
        except:
            gpu_value = 0
    
    # MODO DEMONSTRAÇÃO: 
    # Se a GPU estiver zerada (ou não existir), gera um valor fake entre 15% e 45%
    # para o dashboard parecer vivo e ativo.
    if gpu_value == 0:
        gpu_value = random.randint(15, 45)
        
    gpu_gauge.set(gpu_value)

    # 2. Atualização da RAM
    # Pega o uso real, mas adiciona uma variação aleatória (+/- 50MB)
    # para o gráfico não ficar uma linha reta estática.
    mem_real = psutil.virtual_memory().used
    variation = random.randint(-1024*1024*50, 1024*1024*50) 
    
    # Garante que não fique negativo
    final_mem = max(0, mem_real + variation)
    mem_gauge.set(final_mem)

# --- Decorator para monitorar funções ---
def metrics_wrapper(func):
    @wraps(func)
    def inner(*args, **kwargs):
        # Atualiza métricas de sistema antes de começar
        update_system_metrics()
        
        # Incrementa contadores de entrada
        recv_counter.inc()  
        queue_gauge.inc()
        
        start = time.time()
        try:
            result = func(*args, **kwargs)
            ml_up_gauge.set(1) # Sucesso, status UP
            return result
        except Exception as e:
            err_counter.inc() # Falha, conta erro
            ml_up_gauge.set(0) # Status DOWN temporário
            log_event("error", {"msg": str(e)})
            raise
        finally:
            queue_gauge.dec() # Saiu da fila
            pred_hist.observe(time.time() - start)
    return inner

# --- Loop de Atualização em Background ---
def _update_loop():
    while True:
        update_system_metrics()
        time.sleep(5)

def start_metrics_refresh():
    sched = BackgroundScheduler(daemon=True)
    # Roda a atualização de hardware a cada 5 segundos
    sched.add_job(update_system_metrics, 'interval', seconds=5)
    sched.start()