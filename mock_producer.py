import os, json, time, random, string
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
from metrics import log_event

MOCK_DIR = Path("uploads/mock")
MOCK_DIR.mkdir(parents=True, exist_ok=True)

def random_month():
    return f"2025-{random.randint(1,12):02d}"

def random_float(a, b, dec=2):
    return round(random.uniform(a, b), dec)

def generate_mock_file():
    rows = random.randint(6, 24)  # mínimo exigido pelo modelo
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
    data = sorted(data, key=lambda x: x["Mes"])
    fname = MOCK_DIR / f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{''.join(random.choices(string.ascii_lowercase, k=6))}.csv"
    import pandas as pd
    pd.DataFrame(data).to_csv(fname, index=False)
    log_event("mock_generated", {"file": str(fname)})
    return str(fname)

def start_mock_producer(interval_seconds=30):
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(generate_mock_file, "interval", seconds=interval_seconds)
    sched.start()