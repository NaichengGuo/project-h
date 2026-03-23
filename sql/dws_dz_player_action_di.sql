-- excute command: spark-submit dws_dz_seat_info_di-pyspark.py 2025-12-25 

-- CREATE EXTERNAL TABLE IF NOT EXISTS poker.dws_dz_player_action_di (
--   `createdate` string COMMENT '日期，格式 yyyy-MM-dd',
--   `sztoken` string COMMENT '对应游戏桌的 szToken',
--   `nround` int COMMENT '第几手',
--   `playerid` string COMMENT '玩家ID',
--   `seat` string COMMENT '座位信息',
--   `json_index` int COMMENT 'JSON索引序号',
--   `minbetscore` int COMMENT '最小下注分数',
--   `maxbetscore` int COMMENT '最大下注分数',
--   `minaddscore` int COMMENT '最小加注分数',
--   `action` string COMMENT '玩家操作类型',
--   `seatbetstate` int COMMENT '座位下注状态',
--   `betscore` int COMMENT '下注分数',
--   `seatcurbet` int COMMENT '座位当前下注',
--   `poolscore` int COMMENT '池中分数',
--   `predealct` int COMMENT '预发牌计数',
--   `commonCard` string COMMENT '公共牌信息',
--   `stage` string COMMENT '游戏阶段（preflop/flop/turn/river）',
--   `gameresult` string COMMENT '游戏结果',
--   `isjumpinsure` int COMMENT '是否跳出买保险',
--   `isInsure` int COMMENT '是否买保险',
--   `score` int COMMENT '得分',
--   `insureWinScores` int COMMENT '保险赢分',
--   `Betaction` string COMMENT '下注动作',
--   `gametype` int COMMENT '游戏类型'
-- )
-- COMMENT 'dws层：德州扑克游戏操作详情明细表'
-- PARTITIONED BY (
--   `dt` string COMMENT '分区字段，格式 yyyy-MM-dd'
-- )
-- STORED AS PARQUET
-- LOCATION 's3://aws-logs-796973487589-ap-southeast-1/hive/warehouse/poker/dws_dz_game_action_detail_di'
-- TBLPROPERTIES (
--   'aws.spark.fgac.transient.isRegisteredWithLakeFormation'='false',
--   'bucketing_version'='2',
--   'transient_lastDdlTime'='1766820051'
-- );


WITH 
-- 1. Base Log: Read DWD once, parse JSON once to avoid repeated extraction
base_log AS (
    SELECT
        dwd.sztoken,
        dwd.nround,
        dwd.playerid,
        get_json_object(dwd.CardData, '$.json_index') AS json_index,
        get_json_object(dwd.CardData, '$.name') AS action,
        dwd.CardData,
        -- Extract the data object once
        get_json_object(dwd.CardData, '$.data') AS data_json
    FROM poker.dwd_dz_manual_data_di dwd -- pyspark任务
    WHERE dt = '${dt}' AND playerid <> 0
),

-- 2. Parsed Log: Extract all necessary fields from the JSON
parsed_log AS (
    SELECT
        sztoken,
        nround,
        playerid,
        json_index,
        action,
        -- Metrics
        get_json_object(data_json, '$.minBetScore') as minbetscore,
        get_json_object(data_json, '$.maxBetScore') as maxbetscore,
        get_json_object(data_json, '$.minAddScore') as minaddscore,
        get_json_object(data_json, '$.seatBetState') as seatbetstate,
        get_json_object(data_json, '$.betScore') as betscore,
        get_json_object(data_json, '$.seatCurBet') as seatcurbet,
        get_json_object(data_json, '$.poolScore') as poolscore,
        get_json_object(data_json, '$.score') as score,
        get_json_object(data_json, '$.state') as state,
        
        -- Seat Logic Fields
        get_json_object(data_json, '$.curSeat') as curSeat,
        get_json_object(get_json_object(data_json, '$.seatInfos[0]'), '$.seat') as seatInfoSeat,
        get_json_object(data_json, '$.seat') as dataSeat,
        
        -- Complex Fields (keep raw string for lateral views/regex)
        get_json_object(data_json, '$.commonCards') as commonCards_raw,
        get_json_object(data_json, '$.insureWinLos') as insureWinLos_raw,
        get_json_object(data_json, '$.seatCurBets') as seatCurBets_raw,
        get_json_object(data_json, '$.smallBlindSeat') as smallBlindSeat,
        get_json_object(data_json, '$.bigBlindSeat') as bigBlindSeat
    FROM base_log
),

-- 3. Seat Info: Read DWS once
seat_info AS (
    SELECT
        createdate,
        sztoken,
        nround,
        gametype,
        playerid,
        seat
    FROM poker.dws_dz_seat_info_di
    WHERE dt='${dt}'
    GROUP BY createdate, sztoken, nround, gametype, playerid, seat
),

-- 4. T2: BuyInsure Score
t2 AS (
    SELECT
        sztoken,
        nround,
        dataSeat as seat,
        action,
        sum(cast(score as double)) as score
    FROM parsed_log
    WHERE action = 'S2CBuyInsure' AND cast(score as double) <> 0
    GROUP BY sztoken, nround, dataSeat, action
),

