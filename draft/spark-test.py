from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, get_json_object, explode, lit, substring
from pyspark.sql.types import StringType, ArrayType, StructType, StructField
import json

# 配置 SparkSession 使用 Glue Catalog 作为 Hive 数据库的元数据存储
spark = SparkSession.builder \
    .appName("GlueMetastoreExample") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("spark.sql.warehouse.dir", "s3://aws-logs-796973487589-ap-southeast-1/hive/warehouse") \
    .config("spark.hadoop.hive.metastore.client.factory.class", "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory") \
    .enableHiveSupport() \
    .getOrCreate()

# 定义explode_json_array的等效UDF
def explode_json_array(json_array_str):
    """
    模拟Hive的explode_json_array UDF功能
    参考: /mnt/workspace/udf.java
    逻辑: 解析JSON数组, 遍历每个对象, 添加json_index字段, 并返回JSON字符串列表
    """
    if json_array_str is None:
        return []
    try:
        # 解析JSON数组字符串
        json_array = json.loads(json_array_str)
        if isinstance(json_array, list):
            result = []
            for i, item in enumerate(json_array):
                # Java UDF中使用 JSON.parseObject, 假定元素为JSON对象
                if isinstance(item, dict):
                    item['json_index'] = i
                    result.append(json.dumps(item))
                # 注意: Java代码中如果元素不是对象会抛出异常中断处理
                # 这里我们仅处理是字典的项，忽略非字典项以保持稳健性
            return result
        else:
            return []
    except Exception:
        # 解析失败返回空列表
        return []

# 注册explode_json_array UDF
explode_json_array_udf = udf(explode_json_array, ArrayType(StringType()))

# 使用PySpark DataFrame API实现指定的SQL逻辑
print("Executing PySpark implementation...")

df = spark.sql("""select *,get_json_object(carddata,'$.data') as data from poker.dwd_dz_manual_data_di where dt='2025-12-25' limit 10""")

result_df = df.withColumn("SeatInfo", explode(explode_json_array_udf(col("data")))) \
    .select(
        #substring(col("CreateTime"), 1, 10).alias("createdate"),
        col("sztoken"),
        col("nround"),
        col("gametype"),
        get_json_object(col("SeatInfo"), "$.nPlayerId").alias("playerid"),
        get_json_object(col("SeatInfo"), "$.seat").alias("seat")
    )

# 展示结果
result_df.show(10, truncate=False)

