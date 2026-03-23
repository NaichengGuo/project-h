import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json

if len(sys.argv) == 2:
    dt = sys.argv[1]
elif len(sys.argv) == 1:
    dt = (datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=1)).strftime("%Y-%m-%d")
else:
    raise SystemExit("Usage: spark-submit xxx.py <dt>")

spark = SparkSession.builder \
    .appName("DWS_DZ_Player_Action_DI") \
    .config("spark.executor.memory", "8g") \
    .config("spark.executor.memoryOverhead", "1g") \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.cores", "4") \
    .config("spark.executor.instances", "4") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("hive.metastore.client.factory.class", "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory") \
    .config("spark.hadoop.hive.exec.dynamic.partition.mode", "nonstrict") \
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
    .enableHiveSupport() \
    .getOrCreate()

def pick_col(df, *candidates):
    for name in candidates:
        if name in df.columns:
            return col(name)
    raise ValueError(f"Missing columns, tried: {candidates}")

# 读取源表 dwd_dz_manual_data_di
dwd_src_df = spark.table("poker.dwd_dz_manual_data_di").filter(col("dt") == dt)
dwd_df = dwd_src_df.select(
    pick_col(dwd_src_df, "createtime", "CreateTime").alias("CreateTime"),
    col("sztoken"),
    col("nround"),
    pick_col(dwd_src_df, "gametype", "ngametype").alias("gametype"),
    pick_col(dwd_src_df, "playerid", "nplayerid").alias("playerid"),
    pick_col(dwd_src_df, "carddata", "CardData").alias("CardData"),
    col("dt")
)

# 读取源表 ods_dz_db_table_dz_game_score_detail_df
game_score_src_df = spark.table("poker.ods_dz_db_table_dz_game_score_detail_df").filter(col("dt") == dt)
game_score_df = game_score_src_df.select(
    col("sztoken"),
    col("nround"),
    pick_col(game_score_src_df, "nplayerid", "playerid").alias("playerid"),
    col("gameresult")
).dropDuplicates(["sztoken", "nround", "playerid", "gameresult"])

# Step 1: 处理有 seat 的数据 (对应 Hive 中的第一个子查询 a)
# 首先，从 CardData 中提取需要的字段
dwd_with_fields = dwd_df.select(
    col("CreateTime"),
    col("sztoken"),
    col("nround"),
    col("gametype"),
    col("playerid"),
    col("CardData"),
    get_json_object(col("CardData"), "$.name").alias("action_name"),
    get_json_object(col("CardData"), "$.json_index").alias("json_index_raw")
).filter(col("playerid") != 0)

# 提取 seat 字段 (根据 action_name 不同而不同)
dwd_with_seat = dwd_with_fields.withColumn(
    "seat",
    when(col("action_name") == "S2CStatePlayerOp", get_json_object(col("CardData"), "$.data.curSeat"))
    .when(col("action_name") == "S2CStateBuyInsure", get_json_object(get_json_object(col("CardData"), "$.data.seatInfos[0]"), "$.seat"))
    .otherwise(get_json_object(col("CardData"), "$.data.seat"))
).filter(
    col("action_name").isin([
        'S2CDelayOpTime',
        'S2CGiveUp',
        'S2CStatePlayerOp',
        'S2CBuyInsure',
        'S2CDealTwiceOp',
        'S2CPushBet',
        'S2CShowHandCard',
        'S2CShowMyCard',
        'S2CStateBuyInsure',
        'S2CUpdateScore'
    ])
)

