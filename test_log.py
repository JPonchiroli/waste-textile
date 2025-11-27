# test_log.py
from ml._main import process_file
from metrics import log_event

log_event("manual_test", {"msg": "iniciando teste"})
out, figs = process_file("uploads/mock/mock_20251126_223000_abc123.csv", "uploads")
log_event("manual_test", {"msg": "processado", "out": out})