-- 5. T3: Conclude (Lateral View)
t3 AS (
    SELECT
        p.sztoken,
        p.nround,
        t.seat_index + 1 as seat,
        p.action,
        t.value
    FROM parsed_log p
    LATERAL VIEW posexplode(split(regexp_replace(p.insureWinLos_raw, '[\\[\\]]', ''), ',')) t as seat_index, value
    WHERE p.action = 'S2CStateConclude' AND t.value <> 0
    GROUP BY p.sztoken, p.nround, t.seat_index, p.action, t.value
),

-- 6. T4: BuyInsure State
t4 AS (
    SELECT
        sztoken,
        nround,
        dataSeat as seat,
        json_index,
        state,
        action
    FROM parsed_log
    WHERE action = 'S2CBuyInsure'
    GROUP BY sztoken, nround, dataSeat, json_index, state, action
),

-- 7. C: GameStart (Lateral View)
c AS (
    SELECT
        p.sztoken,
        p.action,
        p.nround,
        (t.seat_index + 1) as seat,
        t.seatcurbet,
        t.seatcurbet as betscore,
        if((t.seat_index+1) = p.smallBlindSeat, 1, 0) as issmallBlind,
        if((t.seat_index+1) = p.bigBlindSeat, 1, 0) as isbigBlind,
        p.poolScore
    FROM parsed_log p
    LATERAL VIEW posexplode(split(regexp_replace(p.seatCurBets_raw, '[\\[\\]]', ''), ',')) t as seat_index, seatcurbet
    WHERE p.action = 'S2CStateGameStart'
    GROUP BY p.sztoken, p.action, p.nround, t.seat_index, t.seatcurbet, p.smallBlindSeat, p.bigBlindSeat, p.poolScore
),

-- 8. T1: Main Event Stream (Reconstructing the Union Logic)
t1_events AS (
    SELECT
        p.*,
        CASE 
            WHEN p.action = 'S2CStatePlayerOp' THEN p.curSeat
            WHEN p.action = 'S2CStateBuyInsure' THEN p.seatInfoSeat
            ELSE p.dataSeat
        END as derived_seat,
        if(p.action='S2CStateBuyInsure', 1, 0) as isjumpinsure,
        if(p.action='S2CStateDealCard', regexp_replace(p.commonCards_raw, '[\\[\\]]', ''), null) as commonCards
    FROM parsed_log p
),

-- Logic Part A: action IN (...) -> Join on seat
t1_part_a AS (
    SELECT
        s.createdate,
        e.sztoken,
        e.nround,
        s.playerid,
        s.seat,
        e.json_index,
        e.minbetscore,
        e.maxbetscore,
        e.minaddscore,
        e.action,
        e.seatbetstate,
        e.betscore,
        e.seatcurbet,
        e.poolscore,
        e.isjumpinsure,
        null as commonCards,
        s.gametype
    FROM t1_events e
    JOIN seat_info s ON e.sztoken = s.sztoken AND e.nround = s.nround AND e.derived_seat = s.seat
    WHERE e.action IN (
        'S2CDelayOpTime', 'S2CGiveUp', 'S2CStatePlayerOp', 'S2CBuyInsure',
        'S2CDealTwiceOp', 'S2CPushBet', 'S2CShowHandCard', 'S2CShowMyCard',
        'S2CStateBuyInsure', 'S2CUpdateScore'
    )
),

-- Logic Part B: action NOT IN (...) -> Join on sztoken, nround (Broadcast to all seats)
t1_part_b AS (
    SELECT
        s.createdate,
        e.sztoken,
        e.nround,
        s.playerid,
        s.seat,
        e.json_index,
        e.minbetscore,
        e.maxbetscore,
        e.minaddscore,
        e.action,
        e.seatbetstate,
        e.betscore,
        e.seatcurbet,
        e.poolscore,
        e.isjumpinsure,
        e.commonCards,
        s.gametype
    FROM t1_events e
    JOIN seat_info s ON e.sztoken = s.sztoken AND e.nround = s.nround
    WHERE e.action NOT IN (
        'S2CDelayOpTime', 'S2CGiveUp', 'S2CStatePlayerOp', 'S2CBuyInsure',
        'S2CDealTwiceOp', 'S2CPushBet', 'S2CShowHandCard', 'S2CShowMyCard',
        'S2CStateBuyInsure', 'S2CUpdateScore',
        'RoomInfos', 'SeatInfos'
    )
),

t1_combined AS (
    SELECT * FROM t1_part_a
    UNION ALL
    SELECT * FROM t1_part_b
),

-- 9. Game Result (Read ODS once)
game_result AS (
    select sztoken, nround, nplayerid as playerid, gameresult
    from poker.ods_dz_db_table_dz_game_score_detail_df
    where dt='${dt}'
    group by sztoken, nround, nplayerid, gameresult
),

