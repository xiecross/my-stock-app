#!/usr/bin/env python3
"""
测试股票搜索性能
对比本地数据库搜索和在线搜索的速度
"""

import time
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_search_performance():
    """测试搜索性能"""
    print("=" * 60)
    print("股票搜索性能测试")
    print("=" * 60)
    
    # 导入必要的模块
    from stock_app import search_stock_fast, search_stock_online, get_cached_stock_database
    
    # 检查数据库状态
    print("\n1. 检查本地数据库...")
    stocks, update_time = get_cached_stock_database()
    if stocks:
        print(f"   ✅ 数据库已加载: {len(stocks):,} 只股票")
    else:
        print("   ⚠️  数据库为空，将使用在线搜索")
    
    # 测试查询
    test_queries = ["茅台", "600519", "平安", "招商", "000001"]
    
    print("\n2. 测试本地搜索性能...")
    for query in test_queries:
        start = time.time()
        results = search_stock_fast(query)
        elapsed = (time.time() - start) * 1000  # 转换为毫秒
        
        if results is not None and not results.empty:
            print(f"   查询 '{query}': {len(results)} 条结果, 耗时 {elapsed:.2f}ms")
        else:
            print(f"   查询 '{query}': 无结果, 耗时 {elapsed:.2f}ms")
    
    print("\n3. 对比在线搜索性能...")
    query = "茅台"
    print(f"   测试查询: '{query}'")
    
    # 在线搜索
    start = time.time()
    results_online = search_stock_online(query)
    elapsed_online = (time.time() - start) * 1000
    
    # 本地搜索
    start = time.time()
    results_local = search_stock_fast(query)
    elapsed_local = (time.time() - start) * 1000
    
    print(f"\n   在线搜索: {elapsed_online:.2f}ms")
    print(f"   本地搜索: {elapsed_local:.2f}ms")
    
    if elapsed_online > 0 and elapsed_local > 0:
        speedup = elapsed_online / elapsed_local
        print(f"   ⚡ 加速比: {speedup:.1f}x")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_search_performance()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
