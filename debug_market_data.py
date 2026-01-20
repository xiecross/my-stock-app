import akshare as ak
import pandas as pd
import time

code = "600519"

print(f"Testing market data for {code}...")

# 1. Test stock_individual_info_em (Currently used)
print("\n--- individual_info_em ---")
try:
    df = ak.stock_individual_info_em(symbol=code)
    print(df)
except Exception as e:
    print(f"Error: {e}")

# 2. Test stock_bid_ask_em (Real-time bid/ask?)
print("\n--- stock_bid_ask_em ---")
try:
    df = ak.stock_bid_ask_em(symbol=code)
    print(df)
except Exception as e:
    print(f"Error: {e}")

# 3. Test stock_zh_a_spot_em (Full list - too slow, but checking if we can filter?)
# It doesn't accept symbol argument usually.

# 4. Test minute data for latest price
print("\n--- stock_zh_a_hist_min_em ---")
try:
    df = ak.stock_zh_a_hist_min_em(symbol=code, period="1", adjust="qfq")
    print(df.tail(1))
except Exception as e:
    print(f"Error: {e}")
