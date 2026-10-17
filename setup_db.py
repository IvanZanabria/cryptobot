"""Crea la base de datos 'cryptobot' y sus tablas leyendo schema.sql.
Uso: python setup_db.py
"""
import os
import re
import sys
from pathlib import Path

import pymysql

HOST = os.environ.get("DB_HOST", "localhost")
PORT = int(os.environ.get("DB_PORT", "3306"))
USER = os.environ.get("DB_USER", "root")
PASSWORD = os.environ.get("DB_PASSWORD", "")

try:
    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, charset="utf8mb4")
except Exception as e:
    print(f"\n[ERROR] No se pudo conectar a MySQL en {HOST}:{PORT} con el usuario '{USER}'.\n  Detalle: {e}\n")
    print("Revisa que:\n"
          "  1. En XAMPP el modulo MySQL este en verde (Start).\n"
          "  2. El puerto sea el correcto. XAMPP usa 3306 por defecto; si el tuyo es otro\n"
          "     (se ve en el panel de XAMPP junto a MySQL), cambia DB_PORT en iniciar.bat.\n"
          "  3. Si tu root tiene contrasena, ponla en DB_PASSWORD en iniciar.bat.")
    sys.exit(1)

sql = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
sql = re.sub(r"--.*", "", sql)  # quitar comentarios
with conn.cursor() as cur:
    for sentencia in (s.strip() for s in sql.split(";")):
        if sentencia:
            cur.execute(sentencia)
conn.commit()
conn.close()
print(f"[OK] Base de datos 'cryptobot' lista en {HOST}:{PORT}")
