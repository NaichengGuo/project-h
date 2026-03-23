import pymysql
import random
from datetime import datetime, timedelta

def init_db():
    # 数据库连接配置 (参考 mysql-ec2.ipynb)
    config = {
        'host': '10.0.14.253',
        'port': 3306,
        'user': 'root',
        'password': 'Root123!',
        'database': 'algo_admin',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    try:
        connection = pymysql.connect(**config)
        
        with connection.cursor() as cursor:
            # 1. 建表代码
            print("Creating table ...")
            
            # 为了演示，如果表存在则先删除 (生产环境请谨慎使用 DROP)
            # drop_sql = "DROP TABLE IF EXISTS daily_system_stats"
            # cursor.execute(drop_sql)
            



            create_sql = """
    CREATE TABLE daily_game_stats (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stat_date DATE NOT NULL COMMENT '统计日期',
        
        -- 基础运营数据
        round_cnt INT DEFAULT 0 COMMENT '昨日游戏总局数',
        day_real_player_cnt INT DEFAULT 0 COMMENT '昨日活跃用户数(非机器人)',
        month_real_player_cnt INT DEFAULT 0 COMMENT '近一个月活跃用户数(MAU)',
        new_player_cnt INT DEFAULT 0 COMMENT '昨日新增用户数',
        
        -- 机器人数据
        robot_round_cnt INT DEFAULT 0 COMMENT '机器人游戏局数',
        robot_round_pct FLOAT DEFAULT 0.0 COMMENT '机器人游戏占比',
        robot_win_round_cnt INT DEFAULT 0 COMMENT '机器人赢局数',
        robot_win_round_pct FLOAT DEFAULT 0.0 COMMENT '机器人胜率',
        
        -- 发牌干预数据
        preset_round_cnt INT DEFAULT 0 COMMENT '发牌干预局数',
        preset_player_cnt INT DEFAULT 0 COMMENT '发牌干预人数',
        reward_player_cnt INT DEFAULT 0 COMMENT '发牌干预被奖励人数',
        reward_win_round_cnt INT DEFAULT 0 COMMENT '发牌干预被奖励者赢局数',
        
        -- 风控异常数据
        collusion_player_cnt INT DEFAULT 0 COMMENT '疑似伙牌用户数',
        same_ip_player_cnt INT DEFAULT 0 COMMENT '同IP用户数',
        abnormal_high_win_player_cnt INT DEFAULT 0 COMMENT '异常高胜率用户数',
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY idx_date (stat_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日游戏业务统计表';
            """
            cursor.execute(create_sql)
            print("Table created successfully.")

            # 2. 插入模拟数据
            print("Inserting mock data...")
            
            insert_sql = """
            INSERT INTO daily_system_stats_test 
            (stat_date, total_requests, avg_response_time, error_count, cpu_usage, memory_usage) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            mock_data = []
            today = datetime.now().date()
            
            # 生成过去 30 天的数据
            for i in range(30):
                date = today - timedelta(days=i)
                total_requests = random.randint(1000, 50000)
                avg_response_time = round(random.uniform(20.0, 500.0), 2)
                error_count = random.randint(0, int(total_requests * 0.05))
                cpu_usage = round(random.uniform(10.0, 90.0), 2)
                memory_usage = round(random.uniform(20.0, 80.0), 2)
                
                mock_data.append((
                    date, 
                    total_requests, 
                    avg_response_time, 
                    error_count, 
                    cpu_usage, 
                    memory_usage
                ))
            
            cursor.executemany(insert_sql, mock_data)
            connection.commit()
            print(f"Inserted {len(mock_data)} rows of mock data.")
            
            # 验证插入结果
            cursor.execute("SELECT COUNT(*) as cnt FROM daily_system_stats")
            result = cursor.fetchone()
            print(f"Current row count: {result['cnt']}")

    except Exception as e:
        print(f"Error: {e}")
        if 'connection' in locals() and connection.open:
            connection.rollback()
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    init_db()
