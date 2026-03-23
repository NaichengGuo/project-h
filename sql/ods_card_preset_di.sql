insert overwrite table poker.ods_card_preset_di partition(dt='${dt}')
select get_json_object(tstr,'$.szToken') as sztoken
      ,get_json_object(tstr,'$.nround') as nround
      ,get_json_object(tstr,'$.gametype') as ngametype 
      ,get_json_object(tstr,'$.smallblind') as smallblind
      ,get_json_object(tstr,'$.nplayerid') as nplayerid
      ,get_json_object(tstr,'$.seat') as seat
      ,get_json_object(tstr,'$.score') as startscore 
      ,get_json_object(tstr,'$.brobot') as brobot
      ,get_json_object(tstr,'$.cards') as handcards --
      ,get_json_object(tstr,'$.commoncards') as commoncards
      ,get_json_object(tstr,'$.bPreset') as bpreset
      ,get_json_object(tstr,'$.inventionType') as inventiontype
      ,get_json_object(tstr,'$.presetType') as presettype
      ,get_json_object(tstr,'$.redisScore') as redisscore
from poker.ods_temp_test_tab
where dt='${dt}';