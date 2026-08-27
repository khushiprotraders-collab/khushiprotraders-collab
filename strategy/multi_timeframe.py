import pandas as pd
from datetime import datetime, timedelta
from core.auth import get_auth
from core.indicators import compute_all_indicators
from config.settings import TIMEFRAME_INTERVALS, TIMEFRAME_DAYS, TIMEFRAME_WEIGHTS

class MultiTimeframeAnalyzer:
    def __init__(self):
        self.auth = get_auth()

    def fetch_tf_data(self, interval, days_back):
        now = datetime.now()
        from_date = (now - timedelta(days=days_back)).strftime("%Y-%m-%d 09:15")
        to_date = now.strftime("%Y-%m-%d %H:%M")
        candles = self.auth.get_candles('99926000', interval, from_date, to_date)
        if not candles:
            return pd.DataFrame()
        df = pd.DataFrame(candles, columns=['date','open','high','low','close','volume'])
        df['date'] = pd.to_datetime(df['date'])
        return df

    def analyze_tf(self, df):
        if df.empty or len(df) < 20:
            return 0, []
        df = compute_all_indicators(df)
        latest = df.iloc[-1]
        signals = []
        score = 0.0

        if latest['rsi'] < 30:
            signals.append(f"RSI Oversold ({latest['rsi']:.1f})")
            score += 0.2
        elif latest['rsi'] > 70:
            signals.append(f"RSI Overbought ({latest['rsi']:.1f})")
            score -= 0.2

        if latest['macd'] > latest['macd_signal']:
            signals.append("MACD Bullish")
            score += 0.25
        else:
            signals.append("MACD Bearish")
            score -= 0.25

        if latest['close'] > latest['sma_20']:
            signals.append("Price > SMA20")
            score += 0.15
        else:
            signals.append("Price < SMA20")
            score -= 0.15

        if latest['close'] > latest['sma_50']:
            signals.append("Price > SMA50")
            score += 0.15
        else:
            signals.append("Price < SMA50")
            score -= 0.15

        if latest['direction'] == 1:
            signals.append("SuperTrend Bullish")
            score += 0.15
        else:
            signals.append("SuperTrend Bearish")
            score -= 0.15

        return max(-1, min(1, score)), signals

    def analyze(self):
        total_score = 0.0
        total_weight = 0.0
        all_signals = []
        tf_results = {}

        for tf, weight in TIMEFRAME_WEIGHTS.items():
            interval = TIMEFRAME_INTERVALS.get(tf)
            days = TIMEFRAME_DAYS.get(tf, 5)
            if not interval:
                continue
            df = self.fetch_tf_data(interval, days)
            score, signals = self.analyze_tf(df)
            tf_results[tf] = {'score': score, 'signals': signals}
            total_score += score * weight
            total_weight += weight
            if signals:
                all_signals.extend(signals[:2])

        if total_weight == 0:
            return {'signal': 'NEUTRAL', 'confidence': 0.0, 'score': 0.0, 'top_signals': [], 'tf_results': {}}

        final_score = total_score / total_weight
        confidence = min(0.95, 0.5 + abs(final_score))

        if final_score > 0.3:
            signal = 'BULLISH'
            direction = 'CE'
        elif final_score < -0.3:
            signal = 'BEARISH'
            direction = 'PE'
        else:
            signal = 'NEUTRAL'
            direction = 'NONE'

        return {
            'signal': signal,
            'direction': direction,
            'score': final_score,
            'confidence': confidence,
            'top_signals': list(dict.fromkeys(all_signals))[:5],
            'tf_results': tf_results
        }
