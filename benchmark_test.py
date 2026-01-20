import akshare as ak
import time

print("Benchmarking AkShare functions...")

# 1. Benchmark full list
start = time.time()
try:
    df = ak.stock_zh_a_spot_em()
    print(f"Full list fetch (stock_zh_a_spot_em): {time.time() - start:.2f} seconds. Rows: {len(df)}")
except Exception as e:
    print(f"Full list fetch failed: {e}")

# 2. Benchmark single stock info
start = time.time()
try:
    info = ak.stock_individual_info_em(symbol="600519")
    print(f"Single stock info (stock_individual_info_em): {time.time() - start:.2f} seconds")
except Exception as e:
    print(f"Single stock info failed: {e}")

# 3. Check if lighter list API exists
try:
    start = time.time()
    df_light = ak.stock_info_a_code_name()
    print(f"Lighter list (stock_info_a_code_name): {time.time() - start:.2f} seconds. Rows: {len(df_light)}")
except AttributeError:
    print("stock_info_a_code_name does not exist")
except Exception as e:
    print(f"Lighter list fetch failed: {e}")
