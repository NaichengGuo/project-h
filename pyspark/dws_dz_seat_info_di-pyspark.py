import sys
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import (
    col, udf, get_json_object, explode, lit, substring, when, 
    regexp_replace, split, posexplode, sum, last, coalesce, 
    size, collect_set, row_number, array
)
from pyspark.sql.types import StringType, ArrayType

## 建表语句
# CREATE EXTERNAL TABLE IF NOT EXISTS `poker.dws_dz_seat_info_di` (
#   `createdate` string COMMENT '日期，格式 yyyy-MM-dd',
#   `sztoken` string COMMENT '对应游戏桌的 szToken',
#   `nround` int COMMENT '第几手',
#   `gametype` int COMMENT '游戏类型',
#   `playerid` STRING COMMENT '玩家ID（非旁观者）',
#   `seat` string COMMENT '座位信息'
# )
# COMMENT 'dws层：牌谱中每手牌的玩家座位明细表'
# PARTITIONED BY (
#   `dt` string COMMENT '分区字段，格式 yyyy-MM-dd'
# )
# STORED AS PARQUET
# LOCATION 's3://aws-logs-796973487589-ap-southeast-1/hive/warehouse/poker/dws_dz_seat_info_di'
# TBLPROPERTIES (
#   'aws.spark.fgac.transient.isRegisteredWithLakeFormation'='false',
#   'bucketing_version'='2',
#   'transient_lastDdlTime'='1766820051'
# );

# Initialize Spark
spark = SparkSession.builder \
    .appName("SparkSQLConversion") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("spark.sql.warehouse.dir", "s3://aws-logs-796973487589-ap-southeast-1/hive/warehouse") \
    .config("spark.hadoop.hive.metastore.client.factory.class", "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory") \
    .enableHiveSupport() \
    .getOrCreate()

# UDF Definition: explode_json_array
# 参考 spark-test.py 中的实现
def explode_json_array(json_array_str):
    if json_array_str is None:
        return []
    try:
        json_array = json.loads(json_array_str)
        if isinstance(json_array, list):
            result = []
            for i, item in enumerate(json_array):
                if isinstance(item, dict):
                    item['json_index'] = i
                    result.append(json.dumps(item))
            return result
        else:
            return []
    except Exception:
        return []

explode_json_array_udf = udf(explode_json_array, ArrayType(StringType()))

# Parameters
if len(sys.argv) > 1:
    dt_val = sys.argv[1]
else:
    dt_val = (datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(hours=24)).strftime('%Y-%m-%d')

# Load Data
# dwd_df = spark.table("poker.dwd_dz_manual_data_di").filter(col("dt") == dt_val)
# score_detail_df = spark.table("poker.ods_dz_db_table_dz_game_score_detail_df").filter(col("dt") == dt_val)

dwd_df = spark.sql(f"""
select 
  CreateTime,playerid,
  sztoken,nround,gametype
  ,case when (substr(json_data,1,1)=='[')  then json_data
  else get_json_object(json_data,'$.data')
  end as json_data,dt
from 
(
select *,get_json_object(carddata,'$.data') as json_data,carddata
from 
poker.dwd_dz_manual_data_di 
where dt='{dt_val}' 
and get_json_object(carddata,'$.name')='SeatInfos'
and playerid<>0
)t
""")

result_df = dwd_df.withColumn("SeatInfo", explode(explode_json_array_udf(col("json_data"))))\
            .select(
            substring(col("CreateTime"), 1, 10).alias("createdate"),
            col("sztoken"),
            col("nround"),
            col("gametype"),
            get_json_object(col("SeatInfo"), "$.nPlayerId").alias("playerid"),
            get_json_object(col("SeatInfo"), "$.seat").alias("seat"),
            col("dt")
        )
result_df.show()
spark.conf.set("hive.exec.dynamic.partition.mode", "nonstrict")
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
result_df.write.mode("overwrite").insertInto("poker.dws_dz_seat_info_di")
