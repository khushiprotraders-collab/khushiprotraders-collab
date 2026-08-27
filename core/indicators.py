import pandas as pd
import numpy as np

def compute_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(data, fast=12, slow=26, signal=9):
    exp1 = data.ewm(span=fast, adjust=False).mean()
    exp2 = data.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line, macd - signal_line

def compute_atr(high, low, close, window=14):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_supertrend(high, low, close, period=10, multiplier=3):
    atr = compute_atr(high, low, close, period)
    hl2 = (high + low) / 2
    upper = hl2 + (multiplier * atr)
    lower = hl2 - (multiplier * atr)
    st = pd.Series(index=close.index)
    direction = pd.Series(index=close.index)
    for i in range(period, len(close)):
        if i == period:
            direction.iloc[i] = 1 if close.iloc[i] > upper.iloc[i] else -1
        else:
            if direction.iloc[i-1] == 1:
                direction.iloc[i] = -1 if close.iloc[i] < lower.iloc[i] else 1
            else:
                direction.iloc[i] = 1 if close.iloc[i] > upper.iloc[i] else -1
        st.iloc[i] = lower.iloc[i] if direction.iloc[i] == 1 else upper.iloc[i]
    return st, direction

def compute_all_indicators(df):
    result = df.copy()
    result['rsi'] = compute_rsi(result['close'], 14)
    result['macd'], result['macd_signal'], result['macd_hist'] = compute_macd(result['close'])
    result['atr'] = compute_atr(result['high'], result['low'], result['close'], 14)
    result['sma_20'] = result['close'].rolling(20).mean()
    result['sma_50'] = result['close'].rolling(50).mean()
    result['ema_9'] = result['close'].ewm(span=9, adjust=False).mean()
    result['supertrend'], result['direction'] = compute_supertrend(result['high'], result['low'], result['close'])
    return result
