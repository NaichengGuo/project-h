import sys
import os
import argparse
import concurrent.futures
from datetime import datetime, timedelta

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
import redis_utils
from read_hive_table import HiveReader, get_hive_reader

# Query Configuration Map
# Each entry maps a query identifier to its SQL template and Redis key format
QUERY_MAP = {
    "new_user": {
        "sql": "select distinct nplayerid from poker.ods_dz_db_table_user_df where dt='{dt}'",
        "key_fmt": "new_user:{}",
        "desc": "Fresh user flags from ODS table",
        "ttl":-1,
        "value":1
    },
    "suspect_user": {
        "sql": 
        """
        select distinct suspect_playerid as nplayerid from(
        select distinct player1_id as suspect_playerid 
        from poker.dws_dz_player_collusion_cross_df 
        where dt='{dt}'
        and same_cnt>=20
        and win_rate>=0.7
        and (player1_same_rate>=0.75 or player2_same_rate>=0.75)
        and total_desk>=3
        union all 
        select distinct player2_id  as suspect_playerid 
        from poker.dws_dz_player_collusion_cross_df 
        where dt='{dt}'
        and same_cnt>=20
        and win_rate>=0.7
        and (player1_same_rate>=0.75 or player2_same_rate>=0.75)
        and total_desk>=3
        )t
        """,
        "key_fmt": "suspect_user:{}",
        "desc": "Fresh user flags from ODS table",
        "ttl": 86400*2,
        "value":3
    },
}

def write_to_redis(df, key_fmt, value=1, ttl=86400*2, max_workers=1):
    """
    Writes data from dataframe to Redis using a key format.
    
    Args:
        df: DataFrame containing 'nplayerid'
        key_fmt: String format for the key (e.g., "user:{}:flag")
        value: Value to set in Redis
        ttl: Time to live in seconds
        max_workers: Number of threads for parallel execution
    """
    if df.empty:
        print("DataFrame is empty, skipping Redis write.")
        return

    print(f"Starting Redis update with {max_workers} workers. Total keys: {len(df)}")
    
    def _process_user(nplayerid):
        try:
            key = key_fmt.format(nplayerid)
            # Using the existing send_redis_request from redis_utils
            redis_utils.send_redis_request("set", key=key, value=value, ttl=ttl)
            #print(f'key:{key}')
        except Exception as e:
            print(f"Failed to write key for user {nplayerid}: {e}")

    # Use tolist() for faster iteration than iterrows()
    user_ids = df['nplayerid'].tolist()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(_process_user, uid) for uid in user_ids]
        
        # Wait for completion and check for exceptions
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if i % 100 == 0 and i > 0:
                print(f"Processed {i} keys...")
            try:
                future.result()
            except Exception as e:
                print(f"Worker exception: {e}")

    print("Redis update completed.")

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Run Hive query and update Redis flags.")
    parser.add_argument(
        '--type', 
        required=True, 
        choices=QUERY_MAP.keys(),
        help='Type of query to execute. Available types: ' + ', '.join(QUERY_MAP.keys())
    )
    
    args = parser.parse_args()
    
    # Get configuration for the selected type
    config = QUERY_MAP[args.type]
    print(f"Selected query type: {args.type}")
    print(f"Description: {config.get('desc', 'No description')}")
   

    reader = get_hive_reader()
    
    # Calculate date (UTC+8 yesterday)
    dt = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Target date (dt): {dt}")
    
    # Format SQL with date
    query = config['sql'].format(dt=dt)
    key_fmt = config['key_fmt']
    
    print(f"Executing Hive query: {query}")
    print(f"Target Redis Key Format: {key_fmt}")
    
    ttl_value = config.get('ttl', -1)
    print(f"TTL: {ttl_value}")

    try:
        df = reader.query(query)
        print(f"Query returned {df.shape[0]} rows.")
        
        if not df.empty:
            write_to_redis(df, value=config.get('value', 1), key_fmt=key_fmt, ttl=ttl_value)
            
    except Exception as e:
        print(f"Error executing query or processing data: {e}")
    finally:
        reader.close()

if __name__ == "__main__":
    main()
