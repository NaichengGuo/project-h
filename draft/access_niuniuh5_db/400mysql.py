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
with sztoken_award_400 as(
select distinct
  sztoken
  ,szroomname
  ,createtime
  ,substr(createtime,1,10) as create_dt
  ,cast(get_json_object(szRuleJson,'$.joinFeeUcoin') as bigint)/1000000 as entry_fee
  ,cast(get_json_object(szRuleJson,'$.awards[0].award') as bigint)/1000000 as award
from table_dz_game_info
where substr(createtime,1,10)='${dt}'
and ngametype=400)

,winner_reward_400 as(
select sztoken,nplayerid,reward/1000000 as reward
from table_dz_match_result
where substr(tCreateTime,1,10)='${dt}'
and ngametype=400
)

,player_pnl_400 as(
select t1.sztoken,t2.nplayerid,create_dt
  ,case when t2.reward>0 then t2.reward-t1.entry_fee
    else -t1.entry_fee end as player_pnl
from sztoken_award_400 t1
left join winner_reward_400 t2
on t1.sztoken=t2.sztoken)

,player_pnl_400_robot as(
select t1.nplayerid,sztoken,t2.brobot,player_pnl 
from player_pnl_400 t1
left join table_user  t2
on t1.nplayerid=t2.nplayerid
where create_dt='${dt}'
and dt='${dt}')

select nplayerid,400 as ngametype,brobot,
  round(sum(player_pnl),2) as total_score
from player_pnl_400_robot
group by nplayerid,400,brobot;
"""

df=read_from_mysql(sql_400)
df.head()
