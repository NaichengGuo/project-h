

WITH player_total AS (
    SELECT 
        nplayerid,
        COUNT(DISTINCT CONCAT(sztoken, '-', nround)) AS total_games
    FROM poker.dws_db_player_game_result_di   
    WHERE dt = '${dt}'
    GROUP BY nplayerid
),
game_pairs AS (
    SELECT 
        a.sztoken,
        a.nround,
        LEAST(a.nplayerid, b.nplayerid) AS player1_id,
        GREATEST(a.nplayerid, b.nplayerid) AS player2_id,
        a.gameresult AS p1_result,
        b.gameresult AS p2_result
    FROM poker.dws_db_player_game_result_di a
    JOIN poker.dws_db_player_game_result_di b 
        ON a.sztoken = b.sztoken 
        AND a.nround = b.nround 
        AND a.nplayerid < b.nplayerid
    WHERE a.dt = '${dt}'
      AND b.dt = '${dt}'
),
pair_stats AS (
    SELECT 
        player1_id,
        player2_id,
        COUNT(DISTINCT CONCAT(sztoken, '-', nround)) AS total_games,
        COUNT(DISTINCT sztoken) AS total_desk,
        SUM(CASE WHEN p1_result > 0 OR p2_result > 0 THEN 1 ELSE 0 END) AS win_games,
        SUM(p1_result + p2_result) AS total_gameresult,
        COUNT(DISTINCT CONCAT(sztoken, '-', nround)) AS same_cnt
    FROM game_pairs
    GROUP BY player1_id, player2_id
),
-- 获取每个 player 最近30天的唯一登录IP（去重）
player_recent_ips AS (
    SELECT 
        nplayerid,
        preloginip
    FROM poker.ods_dz_db_table_user_df
    WHERE dt = '${dt}'
      AND substr(prelogintime, 1, 10) >= date_sub('${dt}', 30)
      AND substr(prelogintime, 1, 10) <= '${dt}'
      AND preloginip IS NOT NULL
      AND preloginip != ''
    GROUP BY nplayerid, preloginip
)
-- 基于已有 pair，计算每对玩家的共享IP
,pair_shared_ips AS (
    SELECT 
        ps.player1_id,
        ps.player2_id,
        COUNT(ip1.preloginip) AS shared_ip_cnts,
         COLLECT_LIST(ip1.preloginip) AS shared_ip
    FROM pair_stats ps
    JOIN player_recent_ips ip1 ON ps.player1_id = ip1.nplayerid
    JOIN player_recent_ips ip2 ON ps.player2_id = ip2.nplayerid
    WHERE ip1.preloginip = ip2.preloginip
    GROUP BY ps.player1_id, ps.player2_id
)

-- 主查询
insert overwrite table poker.dws_dz_player_collusion_cross_df partition (dt='${dt}')
SELECT 
    ps.player1_id,
    ps.player2_id,
    ps.total_games,
    ps.total_desk,
    ps.win_games,
    ROUND(ps.win_games * 1.0 / ps.total_games, 4) AS win_rate,
    ps.total_gameresult,
    ps.same_cnt,
    ROUND(ps.same_cnt * 1.0 / pt1.total_games, 9) AS player1_same_rate,
    ROUND(ps.same_cnt * 1.0 / pt2.total_games, 9) AS player2_same_rate,
    0 as player1_aggressive,
    0 as player1_agr_pct,
    0 as player1_call,
    0 as player1_call_pct,
    0 as player1_fold,
    0 as player1_fold_pct,
    0 as player2_aggressive,
    0 as player2_agr_pct,
    0 as player2_call,
    0 as player2_call_pct,
    0 as player2_fold,
    0 as player2_fold_pct,    
    si.shared_ip_cnts AS shared_ip_cnts,
    si.shared_ip AS shared_ip
FROM pair_stats ps
JOIN player_total pt1 ON ps.player1_id = pt1.nplayerid
JOIN player_total pt2 ON ps.player2_id = pt2.nplayerid
LEFT JOIN pair_shared_ips si 
    ON ps.player1_id = si.player1_id 
    AND ps.player2_id = si.player2_id
ORDER BY ps.player1_id, ps.player2_id;
