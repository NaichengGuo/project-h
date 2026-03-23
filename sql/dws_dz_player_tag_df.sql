-- CREATE EXTERNAL TABLE `poker.dws_dz_player_tag_df`(
--   `playerid` bigint COMMENT '玩家ID',
--   `total_hands` bigint COMMENT '总手牌数',
--   `vpip` double COMMENT '自愿入池率(VPIP)',
--   `pfr` double COMMENT '翻牌前加注率(PFR)',
--   `three_bet_pct` double COMMENT '3-bet频率',
--   `cbet_pct` double COMMENT '持续下注率(C-bet)',
--   `af` double COMMENT '激进系数(AF)',
--   `allin_frequency` double COMMENT 'All-in频率',
--   `fold_rate` double COMMENT '弃牌率',
--   `playing_style` string COMMENT '玩家风格标签',
--   `data_quality` string COMMENT '数据质量评级'
-- )
-- COMMENT '德州扑克玩家牌风标签表'
-- PARTITIONED BY (
--   `dt` string COMMENT '数据日期分区'
-- )
-- STORED AS PARQUET
-- LOCATION 's3://aws-logs-796973487589-ap-southeast-1/hive/warehouse/poker/dws_dz_player_tag_df';

-- 增强版德州扑克玩家牌风分析（含修正后的 3-bet 和 C-bet 逻辑）
WITH base as(
select distinct sztoken,nround,playerid,json_index,action,stage,betaction
from poker.dws_dz_player_action_di p
where dt >= date_sub('${dt}', 7)
    and p.betaction is not null 
    and p.betaction not in ('init')
),
-- Step 1: 提取每局 preflop 阶段的所有加注动作，并分配全局顺序
preflop_raise_actions AS (
  SELECT 
    sztoken,
    nround,
    playerid,
    json_index,
    betaction,
    ROW_NUMBER() OVER (
      PARTITION BY sztoken, nround 
      ORDER BY json_index
    ) AS raise_order_in_preflop
  FROM base
  WHERE stage = 'preflop'
    AND betaction IN ('raise', 'allin')
),

-- Step 2: 标记每个玩家每局是否执行了 3-bet（即 preflop 中非首次加注）
player_hand_3bet AS (
  SELECT 
    sztoken,
    nround,
    playerid,
    MAX(CASE WHEN raise_order_in_preflop > 1 THEN 1 ELSE 0 END) AS is_3bet
  FROM preflop_raise_actions
  GROUP BY sztoken, nround, playerid
),

-- -- Step 3: 提取每局 flop 阶段的首个下注玩家（用于 C-bet 判断）
-- flop_first_bettor AS (
--   SELECT 
--     sztoken,
--     nround,
--     playerid
--   FROM (
--     SELECT 
--       sztoken,
--       nround,
--       playerid,
--       ROW_NUMBER() OVER (
--         PARTITION BY sztoken, nround 
--         ORDER BY json_index
--       ) AS rn
--     FROM base
--     WHERE stage = 'flop'
--       AND betaction IN ('raise', 'allin')
--   ) t
--   WHERE rn = 1
-- ),

-- Step 4: 提取所有在 preflop 加注的玩家（用于 C-bet 判断）
preflop_raiser AS (
  SELECT DISTINCT
    sztoken,
    nround,
    playerid
  FROM base
  WHERE stage = 'preflop'
    AND betaction IN ('raise', 'allin')
),

-- 提取所有preflop加注且flop阶段持续加注的玩家（用于 C-bet 判断）
cbet_player as(
 select distinct t1.sztoken,
    t1.nround,
    t1.playerid
  from preflop_raiser t1
  inner join 
  (SELECT DISTINCT
    sztoken,
    nround,
    playerid
  FROM base
  WHERE stage = 'flop'
    AND betaction IN ('raise', 'allin')) t2
  on t1.sztoken=t2.sztoken
  and t1.nround=t2.nround
  and t1.playerid=t2.playerid
),


-- Step 5: 聚合每局每位玩家的核心行为（主表）
player_hand_actions AS (
  SELECT
    p.sztoken,
    p.nround,
    p.playerid,
    
    -- VPIP: preflop 非弃牌
    MAX(CASE WHEN p.stage = 'preflop' AND p.betaction IN ('call', 'raise', 'allin') THEN 1 ELSE 0 END) AS is_vpip,
    
    -- PFR: preflop 加注
    MAX(CASE WHEN p.stage = 'preflop' AND p.betaction IN ('raise', 'allin') THEN 1 ELSE 0 END) AS is_pfr,
    
    -- 3-bet: 来自修正逻辑
    MAX(COALESCE(t.is_3bet, 0)) AS is_3bet,
    
    -- C-bet: preflop 加注者 + flop 首个下注者
    MAX(CASE 
        WHEN f.playerid IS NOT NULL THEN 1 
        ELSE 0 
    END) AS is_cbet,
    
    -- Post-flop 攻击性行为（flop/turn/river）
    SUM(CASE WHEN p.stage IN ('flop', 'turn', 'river') AND p.betaction IN ('raise', 'allin') THEN 1 ELSE 0 END) AS aggression_actions,
    SUM(CASE WHEN p.stage IN ('flop', 'turn', 'river') AND p.betaction IN ('call', 'check') THEN 1 ELSE 0 END) AS passive_actions,
    
    -- 全局弃牌次数 & All-in 次数
    SUM(CASE WHEN p.betaction = 'Fold' THEN 1 ELSE 0 END) AS fold_count,
    SUM(CASE WHEN p.betaction = 'allin' THEN 1 ELSE 0 END) AS allin_count,
    
    -- 总动作数（用于计算比率）
    COUNT(*) AS total_actions_per_hand
    
  FROM base p
  LEFT JOIN player_hand_3bet t
    ON p.sztoken = t.sztoken
   AND p.nround = t.nround
   AND p.playerid = t.playerid
  LEFT JOIN cbet_player f
    ON p.sztoken = f.sztoken
   AND p.nround = f.nround
   AND p.playerid = f.playerid
  LEFT JOIN preflop_raiser r
    ON p.sztoken = r.sztoken
   AND p.nround = r.nround
   AND p.playerid = r.playerid
  -- WHERE f.playerid IS NOT NULL  -- 仅保留 C-bet 手牌（若需保留所有手牌，请移除此条件并在 CASE 中判断）
  GROUP BY p.sztoken, p.nround, p.playerid
),


