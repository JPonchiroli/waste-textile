import os, json, time, random, string
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd

# Importa as métricas do metrics.py
from metrics import log_event, recv_counter, queue_gauge, err_counter, ml_up_gauge

MOCK_DIR = Path("uploads/mock")
MOCK_DIR.mkdir(parents=True, exist_ok=True)

def random_month():
    return f"2025-{random.randint(1,12):02d}"

def random_float(a, b, dec=2):
    return round(random.uniform(a, b), dec)

def generate_mock_file():
    print(f"[{datetime.now().time()}] Gerando mock...") # Log no terminal para você ver funcionando
    
    # 1. Sobe a fila (Simula início)
    queue_gauge.inc()
    
    try:
        # Tempo de processamento fake (4 a 6s) para o Prometheus pegar o pulso
        time.sleep(random.uniform(4, 6))

        rows = random.randint(6, 24)
        data = [
            {
                "Mes": random_month(),
                "Producao_Total_kg": random_float(1000, 5000),
                "Eficiencia_kg_h": random_float(50, 120),
                "Horas_Operacionais": random_float(150, 220),
                "Residuo_kg": random_float(100, 500),
            }
            for _ in range(rows)
        ]
        
        # Cria nome único
        fname = MOCK_DIR / f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{''.join(random.choices(string.ascii_lowercase, k=6))}.csv"
        
        # Salva CSV
        df = pd.DataFrame(data)
        df.to_csv(fname, index=False)
        
        log_event("mock_generated", {"file": str(fname)})

        # 2. Atualiza contadores
        recv_counter.inc()
        ml_up_gauge.set(1) # IA Online

        # Simula erro ocasional (10% chance)
        if random.random() < 0.1:
            print("Simulando erro aleatório...")
            raise Exception("Erro simulado de validação")

    except Exception as e:
        err_counter.inc()
        log_event("mock_error", {"msg": str(e)})
        ml_up_gauge.set(0) # IA Offline momentaneamente
    
    finally:
        # 3. Desce a fila (Fim)
        queue_gauge.dec()
        print("Mock finalizado.")

def start_mock_producer(interval_seconds=15):
    sched = BackgroundScheduler(daemon=True)
    # max_instances=5 evita erro se o job demorar mais que o intervalo
    sched.add_job(generate_mock_file, "interval", seconds=interval_seconds, max_instances=5)
    sched.start()