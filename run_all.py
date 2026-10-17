"""Lanza todo el sistema en paralelo: N productores + consumidor + API pública.
Uso: python run_all.py [N_PRODUCTORES]   (por defecto 2)
Para añadir un productor nuevo en caliente (genera una alerta):
    python productor.py P3
"""
import subprocess
import sys
import time

n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
procs = [subprocess.Popen([sys.executable, "consumidor.py"]),
         subprocess.Popen([sys.executable, "api.py"])]
time.sleep(1)
for i in range(1, n + 1):
    procs.append(subprocess.Popen([sys.executable, "productor.py", f"P{i}"]))
    time.sleep(2)  # escalonado para ver cada alerta aparecer por separado

print("Sistema en marcha. Ctrl+C para detener.")
try:
    for p in procs:
        p.wait()
except KeyboardInterrupt:
    for p in procs:
        p.terminate()
