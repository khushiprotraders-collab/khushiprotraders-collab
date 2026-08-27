#!/usr/bin/env python3
"""
KPT Professional — NIFTY Options Paper Trading System
Multi-timeframe analysis with Telegram alerts
"""
from strategy.signal_generator import SignalEngine

if __name__ == "__main__":
    engine = SignalEngine()
    engine.run()