# 提取其他字段
dwd_with_all_fields = dwd_with_seat.select(
    col("CreateTime"),
    col("sztoken"),
    col("nround"),
    col("gametype"),
    col("playerid"),
    col("seat"),
    col("json_index_raw"),
    get_json_object(col("CardData"), "$.data.minBetScore").alias("minbetscore"),
    get_json_object(col("CardData"), "$.data.maxBetScore").alias("maxbetscore"),
    get_json_object(col("CardData"), "$.data.minAddScore").alias("minaddscore"),
    col("action_name").alias("action"),
    get_json_object(col("CardData"), "$.data.seatBetState").cast("int").alias("seatbetstate"),
    get_json_object(col("CardData"), "$.data.betScore").alias("betscore"),
    get_json_object(col("CardData"), "$.data.seatCurBet").alias("seatcurbet"),
    get_json_object(col("CardData"), "$.data.poolScore").alias("poolscore"),
    when(col("action_name") == "S2CStateBuyInsure", 1).otherwise(0).alias("isjumpinsure")
).filter(col("seat").isNotNull())

# 去重 (group by) - 在 PySpark 中我们用 distinct() 或者 dropDuplicates()
dwd_with_all_fields_distinct = dwd_with_all_fields.dropDuplicates([
    "sztoken", "nround", "seat", "json_index_raw", "minbetscore", "maxbetscore", "minaddscore",
    "action", "seatbetstate", "betscore", "seatcurbet", "poolscore", "isjumpinsure"
])

# Step 2: 处理无 seat 的数据 (对应 Hive 中的第二个子查询 a)
dwd_no_seat = dwd_with_fields.filter(
    ~col("action_name").isin([
        'S2CDelayOpTime',
        'S2CGiveUp',
        'S2CStatePlayerOp',
        'S2CBuyInsure',
        'S2CDealTwiceOp',
        'S2CPushBet',
        'S2CShowHandCard',
        'S2CShowMyCard',
        'S2CStateBuyInsure',
        'S2CUpdateScore',
        'RoomInfos',
        'SeatInfos'
    ])
).withColumn(
    "commonCards",
    when(col("action_name") == "S2CStateDealCard", regexp_replace(regexp_replace(get_json_object(col("CardData"), "$.data.commonCards"), r"\\[", ""), r"\\]", "")).otherwise(lit(None))
).select(
    col("CreateTime"),
    col("sztoken"),
    col("nround"),
    col("gametype"),
    col("playerid"),
    col("json_index_raw"),
    get_json_object(col("CardData"), "$.data.minBetScore").alias("minbetscore"),
    get_json_object(col("CardData"), "$.data.maxBetScore").alias("maxbetscore"),
    get_json_object(col("CardData"), "$.data.minAddScore").alias("minaddscore"),
    col("action_name").alias("action"),
    get_json_object(col("CardData"), "$.data.seatBetState").cast("int").alias("seatbetstate"),
    get_json_object(col("CardData"), "$.data.betScore").alias("betscore"),
    get_json_object(col("CardData"), "$.data.seatCurBet").alias("seatcurbet"),
    get_json_object(col("CardData"), "$.data.poolScore").alias("poolscore"),
    when(col("action_name") == "S2CStateBuyInsure", 1).otherwise(0).alias("isjumpinsure"),
    col("commonCards")
).dropDuplicates([
    "sztoken", "nround", "json_index_raw", "minbetscore", "maxbetscore", "minaddscore",
    "action", "seatbetstate", "betscore", "seatcurbet", "poolscore", "isjumpinsure", "commonCards"
])

# Step 3: 从 SeatInfos 中提取玩家座位信息 (对应 Hive 中的 b 子查询)
seat_info_df = dwd_df.filter(
    (get_json_object(col("CardData"), "$.name") == "SeatInfos") &
    (col("playerid") != 0)
).select(
    substring(col("CreateTime"), 1, 10).alias("createdate"),
    col("sztoken"),
    col("nround"),
    col("gametype"),
    get_json_object(col("CardData"), "$.data").alias("seat_data_raw")
)

seat_info_schema = ArrayType(StructType([
    StructField("nPlayerId", LongType(), True),
    StructField("seat", LongType(), True),
]))

