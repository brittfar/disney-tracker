import sqlite3
import pandas as pd

DB_PATH = 'disney_complete.db'

def find_bloat():
    print(f"📊 Analyzing {DB_PATH} for removable data...")
    conn = sqlite3.connect(DB_PATH)
    
    # Get stats for every ride
    query = """
    SELECT 
        ride_name,
        COUNT(*) as total_rows,
        AVG(wait_time) as avg_wait,
        MAX(wait_time) as max_wait
    FROM wait_times
    GROUP BY ride_name
    ORDER BY avg_wait ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"\nFound {len(df)} total attractions.")
    print("-" * 60)
    print(f"{'RIDE NAME':<50} | {'AVG WAIT':<10} | {'MAX WAIT':<10} | {'ROWS (Space)'}")
    print("-" * 60)
    
    # 1. Shows & Low Wait Attractions (Candidates for deletion)
    junk_candidates = df[
        (df['avg_wait'] < 10) |  # Average wait is less than 10 mins
        (df['ride_name'].str.contains('Meet|Greet|Exhibit|Trail|Gallery|Adventure|Review|Short Film|Vacation Fun', case=False))
    ]
    
    for _, row in junk_candidates.iterrows():
        print(f"{row['ride_name'][:50]:<50} | {row['avg_wait']:<10.1f} | {row['max_wait']:<10} | {row['total_rows']:,}")

    total_waste = junk_candidates['total_rows'].sum()
    percent_waste = (total_waste / df['total_rows'].sum()) * 100
    
    print("-" * 60)
    print(f"⚠️  POTENTIAL SAVINGS: Removing these {len(junk_candidates)} attractions")
    print(f"🗑️  Would delete {total_waste:,} rows ({percent_waste:.1f}% of your database).")

if __name__ == "__main__":
    find_bloat()