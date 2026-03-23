import pymysql
import pandas as pd

def read_from_mysql(sql=None):
    assert sql is not None, "sql must be provided"
    # 数据库连接配置
    config = {
        'host': '10.0.0.9',      # 数据库地址
        'port': 3306,             # 端口
        'user': 'bigquery_user',           # 用户名
        'password': 'xdf#42sdfkjdfiyuISYFj76',   # 密码
        'database': 'niuniuh5_db',    # 数据库名
        'charset': 'utf8mb4',     # 字符集
        'cursorclass': pymysql.cursors.DictCursor
    }

    try:
        # 建立连接
        connection = pymysql.connect(**config)
        res=[]
        try:
            # 方法1：使用 cursor 执行 SQL
            with connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                #print("--- Cursor Result ---")
                for row in result:
                    #print(row)
                    res.append(row)
            #方法2：使用 pandas 读取 (推荐用于数据分析)
            #df = pd.read_sql(sql, connection)
            # print("\n--- Pandas DataFrame ---")
            # print(df.head())
            #return df
            return pd.DataFrame(res)
        finally:
            # 关闭连接
            connection.close()
            
    except Exception as e:
        print(f"Error: {e}")

sql_400="""
SELECT
    t_robot.nplayerid,
    400 as ngametype,
    t_robot.brobot,
    ROUND(SUM(t_pnl.player_pnl), 2) as total_score
FROM (
    SELECT
        t1.sztoken,
        t2.nplayerid,
        t1.create_dt,
        CASE
            WHEN t2.reward > 0 THEN t2.reward - t1.entry_fee
            ELSE -t1.entry_fee
        END as player_pnl
    FROM (
        SELECT DISTINCT
            sztoken,
            szroomname,
            createtime,
            substr(createtime, 1, 10) as create_dt,
            CAST(szRuleJson->>'$.joinFeeUcoin' AS UNSIGNED)/1000000 as entry_fee,
            CAST(szRuleJson->>'$.awards[0].award' AS UNSIGNED)/1000000 as award
        FROM table_dz_game_info
        WHERE substr(createtime, 1, 10) = '{dt}'
        AND ngametype = 400
    ) t1
    LEFT JOIN (
        SELECT
            sztoken,
            nplayerid,
            reward/1000000 as reward
        FROM table_dz_match_result
        WHERE substr(tCreateTime, 1, 10) = '{dt}'
        AND ngametype = 400
    ) t2 ON t1.sztoken = t2.sztoken
) t_pnl
LEFT JOIN table_user t_robot ON t_pnl.nplayerid = t_robot.nplayerid
WHERE t_pnl.create_dt = '{dt}'
GROUP BY t_robot.nplayerid, t_robot.brobot;
"""

dt = "2026-01-12"
sql_400 = sql_400.format(dt=dt)

df=read_from_mysql(sql_400)
print(df.head())
