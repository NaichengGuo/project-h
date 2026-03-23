import time
import argparse
import sys
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
from pyhive import hive
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.fs as pafs

# Configure logging
def setup_logging(debug=False):
    logger = logging.getLogger('read_hive')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

class HiveReader:
    def __init__(self, host: str, port: int, username: str, database: str):
        self.host = host
        self.port = port
        self.username = username
        self.database = database
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
        
        raise Exception(f"Could not connect to Hive after {max_retries} attempts")

    def read(self, table_name: str, limit: int = 10) -> Tuple[List[str], List[Tuple]]:
        """
        Reads data from a Hive table.
        Returns a tuple of (column_names, rows).
        """
        sql = f"SELECT * FROM {table_name} LIMIT {limit}"
        
        try:
            logger.info(f"Executing query: {sql}")
            self.cursor.execute(sql)
            
            # Get column names
            columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
            
            # Fetch results
            rows = self.cursor.fetchall()
            logger.info(f"Fetched {len(rows)} rows from {table_name}")
            
            return columns, rows
            
        except Exception as e:
            logger.error(f"Error reading from Hive: {e}")
            # Try to reconnect and retry once
            try:
                logger.info("Attempting to reconnect and retry read...")
                self.connect()
                self.cursor.execute(sql)
                columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
                rows = self.cursor.fetchall()
                logger.info("Retry read successful.")
                return columns, rows
            except Exception as retry_e:
                logger.error(f"Retry failed: {retry_e}")
                raise retry_e

    def query(self, sql: str) -> pd.DataFrame:
        """
        Executes a SQL query and returns the result as a pandas DataFrame.
        """
        try:
            logger.info(f"Executing query: {sql}")
            return pd.read_sql(sql, self.conn)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            # Try to reconnect and retry once
            try:
                logger.info("Attempting to reconnect and retry query...")
                self.connect()
                return pd.read_sql(sql, self.conn)
            except Exception as retry_e:
                logger.error(f"Retry query failed: {retry_e}")
                raise retry_e

    def get_table_location(self, table_name: str) -> str:
        sql = f"DESCRIBE FORMATTED {table_name}"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        for row in rows:
            key = (row[0] or "").strip()
            value = (row[1] or "").strip()
            if key.startswith("Location:"):
                return value
        raise ValueError(f"Location not found for table: {table_name}")

    def get_partition_columns(self, table_name: str) -> List[str]:
        sql = f"DESCRIBE FORMATTED {table_name}"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        partition_columns: List[str] = []
        section = ""
        for row in rows:
            key = (row[0] or "").strip()
            data_type = (row[1] or "").strip()
            if key == "# Partition Information":
                section = "partition_header"
                continue
            if key.startswith("# Detailed Table Information"):
                break
            if section == "partition_header" and key == "col_name" and data_type == "data_type":
                section = "partition_columns"
                continue
            if section == "partition_columns":
                if not key or key.startswith("#"):
                    continue
                partition_columns.append(key)
        return partition_columns

    def read_partition_from_s3(self, table_name: str, partition_spec: Dict[str, str], limit: int = 10) -> pd.DataFrame:
        table_location = self.get_table_location(table_name)
        if table_location.startswith("s3a://"):
            table_location = "s3://" + table_location[len("s3a://"):]
        if not table_location.startswith("s3://"):
            raise ValueError(f"Table location is not on S3: {table_location}")

        s3_partition_path = table_location.rstrip("/")
        if partition_spec:
            ordered_partition_path = "/".join([f"{k}={v}" for k, v in partition_spec.items()])
            s3_partition_path = f"{s3_partition_path}/{ordered_partition_path}"

        logger.info(f"Reading S3 partition path: {s3_partition_path}")
        parsed = urlparse(s3_partition_path)
        dataset_path = f"{parsed.netloc}{parsed.path}".lstrip("/")
        s3_fs = pafs.S3FileSystem()
        dataset = ds.dataset(dataset_path, filesystem=s3_fs, format="parquet")
        table = dataset.to_table()
        df = table.to_pandas()
        if limit is not None and limit > 0:
            return df.head(limit)
        return df

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("Connection closed.")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

def get_hive_reader():
    
    hive_host   = '10.0.21.126'
    hive_port   = 10000
    hive_user   = 'root'
    hive_db     = 'default'
    reader = None
    
    reader = HiveReader(hive_host, hive_port, hive_user, hive_db)
    return reader


def parse_partition_spec(partition_spec: Optional[str]) -> Dict[str, str]:
    if not partition_spec:
        return {}
    result: Dict[str, str] = {}
    parts = [p.strip() for p in partition_spec.split(",") if p.strip()]
    for part in parts:
        if "=" not in part:
            raise ValueError(f"Invalid partition spec segment: {part}")
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"Invalid partition spec segment: {part}")
        result[key] = value
    return result
#poker.ods_dz_db_table_user_df
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read Hive Table')
    
    # Hive arguments
    parser.add_argument('--hive-host', default='10.0.21.126', help='Hive host')
    parser.add_argument('--hive-port', type=int, default=10000, help='Hive port')
    parser.add_argument('--hive-user', default='root', help='Hive username')
    parser.add_argument('--hive-db', default='default', help='Hive database')
    parser.add_argument('--table', required=False, help='Hive table to read from')
    parser.add_argument('--limit', type=int, default=10, help='Number of rows to read')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--read-from-s3', action='store_true', help='Read from S3 table location directly')
    parser.add_argument('--partition-spec', default='', help='Partition spec, e.g. dt=2026-03-17 or dt=2026-03-17,region=sg')
    
    args = parser.parse_args()
    
    setup_logging(args.debug)
    
    reader = None
    try:
        reader = HiveReader(args.hive_host, args.hive_port, args.hive_user, args.hive_db)
        if args.read_from_s3:
            partition_spec = parse_partition_spec(args.partition_spec)
            df = reader.read_partition_from_s3(args.table, partition_spec, args.limit)
            print("\n" + "=" * 50)
            print(f"Table: {args.table} (S3 direct read, Top {args.limit} rows)")
            print("=" * 50)
            print(df.to_string(index=False))
            print("=" * 50 + "\n")
        else:
            columns, rows = reader.read(args.table, args.limit)
            print("\n" + "="*50)
            print(f"Table: {args.table} (Top {args.limit} rows)")
            print("="*50)
            print(" | ".join(columns))
            print("-" * 50)
            for row in rows:
                print(" | ".join(str(item) for item in row))
            print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"Program failed: {e}")
        sys.exit(1)
    finally:
        if reader:
            reader.close()
