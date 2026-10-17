"""Sistema de alertas: precios (caida, subida, divergencia) y estado de productores."""
import time
from datetime import datetime

FMT = "%Y-%m-%d %H:%M:%S"


class GestorAlertas:
    """Recibe los ticks recientes (en orden cronologico, el mas nuevo al final)
    y genera/resuelve alertas.

    Tipos:  CAIDA_PRECIO, SUBIDA_PRECIO, DIVERGENCIA,
            NUEVO_PRODUCTOR, PRODUCTOR_INACTIVO, PRODUCTOR_RECUPERADO
    Gravedad: info | advertencia | critica
    Estado:   activa | resuelta
    """

    TIPOS_EVENTO = ("NUEVO_PRODUCTOR", "PRODUCTOR_RECUPERADO")  # caducan solos
    SEGUNDOS_EVENTO = 30
    MIN_MUESTRAS = 10  # ticks minimos de una serie para comparar contra su promedio

    def __init__(self, repo_alertas, repo_productores, umbral_caida=0.01,
                 umbral_critica=0.03, umbral_subida=0.01, umbral_divergencia=0.02,
                 timeout_productor=10, cooldown=30):
        self.repo_alertas = repo_alertas
        self.repo_productores = repo_productores
        self.umbral_caida = umbral_caida
        self.umbral_critica = umbral_critica
        self.umbral_subida = umbral_subida
        self.umbral_divergencia = umbral_divergencia
        self.timeout_productor = timeout_productor
        self.cooldown = cooldown

        self.alertas = repo_alertas.leer()
        for a in self.alertas:  # la BD devuelve "" para NULL: volver a None
            for k in ("cripto", "productor", "resuelta_en"):
                if a.get(k) == "":
                    a[k] = None
        # Estado de cada productor segun ESTE gestor: "activo" | "inactivo"
        self.estado_prod = {}
        self._contador = 0
        self._ultimo_disparo = {}  # clave -> instante del ultimo disparo (cooldown)

    # ---------- utilidades ----------
    @staticmethod
    def _clave(tipo, cripto, productor):
        return (tipo, cripto or "", productor or "")

    def _activa(self, clave):
        for a in self.alertas:
            if a.get("estado") == "activa" and self._clave(
                    a["tipo"], a.get("cripto"), a.get("productor")) == clave:
                return a
        return None

    def _crear(self, tipo, severidad, mensaje, cripto=None, productor=None, estado="activa"):
        self._contador += 1
        alerta = {
            "id_alerta": f"ALT-{int(time.time()*1000)}-{self._contador}",
            "tipo": tipo,
            "severidad": severidad,
            "cripto": cripto,
            "productor": productor,
            "mensaje": mensaje,
            "estado": estado,
            "inicio": time.strftime(FMT),
            "resuelta_en": None,
        }
        self.alertas.append(alerta)
        return alerta

    def _resolver(self, alerta):
        alerta["estado"] = "resuelta"
        alerta["resuelta_en"] = time.strftime(FMT)

    def _puede_disparar(self, clave):
        if self._activa(clave):
            return False
        return time.time() - self._ultimo_disparo.get(clave, 0) >= self.cooldown

    def _disparar(self, nuevas, clave, *args, **kwargs):
        self._ultimo_disparo[clave] = time.time()
        nuevas.append(self._crear(*args, **kwargs))

    def _ya_anunciado(self, prod):
        return any(a["tipo"] == "NUEVO_PRODUCTOR" and a.get("productor") == prod for a in self.alertas)

    # ---------- reglas ----------
    def _revisar_productores(self, ticks, ahora, nuevas):
        # Ultima actividad = lo mas reciente entre el latido (tabla productores) y los ticks
        ultimo = {}
        for p in self.repo_productores.leer():
            try:
                ultimo[p["productor"]] = datetime.strptime(p["ultimo_visto"], FMT)
            except (ValueError, KeyError):
                pass
        for t in ticks:  # cronologico: el ultimo de cada productor es el mas reciente
            if t.productor not in ultimo or t.ts > ultimo[t.productor]:
                ultimo[t.productor] = t.ts

        for prod, ts in ultimo.items():
            viejo = (ahora - ts).total_seconds() > self.timeout_productor
            antes = self.estado_prod.get(prod)

            if antes is None:  # primera vez que este gestor ve al productor
                self.estado_prod[prod] = "inactivo" if viejo else "activo"
                if not viejo and not self._ya_anunciado(prod):
                    nuevas.append(self._crear("NUEVO_PRODUCTOR", "info",
                                              f"Nuevo productor conectado: {prod}", productor=prod))
                elif viejo and not self._activa(self._clave("PRODUCTOR_INACTIVO", None, prod)):
                    nuevas.append(self._crear(
                        "PRODUCTOR_INACTIVO", "critica",
                        f"Productor {prod} sin datos hace mas de {self.timeout_productor} s", productor=prod))

            elif antes == "inactivo" and not viejo:
                self.estado_prod[prod] = "activo"
                a = self._activa(self._clave("PRODUCTOR_INACTIVO", None, prod))
                if a:
                    self._resolver(a)
                nuevas.append(self._crear("PRODUCTOR_RECUPERADO", "info",
                                          f"Productor {prod} volvio a enviar datos", productor=prod))

            elif antes == "activo" and viejo:
                self.estado_prod[prod] = "inactivo"
                nuevas.append(self._crear(
                    "PRODUCTOR_INACTIVO", "critica",
                    f"Productor {prod} sin datos hace mas de {self.timeout_productor} s", productor=prod))
                # El dashboard lee el estado de la tabla productores
                self.repo_productores.guardar([{"productor": prod, "estado": "inactivo",
                                                "ultimo_visto": ts.strftime(FMT)}])

    def _revisar_precios(self, ticks, nuevas):
        series = {}
        for t in ticks:
            if self.estado_prod.get(t.productor) == "inactivo":
                continue  # no alertar precios de un productor caido
            series.setdefault((t.cripto, t.productor), []).append(t.precio)

        for (cripto, prod), precios in series.items():
            if len(precios) < self.MIN_MUESTRAS:
                continue
            promedio = sum(precios) / len(precios)
            actual = precios[-1]  # el mas reciente
            var = actual / promedio - 1

            # CAIDA
            clave = self._clave("CAIDA_PRECIO", cripto, prod)
            if var <= -self.umbral_caida:
                if self._puede_disparar(clave):
                    sev = "critica" if var <= -self.umbral_critica else "advertencia"
                    self._disparar(nuevas, clave, "CAIDA_PRECIO", sev,
                                   f"{cripto} cayo {abs(var)*100:.2f}% bajo su promedio "
                                   f"(${actual:,.2f} vs ${promedio:,.2f}) · {prod}",
                                   cripto=cripto, productor=prod)
            elif var > -self.umbral_caida / 2:
                a = self._activa(clave)
                if a:
                    self._resolver(a)

            # SUBIDA
            clave = self._clave("SUBIDA_PRECIO", cripto, prod)
            if var >= self.umbral_subida:
                if self._puede_disparar(clave):
                    self._disparar(nuevas, clave, "SUBIDA_PRECIO", "info",
                                   f"{cripto} subio {var*100:.2f}% sobre su promedio "
                                   f"(${actual:,.2f} vs ${promedio:,.2f}) · {prod}",
                                   cripto=cripto, productor=prod)
            elif var < self.umbral_subida / 2:
                a = self._activa(clave)
                if a:
                    self._resolver(a)

        # DIVERGENCIA entre productores activos
        ultimos = {}
        for (cripto, prod), precios in series.items():
            ultimos.setdefault(cripto, {})[prod] = precios[-1]
        for cripto, por_prod in ultimos.items():
            clave = self._clave("DIVERGENCIA", cripto, "")
            if len(por_prod) < 2:
                continue
            (p_min, v_min), (p_max, v_max) = (min(por_prod.items(), key=lambda x: x[1]),
                                              max(por_prod.items(), key=lambda x: x[1]))
            dif = v_max / v_min - 1
            if dif >= self.umbral_divergencia:
                if self._puede_disparar(clave):
                    self._disparar(nuevas, clave, "DIVERGENCIA", "advertencia",
                                   f"{cripto}: {p_max} cotiza {dif*100:.2f}% mas caro que {p_min} "
                                   f"(${v_max:,.2f} vs ${v_min:,.2f})", cripto=cripto)
            elif dif < self.umbral_divergencia / 2:
                a = self._activa(clave)
                if a:
                    self._resolver(a)

    def _caducar_eventos(self, ahora):
        """Las alertas informativas de un solo evento se resuelven solas."""
        for a in self.alertas:
            if a.get("estado") == "activa" and a["tipo"] in self.TIPOS_EVENTO:
                try:
                    inicio = datetime.strptime(a["inicio"], FMT)
                except ValueError:
                    continue
                if (ahora - inicio).total_seconds() > self.SEGUNDOS_EVENTO:
                    self._resolver(a)

    # ---------- punto de entrada ----------
    def procesar(self, ticks):
        """Evalua todas las reglas. Devuelve la lista de alertas nuevas."""
        ahora = datetime.now()
        nuevas = []
        antes = [(a["id_alerta"], a.get("estado")) for a in self.alertas]

        self._caducar_eventos(ahora)
        self._revisar_productores(ticks, ahora, nuevas)
        self._revisar_precios(ticks, nuevas)

        self.alertas = self.alertas[-200:]
        if nuevas or antes != [(a["id_alerta"], a.get("estado")) for a in self.alertas[:len(antes)]] \
                or len(self.alertas) != len(antes):
            self.repo_alertas.guardar(self.alertas)
        return nuevas
