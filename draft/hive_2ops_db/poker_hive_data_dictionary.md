# poker 库 Hive 表结构与字段字典


- 数据库：`poker`
- 表数量：`49`
- 说明：字段“含义”优先使用 Hive 字段注释；无注释时标记为“无注释”。

## 目录
- [dwd_dz_manual_data_di](#dwd_dz_manual_data_di)
- [dwd_dz_manual_seatinfo_di](#dwd_dz_manual_seatinfo_di)
- [dwd_dz_table_detail_df](#dwd_dz_table_detail_df)
- [dws_db_game_overview_di](#dws_db_game_overview_di)
- [dws_db_player_game_result_di](#dws_db_player_game_result_di)
- [dws_dz_player_action_di](#dws_dz_player_action_di)
- [dws_dz_player_game_info_di](#dws_dz_player_game_info_di)
- [dws_dz_player_profile_tag_df](#dws_dz_player_profile_tag_df)
- [dws_dz_robot_info_di](#dws_dz_robot_info_di)
- [dws_dz_robot_win_lose_result_di](#dws_dz_robot_win_lose_result_di)
- [dws_dz_seat_info_di](#dws_dz_seat_info_di)
- [dws_dz_table_info_di](#dws_dz_table_info_di)
- [ods_dz_db_table_dz_career_df](#ods_dz_db_table_dz_career_df)
- [ods_dz_db_table_dz_career_total_df](#ods_dz_db_table_dz_career_total_df)
- [ods_dz_db_table_dz_club_diamond_log_df](#ods_dz_db_table_dz_club_diamond_log_df)
- [ods_dz_db_table_dz_club_info_df](#ods_dz_db_table_dz_club_info_df)
- [ods_dz_db_table_dz_club_insure_ucoin_log_df](#ods_dz_db_table_dz_club_insure_ucoin_log_df)
- [ods_dz_db_table_dz_club_member_df](#ods_dz_db_table_dz_club_member_df)
- [ods_dz_db_table_dz_clubprop_cfg_df](#ods_dz_db_table_dz_clubprop_cfg_df)
- [ods_dz_db_table_dz_clubscore_log_df](#ods_dz_db_table_dz_clubscore_log_df)
- [ods_dz_db_table_dz_diamond_log_df](#ods_dz_db_table_dz_diamond_log_df)
- [ods_dz_db_table_dz_game_gold_score_detail_df](#ods_dz_db_table_dz_game_gold_score_detail_df)
- [ods_dz_db_table_dz_game_info_df](#ods_dz_db_table_dz_game_info_df)
- [ods_dz_db_table_dz_game_score_detail_df](#ods_dz_db_table_dz_game_score_detail_df)
- [ods_dz_db_table_dz_game_score_total_df](#ods_dz_db_table_dz_game_score_total_df)
- [ods_dz_db_table_dz_game_settle_df](#ods_dz_db_table_dz_game_settle_df)
- [ods_dz_db_table_dz_insure_settle_df](#ods_dz_db_table_dz_insure_settle_df)
- [ods_dz_db_table_dz_jscore_goods_df](#ods_dz_db_table_dz_jscore_goods_df)
- [ods_dz_db_table_dz_jscore_order_df](#ods_dz_db_table_dz_jscore_order_df)
- [ods_dz_db_table_dz_jscore_user_df](#ods_dz_db_table_dz_jscore_user_df)
- [ods_dz_db_table_dz_league_tree_df](#ods_dz_db_table_dz_league_tree_df)
- [ods_dz_db_table_dz_leagueclub_info_df](#ods_dz_db_table_dz_leagueclub_info_df)
- [ods_dz_db_table_dz_leagueclub_relation_df](#ods_dz_db_table_dz_leagueclub_relation_df)
- [ods_dz_db_table_dz_manual_data_di](#ods_dz_db_table_dz_manual_data_di)
- [ods_dz_db_table_dz_manual_favorite_df](#ods_dz_db_table_dz_manual_favorite_df)
- [ods_dz_db_table_dz_match_result_df](#ods_dz_db_table_dz_match_result_df)
- [ods_dz_db_table_dz_online_df](#ods_dz_db_table_dz_online_df)
- [ods_dz_db_table_dz_profit_detail_df](#ods_dz_db_table_dz_profit_detail_df)
- [ods_dz_db_table_dz_profit_df](#ods_dz_db_table_dz_profit_df)
- [ods_dz_db_table_dz_prop_cfg_df](#ods_dz_db_table_dz_prop_cfg_df)
- [ods_dz_db_table_dz_req_result_df](#ods_dz_db_table_dz_req_result_df)
- [ods_dz_db_table_dz_score_log_df](#ods_dz_db_table_dz_score_log_df)
- [ods_dz_db_table_dz_tablescore_log_df](#ods_dz_db_table_dz_tablescore_log_df)
- [ods_dz_db_table_dz_user_msg_df](#ods_dz_db_table_dz_user_msg_df)
- [ods_dz_db_table_dz_user_notename_df](#ods_dz_db_table_dz_user_notename_df)
- [ods_dz_db_table_dz_user_proplog_df](#ods_dz_db_table_dz_user_proplog_df)
- [ods_dz_db_table_dz_web_token_df](#ods_dz_db_table_dz_web_token_df)
- [ods_dz_db_table_user_df](#ods_dz_db_table_user_df)
- [ods_dz_db_table_web_loginlog_df](#ods_dz_db_table_web_loginlog_df)

## dwd_dz_manual_data_di

- 表名：`poker.dwd_dz_manual_data_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dwd_dz_manual_data_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `gametype` | `int` | 游戏类型 |
| `playerid` | `int` | 用户ID（旁观者为0） |
| `sztoken` | `string` | 对应游戏桌的szToken |
| `nround` | `int` | 第几手 |
| `winscore` | `bigint` | 赢家的输赢 |
| `score` | `bigint` | 自己的输赢 |
| `sztitle` | `string` | 标题 |
| `szhandcard` | `string` | 手牌数据 |
| `szcarddata` | `string` | 牌谱数据 |
| `carddata` | `string` | 展开牌谱数据 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## 表用途总览

| 表名 | 用途 |
|---|---|
| `dwd_dz_manual_data_di` | DWD层牌谱清洗明细，统一结构后供动作、胜率、风控等模型使用。 |
| `dwd_dz_manual_seatinfo_di` | DWD层座位清洗明细，用于还原每手牌座位与玩家关系。 |
| `dwd_dz_table_detail_df` | DWD层表级统计快照，用于表规模、时间范围和容量监控。 |
| `dws_db_game_overview_di` | DWS层全局经营概览指标，用于管理看板。 |
| `dws_db_player_game_result_di` | DWS层玩家对局结果明细，用于玩家输赢与机器人表现分析。 |
| `dws_dz_player_action_di` | DWS层玩家操作行为明细，用于行为分析与异常识别。 |
| `dws_dz_player_game_info_di` | DWS层玩家对局信息主题汇总，用于玩家行为与对局特征分析。 |
| `dws_dz_player_profile_tag_df` | DWS层玩家标签结果，用于精细化运营与召回。 |
| `dws_dz_robot_info_di` | DWS层机器人识别信息，用于机器人行为分析。 |
| `dws_dz_robot_win_lose_result_di` | DWS层机器人输赢汇总，用于机器人收益监控。 |
| `dws_dz_seat_info_di` | DWS层牌桌座位明细，用于桌局结构分析。 |
| `dws_dz_table_info_di` | DWS层Hive表信息汇总，用于元数据与数据质量监控。 |
| `ods_dz_db_table_dz_career_df` | ODS层生涯战绩明细，用于玩家长期表现分析。 |
| `ods_dz_db_table_dz_career_total_df` | ODS层生涯战绩汇总，用于玩家长期表现分析。 |
| `ods_dz_db_table_dz_club_diamond_log_df` | ODS层俱乐部钻石流水明细，用于资产变动分析与对账。 |
| `ods_dz_db_table_dz_club_info_df` | ODS层俱乐部基础信息，用于俱乐部维度分析。 |
| `ods_dz_db_table_dz_club_insure_ucoin_log_df` | ODS层俱乐部保险U币流水，用于保险相关资金核对。 |
| `ods_dz_db_table_dz_club_member_df` | ODS层俱乐部成员关系明细，用于俱乐部结构分析。 |
| `ods_dz_db_table_dz_clubprop_cfg_df` | ODS层俱乐部道具配置，用于价格与策略配置查询。 |
| `ods_dz_db_table_dz_clubscore_log_df` | ODS层俱乐部积分流水明细，用于俱乐部资金核算。 |
| `ods_dz_db_table_dz_diamond_log_df` | ODS层钻石流水明细，用于资产变动分析与对账。 |
| `ods_dz_db_table_dz_game_gold_score_detail_df` | ODS层金币场积分变化明细，用于金币局经营分析与结算核对。 |
| `ods_dz_db_table_dz_game_info_df` | ODS层牌桌基础信息明细，用于关联对局、俱乐部与规则维度。 |
| `ods_dz_db_table_dz_game_score_detail_df` | ODS层牌局积分变化明细，用于还原对局过程和输赢分析。 |
| `ods_dz_db_table_dz_game_score_total_df` | ODS层牌局汇总结果明细，用于桌局级统计和对账。 |
| `ods_dz_db_table_dz_game_settle_df` | ODS层牌局结算明细，用于结算链路核对与报表。 |
| `ods_dz_db_table_dz_insure_settle_df` | ODS层保险结算明细，用于保险业务分析与对账。 |
| `ods_dz_db_table_dz_jscore_goods_df` | ODS层商城商品明细，用于商品配置与经营分析。 |
| `ods_dz_db_table_dz_jscore_order_df` | ODS层商城订单明细，用于订单统计与对账。 |
| `ods_dz_db_table_dz_jscore_user_df` | ODS层积分商城用户信息明细，用于商城用户行为分析。 |
| `ods_dz_db_table_dz_league_tree_df` | ODS层联盟树结构配置，用于层级关系计算。 |
| `ods_dz_db_table_dz_leagueclub_info_df` | ODS层联盟俱乐部基础信息，用于联盟维度分析。 |
| `ods_dz_db_table_dz_leagueclub_relation_df` | ODS层联盟俱乐部关系明细，用于组织关系分析。 |
| `ods_dz_db_table_dz_manual_data_di` | ODS层牌谱原始明细，用于DWD清洗及回放分析。 |
| `ods_dz_db_table_dz_manual_favorite_df` | ODS层牌谱收藏记录，用于用户功能行为分析。 |
| `ods_dz_db_table_dz_match_result_df` | ODS层比赛结果明细，用于赛事排名与奖励分析。 |
| `ods_dz_db_table_dz_online_df` | ODS层在线时长统计，用于活跃和留存分析。 |
| `ods_dz_db_table_dz_profit_detail_df` | ODS层分成明细，用于代理/联盟分润核算。 |
| `ods_dz_db_table_dz_profit_df` | ODS层分成主表，用于分润状态跟踪与结算。 |
| `ods_dz_db_table_dz_prop_cfg_df` | ODS层道具配置，用于价格与策略配置查询。 |
| `ods_dz_db_table_dz_req_result_df` | ODS层请求处理结果明细，用于业务链路追踪。 |
| `ods_dz_db_table_dz_score_log_df` | ODS层用户分数流水明细，用于资产变动追踪。 |
| `ods_dz_db_table_dz_tablescore_log_df` | ODS层桌分流水明细，用于每手牌资金流分析。 |
| `ods_dz_db_table_dz_user_msg_df` | ODS层站内消息明细，用于消息触达与社交行为分析。 |
| `ods_dz_db_table_dz_user_notename_df` | ODS层用户备注信息，用于关系标签与运营分析。 |
| `ods_dz_db_table_dz_user_proplog_df` | ODS层道具使用流水，用于道具消耗与营收分析。 |
| `ods_dz_db_table_dz_web_token_df` | ODS层Web令牌信息，用于登录态管理分析。 |
| `ods_dz_db_table_user_df` | ODS层用户基础信息明细，用于用户画像、活跃与风控分析。 |
| `ods_dz_db_table_web_loginlog_df` | ODS层登录行为明细，用于活跃分析、登录链路排查与风控。 |

## dwd_dz_manual_seatinfo_di

- 表名：`poker.dwd_dz_manual_seatinfo_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dwd_dz_manual_seatinfo_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `createdate` | `date` | createdate |
| `gameid` | `string` | gameid |
| `playerid` | `string` | playerid |
| `start_money` | `bigint` | 开始金额 |
| `play_name` | `string` | playName |
| `play_sex` | `int` | playSex |
| `seat` | `int` | seat |
| `ip` | `string` | ip |
| `niosystem` | `string` | nIOSystem |
| `gps` | `string` | GPS |
| `time` | `bigint` | time |
| `sztoken` | `string` | sztoken |
| `nround` | `int` | nround |
| `gametype` | `int` | 游戏类型 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## dwd_dz_table_detail_df

- 表名：`poker.dwd_dz_table_detail_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dwd_dz_table_detail_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `table_name` | `string` | 表名 |
| `table_comment` | `string` | 表中文描述 |
| `row_count` | `bigint` | 记录数 |
| `size_bytes` | `bigint` | 存储大小 |
| `min_date` | `date` | 最早日期 |
| `max_date` | `date` | 最晚日期 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## dws_db_game_overview_di

- 表名：`poker.dws_db_game_overview_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_db_game_overview_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `ngametype` | `string` | 游戏类型 |
| `sztoken_cnt` | `int` | 总赢牌桌数 |
| `round_cnt` | `int` | 总输牌局数 |
| `player_cnt` | `int` | 参与玩家数 |
| `non_robot_player_cnt` | `int` | 非机器人玩家数 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## dws_db_player_game_result_di

- 表名：`poker.dws_db_player_game_result_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_db_player_game_result_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `ngametype` | `int` | 游戏类型 |
| `sztoken` | `string` | 桌号 |
| `nplayerid` | `int` | 玩家ID |
| `nround` | `int` | 局数 |
| `gameresult` | `bigint` | 游戏结果 |
| `brobot` | `int` | 是否机器人 |
| `robotversion` | `string` | 机器人版本号 |
| `createtime` | `string` | 创建时间 |
| `starttime` | `string` | 开始时间 |
| `endtime` | `string` | 结束时间 |
| `create_dt` | `string` | 游戏时间 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## dws_dz_player_action_di

- 表名：`poker.dws_dz_player_action_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_dz_game_action_detail_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `createdate` | `string` | 日期，格式 yyyy-MM-dd |
| `sztoken` | `string` | 对应游戏桌的 szToken |
| `nround` | `int` | 第几手 |
| `playerid` | `string` | 玩家ID |
| `seat` | `string` | 座位信息 |
| `json_index` | `int` | JSON索引序号 |
| `minbetscore` | `int` | 最小下注分数 |
| `maxbetscore` | `int` | 最大下注分数 |
| `minaddscore` | `int` | 最小加注分数 |
| `action` | `string` | 玩家操作类型 |
| `seatbetstate` | `int` | 座位下注状态 |
| `betscore` | `int` | 下注分数 |
| `seatcurbet` | `int` | 座位当前下注 |
| `poolscore` | `int` | 池中分数 |
| `predealct` | `int` | 预发牌计数 |
| `commoncard` | `string` | 公共牌信息 |
| `stage` | `string` | 游戏阶段（preflop/flop/turn/river） |
| `gameresult` | `string` | 游戏结果 |
| `isjumpinsure` | `int` | 是否跳出买保险 |
| `isinsure` | `int` | 是否买保险 |
| `score` | `int` | 得分 |
| `insurewinscores` | `int` | 保险赢分 |
| `betaction` | `string` | 下注动作 |
| `gametype` | `int` | 游戏类型 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 分区字段，格式 yyyy-MM-dd |

## dws_dz_player_game_info_di

- 表名：`poker.dws_dz_player_game_info_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_dz_player_game_info_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `sztoken` | `string` | 标识符 |
| `nround` | `int` | 轮次 |
| `playerid` | `string` | 玩家ID |
| `startmoney` | `double` | 初始金额 |
| `playname` | `string` | 玩家名称 |
| `playsex` | `string` | 玩家性别 |
| `seat` | `int` | 座位号 |
| `seatcharacter` | `string` | 座位角色/座位特征 |
| `handcards` | `string` | 手牌 |
| `playresult` | `string` | 游戏结果 |
| `gamescore` | `int` | 游戏得分 |
| `gameresult` | `int` | 游戏赢家结果分数 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## dws_dz_player_profile_tag_df

- 表名：`poker.dws_dz_player_profile_tag_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_dz_player_profile_tag_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `nplayerid` | `bigint` | 玩家ID |
| `regtime` | `string` | 注册时间 |
| `brobot` | `int` | 是否机器人（0-真人，1-机器人） |
| `preloginip` | `string` | 最近登录IP |
| `prelogintime` | `string` | 最近登录时间 |
| `sznickname` | `string` | 玩家昵称 |
| `nclubid` | `bigint` | 所属俱乐部ID |
| `vpip` | `decimal(5,4)` | VPIP（翻前入池率） |
| `pfr` | `decimal(5,4)` | PFR（翻前加注率） |
| `three_bet_pct` | `decimal(5,4)` | 3-bet率（翻前再加注率） |
| `cbet_pct` | `decimal(5,4)` | C-bet率（持续下注率） |
| `af` | `decimal(5,4)` | 攻击因子（Aggression Factor） |
| `allin_frequency` | `decimal(5,4)` | 全下频率 |
| `fold_rate` | `decimal(5,4)` | 弃牌率 |
| `playing_style` | `string` | 牌风标签（如TAG/LAG/Maniac等） |
| `data_quality` | `string` | 数据质量（high/medium/low/insufficient） |
| `preferred_gametype` | `int` | 偏好游戏类型 |
| `preferred_game_rounds` | `bigint` | 偏好游戏类型局数 |
| `active_days` | `int` | 近30天活跃天数 |
| `avg_round_duration_mins` | `decimal(6,2)` | 平均单局时长（分钟） |
| `peak_active_hour` | `int` | 最活跃时段（小时，0-23） |
| `activity_level` | `string` | 活跃度标签（high/medium/low/silent） |
| `collusion_status` | `string` | 伙牌风险标签（normal/collusion_suspected） |
| `total_hands_vs_bot` | `bigint` | 对战机器人总手牌数 |
| `win_rate_vs_bot` | `decimal(5,4)` | 对战机器人胜率 |
| `avg_profit_vs_bot` | `decimal(10,2)` | 对战机器人平均每局盈利 |
| `high_stakes_ratio` | `decimal(5,4)` | 高额桌占比（ngametype=450） |
| `bot_hands_ratio` | `decimal(5,4)` | 机器人对局占比 |
| `player_profile_label` | `string` | 机器人对战画像标签 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## dws_dz_robot_info_di

- 表名：`poker.dws_dz_robot_info_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_dz_robot_info_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `playerid` | `int` | 玩家ID |
| `sztoken` | `string` | sztoken |
| `nround` | `int` | nround |
| `robotversion` | `string` | 机器人版本号 |
| `brobot` | `int` | 是否是机器人 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## dws_dz_robot_win_lose_result_di

- 表名：`poker.dws_dz_robot_win_lose_result_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_dz_robot_win_lose_result_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `create_dt` | `string` | 统计日期 |
| `brobot` | `int` | 机器人标识 |
| `robotversion` | `string` | 机器人版本号 |
| `ngametype` | `int` | 游戏类型 |
| `win_cnt` | `int` | 总赢牌局数 |
| `tie_cnt` | `int` | 总平牌局数 |
| `lose_cnt` | `int` | 总输牌局数 |
| `total_cnt` | `int` | 总局数 |
| `win_score` | `double` | 总赢牌分值 |
| `tie_score` | `double` | 总平牌分值 |
| `lose_score` | `double` | 总输牌分值 |
| `total_score` | `double` | 总分值 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## dws_dz_seat_info_di

- 表名：`poker.dws_dz_seat_info_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_dz_seat_info_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `createdate` | `string` | 日期，格式 yyyy-MM-dd |
| `sztoken` | `string` | 对应游戏桌的 szToken |
| `nround` | `int` | 第几手 |
| `gametype` | `int` | 游戏类型 |
| `playerid` | `string` | 玩家ID（非旁观者） |
| `seat` | `string` | 座位信息 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 分区字段，格式 yyyy-MM-dd |

## dws_dz_table_info_di

- 表名：`poker.dws_dz_table_info_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/dws_dz_table_info_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `sztoken` | `string` | 标识符 |
| `nround` | `int` | 轮次 |
| `nplayer` | `int` | 玩家人数 |
| `nwatcher` | `int` | 旁观者人数 |
| `roomid` | `int` | 牌桌ID |
| `clubname` | `string` | 俱乐部名称 |
| `smallblindamt` | `int` | 小盲注金额 |
| `bigblindamt` | `int` | 大盲注金额 |
| `isinsurance` | `int` | 是否有保险,1是，0否 |
| `result` | `string` | 游戏结果 |
| `winnerplayerid` | `int` | 获胜玩家ID |
| `nwinscore` | `int` | 获得的分数 |
| `gameresult` | `int` | 游戏赢家结果分数 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_career_df

- 表名：`poker.ods_dz_db_table_dz_career_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_career_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `ngametype` | `int` | 游戏类型 |
| `nplayerid` | `int` | 用户ID |
| `ntotaltable` | `int` | 总局数 |
| `ntotalround` | `int` | 总手数 |
| `ntotalscore` | `bigint` | 总盈亏 |
| `inpool` | `int` | 入池手数 |
| `flopraise` | `int` | 翻牌前加注次数 |
| `flopraisechance` | `int` | 翻牌前可加注次数 |
| `allin` | `int` | Allin手数 |
| `allinwin` | `int` | Allin胜利手数 |
| `createtime` | `date` | 发生日期 (DATE) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_career_total_df

- 表名：`poker.ods_dz_db_table_dz_career_total_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_career_total_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `ngametype` | `int` | 游戏类型 |
| `nplayerid` | `int` | 玩家ID |
| `ntotaltable` | `int` | 总局数 |
| `ntotalround` | `int` | 总手数 |
| `ntotalscore` | `bigint` | 总盈亏 |
| `inpool` | `int` | 入池手数 |
| `flopraise` | `int` | 翻牌前加注次数 |
| `flopraisechance` | `int` | 翻牌前可加注次数 |
| `allin` | `int` | Allin手数 |
| `allinwin` | `int` | Allin胜利手数 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_club_diamond_log_df

- 表名：`poker.ods_dz_db_table_dz_club_diamond_log_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_club_diamond_log_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nplayerid` | `int` | 用户ID |
| `ngametype` | `int` | 游戏ID |
| `nclubid` | `int` | 俱乐部ID |
| `ndiamond` | `bigint` | 变动数量 |
| `nclubdiamond` | `bigint` | 变动后俱乐部的钻石 |
| `ntype` | `int` | 变化类型: 1-部长往俱乐部充值钻石, 2-俱乐部开房消耗, 11-解散俱乐部退钻 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `szremark` | `string` | 备注 |
| `sztoken` | `string` | 订单号: 俱乐部号-时间-房间号 |
| `ntokenstate` | `int` | 订单状态:0-初始 1-进行中 2-已完成 (默认0) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_club_info_df

- 表名：`poker.ods_dz_db_table_dz_club_info_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_club_info_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `nclubid` | `int` | 俱乐部ID |
| `nopid` | `int` | 运营商ID |
| `leagueflag` | `int` | 联盟标记 0-否 1-是 |
| `nexclubid` | `int` | 上级俱乐部标记 |
| `nlevel` | `int` | 等级 |
| `nscore` | `bigint` | 基金账户 |
| `ndiamond` | `bigint` | 俱乐部钻石 |
| `ucointable` | `bigint` | 牌局资金池U币 |
| `ucointablewarnval` | `bigint` | 牌局资金池警告值 |
| `ucoininsure` | `bigint` | 保险池U币 |
| `lockucoininsure` | `bigint` | 锁定保险池U币 |
| `autorecharge` | `tinyint` | 自动充值(0-否 1-是) |
| `autorechargeamount` | `int` | 自动充值的数量 |
| `autorechargeneed` | `int` | 低于此值则自动充值 |
| `autoucoinbuyflag` | `int` | 自动使用U币购房卡(0-否 1-是) |
| `nicon` | `int` | 图标 |
| `szclubname` | `string` | 俱乐部名字 |
| `country` | `int` | 国家地区 |
| `nstatus` | `tinyint` | 状态(1-正常，2-冻结，3-解散) |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `endtime` | `string` | 解散时间 (TIMESTAMP → STRING) |
| `createplayerid` | `int` | 创建者ID |
| `createname` | `string` | 创建者名字 |
| `sznotemsg` | `string` | 俱乐部公告 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_club_insure_ucoin_log_df

- 表名：`poker.ods_dz_db_table_dz_club_insure_ucoin_log_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_club_insure_ucoin_log_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `ngametype` | `int` | 游戏类型 |
| `nplayerid` | `int` | 用户ID |
| `nclubid` | `int` | 俱乐部ID |
| `sztoken` | `string` | 桌子唯一标识 |
| `namount` | `bigint` | 变动数量 |
| `ntype` | `int` | 变化类型 1 充值 2 提现 3保险锁定 4保险解锁 5保险赔付 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `szremark` | `string` | 备注 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_club_member_df

- 表名：`poker.ods_dz_db_table_dz_club_member_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_club_member_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nclubid` | `int` | 俱乐部ID |
| `nplayerid` | `int` | 用户ID |
| `sznickname` | `string` | 昵称 |
| `szheadpicurl` | `string` | 头像 |
| `nlevel` | `tinyint` | 权限（1-部长，2-管理，3-成员） |
| `createclubflag` | `tinyint` | 是否能创建俱乐部 1-可 0-否 默认0 |
| `nextendid` | `int` | 上线代理ID |
| `nstatus` | `tinyint` | 状态（1-正常，2-冻结，3-退出，4-踢出） |
| `tjointime` | `string` | 加入俱乐部时间 (TIMESTAMP → STRING) |
| `texittime` | `string` | 离开俱乐部时间 (TIMESTAMP → STRING) |
| `brobot` | `tinyint` | 机器人标志 0-不是 1-是 (默认0) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_clubprop_cfg_df

- 表名：`poker.ods_dz_db_table_dz_clubprop_cfg_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_clubprop_cfg_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `nclubid` | `int` | 俱乐部ID |
| `nslotid` | `int` | 价格档位(1~9) |
| `npropid` | `int` | 道具ID |
| `namount` | `bigint` | 价格 |
| `nstatus` | `int` | 状态 0-无效 1-有效 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_clubscore_log_df

- 表名：`poker.ods_dz_db_table_dz_clubscore_log_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_clubscore_log_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nplayerid` | `int` | 用户ID |
| `nclubid` | `int` | 俱乐部ID |
| `namount` | `bigint` | 变动数量 |
| `nclubscore` | `bigint` | 变动后俱乐部基金账户数量 |
| `ntype` | `int` | 1-部长充值获得 2-部长发给成员 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `szremark` | `string` | 备注 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_diamond_log_df

- 表名：`poker.ods_dz_db_table_dz_diamond_log_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_diamond_log_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `ngametype` | `int` | 游戏类型 |
| `nplayerid` | `int` | 用户ID |
| `nclubid` | `int` | 俱乐部ID |
| `ndiamond` | `bigint` | 变动数量 |
| `nprice` | `int` | 充值金额 |
| `szoperator` | `string` | 操作员 |
| `nplayerdiamond` | `bigint` | 变动后玩家身上钻石数 |
| `ntype` | `int` | 1-钻石兑换商城礼包 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `szremark` | `string` | 备注 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_game_gold_score_detail_df

- 表名：`poker.ods_dz_db_table_dz_game_gold_score_detail_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_game_gold_score_detail_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `ngametype` | `int` | 游戏类型 |
| `ngamemode` | `int` | 模式 1-快速 2-标准 |
| `nroomtype` | `int` | 房间类型:1 普通局 2 钻石局 |
| `nsubgametype` | `int` | 游戏子类型 |
| `nplayseat` | `int` | 无注释 |
| `noptime` | `int` | 无注释 |
| `leagueflag` | `int` | 0-普通桌 1-联盟桌 2-运营商大厅桌 100-超级俱乐部桌 |
| `sztoken` | `string` | 对应游戏桌szToken |
| `nclubid` | `int` | 俱乐部ID |
| `nleagueclubid` | `int` | 联盟俱乐部ID |
| `nrelationid` | `int` | 关联俱乐部ID |
| `nplayerid` | `int` | 玩家ID |
| `brobot` | `int` | 机器人标识 |
| `starttime` | `string` | 开始时间 (TIMESTAMP → STRING) |
| `endtime` | `string` | 结束时间 (TIMESTAMP → STRING) |
| `nround` | `int` | 第几手 |
| `startscore` | `bigint` | 开始积分(牌桌内计分牌) |
| `npool` | `bigint` | 底池数 |
| `pubcard` | `string` | 公共牌 |
| `handcard` | `string` | 手牌 |
| `finalpokerstyle` | `string` | 最终牌型(最大组合) |
| `gameresult` | `bigint` | 游戏成绩（和保险，服务费无关） |
| `nscore` | `int` | 得分(扣除抽成后) |
| `ninsure` | `int` | 保险 |
| `ntax` | `int` | 单局赢家抽成（如果有设置则扣） |
| `endscore` | `bigint` | 最后积分(牌桌内计分牌) |
| `roomrate` | `bigint` | 房费 |
| `uroomrate` | `bigint` | 房费U币值 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_game_info_df

- 表名：`poker.ods_dz_db_table_dz_game_info_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_game_info_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `ngametype` | `int` | 游戏类型 |
| `ngamemode` | `int` | 模式 1-快速 2-标准 |
| `leagueflag` | `int` | 0-普通桌 1-联盟桌 2-运营商大厅桌 100-超级俱乐部桌 |
| `sztoken` | `string` | 桌子唯一标识 |
| `nplayerid` | `int` | 创建人ID |
| `nroomid` | `int` | 房间ID |
| `nroomtype` | `int` | 房间类型:1 普通局 2 钻石局 |
| `ucoinratio` | `int` | 钻石局时，1U币可兑换的记分牌数量 |
| `nclubid` | `int` | 俱乐部ID |
| `szroomname` | `string` | 房间名称 |
| `szroomdesc` | `string` | 房间描述 |
| `szrulejson` | `string` | 规则打包JSON |
| `insureflag` | `tinyint` | 保险局标志 0-否 1-是 |
| `nfront` | `int` | 前注 |
| `nbigblind` | `int` | 大盲 |
| `nsmallblind` | `int` | 小盲 |
| `nroomtime` | `int` | 房间时长(分钟) |
| `nplaycount` | `int` | 人数 |
| `nrealplaycount` | `int` | 真实人数（后台用于统计普通房参与人数） |
| `nautostartcount` | `int` | 自动开始人数(0-不自动开始) |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `tableendtime` | `string` | 牌桌结束时间 (TIMESTAMP → STRING) |
| `totalbring` | `bigint` | 总带入 |
| `totalround` | `int` | 总手数 |
| `totalinsure` | `bigint` | 总保险池 |
| `totalfee` | `bigint` | 总服务费 |
| `totalprop` | `bigint` | 道具总消耗 |
| `totalroomrate` | `bigint` | 总房费 |
| `tycoonid` | `int` | 土豪玩家ID |
| `bigfishid` | `int` | 大鱼玩家ID |
| `mvpid` | `int` | MVP玩家ID |
| `szconcludedata` | `string` | 结算数据 |
| `concludestate` | `int` | 结算状态 0:未结算 1:正在结算 2:已结算 3:正在手动结算 4:已手动结算 |
| `szinsuredata` | `string` | 保险数据 |
| `insurestate` | `int` | 保险状态 0:未结算 1:正在结算 2:已结算 3:正在手动结算 4:已手动结算 |
| `insuretotal` | `bigint` | 保险汇总 |
| `benefittotal` | `bigint` | 抽水汇总 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_game_score_detail_df

- 表名：`poker.ods_dz_db_table_dz_game_score_detail_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_game_score_detail_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `ngametype` | `int` | 游戏类型 |
| `ngamemode` | `int` | 模式 1-快速 2-标准 |
| `nroomtype` | `int` | 房间类型:1 普通局 2 钻石局 |
| `leagueflag` | `int` | 0-普通桌 1-联盟桌 2-运营商大厅桌 100-超级俱乐部桌 |
| `sztoken` | `string` | 对应游戏桌szToken |
| `nclubid` | `int` | 俱乐部ID |
| `nleagueclubid` | `int` | 联盟俱乐部ID |
| `nrelationid` | `int` | 关联俱乐部ID |
| `nplayerid` | `int` | 玩家ID |
| `starttime` | `string` | 开始时间 (TIMESTAMP → STRING) |
| `endtime` | `string` | 结束时间 (TIMESTAMP → STRING) |
| `nround` | `int` | 第几手 |
| `startscore` | `bigint` | 开始积分(牌桌内计分牌) |
| `npool` | `bigint` | 底池数 |
| `pubcard` | `string` | 公共牌 |
| `handcard` | `string` | 手牌 |
| `finalpokerstyle` | `string` | 最终牌型(最大组合) |
| `gameresult` | `bigint` | 游戏成绩（和保险，服务费无关） |
| `nscore` | `int` | 得分(扣除抽成后) |
| `ninsure` | `int` | 保险 |
| `ntax` | `int` | 单局赢家抽成（如果有设置则扣） |
| `endscore` | `bigint` | 最后积分(牌桌内计分牌) |
| `roomrate` | `bigint` | 房费 |
| `uroomrate` | `bigint` | 房费U币值 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_game_score_total_df

- 表名：`poker.ods_dz_db_table_dz_game_score_total_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_game_score_total_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `ngametype` | `int` | 游戏类型 |
| `ngamemode` | `int` | 模式 1-快速 2-标准 |
| `leagueflag` | `int` | 0-普通桌 1-联盟桌 2-运营商大厅桌 100-超级俱乐部桌 |
| `nroomtype` | `int` | 房间类型:1 普通局 2 钻石局 |
| `sztoken` | `string` | 对应游戏桌szToken |
| `nclubid` | `int` | 俱乐部ID |
| `nleagueclubid` | `int` | 联盟俱乐部ID |
| `nrelationid` | `int` | 关联俱乐部ID |
| `nplayerid` | `int` | 玩家ID |
| `gameresult` | `bigint` | 游戏成绩（和保险，服务费无关） |
| `ugameresult` | `bigint` | 游戏成绩U币对应值 |
| `totalscore` | `int` | 总输赢 |
| `utotalscore` | `bigint` | 总输赢U币对应值 |
| `totalprop` | `int` | 道具总消耗 |
| `utotalprop` | `bigint` | 道具U币对应值 |
| `totalbring` | `bigint` | 总带入 |
| `totalout` | `bigint` | 总带出(包括最后的结算带出) |
| `totalfee` | `bigint` | 总服务费 |
| `ninsure` | `bigint` | 保险池 |
| `uinsure` | `bigint` | 保险U币对应值 |
| `totaltax` | `bigint` | 总服务费（抽水合计） |
| `utotaltax` | `bigint` | 抽水U币对应值 |
| `totalroomrate` | `bigint` | 总房费 |
| `utotalroomrate` | `bigint` | 总房费U币值 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_game_settle_df

- 表名：`poker.ods_dz_db_table_dz_game_settle_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_game_settle_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `nclubid` | `int` | 俱乐部ID |
| `szorder` | `string` | 订单号 |
| `sztoken` | `string` | 桌子唯一标识 |
| `szcontent` | `string` | 结算数据(JSON) |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `dealtime` | `string` | 处理时间 (TIMESTAMP → STRING) |
| `nstatus` | `int` | 状态 0-未处理 1-成功 2-失败 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_insure_settle_df

- 表名：`poker.ods_dz_db_table_dz_insure_settle_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_insure_settle_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `nclubid` | `int` | 俱乐部ID |
| `szorder` | `string` | 订单号 |
| `sztoken` | `string` | 桌子唯一标识 |
| `nround` | `int` | 手数 |
| `szcontent` | `string` | 结算数据(JSON) |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `dealtime` | `string` | 处理时间 (TIMESTAMP → STRING) |
| `nstatus` | `int` | 状态 0-未处理 1-成功 2-失败 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_jscore_goods_df

- 表名：`poker.ods_dz_db_table_dz_jscore_goods_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_jscore_goods_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 商品ID |
| `nclubid` | `int` | 运营商ID |
| `ngoodsid` | `int` | 道具ID |
| `ngoodsamount` | `int` | 道具兑换数量 |
| `szname` | `string` | 名称 |
| `ntype` | `int` | 类型 1-虚拟商品 |
| `norder` | `int` | 排序 |
| `szurl` | `string` | 图片地址 |
| `showoriprice` | `int` | 是否显示原价 1-显示原价 2-不显示原价 |
| `noriprice` | `bigint` | 原价 |
| `nprice` | `bigint` | 现价 |
| `nbuylimit` | `int` | 玩家购买限制 |
| `szexplain` | `string` | 商品描述 |
| `tcreatetime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `nstatus` | `int` | 状态 0-下架 1-上架 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_jscore_order_df

- 表名：`poker.ods_dz_db_table_dz_jscore_order_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_jscore_order_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 订单ID |
| `nplayerid` | `int` | 玩家ID |
| `ngoldclubid` | `int` | 金币场俱乐部ID |
| `ngoodsid` | `int` | 积分商品ID |
| `szname` | `string` | 名称 |
| `ntype` | `int` | 类型 1-游戏物品 2-虚拟商品 3-生活用品 4-电子数码 |
| `namount` | `int` | 数量 |
| `nplayerscore` | `bigint` | 订单后余额 |
| `nitemprice` | `bigint` | 单价 |
| `ntotalprice` | `bigint` | 总价 |
| `ngoodsamount` | `bigint` | 道具兑换总数 |
| `tordertime` | `string` | 下单时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_jscore_user_df

- 表名：`poker.ods_dz_db_table_dz_jscore_user_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_jscore_user_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 商品ID |
| `nplayerid` | `int` | 玩家ID |
| `nscore` | `bigint` | 积分余额 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_league_tree_df

- 表名：`poker.ods_dz_db_table_dz_league_tree_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_league_tree_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nclubid` | `int` | 联盟ID |
| `ntopid` | `int` | 顶层俱乐部ID |
| `nrelationid` | `int` | 关联俱乐部ID |
| `leagueinsureratio` | `int` | 联盟共担保险分成比例 1000 – 100% |
| `createtableflag` | `int` | 俱乐部可创房标记 0-否 1-是 |
| `nstatus` | `int` | 状态 1-有效 0-无效 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_leagueclub_info_df

- 表名：`poker.ods_dz_db_table_dz_leagueclub_info_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_leagueclub_info_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nplayerid` | `int` | 用户ID |
| `nclubid` | `int` | 联盟俱乐部ID |
| `leagueflag` | `int` | 1联盟俱乐部 2公共俱乐部 100超级公共俱乐部 |
| `nleagueclubid` | `int` | 联盟俱乐部ID |
| `nrelationid` | `int` | 关联俱乐部ID |
| `nstatus` | `int` | 状态 1-有效 0-无效 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_leagueclub_relation_df

- 表名：`poker.ods_dz_db_table_dz_leagueclub_relation_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_leagueclub_relation_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nclubid` | `int` | 联盟俱乐部ID |
| `nrelationid` | `int` | 关联俱乐部ID |
| `propratio` | `int` | 道具分成比例 1000 – 100.0% |
| `insureratio` | `int` | 保险分成比例 1000 – 100.0% |
| `benefitratio` | `int` | 抽水分成比例 1000 – 100.0% |
| `roomrateratio` | `int` | 房费分成比例 1000 – 100.0% |
| `matchratio` | `int` | 比赛分成比例 1000 – 100.0% |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_manual_data_di

- 表名：`poker.ods_dz_db_table_dz_manual_data_di`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_manual_data_di`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `decimal(20,0)` | 无注释 |
| `ngametype` | `int` | 无注释 |
| `nplayerid` | `int` | 无注释 |
| `sztoken` | `string` | 无注释 |
| `front` | `bigint` | 无注释 |
| `smallblind` | `bigint` | 无注释 |
| `bigblind` | `bigint` | 无注释 |
| `nround` | `int` | 无注释 |
| `nwinscore` | `bigint` | 无注释 |
| `nscore` | `bigint` | 无注释 |
| `sztitle` | `string` | 无注释 |
| `szhandcard` | `string` | 无注释 |
| `szcarddata` | `string` | 无注释 |
| `favouritenum` | `int` | 无注释 |
| `createtime` | `timestamp` | 无注释 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 无注释 |

## ods_dz_db_table_dz_manual_favorite_df

- 表名：`poker.ods_dz_db_table_dz_manual_favorite_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_manual_favorite_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `nplayerid` | `int` | 玩家ID |
| `newtitle` | `string` | 新的名称 |
| `sztoken` | `string` | 对应游戏桌的szToken |
| `nround` | `int` | 第几手 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_match_result_df

- 表名：`poker.ods_dz_db_table_dz_match_result_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_match_result_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `ngametype` | `int` | 游戏类型 |
| `ngamemode` | `int` | 模式 1-快速 2-标准 |
| `nclubid` | `int` | 俱乐部ID |
| `nplayerid` | `int` | 用户ID |
| `sztoken` | `string` | token |
| `rebuycount` | `int` | rebuy次数 |
| `rank` | `int` | 名次 |
| `reward` | `bigint` | 奖励 U |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_online_df

- 表名：`poker.ods_dz_db_table_dz_online_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_online_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `nplayerid` | `bigint` | 用户ID |
| `nopid` | `bigint` | 运营商ID |
| `onlineday` | `date` | 统计日期 |
| `onlinesecond` | `bigint` | 累计在线秒数 |
| `rectime` | `timestamp` | 更新时间 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_profit_detail_df

- 表名：`poker.ods_dz_db_table_dz_profit_detail_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_profit_detail_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `profitid` | `int` | 对应table_dz_profit表的ID |
| `nplayerid` | `int` | 分成受益人Id |
| `nsourcetype` | `int` | 代理收益:1- 直属 2- 下级 部长收益:10- 一级代理 11- 下级俱乐部 12- 玩家 盟主收益: 20- 俱乐部 |
| `nclubidtype` | `int` | 俱乐部类型: 1- 普通俱乐部 2- 联盟 |
| `nlowid` | `int` | 下级Id |
| `nsourceid` | `int` | 来源ID |
| `nclubid` | `int` | 俱乐部ID(联盟ID) |
| `nleagueclubid` | `int` | 联盟俱乐部ID |
| `nrelationid` | `int` | 俱乐部ID（联盟局和普通俱乐部局时都会写入） |
| `namount` | `bigint` | 分成额 |
| `ntype` | `int` | 分成类型 1房费，2道具，3抽水，4保险 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_profit_df

- 表名：`poker.ods_dz_db_table_dz_profit_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_profit_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nplayerid` | `int` | 来源玩家 |
| `nextendid` | `int` | 上级ID |
| `ngametype` | `int` | 游戏类型 |
| `sztoken` | `string` | 对应游戏桌szToken |
| `leagueflag` | `int` | 0-普通桌 1-联盟桌 2-运营商大厅桌 100-超级俱乐部桌 |
| `nclubid` | `int` | 俱乐部ID（联盟俱乐部ID） |
| `nleagueclubid` | `int` | 联盟俱乐部ID |
| `nrelationid` | `int` | 关联俱乐部ID |
| `namount` | `bigint` | 分成额 |
| `ntype` | `int` | 分成类型 1房费，2道具，3抽水，4保险 |
| `nstatus` | `int` | 状态 0:待分成 1:已分成 |
| `szmark` | `string` | 备注 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `confirmtime` | `string` | 分成操作完成时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_prop_cfg_df

- 表名：`poker.ods_dz_db_table_dz_prop_cfg_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_prop_cfg_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `npropid` | `int` | 道具ID |
| `propname` | `string` | 道具名称 |
| `ntype` | `int` | 道具类型 |
| `namount` | `bigint` | 价格 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_req_result_df

- 表名：`poker.ods_dz_db_table_dz_req_result_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_req_result_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `msgid` | `int` | 牌局请求时对应 table_dz_user_msg 的 ID |
| `ntype` | `int` | 类型（1-牌局带入请求 2-带出请求 3-牌谱请求 5-资金池请求 6-联盟邀请俱乐部加入 7-代理邀请成为下线） |
| `nplayerid` | `int` | 用户ID（目标用户） |
| `nsendid` | `int` | 发送者ID |
| `nopid` | `int` | 操作者ID |
| `szopname` | `string` | 操作者昵称 |
| `szcontent` | `string` | 内容 |
| `sztoken` | `string` | 桌子token |
| `ncheck` | `int` | 处理状态 (0-未处理 1-拒绝 2-同意 3-超时拒绝) |
| `checktime` | `string` | 处理时间 (TIMESTAMP → STRING) |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_score_log_df

- 表名：`poker.ods_dz_db_table_dz_score_log_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_score_log_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 主键，自增 |
| `ngametype` | `int` | 游戏类型 |
| `nclubid` | `int` | clubid |
| `nplayerid` | `int` | playerid |
| `sztoken` | `string` | szToken |
| `namount` | `bigint` | 变动金额 |
| `nprice` | `int` | 充值金额 |
| `szoperator` | `string` | 操作员 |
| `nplayerscore` | `bigint` | 变动后身上金额 |
| `ntype` | `int` | 变动类型 1- 带入 2-带出 3 钻石兑换 4 部长发放获得 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `szremark` | `string` | 备注 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_tablescore_log_df

- 表名：`poker.ods_dz_db_table_dz_tablescore_log_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_tablescore_log_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 主键，自增 |
| `ngametype` | `int` | 游戏类型 |
| `nclubid` | `int` | clubid |
| `nplayerid` | `int` | playerid |
| `sztable` | `string` | szToken |
| `nround` | `int` | 局数 |
| `namount` | `bigint` | 变动金额 |
| `ntablescore` | `bigint` | 变动后桌面金额 |
| `ntype` | `int` | 变动类型 1- 带入 2-带出 3 游戏获得 4游戏失掉 5 买保险 6 保险获得 7 保险扣除 |
| `createtime` | `string` | 创建时间 (TIMESTAMP → STRING) |
| `szremark` | `string` | 备注 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_user_msg_df

- 表名：`poker.ods_dz_db_table_dz_user_msg_df`
- 表说明：无表注释
- 存储位置：`***/poker/warehouse/test/ods_dz_db_table_dz_user_msg_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nplayerid` | `int` | 用户ID（目标用户） |
| `nsendid` | `int` | 发送者ID |
| `ntype` | `int` | 类型（1-牌局请求 2-俱乐部币请求 3-好友申请添加请求 4-好友聊天信息） |
| `data1` | `bigint` | 资金请求时：请求数量；联盟邀请时：联盟俱乐部ID |
| `data2` | `int` | 资金请求时：俱乐部ID；联盟邀请时：关联俱乐部ID |
| `data3` | `int` | 联盟邀请时：道具分成比例 |
| `data4` | `int` | 联盟邀请时：保险分成比例 |
| `data5` | `int` | 联盟邀请时：抽水分成比例 |
| `data6` | `int` | 联盟邀请时：房费分成比例 |
| `data7` | `int` | 联盟邀请时：比赛分成比例 |
| `data8` | `int` | 联盟邀请时：道具分成2比例 |
| `data9` | `int` | 联盟邀请时：保险分成2比例 |
| `data10` | `int` | 联盟邀请时：抽水分成2比例 |
| `data11` | `int` | 联盟邀请时：房费分成2比例 |
| `data12` | `int` | 联盟邀请时：比赛分成2比例 |
| `szcontent` | `string` | 内容 |
| `nstatus` | `int` | 读取状态（0-未读,1-已读） |
| `createtime` | `string` | 加入时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_user_notename_df

- 表名：`poker.ods_dz_db_table_dz_user_notename_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_user_notename_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nplayerid` | `int` | 用户ID |
| `ndestid` | `int` | 目标ID（对其添加备注名） |
| `sznotename` | `string` | 备注名字 |
| `szfeature` | `string` | 打法特征 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_user_proplog_df

- 表名：`poker.ods_dz_db_table_dz_user_proplog_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_user_proplog_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引ID |
| `nplayerid` | `int` | 玩家ID |
| `nclubid` | `int` | 俱乐部ID |
| `npropid` | `int` | 道具ID |
| `ncount` | `int` | 使用道具的数量 |
| `namount` | `bigint` | 金币价格(按实际购买时的价格) |
| `nucoin` | `bigint` | 对应U币价格(按当时比例) |
| `sztoken` | `string` | 对应游戏桌szToken |
| `nround` | `int` | 第N局 |
| `createtime` | `string` | 购买时间 (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_dz_web_token_df

- 表名：`poker.ods_dz_db_table_dz_web_token_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_dz_web_token_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `id` | `bigint` | 索引 |
| `nplayerid` | `int` | 用户ID |
| `sztoken` | `string` | 登录串(nPlayerID-UNIXTIME-随机数5位) |
| `createtime` | `string` | 创建时间（超过15天则过期） (TIMESTAMP → STRING) |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 数据日期分区 |

## ods_dz_db_table_user_df

- 表名：`poker.ods_dz_db_table_user_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_user_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `nplayerid` | `int` | 玩家ID |
| `szcreatetime` | `string` | 创建时间 |
| `nactive` | `int` | 用户状态：0禁止登录，1正常，2禁提，6禁玩禁提，4预留 |
| `prelogintime` | `string` | 最后一次访问时间 |
| `preloginip` | `string` | 最后一次访问ip |
| `reset4` | `string` | 冗余字段 |
| `strre1` | `string` | 冗余字段 |
| `brobot` | `string` | 是否机器人 |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 无注释 |

## ods_dz_db_table_web_loginlog_df

- 表名：`poker.ods_dz_db_table_web_loginlog_df`
- 表说明：无表注释
- 存储位置：`***/hive/warehouse/poker/ods_dz_db_table_web_loginlog_df`

### 字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `nplayerid` | `int` | 玩家ID |
| `nclubid` | `string` | 俱乐部id |
| `nactive` | `int` | 用户状态：0禁止登录，1正常，2禁提，6禁玩禁提，4预留 |
| `sztime` | `string` | 时间 |
| `loginip` | `string` | 访问ip |

### 分区字段

| 字段名 | 类型 | 含义 |
|---|---|---|
| `dt` | `string` | 无注释 |
