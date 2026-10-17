# Crypto Bot — cómo abrirlo en Windows

## Requisitos (una sola vez)
1. **Python 3.10 o superior** (https://www.python.org). Al instalar, marca *"Add Python to PATH"*.
2. **XAMPP** (https://www.apachefriends.org).

## Pasos
1. Abre el **Panel de control de XAMPP** y pulsa **Start** en **MySQL** (debe quedar en verde).
   Fíjate en el número de **puerto** que aparece junto a MySQL (normalmente `3306`).
2. Descomprime esta carpeta y haz **doble clic en `iniciar.bat`**. Ese archivo:
   - crea el entorno virtual e instala las dependencias,
   - crea la base de datos `cryptobot` y sus 4 tablas (`schema.sql`),
   - arranca el consumidor, la API y 2 productores,
   - abre el navegador en **http://localhost:5000**.
3. Para ver una alerta de "nuevo productor", abre otra terminal en esta carpeta y ejecuta:
   ```
   .venv\Scripts\activate
   python productor.py P3
   ```
4. Para detener todo: cierra la ventana negra o presiona `Ctrl+C`.

## Si algo falla
| Síntoma | Solución |
|---|---|
| `No se pudo conectar a MySQL` | MySQL no está iniciado en XAMPP, o el puerto es distinto. Edita `DB_PORT` en `iniciar.bat`. |
| `Access denied for user 'root'` | Tu root tiene contraseña: ponla en `DB_PASSWORD` dentro de `iniciar.bat`. |
| La página abre pero todo está en 0 | Espera ~15 s: las alertas y compras necesitan algunos datos acumulados. |
| `python` no se reconoce | Reinstala Python marcando *Add to PATH*, o edita `iniciar.bat` y usa `py`. |
| No abre desde otro dispositivo | Permite Python en el Firewall de Windows (puerto 5000). |

## Archivos
- `productor.py` genera precios simulados (BTC, ETH, SOL) y los guarda en MySQL. `python productor.py P3` añade otro productor.
- `consumidor.py` decide las compras; `alertas.py` genera las alertas.
- `api.py` + `dashboard.html` muestran todo en el navegador.
- `analisis_spark.py` / `procesador_spark.py` son análisis opcionales con PySpark (requieren Java: `pip install pyspark`).
