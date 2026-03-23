import pandas as pd
import pymysql
from pyhive import hive
from datetime import datetime, timedelta
import sys

def sync_data(dt_str=None):
    # 1. 获取日期参数或使用昨日
    if dt_str is None:
        yesterday = datetime.now() - timedelta(days=1)
        dt_str = yesterday.strftime('%Y-%m-%d')
    print(f"Processing data for date: {dt_str}")

    # 2. Hive 查询 (生成 DF)
    print("Connecting to Hive...")
    hive_conn = hive.connect(
        host="10.0.21.126",
        port=10000,
        username="root",
        database="default"
    )
    
    # Hive Query from local-mysql-test.ipynb
    query ="""
    select case when dt_cnt>=5 then 'high'
            when dt_cnt>=3 then 'mid'
            when dt_cnt>=1 then 'low'
            else 'silenct' end as active_tag,
        '${dt}' as dt,
            count(distinct nplayerid) as player_cnt
    from(
    select nplayerid,count(distinct dt) as dt_cnt
    from poker.dws_db_player_game_result_di 
    where brobot=0
    and dt>=date_sub('${dt}',30)
    and dt<='${dt}'
    group by nplayerid)t
    group by case when dt_cnt>=5 then 'high'
                when dt_cnt>=3 then 'mid'
                when dt_cnt>=1 then 'low'
                else 'silenct' end, '${dt}'"""

    # 替换日期参数
    query = query.replace('${dt}', dt_str)

    print("Executing Hive query...")
    # 使用 pandas read_sql 直接获取 DataFrame
    df = pd.read_sql(query, hive_conn)
    print(f"Hive query returned {len(df)} rows.")
    
    hive_conn.close()

    if df.empty:
        print("No data found, skipping MySQL insertion.")
        return

    # 3. MySQL 连接 (参考 init_daily_stats.py)
    print("Connecting to MySQL...")
    mysql_config = {
        'host': '10.0.14.253',
        'port': 3306,
        'user': 'root',
        'password': 'Root123!',
        'database': 'algo_admin',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    mysql_conn = pymysql.connect(**mysql_config)
    
    try:
        with mysql_conn.cursor() as cursor:
            # 4. 建表 (user_active_tag)
            # 根据 Hive 查询的字段结构建表
            # create_table_sql = """
            # CREATE TABLE IF NOT EXISTS user_active_tag (
            #     id INT AUTO_INCREMENT PRIMARY KEY,
            #     dt DATE NOT NULL COMMENT '统计日期',
            #     active_tag VARCHAR(50) NOT NULL COMMENT '活跃标签',
            #     player_cnt INT NOT NULL DEFAULT 0 COMMENT '玩家数量',
            #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            #     UNIQUE KEY idx_dt_active_tag (dt, active_tag)
            # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户活跃度标签统计';
            # """
            # print("Checking/Creating table...")
            # cursor.execute(create_table_sql)
            
            # 5. 插入数据
            print("Inserting data into MySQL...")
            # 先删除该日期的所有旧数据，确保是 overwrite 而非 update
            delete_sql = "DELETE FROM user_active_tag WHERE dt = %s"
            print(f"Deleting old data for date: {dt_str}...")
            cursor.execute(delete_sql, (dt_str,))
            
            insert_sql = """
            INSERT INTO user_active_tag (
                dt, active_tag, player_cnt
            ) VALUES (
                %s, %s, %s
            );
            """
            
            # 辅助函数：安全地从行中获取值
            def get_val(row, key, default=None):
                val = None
                if key in row:
                    val = row[key]
                else:
                    # 尝试匹配带有前缀的列名 (例如 t1.table_name)
                    for col in row.index:
                        if col.endswith('.' + key):
                            val = row[col]
                            break
                
                # 处理空值
                if pd.isna(val) or val is None:
                    return default
                return val

            for _, row in df.iterrows():
                # 提取数据
                params = (
                    get_val(row, 'dt', dt_str),
                    get_val(row, 'active_tag'),
                    get_val(row, 'player_cnt', 0)
                )
                cursor.execute(insert_sql, params)
            
            mysql_conn.commit()
            print("Insertion complete.")

    finally:
        mysql_conn.close()

if __name__ == "__main__":
    dt_str = None
    if len(sys.argv) > 1:
        dt_str = sys.argv[1]
    sync_data(dt_str)