seat_info_exploded = seat_info_df.withColumn(
    "seat_data",
    when(substring(col("seat_data_raw"), 1, 1) == "[", col("seat_data_raw")).otherwise(get_json_object(col("seat_data_raw"), "$.data"))
).withColumn(
    "seat_info_arr",
    explode(from_json(col("seat_data"), seat_info_schema))
).select(
    col("createdate"),
    col("sztoken"),
    col("nround"),
    col("gametype"),
    col("seat_info_arr.nPlayerId").cast("string").alias("playerid"),
    col("seat_info_arr.seat").cast("string").alias("seat")
).filter(
    col("playerid").isNotNull() & col("seat").isNotNull()
).dropDuplicates([
    "createdate", "sztoken", "nround", "gametype", "playerid", "seat"
])

# Step 4: 合并有 seat 和无 seat 的数据，并关联座位信息
# 4.1 有 seat 的数据与座位信息关联
a_has_seat = dwd_with_all_fields_distinct.alias("a_has_seat")
b_seat_info = seat_info_exploded.alias("b_seat_info")

has_seat_joined = a_has_seat.join(
    b_seat_info,
    on=["sztoken", "nround", "seat"],
    how="inner"
).select(
    col("b_seat_info.createdate").alias("createdate"),
    col("a_has_seat.sztoken").alias("sztoken"),
    col("a_has_seat.nround").alias("nround"),
    col("b_seat_info.playerid").alias("playerid"),
    col("a_has_seat.seat").alias("seat"),
    col("a_has_seat.json_index_raw").alias("json_index"),
    col("a_has_seat.minbetscore").alias("minbetscore"),
    col("a_has_seat.maxbetscore").alias("maxbetscore"),
    col("a_has_seat.minaddscore").alias("minaddscore"),
    col("a_has_seat.action").alias("action"),
    col("a_has_seat.seatbetstate").alias("seatbetstate"),
    col("a_has_seat.betscore").alias("betscore"),
    col("a_has_seat.seatcurbet").alias("seatcurbet"),
    col("a_has_seat.poolscore").alias("poolscore"),
    col("a_has_seat.isjumpinsure").alias("isjumpinsure"),
    lit(None).alias("commonCards"),
    col("a_has_seat.gametype").alias("gametype")
)

# 4.2 无 seat 的数据与所有座位关联 (笛卡尔积)
b_no_seat = dwd_no_seat.alias("b_no_seat")
b_no_seat_seats = seat_info_exploded.select(
    col("createdate"),
    col("sztoken"),
    col("nround"),
    col("playerid"),
    col("seat"),
    col("gametype")
).alias("b_no_seat_seats")

no_seat_cross = b_no_seat.join(
    b_no_seat_seats,
    on=["sztoken", "nround"],
    how="inner"
).select(
    col("b_no_seat_seats.createdate").alias("createdate"),
    col("b_no_seat.sztoken").alias("sztoken"),
    col("b_no_seat.nround").alias("nround"),
    col("b_no_seat_seats.playerid").alias("playerid"),
    col("b_no_seat_seats.seat").alias("seat"),
    col("b_no_seat.json_index_raw").alias("json_index"),
    col("b_no_seat.minbetscore").alias("minbetscore"),
    col("b_no_seat.maxbetscore").alias("maxbetscore"),
    col("b_no_seat.minaddscore").alias("minaddscore"),
    col("b_no_seat.action").alias("action"),
    col("b_no_seat.seatbetstate").alias("seatbetstate"),
    col("b_no_seat.betscore").alias("betscore"),
    col("b_no_seat.seatcurbet").alias("seatcurbet"),
    col("b_no_seat.poolscore").alias("poolscore"),
    col("b_no_seat.isjumpinsure").alias("isjumpinsure"),
    col("b_no_seat.commonCards").alias("commonCards"),
    col("b_no_seat.gametype").alias("gametype")
)

# 4.3 合并两个部分
unioned_df = has_seat_joined.unionByName(no_seat_cross)

# Step 5: 计算窗口函数 (对应 Hive 中 t1 子查询中的 LAST_VALUE 等)
# 定义窗口规范
window_spec = Window.partitionBy("sztoken", "nround", "playerid").orderBy(col("json_index").cast("int"))

