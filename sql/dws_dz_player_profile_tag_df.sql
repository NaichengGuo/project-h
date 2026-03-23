-- 用户层标签汇总表
WITH 
-- 1. 基础用户信息
base AS (
  SELECT 
    nplayerid,
    szcreatetime AS regtime,
    brobot,
    preloginip,
    prelogintime
  FROM poker.ods_dz_db_table_user_df 
  WHERE dt = '${dt}'
),

-- 2. 俱乐部 & 昵称
player_name AS (
select nplayerid,sznickname,nclubid from(
  SELECT 
    nplayerid,
    sznickname,
    nclubid,
    row_number() over(partition by nplayerid order by nclubid asc) as rn
  FROM poker.ods_dz_db_table_dz_club_member_df 
  WHERE dt = '${dt}'
  )t
  where rn=1
),

-- 3. 牌风数据
play_style AS (
  SELECT 
    playerid,
    vpip,
    pfr,
    three_bet_pct,
    cbet_pct,
    af,
    allin_frequency,
    fold_rate,
    playing_style,
    data_quality
  FROM poker.dws_dz_player_tag_df 
  WHERE dt = '${dt}'
),

-- 4. 最喜欢的游戏类型
user_game_counts AS (
  SELECT 
    nplayerid,
    ngametype,
    COUNT(DISTINCT CONCAT(sztoken, nround)) AS round_cnts
  FROM poker.dws_db_player_game_result_di 
  WHERE dt >= DATE_SUB('${dt}', 30)
    AND nplayerid IS NOT NULL
    AND ngametype IS NOT NULL
  GROUP BY nplayerid, ngametype
),
user_preferred_game AS (
  SELECT 
    nplayerid,
    ngametype AS preferred_gametype,
    round_cnts AS preferred_game_rounds,
    ROW_NUMBER() OVER (PARTITION BY nplayerid ORDER BY round_cnts DESC, ngametype ASC) AS rn
  FROM user_game_counts
),
preferred_game_result AS (
  SELECT 
    nplayerid,
    preferred_gametype,
    preferred_game_rounds
  FROM user_preferred_game
  WHERE rn = 1
),

-- 5. 活跃行为（平均时长、活跃时段、活跃标签）
player_daily_activity AS (
  SELECT 
    nplayerid,
    SUBSTRING(createtime, 1, 10) AS game_date
  FROM poker.dws_db_player_game_result_di
  WHERE dt >= DATE_SUB('${dt}', 30)
    AND nplayerid IS NOT NULL
    AND createtime IS NOT NULL
    AND createtime != ''
),
player_active_days AS (
  SELECT 
    nplayerid,
    COUNT(DISTINCT game_date) AS active_days
  FROM player_daily_activity
  GROUP BY nplayerid
),
game_rounds_with_duration AS (
  SELECT 
    nplayerid,
    UNIX_TIMESTAMP(endtime, 'yyyy-MM-dd HH:mm:ss') - UNIX_TIMESTAMP(starttime, 'yyyy-MM-dd HH:mm:ss') AS round_duration_seconds
  FROM poker.dws_db_player_game_result_di
  WHERE dt >= DATE_SUB('${dt}', 30)
    AND nplayerid IS NOT NULL
    AND starttime IS NOT NULL 
    AND endtime IS NOT NULL
    AND starttime != '' 
    AND endtime != ''
    AND UNIX_TIMESTAMP(endtime, 'yyyy-MM-dd HH:mm:ss') > UNIX_TIMESTAMP(starttime, 'yyyy-MM-dd HH:mm:ss')
),
player_avg_duration AS (
  SELECT 
    nplayerid,
    ROUND(AVG(round_duration_seconds) / 60.0, 2) AS avg_round_duration_mins
  FROM game_rounds_with_duration
  GROUP BY nplayerid
),
player_hourly_activity AS (
  SELECT 
    nplayerid,
    CAST(SUBSTRING(starttime, 12, 2) AS INT) AS start_hour,
    COUNT(*) AS hour_rounds
  FROM poker.dws_db_player_game_result_di
  WHERE dt >= DATE_SUB('${dt}', 30)
    AND nplayerid IS NOT NULL
    AND starttime IS NOT NULL
    AND starttime != ''
  GROUP BY nplayerid, CAST(SUBSTRING(starttime, 12, 2) AS INT)
),
player_peak_hour AS (
  SELECT 
    nplayerid,
    start_hour AS peak_active_hour
  FROM (
    SELECT 
      nplayerid,
      start_hour,
      ROW_NUMBER() OVER (PARTITION BY nplayerid ORDER BY hour_rounds DESC, start_hour ASC) AS rn
    FROM player_hourly_activity
  ) t
  WHERE rn = 1
),
activity_summary AS (
  SELECT 
    COALESCE(pad.nplayerid, pav.nplayerid, ph.nplayerid) AS nplayerid,
    COALESCE(pad.active_days, 0) AS active_days,
    pav.avg_round_duration_mins,
    ph.peak_active_hour,
    CASE 
      WHEN pad.active_days >= 5 THEN 'high'
      WHEN pad.active_days >= 3 THEN 'medium'
      WHEN pad.active_days >= 1 THEN 'low'
      ELSE 'silent'
    END AS activity_level
  FROM player_active_days pad
  FULL OUTER JOIN player_avg_duration pav ON pad.nplayerid = pav.nplayerid
  FULL OUTER JOIN player_peak_hour ph ON COALESCE(pad.nplayerid, pav.nplayerid) = ph.nplayerid
),

