with non_gold_score as(
select ngametype,sztoken,nplayerid,nround,gameresult,substr(createtime,1,10) as create_dt
from poker.ods_dz_db_table_dz_game_score_detail_df 
where dt='${dt}'
and substr(createtime,1,10)='${dt}')

,non_gold_sum as(
select t1.*,t2.brobot,t2.robotversion
from non_gold_score t1
left join poker.dws_dz_robot_info_di t2
on t1.sztoken=t2.sztoken
and t1.nround=t2.nround
and t1.nplayerid=t2.playerid)

,gold_score as(
select ngametype,sztoken,nplayerid,nround,gameresult,substr(createtime,1,10) as create_dt
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

insert overwrite table poker.dws_dz_player_win_lose_round_di partition(dt='${dt}')
select 
  nplayerid
  ,ngametype
  ,coalesce(brobot,0) as brobot
  ,count(distinct case when gameresult>0 then concat(sztoken,nround) end)  as win_cnt
  ,count(distinct case when gameresult=0 then concat(sztoken,nround) end) as tie_cnt
  ,count(distinct case when gameresult<0 then concat(sztoken,nround) end)  as lose_cnt
  ,count(distinct concat(sztoken,nround)) as total_cnt
  ,0 as total_robot_round
  ,0 as total_human_round
  ,0 as win_robot_round
  ,0 as win_human_round
  ,0 as lose_to_robot_round
  ,0 as lose_to_human_round
from sum_score
group by nplayerid
  ,ngametype
  ,coalesce(brobot,0);