# 计算 minbetscore, maxbetscore, minaddscore, poolscore, commonCard
# 注意：Hive 中的 LAST_VALUE(..., true) 表示忽略 NULLs，PySpark 默认也忽略 NULLs，所以可以直接用。
# 对于 LAST_VALUE，我们需要指定范围
window_spec_unbounded = Window.partitionBy("sztoken", "nround", "playerid").orderBy(col("json_index").cast("int")).rowsBetween(Window.unboundedPreceding, Window.currentRow)
window_spec_unbounded_following = Window.partitionBy("sztoken", "nround", "playerid").orderBy(col("json_index").cast("int")).rowsBetween(Window.currentRow, Window.unboundedFollowing)

# 计算各个字段
t1_final = unioned_df \
    .withColumn("minbetscore", coalesce(last(col("minbetscore"), ignorenulls=True).over(window_spec_unbounded), first(col("minbetscore"), ignorenulls=True).over(window_spec_unbounded_following))) \
    .withColumn("maxbetscore", coalesce(last(col("maxbetscore"), ignorenulls=True).over(window_spec_unbounded), first(col("maxbetscore"), ignorenulls=True).over(window_spec_unbounded_following))) \
    .withColumn("minaddscore", coalesce(last(col("minaddscore"), ignorenulls=True).over(window_spec_unbounded), first(col("minaddscore"), ignorenulls=True).over(window_spec_unbounded_following))) \
    .withColumn("poolscore", last(col("poolscore"), ignorenulls=True).over(window_spec_unbounded)) \
    .withColumn("commonCard", last(col("commonCards"), ignorenulls=True).over(window_spec_unbounded))

# Step 6: 处理 t2 (S2CBuyInsure 的 score)
t2_df = dwd_df.filter(
    (col("dt") == dt) &
    (get_json_object(col("CardData"), "$.name") == "S2CBuyInsure") &
    (get_json_object(col("CardData"), "$.data.score") != "0") &
    (col("playerid") != 0)
).select(
    col("sztoken"),
    col("nround"),
    get_json_object(col("CardData"), "$.data.seat").alias("seat"),
    get_json_object(col("CardData"), "$.name").alias("action"),
    get_json_object(col("CardData"), "$.data.score").cast("double").alias("score")
).filter(
    col("seat").isNotNull()
).groupBy("sztoken", "nround", "seat", "action").agg(sum(col("score")).alias("score"))

# Step 7: 处理 t3 (S2CStateConclude 的 insureWinLos)
# 使用 posexplode 模拟
t3_df = dwd_df.filter(
    (col("dt") == dt) &
    (get_json_object(col("CardData"), "$.name") == "S2CStateConclude") &
    (col("playerid") != 0)
).select(
    col("sztoken"),
    col("nround"),
    get_json_object(col("CardData"), "$.name").alias("action"),
    col("CardData")
)

# 使用 UDF 模拟 posexplode
def posexplode_insure_winlos(json_str):
    if not json_str:
        return []
    try:
        # 解析 JSON
        data = json.loads(json_str)
        if not isinstance(data, dict) or "data" not in data or "insureWinLos" not in data["data"]:
            return []
        insure_win_los_str = data["data"]["insureWinLos"]
        # 移除方括号并分割
        values_str = insure_win_los_str.replace("[", "").replace("]", "")
        values_list = values_str.split(",")
        result = []
        for i, val in enumerate(values_list):
            if val.strip(): # 非空值
                result.append({"seat_index": i, "value": int(val.strip())})
        return result
    except Exception as e:
        print(f"Error parsing insureWinLos: {e}")
        return []

posexplode_insure_winlos_udf = udf(posexplode_insure_winlos, ArrayType(StructType([
    StructField("seat_index", IntegerType(), True),
    StructField("value", IntegerType(), True)
])))

t3_exploded = t3_df.withColumn(
    "insure_win_los_arr",
    posexplode_insure_winlos_udf(col("CardData"))
).select(
    col("sztoken"),
    col("nround"),
    col("action"),
    explode(col("insure_win_los_arr")).alias("insure_win_los_item")
).select(
    col("sztoken"),
    col("nround"),
    (col("insure_win_los_item.seat_index") + 1).alias("seat"),
    col("action"),
    col("insure_win_los_item.value").alias("value")
).filter(col("value") != 0).dropDuplicates(["sztoken", "nround", "seat", "action", "value"])

