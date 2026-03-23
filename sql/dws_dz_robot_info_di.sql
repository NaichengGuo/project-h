insert overwrite table poker.dws_dz_robot_info_di partition(dt='${dt}')
select t1.playerid
  ,sztoken
  ,nround
  ,robotversion
  ,brobot
from
(select 
   playerid
  ,sztoken
  ,nround
  ,get_json_object(get_json_object(carddata, '$.data'),'$.modelVersion') AS robotversion
  ,dt
from poker.dwd_dz_manual_data_di
where dt ='${dt}'
and get_json_object(carddata,'$.name')='ModelVer') t1
left join poker.ods_dz_db_table_user_df t2
on t1.playerid=t2.nplayerid
where t2.dt ='${dt}'; 