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
    query = """

WITH valid_tables AS (
  -- 步骤1: 找出包含至少1个非机器人和1个机器人玩家的桌子
  select distinct t1.sztoken,t1.nround,t1.ngametype from
  (SELECT distinct sztoken,nround,ngametype
  FROM poker.dws_db_player_game_result_di
  where brobot=0
  and dt='${dt}') t1
  inner join 
  (SELECT distinct sztoken,nround,ngametype
  FROM poker.dws_db_player_game_result_di
  where brobot=1
  and dt='${dt}') t2
  on t1.sztoken=t2.sztoken
  and t1.nround=t2.nround
),
robot_performance AS (
  -- 步骤2: 计算每个机器人在有效桌子中的净收益
  SELECT t1.sztoken,t1.nround,t1.ngametype,robotversion,
    SUM(gameresult) AS total_robot_profit
  FROM poker.dws_db_player_game_result_di t1
  inner join valid_tables t2
  on t1.sztoken=t2.sztoken
  and t1.nround=t2.nround
  where brobot = 1
  GROUP BY t1.sztoken,t1.nround,t1.ngametype,robotversion
)
-- 步骤3: 计算胜率（盈利机器人占比）
SELECT 
  '${dt}' as dt,
  1 as brobot,
  robotversion,
  ngametype,
  -- COUNT(CASE WHEN total_profit > 0 THEN 1 END) * 1.0 / COUNT(*) AS robot_win_rate,
  COUNT(sztoken) AS total_round_cnt,
  COUNT(CASE WHEN total_robot_profit > 0 THEN 1 END) AS win_round_cnt,
  0 as total_player_cnt,
  0 as win_player_cnt,
  sum(total_robot_profit) as gameresult
FROM robot_performance
group by '${dt}',1,robotversion,ngametype"""
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
            # 4. 建表 (robot_game_stats)
            # 根据 Hive 查询的字段结构建表
            # 先删除旧表
            # drop_table_sql = "DROP TABLE IF EXISTS robot_game_stats"
            # print("Dropping old table...")
            # cursor.execute(drop_table_sql)
            
            # create_table_sql = """
            # CREATE TABLE IF NOT EXISTS robot_game_stats (
            #     id INT AUTO_INCREMENT PRIMARY KEY,
            #     dt DATE NOT NULL COMMENT '统计日期',
            #     brobot TINYINT NOT NULL COMMENT '是否为机器人 (0:否, 1:是)',
            #     robotversion VARCHAR(64) COMMENT '机器人版本',
            #     ngametype INT NOT NULL COMMENT '游戏类型',
            #     total_round_cnt INT DEFAULT 0 COMMENT '总游戏局数',
            #     win_round_cnt INT DEFAULT 0 COMMENT '赢的游戏局数',
            #     total_player_cnt INT DEFAULT 0 COMMENT '总玩家数',
            #     win_player_cnt INT DEFAULT 0 COMMENT '赢的玩家数',
            #     gameresult BIGINT DEFAULT 0 COMMENT '游戏结果总和',
            #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            #     UNIQUE KEY idx_date_robot_version_gametype (dt, brobot, robotversion, ngametype)
            # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机器人游戏统计表';
            # """
            # print("Checking/Creating table...")
            # cursor.execute(create_table_sql)
            
            # 5. 插入数据
            print("Inserting data into MySQL...")
            # 先删除该日期的所有旧数据，确保是 overwrite 而非 update
            delete_sql = "DELETE FROM robot_game_stats WHERE dt = %s"
            print(f"Deleting old data for date: {dt_str}...")
            cursor.execute(delete_sql, (dt_str,))
            
            insert_sql = """
            INSERT INTO robot_game_stats (
                dt, brobot, robotversion, ngametype, total_round_cnt, win_round_cnt, total_player_cnt, win_player_cnt, gameresult
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
            """
            
            # 辅助函数：安全地从行中获取值
            def get_val(row, key, default=0):
                val = None
                if key in row:
                    val = row[key]
                else:
                    # 尝试匹配带有前缀的列名 (例如 t1.round_cnt)
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
                    get_val(row, 'brobot'),
                    get_val(row, 'robotversion'),
                    get_val(row, 'ngametype'),
                    get_val(row, 'total_round_cnt'),
                    get_val(row, 'win_round_cnt'),
                    get_val(row, 'total_player_cnt'),
                    get_val(row, 'win_player_cnt'),
                    get_val(row, 'gameresult')
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