# Step 8: 处理 t4 (S2CBuyInsure 的 state)
t4_df = dwd_df.filter(
    (col("dt") == dt) &
    (get_json_object(col("CardData"), "$.name") == "S2CBuyInsure") &
    (col("playerid") != 0)
).select(
    col("sztoken"),
    col("nround"),
    get_json_object(col("CardData"), "$.name").alias("action"),
    get_json_object(col("CardData"), "$.json_index").alias("json_index"),
    get_json_object(col("CardData"), "$.data.seat").alias("seat"),
    get_json_object(col("CardData"), "$.data.state").cast("int").alias("state")
).filter(
    col("seat").isNotNull()
).groupBy("sztoken", "nround", "seat", "json_index", "action", "state").count().drop("count")

# Step 9: 将 t1 与 t2, t3, t4 左连接
t1_with_t2 = t1_final.join(t2_df, on=["sztoken", "nround", "seat", "action"], how="left")
t1_with_t2_t3 = t1_with_t2.join(t3_exploded, on=["sztoken", "nround", "seat", "action"], how="left")
t1_with_all_raw = t1_with_t2_t3.join(t4_df, on=["sztoken", "nround", "seat", "action", "json_index"], how="left")

t1_with_all = t1_with_all_raw \
    .withColumn("value", coalesce(last(col("value"), ignorenulls=True).over(window_spec_unbounded), first(col("value"), ignorenulls=True).over(window_spec_unbounded_following))) \
    .withColumn("state", coalesce(last(col("state"), ignorenulls=True).over(window_spec_unbounded), first(col("state"), ignorenulls=True).over(window_spec_unbounded_following)))

# Step 10: 处理 c (S2CStateGameStart)
c_df = dwd_df.filter(
    (col("dt") == dt) &
    (get_json_object(col("CardData"), "$.name") == "S2CStateGameStart") &
    (col("playerid") != 0)
).select(
    col("sztoken"),
    get_json_object(col("CardData"), "$.name").alias("action"),
    col("nround"),
    col("CardData")
)

# 使用 UDF 模拟 posexplode
def posexplode_seat_cur_bets(json_str):
    if not json_str:
        return []
    try:
        # 解析 JSON
        data = json.loads(json_str)
        if not isinstance(data, dict) or "data" not in data or "seatCurBets" not in data["data"]:
            return []
        seat_cur_bets_str = data["data"]["seatCurBets"]
        # 移除方括号并分割
        values_str = seat_cur_bets_str.replace("[", "").replace("]", "")
        values_list = values_str.split(",")
        result = []
        for i, val in enumerate(values_list):
            if val.strip(): # 非空值
                result.append({"seat_index": i, "seatcurbet": int(val.strip())})
        return result
    except Exception as e:
        print(f"Error parsing seatCurBets: {e}")
        return []

posexplode_seat_cur_bets_udf = udf(posexplode_seat_cur_bets, ArrayType(StructType([
    StructField("seat_index", IntegerType(), True),
    StructField("seatcurbet", IntegerType(), True)
])))

c_exploded = c_df.withColumn(
    "seat_cur_bets_arr",
    posexplode_seat_cur_bets_udf(col("CardData"))
).select(
    col("sztoken"),
    col("action"),
    col("nround"),
    col("CardData"),
    explode(col("seat_cur_bets_arr")).alias("seat_cur_bets_item")
).select(
    col("sztoken"),
    col("action"),
    col("nround"),
    (col("seat_cur_bets_item.seat_index") + 1).alias("seat_num"),
    col("seat_cur_bets_item.seatcurbet").alias("seatcurbet"),
    col("seat_cur_bets_item.seatcurbet").alias("betscore"), # betscore = seatcurbet
    when((col("seat_cur_bets_item.seat_index") + 1) == get_json_object(col("CardData"), "$.data.smallBlindSeat").cast("int"), 1).otherwise(0).alias("issmallBlind"),
    when((col("seat_cur_bets_item.seat_index") + 1) == get_json_object(col("CardData"), "$.data.bigBlindSeat").cast("int"), 1).otherwise(0).alias("isbigBlind"),
    get_json_object(col("CardData"), "$.data.poolScore").alias("poolScore")
).withColumn(
    "seat",
    col("seat_num").cast("string")
).drop("seat_num").dropDuplicates(["sztoken", "action", "nround", "seat", "seatcurbet", "betscore", "issmallBlind", "isbigBlind", "poolScore"])

