-- sng场每日输赢
with sztoken_award_400 as(
select distinct
  sztoken
  ,szroomname
  ,createtime
  ,substr(createtime,1,10) as create_dt
  ,cast(get_json_object(szRuleJson,'$.joinFeeUcoin') as bigint)/1000000 as entry_fee
  ,cast(get_json_object(szRuleJson,'$.awards[0].award') as bigint)/1000000 as award
from poker.ods_dz_db_table_dz_game_info_df
where dt='${dt}'
and ngametype=400)

,winner_reward_400 as(
select sztoken,nplayerid,reward/1000000 as reward
from poker.ods_dz_db_table_dz_match_result_df 
where dt='${dt}'
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
left join poker.ods_dz_db_table_user_df  t2
on t1.nplayerid=t2.nplayerid
where create_dt='${dt}'
and dt='${dt}')

,player_result_sng as(
select nplayerid,400 as ngametype,cast(brobot as int) as brobot,
  round(sum(player_pnl),2) as total_score,
  round(sum(case when player_pnl>=0 then player_pnl end),2) as win_score,
  round(sum(case when player_pnl<0 then player_pnl end),2) as lose_score,
  count(distinct sztoken) as total_sztoken
from player_pnl_400_robot
group by nplayerid,400,brobot
)


--79场折U计算
-- table_dz_game_info.UCoinRatio  （szToken）
-- math.floor((score / 1000) / UCoinRatio * 1000000 + 0.5)
--按sztoken取UCoinRatio
,sztoken_ucoinratio as(
select sztoken,UCoinRatio,ngametype
from poker.ods_dz_db_table_dz_game_info_df
where dt='${dt}'
and ngametype in (79,74)
group by sztoken,UCoinRatio,ngametype

)


--取每场积分结果数据
,player_round_u_79 as(
select t1.sztoken,nplayerid,t1.ngametype,substr(Createtime,1,10) as create_dt
    ,sum(nscore) as nscore
    ,coalesce(min(ucoinratio),1) as ucoinratio
    ,round(sum((nscore / 1000 / coalesce(UCoinRatio,1))),4) as player_pnl
from poker.ods_dz_db_table_dz_game_score_detail_df t1
left join sztoken_ucoinratio t2
on t1.sztoken=t2.sztoken
where dt='${dt}'
and t1.ngametype in (79,74)
and substr(Createtime,1,10)='${dt}'
group by t1.sztoken,nplayerid,t1.ngametype,substr(Createtime,1,10))

,player_round_robot as(
select t1.*,t2.brobot
from player_round_u_79 t1
left join poker.ods_dz_db_table_user_df t2
on t1.nplayerid=t2.nplayerid
where create_dt='${dt}'
and dt='${dt}')

,player_result_cash as(
select nplayerid,ngametype,cast(brobot as int) as brobot,
  round(sum(player_pnl),2) as total_score,
  round(sum(case when player_pnl>=0 then player_pnl end),2) as win_score,
  round(sum(case when player_pnl<0 then player_pnl end),2) as lose_score,
  count(distinct sztoken) as total_sztoken
from player_round_robot
group by nplayerid,ngametype,brobot
)

-- 450
--金币场数据
,gold_base as(
select ngametype, sztoken, nplayerid,brobot,gameresult/1000 as gameresult,substr(Createtime,1,10) as create_dt
from poker.ods_dz_db_table_dz_game_gold_score_detail_df 
where dt='${dt}'
and substr(Createtime,1,10)='${dt}')

,player_result_gold as(
select nplayerid,ngametype,cast(brobot as int) as brobot,
  round(sum(gameresult),2) as total_score,
  round(sum(case when gameresult>=0 then gameresult end),2) as win_score,
  round(sum(case when gameresult<0 then gameresult end),2) as lose_score,
  count(distinct sztoken) as total_sztoken
from gold_base
group by  nplayerid,ngametype,brobot)

insert overwrite table poker.dws_dz_player_win_lose_u_di partition(dt='${dt}')
select nplayerid,
      ngametype,
      brobot,
      total_score,
      win_score,
      lose_score,
      0 as win_robot_score,
      0 as win_human_score,
      0 as lose_to_human_score,
      0 as lose_to_robot_score,
      total_sztoken,
      0 as total_robot_sztoken,
      0 as total_human_sztoken
from(
select * from player_result_sng
union all 
select * from player_result_cash
union all 
select * from player_result_gold)t;
