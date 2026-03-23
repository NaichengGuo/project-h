from pyspark.sql import SparkSession
import re
from datetime import datetime, timedelta

# spark = SparkSession.builder \
#     .appName("Get Hive Table Comments") \
#     .enableHiveSupport() \
#     .getOrCreate()

spark = SparkSession.builder \
    .appName("Get Hive Table Comments") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("hive.metastore.client.factory.class", "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory") \
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .config("spark.network.timeout", "600s") \
    .config("spark.executor.heartbeatInterval", "120s") \
    .config("spark.sql.execution.arrow.enabled", "true") \
    .enableHiveSupport() \
    .getOrCreate()

# 计算昨天的日期
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# 1. 设置你要查询的数据库（可选，默认是 default）
db_name = "poker"  # ← 替换为你的数据库名
spark.sql(f"USE {db_name}")

# 2. 获取所有表名
print("Fetching table list...")
tables_df = spark.sql("SHOW TABLES")
table_names = [row.tableName for row in tables_df.collect()]  # 注意字段名可能是 tableName 或 tab_name

# 如果 SHOW TABLES 返回三列 (database, tableName, isTemporary)，则用 row.tableName
# 在某些版本中字段名为 'tab_name'，可打印 row.schema 确认

print(f"Found {len(table_names)} tables.")

# 3. 遍历每个表，执行 DESCRIBE FORMATTED 并提取 comment
results = []

for tbl in table_names:
    try:
        desc_df = spark.sql(f"DESCRIBE FORMATTED `{tbl}`")
        # desc_df.show(desc_df.count(), truncate=False)
        # if tbl=='dws_dz_player_collusion_cross_df':
        #     desc_df.show(desc_df.count(), truncate=False)
        rows = desc_df.collect()

        # 初始化变量
        table_comment = ""
        location = ""

        for row in rows:
            # print(row)
            col_name = str(row[0]).strip() if row[0] is not None else ""
            data_type = str(row[1]) if row[1] is not None else ""
            # print(f"Processing row: {col_name}, {data_type}")
            # comment_col = row[2]  # 暂不需要

            if col_name.upper() == "COMMENT":
                table_comment = data_type
            elif col_name == "Location":
                location = data_type

        # 根据表名前缀设置 min_dt 和 max_dt
        if tbl.startswith("ods"):
            min_dt = "2025-08-11"
        elif tbl.startswith("dwd"):
            # dwd 表一部分是 2025-08-11，其余选择 10-11 月的日期
            # 这里可以根据具体需求调整，示例：按表名哈希决定
            dwd_dates = ["2025-08-11", "2025-10-11", "2025-10-20", "2025-11-05", "2025-11-15"]
            min_dt = dwd_dates[hash(tbl) % len(dwd_dates)]
        else:
            # 其他表使用 2025-08-11 作为默认值
            min_dt = "2025-08-11"
        
        # 所有表的最新日期都是昨天
        max_dt = yesterday

        results.append((tbl, table_comment, location, min_dt, max_dt, yesterday))
        print(f"{tbl}: comment='{table_comment}', location={location}, min_dt={min_dt}, max_dt={max_dt}")

    except Exception as e:
        print(f"Error processing {tbl}: {e}")
        results.append((tbl, "", "", None, None, yesterday))

# 创建最终 DataFrame
result_df = spark.createDataFrame(results, ["table_name", "table_comment", "table_location", "min_dt", "max_dt", "dt"])
result_df.show(truncate=False)

# 可选：保存到文件或表
# result_df.write.mode("overwrite").parquet("s3://your-bucket/table_comments/")

# 写入目标表
result_df.write.mode("overwrite").insertInto("poker.table_info")
