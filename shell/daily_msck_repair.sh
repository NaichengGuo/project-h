#!/bin/bash

# =============================================================================
# Script Name: daily_msck_repair.sh
# Description: Scans all Hive tables in all databases, checks if they are 
#              partitioned, and runs 'MSCK REPAIR TABLE' for partitioned tables.
# Usage:       Run manually or schedule via crontab.
#              ./daily_msck_repair.sh
# =============================================================================

# Define log directory and file
LOG_DIR="/mnt/workspace/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/msck_repair_$(date +%F).log"

# Function to log messages with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Starting MSCK REPAIR daily job..."

# Check if hive command is available
if ! command -v hive &> /dev/null; then
    log "Error: 'hive' command not found. Please ensure Hive is installed and in PATH."
    exit 1
fi

# Target database
db="poker"
log "Processing database: $db"

# Get tables in the database
tables=$(hive -S -e "USE $db; SHOW TABLES")

if [ $? -ne 0 ]; then
    log "Error: Failed to get tables for database $db"
    exit 1
fi

for table in $tables; do
    # Check if table is partitioned
    # We use DESCRIBE FORMATTED and grep for "Partition Information" or "Partitioned: true" 
    # Note: The output format might vary slightly depending on Hive version, 
    # generally "Partition Information" section exists for partitioned tables.
    
    # Optimization: We check checking one by one might be slow if there are many tables.
    # But for shell script simplicity, this is the standard way.
    
    is_partitioned=$(hive -S -e "USE $db; DESCRIBE FORMATTED $table" 2>/dev/null | grep -i "Partition Information")
    
    if [ -n "$is_partitioned" ]; then
        log "Table $db.$table is PARTITIONED. Running MSCK REPAIR..."
        
        # Execute MSCK REPAIR
        # Capture both stdout and stderr to log file
        hive -e "USE $db; MSCK REPAIR TABLE $table" >> "$LOG_FILE" 2>&1
        
        if [ $? -eq 0 ]; then
            log "Successfully repaired table $db.$table"
        else
            log "Failed to repair table $db.$table. Check log for details."
        fi
    else
        # log "Table $db.$table is NOT partitioned. Skipping."
        :
    fi
done

log "MSCK REPAIR daily job completed."
