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
    SELECT 
        nplayerid, regtime, brobot, preloginip, prelogintime, sznickname, nclubid, 
        vpip, pfr, three_bet_pct, cbet_pct, af, allin_frequency, fold_rate, 
        playing_style, data_quality, preferred_gametype, preferred_game_rounds, 
        active_days, avg_round_duration_mins, peak_active_hour, activity_level, 
        collusion_status, total_hands_vs_bot, win_rate_vs_bot, avg_profit_vs_bot, 
        high_stakes_ratio, bot_hands_ratio, player_profile_label
    FROM poker.dws_dz_player_profile_tag_df
    WHERE dt='${dt}' 
    AND active_days > 0
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
            # 4. 建表 (user_profile_stats)
            # create_table_sql = """
            # CREATE TABLE IF NOT EXISTS user_profile_stats (
            #     id INT AUTO_INCREMENT PRIMARY KEY,
            #     dt DATE NOT NULL COMMENT '统计日期',
            #     nplayerid BIGINT NOT NULL COMMENT '玩家ID',
            #     regtime VARCHAR(64) COMMENT '注册时间',
            #     brobot INT COMMENT '是否机器人',
            #     preloginip VARCHAR(64) COMMENT '最近登录IP',
            #     prelogintime VARCHAR(64) COMMENT '最近登录时间',
            #     sznickname VARCHAR(128) COMMENT '玩家昵称',
            #     nclubid BIGINT COMMENT '所属俱乐部ID',
            #     vpip DECIMAL(5,4) COMMENT 'VPIP',
            #     pfr DECIMAL(5,4) COMMENT 'PFR',
            #     three_bet_pct DECIMAL(5,4) COMMENT '3-bet率',
            #     cbet_pct DECIMAL(5,4) COMMENT 'C-bet率',
            #     af DECIMAL(5,4) COMMENT '攻击因子',
            #     allin_frequency DECIMAL(5,4) COMMENT '全下频率',
            #     fold_rate DECIMAL(5,4) COMMENT '弃牌率',
            #     playing_style VARCHAR(64) COMMENT '牌风标签',
            #     data_quality VARCHAR(32) COMMENT '数据质量',
            #     preferred_gametype INT COMMENT '偏好游戏类型',
            #     preferred_game_rounds BIGINT COMMENT '偏好游戏类型局数',
            #     active_days INT COMMENT '近30天活跃天数',
            #     avg_round_duration_mins DECIMAL(6,2) COMMENT '平均单局时长',
            #     peak_active_hour INT COMMENT '最活跃时段',
            #     activity_level VARCHAR(32) COMMENT '活跃度标签',
            #     collusion_status VARCHAR(64) COMMENT '伙牌风险标签',
            #     total_hands_vs_bot BIGINT COMMENT '对战机器人总手牌数',
            #     win_rate_vs_bot DECIMAL(5,4) COMMENT '对战机器人胜率',
            #     avg_profit_vs_bot DECIMAL(10,2) COMMENT '对战机器人平均每局盈利',
            #     high_stakes_ratio DECIMAL(5,4) COMMENT '高额桌占比',
            #     bot_hands_ratio DECIMAL(5,4) COMMENT '机器人对局占比',
            #     player_profile_label VARCHAR(64) COMMENT '机器人对战画像标签',
            #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            #     UNIQUE KEY idx_dt_player (dt, nplayerid)
            # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户画像统计表';
            # """
            # print("Checking/Creating table...")
            # cursor.execute(create_table_sql)
            
            # 5. 插入数据
            print("Inserting data into MySQL...")
            # 先删除该日期的所有旧数据
            delete_sql = "DELETE FROM user_profile_stats WHERE dt = %s"
            print(f"Deleting old data for date: {dt_str}...")
            cursor.execute(delete_sql, (dt_str,))
            
            insert_sql = """
            INSERT INTO user_profile_stats (
                dt, nplayerid, regtime, brobot, preloginip, prelogintime, sznickname, nclubid,
                vpip, pfr, three_bet_pct, cbet_pct, af, allin_frequency, fold_rate,
                playing_style, data_quality, preferred_gametype, preferred_game_rounds,
                active_days, avg_round_duration_mins, peak_active_hour, activity_level,
                collusion_status, total_hands_vs_bot, win_rate_vs_bot, avg_profit_vs_bot,
                high_stakes_ratio, bot_hands_ratio, player_profile_label
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            );
            """
            
            # 辅助函数：安全地从行中获取值
            def get_val(row, key, default=None):
                val = None
                if key in row:
                    val = row[key]
                else:
                    # 尝试匹配带有前缀的列名
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
                    get_val(row, 'nplayerid'),
                    get_val(row, 'regtime'),
                    get_val(row, 'brobot'),
                    get_val(row, 'preloginip'),
                    get_val(row, 'prelogintime'),
                    get_val(row, 'sznickname'),
                    get_val(row, 'nclubid'),
                    get_val(row, 'vpip'),
                    get_val(row, 'pfr'),
                    get_val(row, 'three_bet_pct'),
                    get_val(row, 'cbet_pct'),
                    get_val(row, 'af'),
                    get_val(row, 'allin_frequency'),
                    get_val(row, 'fold_rate'),
                    get_val(row, 'playing_style'),
                    get_val(row, 'data_quality'),
                    get_val(row, 'preferred_gametype'),
                    get_val(row, 'preferred_game_rounds'),
                    get_val(row, 'active_days'),
                    get_val(row, 'avg_round_duration_mins'),
                    get_val(row, 'peak_active_hour'),
                    get_val(row, 'activity_level'),
                    get_val(row, 'collusion_status'),
                    get_val(row, 'total_hands_vs_bot'),
                    get_val(row, 'win_rate_vs_bot'),
                    get_val(row, 'avg_profit_vs_bot'),
                    get_val(row, 'high_stakes_ratio'),
                    get_val(row, 'bot_hands_ratio'),
                    get_val(row, 'player_profile_label')
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
