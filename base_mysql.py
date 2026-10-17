import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from abc import ABC, abstractmethod
from pathlib import Path

# Conexion a MySQL/MariaDB (XAMPP). Se puede cambiar con variables de entorno:
#   DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")   # XAMPP usa 3306 por defecto
DB_NAME = os.environ.get("DB_NAME", "cryptobot")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Orden en que se leen las tablas (None = sin ORDER BY)
ORDEN = {"ordenes": "inicio, id_orden", "alertas": "inicio, id_alerta", "productores": "productor"}


class RepositorioMySQL:
    """Encapsula la lectura/escritura en MySQL con SQLAlchemy."""

    def __init__(self, tabla_nombre, limite=1000):
        self.engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        self.tabla_nombre = tabla_nombre
        self.limite = limite

    @staticmethod
    def _a_texto(columnas, filas):
        # Devuelve diccionarios con todo convertido a str ("" para NULL)
        return [{c: ("" if v is None else str(v)) for c, v in zip(columnas, fila)} for fila in filas]

    def leer(self):
        """Ticks: los ultimos N en orden CRONOLOGICO (el mas reciente al final)."""
        try:
            with self.engine.connect() as conn:
                if self.tabla_nombre == "ticks":
                    r = conn.execute(text(f"SELECT * FROM ticks ORDER BY id DESC LIMIT {int(self.limite)}"))
                    datos = self._a_texto(r.keys(), r.fetchall())
                    datos.reverse()
                    return datos
                orden = ORDEN.get(self.tabla_nombre)
                sql = f"SELECT * FROM {self.tabla_nombre}" + (f" ORDER BY {orden}" if orden else "")
                r = conn.execute(text(sql))
                return self._a_texto(r.keys(), r.fetchall())
        except Exception as e:
            print(f"[DB ERROR LEER {self.tabla_nombre}]: {e}")
            return []

    def guardar(self, datos):
        try:
            with self.engine.begin() as conn:
                if self.tabla_nombre == "productores":
                    for d in datos:
                        conn.execute(
                            text("INSERT INTO productores (productor, ultimo_visto, estado) "
                                 "VALUES (:p, :ts, :est) "
                                 "ON DUPLICATE KEY UPDATE ultimo_visto = VALUES(ultimo_visto), estado = VALUES(estado)"),
                            {"p": d["productor"], "ts": d["ultimo_visto"], "est": d["estado"]},
                        )
                else:
                    # DELETE + INSERT en la MISMA transaccion: la API nunca ve la tabla vacia
                    conn.execute(text(f"DELETE FROM {self.tabla_nombre}"))
                    if datos:
                        pd.DataFrame(datos).to_sql(self.tabla_nombre, conn, if_exists="append", index=False)
        except Exception as e:
            print(f"[DB ERROR GUARDAR {self.tabla_nombre}]: {e}")

    def agregar(self, registros, contar=True):
        if not registros:
            return 0
        try:
            pd.DataFrame(registros).to_sql(self.tabla_nombre, self.engine, if_exists="append", index=False)
            if not contar:
                return len(registros)
            with self.engine.connect() as conn:
                return int(conn.execute(text(f"SELECT COUNT(*) FROM {self.tabla_nombre}")).scalar())
        except Exception as e:
            print(f"[DB ERROR AGREGAR {self.tabla_nombre}]: {e}")
            return 0


class ComponenteBase(ABC):
    """Clase base abstracta con soporte para logs y ejecucion en bucle."""

    def __init__(self, nombre, log_file="logs/precios.log", intervalo=1.0):
        self.nombre = nombre
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.intervalo = intervalo
        self.activo = False

    def log(self, mensaje):
        print(f"[{self.nombre}] {mensaje}")

    @abstractmethod
    def paso(self):
        pass

    def ejecutar(self):
        self.activo = True
        self.log("Iniciando ejecucion...")
        try:
            while self.activo:
                try:
                    self.paso()
                except Exception as e:
                    self.log(f"ERROR: {e}")
                time.sleep(self.intervalo)
        except KeyboardInterrupt:
            self.activo = False
            self.log("Detenido por el usuario.")
