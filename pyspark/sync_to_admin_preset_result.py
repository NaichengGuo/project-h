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
    with preset_result_450 as(
    select t1.*,t2.gameresult
    from
    (select sztoken,nround,ngametype,nplayerid,brobot,handcards,commoncards
        ,inventiontype,presettype
    from poker.ods_card_preset_di 
    where dt='${dt}'
    and bpreset='true'
    and ngametype=450
    )t1
    left join 
    (
    select *
    from poker.ods_dz_db_table_dz_game_gold_score_detail_df 
    where dt='${dt}'
    and ngametype=450
    )t2
    on t1.sztoken=t2.sztoken
    and t1.nplayerid=t2.nplayerid)

    -- 420
    ,preset_result_420 as(
    select t1.*,t2.gameresult
    from
    (select sztoken,nround,ngametype,nplayerid,brobot,handcards,commoncards
        ,inventiontype,presettype
    from poker.ods_card_preset_di 
    where dt='${dt}'
    and bpreset='true'
    and ngametype=420
    )t1
    left join 
    (
    select *
    from poker.ods_dz_db_table_dz_game_score_detail_df 
    where dt='${dt}'
    and ngametype=420
    )t2
    on t1.sztoken=t2.sztoken
    and t1.nround=t2.nround
    and t1.nplayerid=t2.nplayerid)

    ,union_all as(
    select * from preset_result_420 
    union all 
    select * from preset_result_450
    )

    -- 每把只保留一条记录
    select '${dt}' as dt,
        inventiontype,
        ngametype,
        case when brobot=1 and gameresult>=0 then 'robot_good_win'
            when brobot=1 and gameresult<0 then 'robot_good_lose' 
            when brobot=0 and gameresult>=0 then 'human_good_win'
            when brobot=0 and gameresult<0 then 'human_good_lose' end as play_result,
        count(distinct concat(sztoken,nround)) as round_cnt,
        count(distinct nplayerid) as player_cnt
    from union_all
    where presettype=2
    group by '${dt}',inventiontype,ngametype,
        case when brobot=1 and gameresult>=0 then 'robot_good_win'
            when brobot=1 and gameresult<0 then 'robot_good_lose' 
            when brobot=0 and gameresult>=0 then 'human_good_win'
            when brobot=0 and gameresult<0 then 'human_good_lose' end
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
            # 4. 建表 (card_preset_result)
            # 根据 Hive 查询的字段结构建表
            
            # create_table_sql = """
            # CREATE TABLE IF NOT EXISTS card_preset_result (
            #     id INT AUTO_INCREMENT PRIMARY KEY,
            #     dt DATE NOT NULL COMMENT '统计日期',
            #     ngametype INT NOT NULL COMMENT '游戏类型',
            #     inventiontype VARCHAR(64) COMMENT '预设类型',
            #     play_result VARCHAR(32) COMMENT '对局结果类型',
            #     round_cnt INT DEFAULT 0 COMMENT '局数',
            #     player_cnt INT DEFAULT 0 COMMENT '人数',
            #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            #     UNIQUE KEY idx_dt_gametype_inv_result (dt, ngametype, inventiontype, play_result)
            # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预设牌局结果统计表';
            # """
            # print("Checking/Creating table...") 
            # cursor.execute(create_table_sql)
            
            # 5. 插入数据
            print("Inserting data into MySQL...")
            # 先删除该日期的所有旧数据，确保是 overwrite 而非 update
            delete_sql = "DELETE FROM card_preset_result WHERE dt = %s"
            print(f"Deleting old data for date: {dt_str}...")
            cursor.execute(delete_sql, (dt_str,))
            
            insert_sql = """
            INSERT INTO card_preset_result (
                dt, ngametype, inventiontype, play_result, round_cnt, player_cnt
            ) VALUES (
                %s, %s, %s, %s, %s, %s
            );
            """
            
            # 辅助函数：安全地从行中获取值
            def get_val(row, key, default=0):
                val = None
                if key in row:
                    val = row[key]
                else:
                    # 尝试匹配带有前缀的列名
                    # The hive result might have column names like 'table_alias.col_name'
                    for col in row.index:
                        if col.endswith('.' + key) or col == key:
                            val = row[col]
                            break
                
                if pd.isna(val) or val is None:
                    return default
                return val

            count = 0
            for index, row in df.iterrows():
                # Extract values using the helper
                # Note: 'dt' in Hive query is generated as a string literal, so it might be in the dataframe or we use the passed dt_str
                r_dt = get_val(row, 'dt', dt_str)
                r_gametype = get_val(row, 'ngametype', 0)
                r_inv_type = get_val(row, 'inventiontype', 'no_preset')
                r_play_result = get_val(row, 'play_result', 'unknown')
                r_round_cnt = get_val(row, 'round_cnt', 0)
                r_player_cnt = get_val(row, 'player_cnt', 0)
                
                cursor.execute(insert_sql, (r_dt, r_gametype, r_inv_type, r_play_result, r_round_cnt, r_player_cnt))
                count += 1

            mysql_conn.commit()
            print(f"Successfully inserted {count} rows.")

    except Exception as e:
        print(f"Error: {e}")
        mysql_conn.rollback()
    finally:
        mysql_conn.close()
        print("MySQL connection closed.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
    else:
        date_arg = None
    
    sync_data(date_arg)
