#!/bin/bash
# bash shell/run_dws_dz_player_action_di.sh 2025-12-26

DT="${1:-}"
if [ -z "$DT" ]; then
    DT="$(date -d "yesterday" +%F)"
fi

if ! [[ "$DT" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Error: Date format must be YYYY-MM-DD"
    exit 1
fi

SQL_DIR="/mnt/workspace/sql"
SQL_FILES=(
    "$SQL_DIR/dws_dz_player_action_di.sql"
    "$SQL_DIR/dws_dz_robot_info_di.sql"
    "$SQL_DIR/dws_dz_player_win_lose_round_di.sql"
    "$SQL_DIR/dws_dz_robot_win_lose_result_di.sql"
    "$SQL_DIR/dws_dz_player_win_lose_u_di.sql"
    "$SQL_DIR/dws_db_player_game_result_di.sql"
    "$SQL_DIR/ods_card_preset_di.sql"
    "$SQL_DIR/dws_dz_player_collusion_cross_df.sql"
    "$SQL_DIR/dws_dz_player_tag_df.sql"
    "$SQL_DIR/dws_dz_player_profile_tag_df.sql"
)

for SQL_FILE in "${SQL_FILES[@]}"; do
    echo "Running Hive SQL: $SQL_FILE with date=$DT"
    if hive -hivevar dt="$DT" -f "$SQL_FILE"; then
        echo "Success: $SQL_FILE dt=$DT"
    else
        echo "Failed: $SQL_FILE dt=$DT"
        exit 1
    fi
done
