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
    with collusion_player as(
    select distinct dt,playerid from(
    select distinct dt,player1_id as playerid
    from poker.dws_dz_player_collusion_cross_df 
    where dt='${dt}'
    and same_cnt>=20
    and win_rate>=0.7
    and (player1_same_rate>=0.75 or player2_same_rate>=0.75)
    and total_desk>=3
    union all
    select distinct dt,player2_id as playerid
    from poker.dws_dz_player_collusion_cross_df 
    where dt='${dt}'
    and same_cnt>=20
    and win_rate>=0.7
    and (player1_same_rate>=0.75 or player2_same_rate>=0.75)
    and total_desk>=3)t
    )


,same_ip_player as(
select distinct dt,player1_id as playerid
from poker.dws_dz_player_collusion_cross_df 
where dt='${dt}'
and shared_ip_cnts is not null
union all
select distinct dt,player2_id as playerid
from poker.dws_dz_player_collusion_cross_df 
where dt='${dt}'
and shared_ip_cnts is not null
)

,abnormal_high_win_player as(
select * from(
select dt,nplayerid
    ,count(distinct concat(sztoken,nround) ) as round_cnt
    ,count(distinct case when gameresult>0 then concat(sztoken,nround) end ) as win_round_cnt
    ,count(distinct case when gameresult>0 then concat(sztoken,nround) end )/count(distinct concat(sztoken,nround) )  as win_rate
from poker.dws_db_player_game_result_di
where  dt='${dt}'
group by dt,nplayerid)t
where win_rate>=0.8
and round_cnt>=10)

,valid_tables AS (
  -- 步骤1: 找出包含至少1个非机器人玩家的桌子
  SELECT distinct sztoken,nround
  FROM poker.dws_db_player_game_result_di
  where brobot=0
  and dt='${dt}'
),
robot_performance AS (
  -- 步骤2: 计算每个机器人在有效桌子中的净收益
  SELECT t1.sztoken,t1.nround,
    SUM(gameresult) AS total_robot_profit
  FROM poker.dws_db_player_game_result_di t1
  inner join valid_tables t2
  on t1.sztoken=t2.sztoken
  and t1.nround=t2.nround
  where brobot = 1
  GROUP BY t1.sztoken,t1.nround
)
-- 步骤3: 计算胜率（盈利机器人占比）
,robot_stats as(
SELECT '${dt}' as dt,
  COUNT(CASE WHEN total_robot_profit > 0 THEN 1 END) AS robot_win_round_cnt,
  COUNT(*) AS robot_round_cnt
FROM robot_performance)

,total_cnt_pre as(
select dt 
      ,count(distinct concat(sztoken,nround)) as round_cnt
      ,count(distinct case when brobot=0 then nplayerid else null end) as day_real_player_cnt
from poker.dws_db_player_game_result_di 
where dt='${dt}'
group by dt
)

,total_cnt as(
select t1.dt,t1.round_cnt,t2.robot_round_cnt,t2.robot_round_cnt/t1.round_cnt as robot_round_pct
    ,t2.robot_win_round_cnt,t2.robot_win_round_cnt/t2.robot_round_cnt as robot_win_round_pct
    ,t1.day_real_player_cnt
    from total_cnt_pre t1
    inner join robot_stats t2
    on t1.dt=t2.dt)


-- MAU
,month_total_cnt as(
select '${dt}' as dt,month_real_player_cnt from(
select count(distinct case when brobot=0 then nplayerid else null end) as month_real_player_cnt
from poker.dws_db_player_game_result_di 
where dt<='${dt}' and dt>=date_sub('${dt}',30)
)t
)

-- 当日新增用户数
,new_user_cnt as(
select t1.dt
  ,count(distinct case when t2.nplayerid is null then t1.nplayerid end) as new_player_cnt
from 
(select distinct dt,nplayerid 
from poker.ods_dz_db_table_user_df
where dt='${dt}'
and brobot='0') t1
left join 
(select distinct nplayerid
from poker.ods_dz_db_table_user_df
where dt=date_sub('${dt}',1)
and brobot='0') t2
on t1.nplayerid=t2.nplayerid
group by t1.dt
)

-- 发牌干预
,preset_cnt as(
select t1.dt
      ,count(distinct concat(t1.sztoken,t1.nround)) as preset_round_cnt
      ,count(distinct t1.nplayerid) as preset_player_cnt
      ,count(distinct case when presettype=2 then t1.nplayerid end) as reward_player_cnt
      ,count(distinct case when presettype=2 and gameresult>0 then t1.nplayerid end) as reward_win_round_cnt
      -- ,count(distinct case when presettype=2 then nplayerid end) as preset_reward_player_cnt
      -- ,count(distinct concat(t1.sztoken,t1.nround)) as preset_round_cnt
from poker.ods_card_preset_di t1
left join poker.dws_db_player_game_result_di t2
on t1.sztoken=t2.sztoken
and t1.nround=t2.nround
and t1.nplayerid=t2.nplayerid
and t1.dt=t2.dt
where bpreset='true'
and t1.dt='${dt}'
group by t1.dt
)


select t1.*,t2.month_real_player_cnt,t3.new_player_cnt
      ,coalesce(preset_round_cnt,0) as preset_round_cnt
      ,coalesce(preset_player_cnt,0) as preset_player_cnt
      ,coalesce(reward_player_cnt,0) as reward_player_cnt
      ,coalesce(reward_win_round_cnt,0) as reward_win_round_cnt
      ,coalesce(collusion_player_cnt,0) as collusion_player_cnt
      ,coalesce(same_ip_player_cnt,0) as same_ip_player_cnt
      ,coalesce(abnormal_high_win_player_cnt,0) as abnormal_high_win_player_cnt
