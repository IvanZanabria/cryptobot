import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from base_mysql import RepositorioMySQL

try:
    from flask_cors import CORS
except ImportError:
    CORS = None


class ApiServidor:
    """Servidor Flask público que expone órdenes, alertas y logs desde MySQL."""

    def __init__(self, host=None, port=None, log_file="logs/precios.log"):
        self.host = host or os.environ.get("API_HOST", "0.0.0.0")
        self.port = int(port or os.environ.get("API_PORT", "5000"))
        
        self.repo_ordenes = RepositorioMySQL("ordenes")
        self.repo_alertas = RepositorioMySQL("alertas")
        self.repo_productores = RepositorioMySQL("productores")
        self.repo_ticks = RepositorioMySQL("ticks", limite=100)
        
        self.log_file = Path(log_file)
        self.app = Flask(__name__)
        if CORS:
            CORS(self.app)
        self._registrar_rutas()

    def _registrar_rutas(self):
        self.app.add_url_rule("/api/ordenes", "ordenes", lambda: jsonify(self.repo_ordenes.leer()))
        self.app.add_url_rule("/api/alertas", "alertas", lambda: jsonify(self.repo_alertas.leer()))
        self.app.add_url_rule("/api/productores", "productores", lambda: jsonify(self.repo_productores.leer()))
        self.app.add_url_rule("/api/logs", "logs", self.logs)
        self.app.add_url_rule("/", "index", lambda: send_from_directory(".", "dashboard.html"))

    def logs(self):
        """Ultimos 100 ticks (desde MySQL) con el formato que lee el dashboard."""
        ticks = self.repo_ticks.leer()
        return jsonify([f"{t['ts']}|{t['cripto']}|{t['precio']}|{t['volumen']}|{t['productor']}" for t in ticks])

    def ejecutar(self):
        print(f"[API] Escuchando públicamente en http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True)


if __name__ == "__main__":
    ApiServidor().ejecutar()