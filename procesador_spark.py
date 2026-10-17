import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, window, current_timestamp

def ejecutar_analisis_spark():
    # Inicializar Spark con el conector JDBC de MySQL
    spark = SparkSession.builder \
        .appName("CryptoBotSparkAnalytics") \
        .config("spark.jars.packages", "com.mysql:mysql-connector-j:8.3.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    # Leer datos directamente desde MySQL vía JDBC
    jdbc_url = (f"jdbc:mysql://{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '3306')}"
                f"/{os.environ.get('DB_NAME', 'cryptobot')}"
                f"?user={os.environ.get('DB_USER', 'root')}&password={os.environ.get('DB_PASSWORD', '')}")
    
    df_ticks = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "ticks") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()

    print("--- [SPARK] Datos leídos desde MySQL exitosamente ---")
    df_ticks.printSchema()

    # Ejemplo de procesamiento con Spark: Promedio por Cripto y Productor
    df_promedios = df_ticks.groupBy("cripto", "productor") \
        .agg(avg("precio").alias("precio_promedio"))

    df_promedios.show()

if __name__ == "__main__":
    ejecutar_analisis_spark()