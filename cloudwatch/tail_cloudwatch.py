import boto3
import time
import argparse
import sys
import json
import signal
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import List, Dict, Optional
from pyhive import hive

# 配置日志
def setup_logging(log_file='tail_cloudwatch.log', debug=False):
    logger = logging.getLogger('tail_cloudwatch')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # 避免重复添加 handler
    if not logger.handlers:
        # File Handler with rotation (10MB per file, keep 5 files)
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

logger = logging.getLogger('tail_cloudwatch')

class GracefulExiter:
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.info(f"Received signal {signum}, stopping gracefully...")
        self.kill_now = True

class CacheBuffer:
    def __init__(self, max_items: int, max_seconds: float):
        self.max_items = max_items
        self.max_seconds = max_seconds
        self.items: List[Dict] = []
        self.window_start = time.monotonic()
        
    def add(self, batch: List[Dict]):
        now = time.monotonic()
        if not self.items:
            self.window_start = now
        self.items.extend(batch)
        
    def should_flush(self) -> bool:
        if not self.items:
            return False
        if len(self.items) >= self.max_items:
            return True
        if (time.monotonic() - self.window_start) >= self.max_seconds:
            return True
        return False
        
    def pop_all(self) -> List[Dict]:
        out = self.items
        self.items = []
        self.window_start = time.monotonic()
        return out

class HiveWriter:
    def __init__(self, host: str, port: int, username: str, database: str, target_table: str):
        self.host = host
        self.port = port
        self.username = username
        self.database = database
        self.target_table = target_table
        self.conn = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                if self.conn:
                    try:
                        self.conn.close()
                    except:
                        pass
                self.conn = hive.connect(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    database=self.database
                )
                self.cursor = self.conn.cursor()
                logger.info(f"Connected to Hive at {self.host}:{self.port}")
                return
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to connect to Hive (attempt {retry_count}/{max_retries}): {e}")
                time.sleep(5)
        # 如果重试都失败，不抛出异常退出程序，而是允许后续操作失败并继续尝试重连（在 write 中）
        # 或者在这里抛出，让主程序决定。为了长期运行，建议这里抛出，主程序捕获后决定是否退出。
        # 但考虑到构造函数抛出异常比较直接。
        raise Exception(f"Could not connect to Hive after {max_retries} attempts")
        
    def write(self, records: List[Dict]):
        if not records:
            return
            
        values_list = []
        for r in records:
            ts = r.get("timestamp_ms") or int(time.time() * 1000)
            # Convert timestamp to UTC+8
            dt = time.strftime("%Y-%m-%d", time.gmtime((ts / 1000) + 8 * 3600))
            
            # Use 'message' for 'tstr' column
            msg = r.get("message", "")
            # Basic escaping for SQL string to avoid syntax errors
            # Replace backslash first, then single quotes
            msg = msg.replace("\\", "\\\\").replace("'", "\\'")
            
            values_list.append(f"('{msg}', '{dt}')")
            
        if not values_list:
            return
            
        # Construct INSERT statement
        sql = f"INSERT INTO {self.target_table} (tstr, dt) VALUES {','.join(values_list)}"
        
        try:
            logger.info(f"Writing {len(values_list)} records to {self.target_table}...")
            self.cursor.execute(sql)
            logger.info("Write successful.")
        except Exception as e:
            logger.error(f"Error writing to Hive: {e}")
            # Try to reconnect
            try:
                logger.info("Attempting to reconnect and retry write...")
                self.connect()
                self.cursor.execute(sql)
                logger.info("Retry write successful.")
            except Exception as retry_e:
                logger.error(f"Retry failed: {retry_e}")
                # Save to local failover file
                self.save_failed_records(records)

    def save_failed_records(self, records: List[Dict]):
        filename = f"failed_records_{int(time.time())}.json"
        try:
            with open(filename, 'w') as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")
            logger.error(f"Saved {len(records)} failed records to {filename}")
        except Exception as e:
            logger.error(f"Failed to save failed records locally: {e}")

