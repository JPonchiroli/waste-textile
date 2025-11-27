import time, logging, psutil, pynvml, os, json
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

# Métricas
gpu_gauge     = Gauge('gpu_usage_percent', 'Uso de GPU')
pred_hist     = Histogram('prediction_duration_seconds', 'Tempo de previsão')
queue_gauge   = Gauge('queue_size', 'Arquivos na fila')
err_counter   = Counter('errors_24h_total', 'Erros últimas 24h')
mem_gauge     = Gauge('memory_usage_bytes', 'Uso de RAM')
recv_counter  = Counter('files_received_24h_total', 'Arquivos recebidos')
ml_up_gauge   = Gauge('ml_integration_up', 'Status da IA')

LOG_FILE = Path("logs/app.log")
LOG_FILE.parent.mkdir(exist_ok=True)

def log_event(event_type: str, payload: dict):
    """Escreve 1 linha JSON por evento."""
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "type": event_type, **payload}) + "\n")

def update_system_metrics():
    # GPU
    if GPU_HANDLE:
        util = pynvml.nvmlDeviceGetUtilizationRates(GPU_HANDLE)
        gpu_gauge.set(util.gpu)
    # RAM
    mem_gauge.set(psutil.virtual_memory().used)

def metrics_wrapper(func):
    @wraps(func)
    def inner(*args, **kwargs):
        update_system_metrics()
        recv_counter.inc()  # conta cada chamada como "recebido"
        queue_gauge.inc()
        start = time.time()
        try:
            result = func(*args, **kwargs)
            ml_up_gauge.set(1)
            return result
        except Exception as e:
            err_counter.inc()
            ml_up_gauge.set(0)
            log_event("error", {"msg": str(e)})
            raise
        finally:
            queue_gauge.dec()
            pred_hist.observe(time.time() - start)
    return inner

    
def _update_loop():
    while True:
        update_system_metrics()
        time.sleep(5)

def start_metrics_refresh():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(update_system_metrics, 'interval', seconds=5)
    sched.start()