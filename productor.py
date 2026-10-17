import random
import sys
from datetime import datetime
from base_mysql import ComponenteBase, RepositorioMySQL


class Productor(ComponenteBase):
    """Genera ticks de precios y los guarda en MySQL."""

    CRIPTOS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    PRECIOS_INICIALES = {"BTC/USDT": 51500.0, "ETH/USDT": 2400.0, "SOL/USDT": 116.0}

    def __init__(self, productor_id="P1", log_file="logs/precios.log", intervalo=0.3):
        super().__init__(f"PRODUCTOR {productor_id}", log_file, intervalo)
        self.productor_id = productor_id
        self.repo_ticks = RepositorioMySQL("ticks", limite=1000)
        self.repo_productores = RepositorioMySQL("productores", limite=50)
        self.base = {c: p * random.uniform(0.995, 1.005) for c, p in self.PRECIOS_INICIALES.items()}
        self.precios = dict(self.base)

    def _variacion(self, cripto):
        ruido = random.gauss(0, 0.002)
        retorno = (self.base[cripto] - self.precios[cripto]) / self.base[cripto] * 0.01
        if random.random() < 0.02:
            ruido += random.choice([-1, 1]) * random.uniform(0.01, 0.025)
        return ruido + retorno

    def generar_tick(self):
        cripto = random.choice(self.CRIPTOS)
        self.precios[cripto] = round(self.precios[cripto] * (1 + self._variacion(cripto)), 2)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        volumen = round(random.uniform(1, 10), 2)
        
        tick_data = {
            "ts": ts,
            "cripto": cripto,
            "precio": float(self.precios[cripto]),
            "volumen": float(volumen),
            "productor": self.productor_id
        }
        
        linea_log = f"{ts}|{cripto}|{self.precios[cripto]}|{volumen}|{self.productor_id}"
        return tick_data, linea_log

    def paso(self):
        tick_data, linea_log = self.generar_tick()
        # Guardar tick en MySQL
        self.repo_ticks.agregar([tick_data], contar=False)

        # Latido del productor (siempre en minusculas: "activo"); lo lee el consumidor y el dashboard
        self.repo_productores.guardar([{
            "productor": self.productor_id,
            "ultimo_visto": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado": "activo"
        }])
        print(f"  -> {linea_log}")


if __name__ == "__main__":
    Productor(sys.argv[1] if len(sys.argv) > 1 else "P1").ejecutar()