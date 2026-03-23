import pymysql
import pandas as pd



# python /mnt/workspace/draft/hive_2ops_db/sync_poker_hive_to_mysql.py --dt 2026-03-17
def read_from_mysql():
    # 数据库连接配置
    config = {
        'host': 'test.cjudqgucury7.ap-southeast-1.rds.amazonaws.com',      # 数据库地址
        #'host':'54.179.157.179',
        #'host':'127.0.0.1',
        'port': 3306,             # 端口
        'user': 'poker_analysis_user1',           # 用户名
        'password': 'password01',   # 密码
        # 'database': 'algo_admin',    # 数据库名
        'charset': 'utf8mb4',     # 字符集
        'cursorclass': pymysql.cursors.DictCursor
    }

    try:
        # 建立连接
        connection = pymysql.connect(**config)
        try:
            # 方法1：使用 cursor 执行 SQL
            with connection.cursor() as cursor:
                sql = "show databases;"
                cursor.execute(sql)
                result = cursor.fetchall()
                print("--- Cursor Result ---")
                for row in result:
                    print(row)

        finally:
            # 关闭连接
            connection.close()
            
    except Exception as e:
        print(f"Error: {e}")

read_from_mysql()