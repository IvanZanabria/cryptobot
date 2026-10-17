import time
from datetime import datetime

from alertas import GestorAlertas
from base_mysql import ComponenteBase, RepositorioMySQL


class Tick:
    """Una representación del tick proveniente de la base de datos."""

    def __init__(self, ts, cripto, precio, productor):
        self.ts = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S") if isinstance(ts, str) else ts
        self.cripto = cripto
        self.precio = float(precio)
        self.productor = productor

    @classmethod
    def desde_dict(cls, d):
        return cls(d["ts"], d["cripto"], d["precio"], d["productor"])


class Consumidor(ComponenteBase):
    """Evalúa la regla de compra y delega alertas usando MySQL."""

    def __init__(self, log_file="logs/precios.log", ventana=300, umbral=0.999, cooldown_ordenes=30, intervalo=1.0):
        super().__init__("CONSUMIDOR", log_file, intervalo)
        self.repo_ticks = RepositorioMySQL("ticks", limite=ventana)
        self.repo_ordenes = RepositorioMySQL("ordenes", limite=1000)
        self.gestor = GestorAlertas(
            RepositorioMySQL("alertas", limite=200),
            RepositorioMySQL("productores", limite=50)
        )
        self.ventana = ventana
        self.umbral = umbral
        self.cooldown_ordenes = cooldown_ordenes
        self._ultima_orden = {}

    def leer_ticks(self):
        registros = self.repo_ticks.leer()
        if not registros:
            return []
        return [Tick.desde_dict(r) for r in registros]

    def generar_ordenes(self, ticks):
        grupos = {}
        for t in ticks:
            grupos.setdefault((t.cripto, t.productor), []).append(t.precio)
        ordenes = []
        for (cripto, productor), precios in grupos.items():
            promedio = sum(precios) / len(precios)
            actual = precios[-1]
            ya_comprada = time.time() - self._ultima_orden.get((cripto, productor), 0) < self.cooldown_ordenes
            
            if actual <= promedio * self.umbral and not ya_comprada:
                self._ultima_orden[(cripto, productor)] = time.time()
                descuento = round((1 - actual / promedio) * 100, 2)
                ordenes.append({
                    "id_orden": f"ORD-{int(time.time()*1000)}-{cripto.split('/')[0]}-{productor}",
                    "cripto": cripto,
                    "productor": productor,
                    "operacion": "COMPRA",
                    "precio_ejecucion": round(actual, 2),
                    "precio_promedio": round(promedio, 2),
                    "descuento": f"{descuento}%",
                    "inicio": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "estado": "EJECUTADA",
                })
        return ordenes

    def paso(self):
        ticks = self.leer_ticks()
        if not ticks:
            return
        for a in self.gestor.procesar(ticks):
            self.log(f"[ALERTA {a['severidad'].upper()}] {a['mensaje']}")
        ordenes = self.generar_ordenes(ticks)
        if ordenes:
            total = self.repo_ordenes.agregar(ordenes)
            self.log(f"[COMPRA] {len(ordenes)} nueva(s) compra(s) | Total acumulado: {total}")


if __name__ == "__main__":
    Consumidor().ejecutar()