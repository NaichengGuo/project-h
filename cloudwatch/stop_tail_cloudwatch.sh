#!/bin/bash

# 查找进程 ID
PIDS=$(ps -ef | grep "tail_cloudwatch.py" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No running tail_cloudwatch.py process found."
    exit 0
fi

echo "Found process(es): $PIDS"
echo "Sending SIGTERM to allow graceful exit..."

# 发送 SIGTERM 信号
kill $PIDS

# 等待进程退出
for pid in $PIDS; do
    echo -n "Waiting for PID $pid to exit"
    count=0
    while kill -0 $pid 2>/dev/null; do
        echo -n "."
        sleep 1
        count=$((count+1))
        if [ $count -ge 30 ]; then
            echo
            echo "Process $pid did not exit after 30 seconds. Force killing..."
            kill -9 $pid
            break
        fi
    done
    echo " Done."
done

echo "All processes stopped."
