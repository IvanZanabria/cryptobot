import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max, min, stddev

def ejecutar_procesamiento_spark():
    # Inicializar la sesión de Spark con el driver JDBC de MySQL
    spark = SparkSession.builder \
        .appName("CryptoBotSparkAnalytics") \
        .config("spark.jars.packages", "com.mysql:mysql-connector-j:8.3.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    jdbc_url = (f"jdbc:mysql://{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '3306')}"
                f"/{os.environ.get('DB_NAME', 'cryptobot')}"
                f"?user={os.environ.get('DB_USER', 'root')}&password={os.environ.get('DB_PASSWORD', '')}")

    # Leer la tabla de ticks de MySQL en un DataFrame distribuido de Spark
    df_ticks = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "ticks") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()

    print("=== [SPARK] DATOS CARGADOS DESDE MYSQL ===")
    df_ticks.printSchema()

    # Calcular estadísticas avanzadas distribuidas por Cripto y Productor
    print("=== [SPARK] ESTADÍSTICAS DE PRECIOS POR PRODUCTOR ===")
    df_stats = df_ticks.groupBy("cripto", "productor") \
        .agg(
            avg("precio").alias("precio_promedio"),
            max("precio").alias("precio_maximo"),
            min("precio").alias("precio_minimo"),
            stddev("precio").alias("desviacion_estandar")
        )

    df_stats.show(truncate=False)

if __name__ == "__main__":
    ejecutar_procesamiento_spark()