-- 6. 伙牌标签
collusion_player AS (
  SELECT DISTINCT playerid
  FROM (
    SELECT player1_id AS playerid
    FROM poker.dws_dz_player_collusion_cross_df 
    WHERE dt = '${dt}'
      AND same_cnt >= 20
      AND win_rate >= 0.7
      AND (player1_same_rate >= 0.75 OR player2_same_rate >= 0.75)
      AND total_desk >= 3
    UNION ALL
    SELECT player2_id AS playerid
    FROM poker.dws_dz_player_collusion_cross_df 
    WHERE dt = '${dt}'
      AND same_cnt >= 20
      AND win_rate >= 0.7
      AND (player1_same_rate >= 0.75 OR player2_same_rate >= 0.75)
      AND total_desk >= 3
  ) t
),

-- 7. 与机器人对战表现
human_vs_bot_hands AS (
  SELECT 
    h.nplayerid,
    h.gameresult,
    h.ngametype,
    h.create_dt
  FROM poker.dws_db_player_game_result_di h
  LEFT JOIN poker.dws_db_player_game_result_di r
    ON h.sztoken = r.sztoken 
   AND h.nround = r.nround
   AND h.dt = r.dt
  WHERE h.dt >= DATE_SUB('${dt}', 30)
    AND h.brobot = 0
    AND h.nplayerid IS NOT NULL
  GROUP BY h.nplayerid, h.gameresult, h.ngametype, h.create_dt
  HAVING MAX(CASE WHEN r.brobot = 1 THEN 1 ELSE 0 END) = 1
),
player_stats_vs_bot AS (
  SELECT 
    nplayerid,
    COUNT(*) AS total_hands_vs_bot,
    SUM(CASE WHEN gameresult > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate_vs_bot,
    AVG(gameresult) AS avg_profit_vs_bot,
    SUM(CASE WHEN ngametype = 450 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS high_stakes_ratio
  FROM human_vs_bot_hands
  GROUP BY nplayerid
  HAVING COUNT(*) >= 10
),
total_hands_all AS (
  SELECT 
    nplayerid,
    COUNT(DISTINCT CONCAT(sztoken, nround)) AS total_hands_all
  FROM poker.dws_db_player_game_result_di
  WHERE dt >= DATE_SUB('${dt}', 30)
    AND brobot = 0
    AND nplayerid IS NOT NULL
  GROUP BY nplayerid
),
bot_performance AS (
  SELECT 
    s.nplayerid,
    s.total_hands_vs_bot,
    ROUND(s.win_rate_vs_bot, 4) AS win_rate_vs_bot,
    ROUND(s.avg_profit_vs_bot, 2) AS avg_profit_vs_bot,
    s.high_stakes_ratio,
    ROUND(s.total_hands_vs_bot * 1.0 / NULLIF(t.total_hands_all, 0), 4) AS bot_hands_ratio,
    CASE
      WHEN s.win_rate_vs_bot > 0.60 AND s.avg_profit_vs_bot > 0 THEN 'Exploiter (剥削者)'
      WHEN s.win_rate_vs_bot < 0.40 AND s.avg_profit_vs_bot < 0 THEN 'Struggling (挣扎者)'
      WHEN s.win_rate_vs_bot BETWEEN 0.40 AND 0.60 THEN 'Balanced (平衡型)'
      WHEN s.total_hands_vs_bot * 1.0 / NULLIF(t.total_hands_all, 0) > 0.8 THEN 'Bot Hunter (猎人)'
      ELSE 'Unclassified'
    END AS player_profile_label
  FROM player_stats_vs_bot s
  LEFT JOIN total_hands_all t ON s.nplayerid = t.nplayerid
)

-- 最终汇总
-- 最终汇总（修复 NULL 问题）
insert overwrite table poker.dws_dz_player_profile_tag_df partition(dt='${dt}')
SELECT 
  b.nplayerid,
  -- 基础信息（保留 NULL 合理）
  b.regtime,
  b.brobot,
  b.preloginip,
  b.prelogintime,
  
  -- 俱乐部 & 昵称
  COALESCE(n.sznickname, 'unknown') AS sznickname,
  COALESCE(n.nclubid, -1) AS nclubid,
  
  -- 牌风（无数据时设为 NULL + quality=insufficient）
  ps.vpip,
  ps.pfr,
  ps.three_bet_pct,
  ps.cbet_pct,
  ps.af,
  COALESCE(ps.allin_frequency, 0.0) AS allin_frequency,
  COALESCE(ps.fold_rate, 0.0) AS fold_rate,
  COALESCE(ps.playing_style, 'Insufficient Data') AS playing_style,
  COALESCE(ps.data_quality, 'insufficient') AS data_quality,
  
  -- 游戏偏好
  COALESCE(pg.preferred_gametype, -1) AS preferred_gametype,
  COALESCE(pg.preferred_game_rounds, 0) AS preferred_game_rounds,
  
  -- 活跃行为（核心修复点）
  COALESCE(a.active_days, 0) AS active_days,
  COALESCE(a.avg_round_duration_mins, 0.0) AS avg_round_duration_mins,
  COALESCE(a.peak_active_hour, -1) AS peak_active_hour,
  COALESCE(a.activity_level, 'silent') AS activity_level,
  
  -- 伙牌标签
  CASE WHEN c.playerid IS NOT NULL THEN 'collusion_suspected' ELSE 'normal' END AS collusion_status,
  
  -- 机器人对战（无对局时设为 0 / unknown）
  COALESCE(bp.total_hands_vs_bot, 0) AS total_hands_vs_bot,
  COALESCE(bp.win_rate_vs_bot, 0.0) AS win_rate_vs_bot,
  COALESCE(bp.avg_profit_vs_bot, 0.0) AS avg_profit_vs_bot,
  COALESCE(bp.high_stakes_ratio, 0.0) AS high_stakes_ratio,
  COALESCE(bp.bot_hands_ratio, 0.0) AS bot_hands_ratio,
  COALESCE(bp.player_profile_label, 'No Bot Games') AS player_profile_label
  
  -- '${dt}' AS dt

FROM base b
LEFT JOIN player_name n ON b.nplayerid = n.nplayerid
LEFT JOIN play_style ps ON b.nplayerid = ps.playerid
LEFT JOIN preferred_game_result pg ON b.nplayerid = pg.nplayerid
LEFT JOIN activity_summary a ON b.nplayerid = a.nplayerid
LEFT JOIN collusion_player c ON b.nplayerid = c.playerid
LEFT JOIN bot_performance bp ON b.nplayerid = bp.nplayerid
;