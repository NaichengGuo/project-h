## upload /mnt/workspace to s3://aws-logs-796973487589-ap-southeast-1/workspace/
python /mnt/workspace/project-h/scripts/upload_to_s3.py 

## scan all tables in poker database automatically,
## if table is partitioned, then repair it.
bash /mnt/workspace/project-h/shell/daily_msck_repair.sh 

YESDT=$(TZ='Asia/Shanghai' date -d '24 hours ago' +%F)
echo "using yesterday's date: $YESDT"

# Run pyspark mission dws_dz_seat_info_di-pyspark.py # elapsed time 1000s
spark-submit /mnt/workspace/project-h/pyspark/dwd_dz_manual_data_di.py $YESDT
spark-submit /mnt/workspace/project-h/pyspark/dws_dz_seat_info_di-pyspark.py $YESDT
spark-submit /mnt/workspace/project-h/pyspark/dws_dz_player_action_time_di.py $YESDT
bash /mnt/workspace/project-h/shell/run_sql.sh $YESDT
spark-submit /mnt/workspace/project-h/pyspark/database_information.py $YESDT


# Sync to Algo Admin Platform
python /mnt/workspace/project-h/pyspark/sync_to_admin_game_overview_stats.py $YESDT
python /mnt/workspace/project-h/pyspark/sync_to_admin_robot_stats.py $YESDT
python /mnt/workspace/project-h/pyspark/sync_to_admin_robot_stats_3m.py $YESDT
python /mnt/workspace/project-h/pyspark/sync_to_admin_table_info.py $YESDT
python /mnt/workspace/project-h/pyspark/sync_to_admin_active_time.py $YESDT
python /mnt/workspace/project-h/pyspark/sync_to_admin_user_active_tag.py $YESDT
python /mnt/workspace/project-h/pyspark/sync_to_admin_preset_overview.py $YESDT
python /mnt/workspace/project-h/pyspark/sync_to_admin_preset_result.py $YESDT

# Sync to Redis
python /mnt/workspace/project-h/hive/hive2redis.py --type new_user 
python /mnt/workspace/project-h/hive/hive2redis.py --type suspect_user 

# Repair tables
bash /mnt/workspace/project-h/shell/daily_msck_repair.sh 

# Sync to MySQL
python /mnt/workspace/project-h/hive/sync_poker_hive_to_mysql.py --dt $YESDT

# Clean logs
python /mnt/workspace/project-h/scripts/cleanup_logs.py 

#bash /mnt/workspace/project-h/daily_mission/run.sh > /mnt/workspace/project-h/logs/execution_$(date +%Y%m%d_%H%M%S).log 2>&1