# Step 11: 最终主查询 (a left join b and c)
# a 是 t1_with_all
# b 是 game_score_df
# c 是 c_exploded

final_a = t1_with_all.alias("a")
final_b = game_score_df.alias("b")
final_c = c_exploded.alias("c")

# 执行左连接
final_joined = final_a \
    .join(final_b, on=[col("a.sztoken") == col("b.sztoken"), col("a.nround") == col("b.nround"), col("a.playerid") == col("b.playerid")], how="left") \
    .join(final_c, on=[col("a.sztoken") == col("c.sztoken"), col("a.nround") == col("c.nround"), col("a.seat") == col("c.seat"), col("a.action") == col("c.action")], how="left")

# Step 12: 计算最终输出的所有列
# 定义用于排序的窗口
window_for_row_number = Window.partitionBy(col("a.sztoken"), col("a.nround")).orderBy(col("a.json_index").cast("int"), col("sort_key").cast("int"))

# 创建排序键
final_with_sort_key = final_joined.withColumn(
    "sort_key",
    when((col("c.issmallBlind") == 1), 0)
    .when((col("c.isbigBlind") == 1), 1)
    .otherwise(col("a.playerid"))
)

# 计算 row_number
final_with_row_number = final_with_sort_key.withColumn(
    "json_index_rn",
    row_number().over(window_for_row_number)
)

# 计算 predealct
window_predealct = Window.partitionBy(col("a.sztoken"), col("a.nround"), col("a.playerid"), col("a.seat")).orderBy(col("a.json_index").cast("int"))
final_with_predealct = final_with_row_number.withColumn(
    "predealct",
    coalesce(size(collect_set(col("a.commonCard")).over(window_predealct)), lit(0))
)

# 计算 stage
final_with_stage = final_with_predealct.withColumn(
    "stage",
    when(size(split(col("a.commonCard"), ",")) == 3, "flop")
    .when(size(split(col("a.commonCard"), ",")) == 4, "turn")
    .when(size(split(col("a.commonCard"), ",")) == 5, "river")
    .otherwise("preflop")
)

# 计算 poolscore (复杂 case when)
# 先计算 sum(if(a.action ='S2CStateGameStart' and (c.issmallBlind=1 or c.isbigBlind=1),c.betscore,0)) over(partition by a.sztoken,a.nround)
window_sum_blind = Window.partitionBy(col("a.sztoken"), col("a.nround"))
sum_blind_expr = sum(
    when((col("a.action") == "S2CStateGameStart") & ((col("c.issmallBlind") == 1) | (col("c.isbigBlind") == 1)), col("c.betscore")).otherwise(0)
).over(window_sum_blind)

final_with_poolscore = final_with_stage.withColumn(
    "poolscore_final",
    when((col("a.action") == "S2CStateGameStart") & (col("c.issmallBlind") == 1), col("c.betscore"))
    .when((col("a.action") == "S2CStateGameStart") & (col("c.isbigBlind") == 1), sum_blind_expr)
    .when(col("json_index_rn") == 1, when(col("a.action") == "S2CStateGameStart", col("c.betscore")).otherwise(col("a.betscore")))
    .otherwise(col("a.poolscore"))
)

# 计算 isjumpinsure 和 isInsure
final_with_insures = final_with_poolscore.withColumn(
    "isjumpinsure_final",
    when(col("a.score") > 0, 1).otherwise(col("a.isjumpinsure"))
).withColumn(
    "isInsure",
    when(col("a.score") > 0, 1).otherwise(0)
)