-- 10. Intermediate Result (Window Functions Part 1)
intermediate_result AS (
    SELECT
        t1.createdate,
        t1.sztoken,
        t1.nround,
        t1.playerid,
        t1.seat,
        t1.json_index,
        
        -- Fill missing values
        coalesce(LAST_VALUE(t1.minbetscore, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
                 LAST_VALUE(t1.minbetscore, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)) as minbetscore,
                 
        coalesce(LAST_VALUE(t1.maxbetscore, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
                 LAST_VALUE(t1.maxbetscore, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)) as maxbetscore,
                 
        coalesce(LAST_VALUE(t1.minaddscore, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
                 LAST_VALUE(t1.minaddscore, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)) as minaddscore,
                 
        t1.action,
        t1.seatbetstate,
        t1.betscore,
        t1.seatcurbet,
        
        LAST_VALUE(t1.poolscore, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as poolscore,
        
        t1.isjumpinsure,
        
        LAST_VALUE(t1.commonCards, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS commonCard,
        
        t2.score,
        
        coalesce(LAST_VALUE(t3.value, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
                 LAST_VALUE(t3.value, true) OVER (PARTITION BY t1.sztoken, t1.nround, t1.playerid ORDER BY cast(t1.json_index as int) ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)) as value,
                 
        t1.gametype,
        
        case when t4.state = 1 then 'ins_none'
             when t4.state = 2 then 'ins_buy'
             when t4.state = 3 then 'ins_giveup'
             when t4.state = 4 then 'ins_buying'
             when t4.state = 5 then 'ins_bupai_invalid'
             when t4.state = 6 then 'ins_auto_buy'
        end as state
        
    FROM t1_combined t1
    LEFT JOIN t2 ON t1.sztoken = t2.sztoken AND t1.nround = t2.nround AND t1.seat = t2.seat AND t1.action = t2.action
    LEFT JOIN t3 ON t1.sztoken = t3.sztoken AND t1.nround = t3.nround AND t1.seat = t3.seat AND t1.action = t3.action
    LEFT JOIN t4 ON t1.sztoken = t4.sztoken AND t1.nround = t4.nround AND t1.seat = t4.seat AND t1.action = t4.action AND t1.json_index = t4.json_index
)
insert overwrite table poker.dws_dz_player_action_di partition(dt='${dt}')
-- Final Select
SELECT
    a.createdate,
    a.sztoken,
    a.nround,
    a.playerid,
    a.seat,
    row_number() over(partition by a.sztoken,a.nround order by cast(json_index as int), cast(if(c.issmallBlind=1,0,if(c.isbigBlind=1,1,a.playerid)) as int)) json_index,
    a.minbetscore,
    a.maxbetscore,
    a.minaddscore,
    a.action,
    a.seatbetstate,
    if(a.action ='S2CStateGameStart',c.betscore,a.betscore) as betscore,
    if(a.action ='S2CStateGameStart',c.seatcurbet,a.seatcurbet) as seatcurbet,
    case when a.action ='S2CStateGameStart' and c.issmallBlind=1 then c.betscore
         when a.action ='S2CStateGameStart' and c.isbigBlind=1 then sum(if(a.action ='S2CStateGameStart' and (c.issmallBlind=1 or c.isbigBlind=1),c.betscore,0)) over(partition by a.sztoken,a.nround)
         when row_number() over(partition by a.sztoken,a.nround order by cast(json_index as int), cast(if(c.issmallBlind=1,0,if(c.isbigBlind=1,1,a.playerid)) as int))=1 then if(a.action ='S2CStateGameStart',c.betscore,a.betscore)
         else a.poolscore end as poolscore,
    coalesce(count(distinct commonCard) over(partition by a.sztoken, a.nround, a.playerid, a.seat order by cast(json_index as int)), 0) as predealct,
    a.commonCard,
    case when size(split(commonCard,','))=3 then 'flop'
         when size(split(commonCard,','))=4 then 'turn'
         when size(split(commonCard,','))=5 then 'river'
         else 'preflop'
    end as stage,
    b.gameresult,
    if(score>0,1,isjumpinsure) as isjumpinsure,
    if(score>0,1,0) as isInsure,
    score,
    value + coalesce(LAST_VALUE(score, true) OVER (PARTITION BY a.sztoken, a.nround, a.playerid ORDER BY cast(a.json_index as int) ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
                     LAST_VALUE(score, true) OVER (PARTITION BY a.sztoken, a.nround, a.playerid ORDER BY cast(json_index as int) ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)) as insureWinScores,
    case when a.action='S2CBuyInsure' then state
         when a.action ='S2CStateGameStart' then 'init'
         when a.action ='S2CGiveUp' then 'Fold'
         when seatbetstate =1 then 'none'
         when seatbetstate =2 then 'check'
         when seatbetstate =3 then 'call'
         when seatbetstate =4 then 'raise'
         when seatbetstate =5 then 'allin'
         when seatbetstate =6 then 'fold'
    end as Betaction,
    a.gametype
FROM intermediate_result a
LEFT JOIN game_result b ON a.sztoken = b.sztoken AND a.nround = b.nround AND a.playerid = b.playerid
LEFT JOIN c ON a.sztoken = c.sztoken AND a.nround = c.nround AND a.seat = c.seat AND a.action = c.action
;
