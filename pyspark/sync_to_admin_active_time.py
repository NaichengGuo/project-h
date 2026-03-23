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

    with non_gold_score as(
    select ngametype,sztoken,nplayerid,nround,gameresult,createtime,substr(createtime,1,10) as create_dt
    from poker.ods_dz_db_table_dz_game_score_detail_df 
    where dt='${dt}'
    and substr(createtime,1,10)='${dt}'
    )

    ,non_gold_sum as(
    select t1.*,t2.brobot,t2.robotversion
    from non_gold_score t1
    left join poker.dws_dz_robot_info_di t2
    on t1.sztoken=t2.sztoken
    and t1.nround=t2.nround
    and t1.nplayerid=t2.playerid)

    ,gold_score as(
    select ngametype,sztoken,nplayerid,nround,gameresult,createtime,substr(createtime,1,10) as create_dt
    from poker.ods_dz_db_table_dz_game_gold_score_detail_df 
    where dt='${dt}'
    and substr(createtime,1,10)='${dt}')

    ,gold_sum as(
    select t1.*,t2.brobot,t2.robotversion
    from gold_score t1
    left join poker.dws_dz_robot_info_di t2
    on t1.sztoken=t2.sztoken
    and t1.nround=t2.nround
    and t1.nplayerid=t2.playerid)

    ,sum_score as(
    select * from non_gold_sum
    union all 
    select * from gold_sum
    )


    select ngametype,substr(createtime,1,10) as start_dt,substr(createtime,12,2) as start_dt_hr
    ,count(distinct nplayerid) as player_cnt
    ,count(distinct concat(sztoken,nround)) as round_cnt
    from sum_score
    where brobot is null
    group by ngametype,substr(createtime,1,10),substr(createtime,12,2)
    order by substr(createtime,12,2) asc
    """
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
            # 4. 建表 (admin_active_time)
            # 根据 Hive 查询的字段结构建表
            # 先删除旧表
            # drop_table_sql = "DROP TABLE IF EXISTS admin_active_time"
            # print("Dropping old table...")
            # # cursor.execute(drop_table_sql) # 暂时注释掉，避免误删，或者根据需求决定是否保留
            
            # create_table_sql = """
            # CREATE TABLE IF NOT EXISTS admin_active_time (
            #     id INT AUTO_INCREMENT PRIMARY KEY,
            #     ngametype INT COMMENT '游戏类型',
            #     start_dt DATE NOT NULL COMMENT '统计日期',
            #     start_dt_hr VARCHAR(2) NOT NULL COMMENT '统计小时',
            #     player_cnt INT DEFAULT 0 COMMENT '活跃人数',
            #     round_cnt INT DEFAULT 0 COMMENT '对局数',
            #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            #     UNIQUE KEY idx_dt_game_hr (start_dt, ngametype, start_dt_hr)
            # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理后台活跃时段统计';
            # """
            # print("Checking/Creating table...")
            # cursor.execute(create_table_sql)
            
            # 5. 插入数据
            print("Inserting data into MySQL...")
            # 先删除该日期的所有旧数据，确保是 overwrite 而非 update
            delete_sql = "DELETE FROM admin_active_time WHERE start_dt = %s"
            print(f"Deleting old data for date: {dt_str}...")
            cursor.execute(delete_sql, (dt_str,))
            
            insert_sql = """
            INSERT INTO admin_active_time (
                ngametype, start_dt, start_dt_hr, player_cnt, round_cnt
            ) VALUES (
                %s, %s, %s, %s, %s
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
                    get_val(row, 'ngametype'),
                    get_val(row, 'start_dt'),
                    get_val(row, 'start_dt_hr'),
                    get_val(row, 'player_cnt', 0),
                    get_val(row, 'round_cnt', 0)
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
