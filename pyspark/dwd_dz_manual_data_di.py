# dwd_dz_manual_data_di.py
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

if len(sys.argv) != 2:
    print("Usage: spark-submit dwd_dz_manual_data_job.py <dt>")
    sys.exit(1)

dt = sys.argv[1]

spark = SparkSession.builder \
    .appName("DWD Manual Data Job") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("hive.metastore.client.factory.class", "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory") \
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
    .enableHiveSupport() \
    .getOrCreate()

# 允许全动态分区写入
spark.sql("set hive.exec.dynamic.partition.mode=nonstrict")

# # 读单个文件看真实 Schema
    # df_raw = spark.read.parquet("s3://aws-logs-796973487589-ap-southeast-1/hive/warehouse/poker/dwd_dz_manual_data_di/dt=2025-12-24/part-00003-45da6442-0ac4-4d76-87c6-fd736f36f7f2.c000.snappy.parquet")
    # df_raw.printSchema()

ods_df = spark.table("poker.ods_dz_db_table_dz_manual_data_di") \
    .filter(col("dt") == dt) \

# === 等效 Hive UDF: ExplodeJsonArrayUDTF ===
# 1. 将 szcarddata 解析为 JSON 数组（每个元素是完整 JSON 对象）
# 2. 使用 posexplode 添加索引
# 3. 将每个对象转为字符串，并注入 json_index
dwd_df = ods_df \
    .withColumn("json_array", from_json(col("szcarddata"), ArrayType(StringType()))) \
    .select(
        "*",
        posexplode(col("json_array")).alias("json_index", "json_obj_str")
    ) \
    .withColumn("json_obj", from_json(col("json_obj_str"), MapType(StringType(), StringType()))) \
    .withColumn("carddata",
        to_json(
            map_concat(
                col("json_obj"),
                create_map(lit("json_index"), col("json_index").cast("string"))
            )
        )
    ) \
    .select(
        "id",
        "ngametype",
        "nplayerid",
        "sztoken",
        "nround",
        "nwinscore",
        "nscore",
        "sztitle",
        "szhandcard",
        "szCardData",
        "carddata",  # ← 与 Hive UDF 输出完全一致
        "createtime",
        "dt"
    )

# # # 写入目标表
dwd_df.write.mode("overwrite").insertInto("poker.dwd_dz_manual_data_di")

print(f"✅ Success for dt={dt}")
spark.stop()