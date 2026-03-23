#!/bin/bash

# 获取脚本所在目录的绝对路径
BASE_DIR='/mnt/workspace/'
LOG_FILE="$BASE_DIR/logs/tail_cloudwatch.log"

# 检查是否已经在运行
if ps -ef | grep "tail_cloudwatch.py" | grep -v grep > /dev/null; then
    echo "Warning: tail_cloudwatch.py is already running."
    ps -ef | grep "tail_cloudwatch.py" | grep -v grep
    read -p "Do you want to start another instance? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Starting tail_cloudwatch.py..."

# 使用 nohup 后台运行
# stdout/stderr 重定向到 /dev/null，因为主要的日志已经由 Python 代码写入到 log 文件中了
nohup python3 "$BASE_DIR/cloudwatch/tail_cloudwatch.py" \
    --log_group_name "/aws/lambda/ec-function" \
    --hive-table "poker.ods_temp_test_tab" \
    --log-file "$LOG_FILE" \
    --interval 2.0 \
    --flush-interval 600.0 \
    > /dev/null 2>&1 &

PID=$!
echo "Process started with PID: $PID"
echo "Logs are being written to: $LOG_FILE"