def tail_logs(log_group_name, filter_pattern=None, interval=2, writer=None, buffer=None, key_word='FLATTENED_GAME_DATA: '):
    client = boto3.client('logs')
    exiter = GracefulExiter()
    
    # Start from current time
    start_time = int(time.time() * 1000)
    
    logger.info(f"Listening to log group: {log_group_name}")
    if filter_pattern:
        logger.info(f"Filter pattern: {filter_pattern}")
    logger.info(f"Keyword filter: {key_word}")
    
    seen_event_ids = set()
    
    while not exiter.kill_now:
        params = {
            'logGroupName': log_group_name,
            'startTime': start_time,
            'interleaved': True
        }
        if filter_pattern:
            params['filterPattern'] = filter_pattern
            
        try:
            response = client.filter_log_events(**params)
            events = response.get('events', [])
            
            # Sort by timestamp
            events.sort(key=lambda x: x.get('timestamp', 0))
            
            if not events:
                # Check flush even if no new events
                if buffer and writer and buffer.should_flush():
                    flushed = buffer.pop_all()
                    if flushed:
                        logger.info(f"Flushing {len(flushed)} records to Hive (timeout)...")
                        writer.write(flushed)
                      
                time.sleep(interval)
                continue
            
            last_timestamp = start_time
            new_events_for_buffer = []
            
            for event in events:
                event_id = event.get('eventId')
                timestamp = event.get('timestamp')
                
                if timestamp < start_time:
                    continue
                if timestamp == start_time and event_id in seen_event_ids:
                    continue
                    
                message = event.get('message', '').rstrip().lstrip()
                
                # Check keyword
                if key_word not in message:
                    continue
                    
                # Extract message part
                message = message.split(key_word)[-1]
                
                # Prepare for buffer
                if buffer:
                    record = {
                        "message": message,
                        "timestamp_ms": timestamp,
                        "ingestion_time_ms": event.get("ingestionTime"),
                        "log_group": log_group_name,
                        "log_stream": event.get("logStreamName")
                    }
                    new_events_for_buffer.append(record)
                
                last_timestamp = timestamp
            
            # Update seen_event_ids
            # To prevent memory leak, only keep IDs for the current last_timestamp
            if last_timestamp > start_time:
                seen_event_ids = {e.get('eventId') for e in events if e.get('timestamp') == last_timestamp}
            else:
                seen_event_ids.update(e.get('eventId') for e in events if e.get('timestamp') == last_timestamp)
            
            start_time = last_timestamp
            
            # Add to buffer
            if buffer and new_events_for_buffer:
                logger.debug(f"Added {len(new_events_for_buffer)} events to buffer")
                buffer.add(new_events_for_buffer)
            
            # Flush if needed
            if buffer and writer and buffer.should_flush():
                flushed = buffer.pop_all()
                if flushed:
                    logger.info(f"Flushing {len(flushed)} records to Hive (size)...")
                    writer.write(flushed)
            
            time.sleep(interval)
            
        except client.exceptions.ResourceNotFoundException:
            logger.error(f"Error: Log group '{log_group_name}' not found.")
            # For long running process, maybe wait and retry? Or exit?
            # Usually if log group is missing, it's a config error.
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(interval)
            
    # Exit cleanup
    logger.info("Loop stopped.")
    if buffer and writer:
         flushed = buffer.pop_all()
         if flushed:
             logger.info(f"Flushing remaining {len(flushed)} records to Hive before exit...")
             writer.write(flushed)
    logger.info("Bye.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tail CloudWatch Logs')
    parser.add_argument('--log_group_name', default='/aws/lambda/ec-function', help='The name of the log group')
    parser.add_argument('--filter', help='The filter pattern to use', default=None)
    parser.add_argument('--interval', type=float, default=2.0, help='Sleep interval in seconds between polls')
    parser.add_argument('--keyword', default='FLATTENED_GAME_DATA: ', help='Keyword to filter logs')
    
    # Hive arguments
    parser.add_argument('--hive-host', default='10.0.21.126', help='Hive host')
    parser.add_argument('--hive-port', type=int, default=10000, help='Hive port')
    parser.add_argument('--hive-user', default='root', help='Hive username')
    parser.add_argument('--hive-db', default='default', help='Hive database')
    parser.add_argument('--hive-table', default='poker.ods_temp_test_tab', help='Hive table to write logs to')
    
    parser.add_argument('--flush-interval', type=float, default=600.0, help='Flush interval in seconds')
    parser.add_argument('--max-buffer-size', type=int, default=10000, help='Max items in buffer before flush')
    parser.add_argument('--log-file', default='/mnt/workspace/logs/tail_cloudwatch.log', help='Log file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    setup_logging(args.log_file, args.debug)
    logger.info("Starting CloudWatch Tailer...")
    
    writer = None
    buffer = None
    
    if args.hive_table:
        logger.info(f"Initializing Hive writer for table: {args.hive_table}...")
        try:
            writer = HiveWriter(args.hive_host, args.hive_port, args.hive_user, args.hive_db, args.hive_table)
            buffer = CacheBuffer(args.max_buffer_size, args.flush_interval)
            logger.info("Hive writer initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Hive writer: {e}")
            sys.exit(1)
    
    tail_logs(args.log_group_name, args.filter, args.interval, writer, buffer, args.keyword)