-- Step 6: 汇总到玩家粒度（增加数据质量判断依据）
player_stats AS (
  SELECT
    playerid,
    COUNT(*) AS total_hands,
    SUM(is_vpip) AS vpip_hands,
    SUM(is_pfr) AS pfr_hands,
    SUM(is_3bet) AS three_bet_hands,
    SUM(is_cbet) AS cbet_hands,
    SUM(aggression_actions) AS agg_count,
    SUM(passive_actions) AS pass_count,
    SUM(fold_count) AS total_folds,
    SUM(allin_count) AS total_allins,
    SUM(total_actions_per_hand) AS total_actions
  FROM player_hand_actions
  GROUP BY playerid
),

-- Step 7: 计算指标、打标签 + 数据质量
player_style_enhanced AS (
  SELECT
    playerid,
    total_hands,
    ROUND(vpip_hands * 1.0 / NULLIF(total_hands, 0), 4) AS vpip,
    ROUND(pfr_hands * 1.0 / NULLIF(total_hands, 0), 4) AS pfr,
    ROUND(three_bet_hands * 1.0 / NULLIF(vpip_hands, 0), 4) AS three_bet_pct,
    ROUND(coalesce(cbet_hands * 1.0 / NULLIF(pfr_hands, 0),0), 4) AS cbet_pct,
    ROUND(total_allins * 1.0 / NULLIF(total_actions, 1), 4) AS allin_frequency,
    ROUND(total_folds * 1.0 / NULLIF(total_actions, 1), 4) AS fold_rate,
    
    -- Aggression Factor (AF)
    CASE 
      WHEN pass_count > 0 
      THEN ROUND(agg_count * 1.0 / pass_count, 4)
      ELSE NULL
    END AS af,
    
    -- 数据质量标签
    CASE
      WHEN total_hands >= 100 AND total_actions >= 200 THEN 'high'
      WHEN total_hands >= 50  AND total_actions >= 100 THEN 'medium'
      WHEN total_hands >= 10  AND total_actions >= 20  THEN 'low'
      ELSE 'insufficient'
    END AS data_quality,
    
    -- 高级风格标签
    CASE
      WHEN total_hands < 10 THEN 'Insufficient Data'
      WHEN (vpip_hands * 1.0 / total_hands > 0.35) 
           AND (pass_count > 0 AND agg_count * 1.0 / pass_count > 3.0)
      THEN 'Maniac (超激进)'
      WHEN (vpip_hands * 1.0 / total_hands <= 0.20) 
           AND (pfr_hands * 1.0 / NULLIF(vpip_hands, 0) >= 0.60)
           AND (three_bet_hands * 1.0 / NULLIF(vpip_hands, 0) >= 0.25)
      THEN 'Strong TAG (高3-bet紧凶)'
      WHEN (vpip_hands * 1.0 / total_hands > 0.25)
           AND (pfr_hands * 1.0 / NULLIF(vpip_hands, 0) < 0.30)
           AND (pass_count > 0 AND agg_count * 1.0 / pass_count < 1.0)
      THEN 'Calling Station (跟注站)'
      WHEN (total_folds * 1.0 / NULLIF(total_actions, 1) > 0.60)
      THEN 'Nit (过度弃牌)'
      WHEN (vpip_hands * 1.0 / total_hands <= 0.20) 
           AND (pfr_hands * 1.0 / NULLIF(vpip_hands, 0) >= 0.60)
      THEN 'Tight-Aggressive (TAG)'
      WHEN (vpip_hands * 1.0 / total_hands > 0.20) 
           AND (pfr_hands * 1.0 / NULLIF(vpip_hands, 0) >= 0.50)
      THEN 'Loose-Aggressive (LAG)'
      WHEN (vpip_hands * 1.0 / total_hands <= 0.20) 
           AND (pfr_hands * 1.0 / NULLIF(vpip_hands, 0) < 0.60)
      THEN 'Tight-Passive (TP)'
      WHEN (vpip_hands * 1.0 / total_hands > 0.20) 
           AND (pfr_hands * 1.0 / NULLIF(vpip_hands, 0) < 0.50)
      THEN 'Loose-Passive (LP)'
      ELSE 'Unclassified'
    END AS playing_style
    
  FROM player_stats
)

-- 最终输出
insert overwrite table poker.dws_dz_player_tag_df partition (dt='${dt}')
SELECT 
  playerid,
  total_hands,
  vpip,
  pfr,
  three_bet_pct,
  cbet_pct,
  af,
  allin_frequency,
  fold_rate,
  playing_style,
  data_quality
FROM player_style_enhanced;