# 计算 insureWinScores
window_insurance = Window.partitionBy(col("a.sztoken"), col("a.nround"), col("a.playerid")).orderBy(col("a.json_index").cast("int")).rowsBetween(Window.unboundedPreceding, Window.currentRow)
window_insurance_following = Window.partitionBy(col("a.sztoken"), col("a.nround"), col("a.playerid")).orderBy(col("a.json_index").cast("int")).rowsBetween(Window.currentRow, Window.unboundedFollowing)

final_with_insurance_scores = final_with_insures.withColumn(
    "insureWinScores",
    col("a.value") + coalesce(
        last(col("a.score"), ignorenulls=True).over(window_insurance),
        last(col("a.score"), ignorenulls=True).over(window_insurance_following)
    )
)

# 计算 Betaction
final_with_betaction = final_with_insurance_scores.withColumn(
    "Betaction",
    when(
        col("a.action") == "S2CBuyInsure",
        when(col("a.state") == 1, lit("ins_none"))
        .when(col("a.state") == 2, lit("ins_buy"))
        .when(col("a.state") == 3, lit("ins_giveup"))
        .when(col("a.state") == 4, lit("ins_buying"))
        .when(col("a.state") == 5, lit("ins_bupai_invalid"))
        .when(col("a.state") == 6, lit("ins_auto_buy"))
    )
    .when(col("a.action") == "S2CStateGameStart", "init")
    .when(col("a.action") == "S2CGiveUp", "Fold")
    .when(col("a.seatbetstate") == 1, "none")
    .when(col("a.seatbetstate") == 2, "check")
    .when(col("a.seatbetstate") == 3, "call")
    .when(col("a.seatbetstate") == 4, "raise")
    .when(col("a.seatbetstate") == 5, "allin")
    .when(col("a.seatbetstate") == 6, "fold")
)

# Step 13: 选择最终输出列
final_output = final_with_betaction.select(
    col("a.createdate").alias("createdate"),
    col("a.sztoken").alias("sztoken"),
    col("a.nround").cast("int").alias("nround"),
    col("a.playerid").alias("playerid"),
    col("a.seat").alias("seat"),
    col("json_index_rn").cast("int").alias("json_index"),
    col("a.minbetscore").cast("int").alias("minbetscore"),
    col("a.maxbetscore").cast("int").alias("maxbetscore"),
    col("a.minaddscore").cast("int").alias("minaddscore"),
    col("a.action").alias("action"),
    col("a.seatbetstate").cast("int").alias("seatbetstate"),
    when(col("a.action") == "S2CStateGameStart", col("c.betscore")).otherwise(col("a.betscore")).cast("int").alias("betscore"),
    when(col("a.action") == "S2CStateGameStart", col("c.seatcurbet")).otherwise(col("a.seatcurbet")).cast("int").alias("seatcurbet"),
    col("poolscore_final").cast("int").alias("poolscore"),
    col("predealct").cast("int").alias("predealct"),
    col("a.commonCard").alias("commonCard"),
    col("stage").alias("stage"),
    col("b.gameresult").cast("double").alias("gameresult"),
    col("isjumpinsure_final").cast("int").alias("isjumpinsure"),
    col("isInsure").cast("int").alias("isInsure"),
    col("a.score").cast("double").alias("score"),
    col("insureWinScores").cast("double").alias("insureWinScores"),
    col("Betaction").alias("Betaction"),
    col("a.gametype").cast("int").alias("gametype")
)

final_output.show()
# Step 14: 写入目标表
# 根据您的需求，这里写入分区表
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

# 先删除当前分区的数据
spark.sql(f"ALTER TABLE poker.dws_dz_player_action_di DROP IF EXISTS PARTITION (dt='{dt}')")

final_output_with_dt = final_output.withColumn("dt", lit(dt))
final_output_with_dt.write.mode("overwrite").insertInto("poker.dws_dz_player_action_di")

print("ETL process completed successfully.")
spark.stop()
