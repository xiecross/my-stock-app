"""
Technical Indicators Calculation Module
Provides various technical analysis indicators for stock data
"""
import pandas as pd
import numpy as np


def calculate_ma(df, periods=[5, 10, 20, 30, 60]):
    """Calculate Moving Averages"""
    result = {}
    for period in periods:
        result[f'MA{period}'] = df['收盘'].rolling(window=period).mean().tolist()
    return result


def calculate_ema(df, periods=[12, 26]):
    """Calculate Exponential Moving Averages"""
    result = {}
    for period in periods:
        result[f'EMA{period}'] = df['收盘'].ewm(span=period, adjust=False).mean().tolist()
    return result


def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = df['收盘'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['收盘'].ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'MACD': macd_line.tolist(),
        'Signal': signal_line.tolist(),
        'Histogram': histogram.tolist()
    }


def calculate_kdj(df, n=9, m1=3, m2=3):
    """Calculate KDJ (Stochastic Oscillator)"""
    low_list = df['最低'].rolling(window=n).min()
    high_list = df['最高'].rolling(window=n).max()
    
    rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
    rsv = rsv.fillna(50)
    
    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    j = 3 * k - 2 * d
    
    return {
        'K': k.tolist(),
        'D': d.tolist(),
        'J': j.tolist()
    }


def calculate_rsi(df, period=14):
    """Calculate RSI (Relative Strength Index)"""
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return {
        'RSI': rsi.tolist()
    }


def calculate_boll(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    middle = df['收盘'].rolling(window=period).mean()
    std = df['收盘'].rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return {
        'Upper': upper.tolist(),
        'Middle': middle.tolist(),
        'Lower': lower.tolist()
    }


def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high_low = df['最高'] - df['最低']
    high_close = np.abs(df['最高'] - df['收盘'].shift())
    low_close = np.abs(df['最低'] - df['收盘'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return {
        'ATR': atr.tolist()
    }


def calculate_obv(df):
    """Calculate On-Balance Volume"""
    obv = [0]
    for i in range(1, len(df)):
        if df['收盘'].iloc[i] > df['收盘'].iloc[i-1]:
            obv.append(obv[-1] + df['成交量'].iloc[i])
        elif df['收盘'].iloc[i] < df['收盘'].iloc[i-1]:
            obv.append(obv[-1] - df['成交量'].iloc[i])
        else:
            obv.append(obv[-1])
    
    return {
        'OBV': obv
    }


def calculate_all_indicators(df):
    """Calculate all technical indicators at once"""
    indicators = {}
    
    # Moving Averages
    indicators['MA'] = calculate_ma(df)
    
    # MACD
    indicators['MACD'] = calculate_macd(df)
    
    # KDJ
    indicators['KDJ'] = calculate_kdj(df)
    
    # RSI
    indicators['RSI'] = calculate_rsi(df)
    
    # Bollinger Bands
    indicators['BOLL'] = calculate_boll(df)
    
    # ATR
    indicators['ATR'] = calculate_atr(df)
    
    # OBV
    indicators['OBV'] = calculate_obv(df)
    
    return indicators