from total_cnt t1
left join month_total_cnt t2
on t1.dt=t2.dt
left join new_user_cnt t3
on t1.dt=t3.dt
left join preset_cnt t4
on t1.dt=t4.dt
left join 
(select dt,count(distinct playerid) as collusion_player_cnt
from collusion_player
group by dt) t5
on t1.dt=t5.dt
left join 
(select dt,count(distinct playerid) as same_ip_player_cnt
from same_ip_player
group by dt) t6
on t1.dt=t6.dt
left join 
(select dt,count(distinct nplayerid) as
abnormal_high_win_player_cnt
from abnormal_high_win_player
group by dt) t7
on t1.dt=t7.dt
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
            # 4. 建表 (daily_game_stats)
            # 参考 init_daily_stats.py 的结构，但适配 Hive 查询的字段
            # create_table_sql = """
            # CREATE TABLE IF NOT EXISTS daily_game_stats (
            #     id INT AUTO_INCREMENT PRIMARY KEY,
            #     stat_date DATE NOT NULL COMMENT '统计日期',
            #     round_cnt INT DEFAULT 0 COMMENT '昨日游戏总局数',
            #     day_real_player_cnt INT DEFAULT 0 COMMENT '昨日活跃用户数(非机器人)',
            #     month_real_player_cnt INT DEFAULT 0 COMMENT '近一个月活跃用户数(MAU)',
            #     new_player_cnt INT DEFAULT 0 COMMENT '昨日新增用户数',
            #     robot_round_cnt INT DEFAULT 0 COMMENT '机器人游戏局数',
            #     robot_round_pct FLOAT DEFAULT 0.0 COMMENT '机器人游戏占比',
            #     robot_win_round_cnt INT DEFAULT 0 COMMENT '机器人赢局数',
            #     robot_win_round_pct FLOAT DEFAULT 0.0 COMMENT '机器人胜率',
            #     preset_round_cnt INT DEFAULT 0 COMMENT '发牌干预局数',
            #     preset_player_cnt INT DEFAULT 0 COMMENT '发牌干预人数',
            #     reward_player_cnt INT DEFAULT 0 COMMENT '发牌干预被奖励人数',
            #     reward_win_round_cnt INT DEFAULT 0 COMMENT '发牌干预被奖励者赢局数',
            #     collusion_player_cnt INT DEFAULT 0 COMMENT '疑似伙牌用户数',
            #     same_ip_player_cnt INT DEFAULT 0 COMMENT '同IP用户数',
            #     abnormal_high_win_player_cnt INT DEFAULT 0 COMMENT '异常高胜率用户数',
            #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #     UNIQUE KEY idx_date (stat_date)
            # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日游戏业务统计表';
            # """
            # print("Checking/Creating table...")
            # cursor.execute(create_table_sql)
            
            # 5. 插入数据
            # 先删除该日期的所有旧数据，确保是 overwrite 而非 update
            delete_sql = "DELETE FROM daily_game_stats WHERE stat_date = %s"
            print(f"Deleting old data for date: {dt_str}...")
            cursor.execute(delete_sql, (dt_str,))

            print("Inserting data into MySQL...")
            insert_sql = """
            INSERT INTO daily_game_stats (
                stat_date, round_cnt, day_real_player_cnt, month_real_player_cnt, new_player_cnt,
                robot_round_cnt, robot_round_pct, robot_win_round_cnt, robot_win_round_pct,
                preset_round_cnt, preset_player_cnt, reward_player_cnt, reward_win_round_cnt,
                collusion_player_cnt, same_ip_player_cnt, abnormal_high_win_player_cnt
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                round_cnt=VALUES(round_cnt),
                day_real_player_cnt=VALUES(day_real_player_cnt),
                month_real_player_cnt=VALUES(month_real_player_cnt),
                new_player_cnt=VALUES(new_player_cnt),
                robot_round_cnt=VALUES(robot_round_cnt),
                robot_round_pct=VALUES(robot_round_pct),
                robot_win_round_cnt=VALUES(robot_win_round_cnt),
                robot_win_round_pct=VALUES(robot_win_round_pct),
                preset_round_cnt=VALUES(preset_round_cnt),
                preset_player_cnt=VALUES(preset_player_cnt),
                reward_player_cnt=VALUES(reward_player_cnt),
                reward_win_round_cnt=VALUES(reward_win_round_cnt),
                collusion_player_cnt=VALUES(collusion_player_cnt),
                same_ip_player_cnt=VALUES(same_ip_player_cnt),
                abnormal_high_win_player_cnt=VALUES(abnormal_high_win_player_cnt);
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
                dt_val = get_val(row, 'dt', dt_str) # 默认为昨天
                
                params = (
                    dt_val,
                    get_val(row, 'round_cnt'),
                    get_val(row, 'day_real_player_cnt'),
                    get_val(row, 'month_real_player_cnt'),
                    get_val(row, 'new_player_cnt'),
                    get_val(row, 'robot_round_cnt'),
                    get_val(row, 'robot_round_pct', 0.0),
                    get_val(row, 'robot_win_round_cnt'),
                    get_val(row, 'robot_win_round_pct', 0.0),
                    get_val(row, 'preset_round_cnt'),
                    get_val(row, 'preset_player_cnt'),
                    get_val(row, 'reward_player_cnt'),
                    get_val(row, 'reward_win_round_cnt'),
                    get_val(row, 'collusion_player_cnt'),
                    get_val(row, 'same_ip_player_cnt'),
                    get_val(row, 'abnormal_high_win_player_cnt')
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
