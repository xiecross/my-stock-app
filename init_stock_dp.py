#!/usr/bin/env python3
"""
股票数据库初始化脚本
首次运行时执行，从网络下载股票列表并保存到本地
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    import akshare as ak
    print("正在从网络获取股票列表...")
    
    stock_list = ak.stock_zh_a_spot_em()
    stocks_dict = {}
    
    for _, row in stock_list.iterrows():
        code = str(row['代码'])
        name = str(row['名称'])
        stocks_dict[code] = name
    
    print(f"成功获取 {len(stocks_dict)} 只股票")
    
    # 保存到文件
    data_dir = Path(__file__).parent / 'data'
    data_dir.mkdir(exist_ok=True)
    
    db_file = data_dir / 'stock_list.json'
    data = {
        'stocks': stocks_dict,
        'update_time': datetime.now().timestamp()
    }
    
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 股票数据库已保存到: {db_file}")
    print(f"📊 股票数量: {len(stocks_dict):,} 只")
    print(f"⏰ 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
except ImportError:
    print("❌ 错误: 未安装 akshare 库")
    print("请运行: pip install akshare")
    sys.exit(1)
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)
