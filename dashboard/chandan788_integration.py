import os, json, time, urllib.request
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from SmartApi import SmartConnect
import pyotp
import mibian
from dotenv import load_dotenv
from config.settings import ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PASSWORD, ANGEL_TOTP_SECRET

load_dotenv()

# ------------------- Option Chain with Greeks -------------------
def get_greeks(spot, strike, days_to_expiry, premium, option_type):
    try:
        iv = max(0.05, min(0.8, (premium / strike) * np.sqrt(365 / max(days_to_expiry,1))))
        bs = mibian.BS([spot, strike, 7.0, days_to_expiry/365], volatility=iv)
        if option_type == 'CE':
            return {'delta': bs.callDelta, 'gamma': bs.callGamma, 'theta': bs.callTheta, 'vega': bs.callVega, 'iv': iv}
        else:
            return {'delta': bs.putDelta, 'gamma': bs.putGamma, 'theta': bs.putTheta, 'vega': bs.putVega, 'iv': iv}
    except:
        return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'iv': 0}

def fetch_option_chain(spot):
    # Download instrument master
    url = "https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json"
    with urllib.request.urlopen(url) as response:
        instruments = json.loads(response.read())
    atm_strike = round(spot/50)*50
    data = []
    for i in instruments:
        if i.get('name') == 'NIFTY' and i.get('instrumenttype') == 'OPTIDX':
            strike = float(i['strike'])/100
            if abs(strike - spot) <= 500:
                symbol = i['symbol']
                opt_type = symbol[-2:] if symbol[-2:] in ['CE','PE'] else ''
                token = i['token']
                # Get premium (simplified: we'll use placeholder if API not available)
                premium = 145.25  # placeholder; in production use ltpData
                days = (datetime.strptime(i['expiry'], '%d%b%Y') - datetime.now()).days
                if days > 0:
                    greeks = get_greeks(spot, strike, days, premium, opt_type)
                    data.append({
                        'strike': strike,
                        'type': opt_type,
                        'premium': premium,
                        'delta': greeks['delta'],
                        'gamma': greeks['gamma'],
                        'theta': greeks['theta'],
                        'vega': greeks['vega'],
                        'iv': greeks['iv'],
                        'expiry': i['expiry'],
                        'days': days
                    })
    return pd.DataFrame(data)

# ------------------- Backtesting -------------------
def run_backtest(df, strategy='ORB', exit_bars=5):
    if len(df) < 5:
        return None
    orb_high = df['high'].iloc[:3].max()
    orb_low = df['low'].iloc[:3].min()
    df['signal'] = 0
    df.loc[df['close'] > orb_high, 'signal'] = 1
    df.loc[df['close'] < orb_low, 'signal'] = -1
    trades = []
    pos = 0; entry = 0; entry_idx = 0
    for i, row in df.iterrows():
        if pos == 0 and row['signal'] != 0:
            pos = row['signal']
            entry = row['close']
            entry_idx = i
        elif pos != 0:
            if (row['signal'] == -pos) or (i - entry_idx >= exit_bars):
                exit_price = row['close']
                pnl = (exit_price - entry) * pos
                trades.append({'entry': entry, 'exit': exit_price, 'pnl': pnl, 'type': 'long' if pos==1 else 'short'})
                pos = 0
    if trades:
        df_trades = pd.DataFrame(trades)
        total_pnl = df_trades['pnl'].sum()
        win_rate = (df_trades['pnl'] > 0).mean()
        avg_profit = df_trades['pnl'].mean()
        sharpe = avg_profit / df_trades['pnl'].std() if df_trades['pnl'].std() != 0 else 0
        return {'total_pnl': total_pnl, 'win_rate': win_rate, 'avg_profit': avg_profit, 'sharpe': sharpe, 'trades': df_trades}
    return None

# ------------------- Streamlit Page -------------------
def chandan788_page():
    st.header("📈 Chandan788 Analysis")
    st.markdown("Option chain with Greeks and backtesting (inspired by SmartAPI.ipynb)")

    # Fetch live spot (if available from KPT engine, else use placeholder)
    try:
        with open('last_signal.json', 'r') as f:
            signal_data = json.load(f)
            spot = signal_data.get('spot', 24000)
    except:
        spot = 24000

    col1, col2 = st.columns(2)
    with col1:
        st.metric("NIFTY Spot", f"{spot:.2f}")
    with col2:
        atm = round(spot/50)*50
        st.metric("ATM Strike", f"{atm:.0f}")

    # Option Chain
    st.subheader("🔎 Option Chain with Greeks")
    with st.spinner("Loading option chain..."):
        df_chain = fetch_option_chain(spot)
        if not df_chain.empty:
            st.dataframe(df_chain.style.format({
                'premium': '{:.2f}',
                'delta': '{:.3f}',
                'gamma': '{:.4f}',
                'theta': '{:.2f}',
                'vega': '{:.2f}',
                'iv': '{:.2%}'
            }), use_container_width=True)
            # Heatmap of premiums
            heatmap_data = df_chain.pivot(index='strike', columns='type', values='premium')
            fig = go.Figure(data=go.Heatmap(z=heatmap_data.values, x=heatmap_data.columns, y=heatmap_data.index, colorscale='Viridis', text=heatmap_data.values, texttemplate='%{text:.1f}'))
            fig.update_layout(height=400, template='plotly_dark', title='Premium Heatmap')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No option data available")

    # Backtest
    st.subheader("📊 Backtest (ORB Strategy)")
    if st.button("Run Backtest"):
        # Fetch historical data (replace with actual API call)
        # For demo, we'll create dummy data
        dates = pd.date_range(end=datetime.now(), periods=100, freq='5min')
        df = pd.DataFrame({
            'date': dates,
            'open': np.random.normal(spot, 20, 100),
            'high': np.random.normal(spot+10, 20, 100),
            'low': np.random.normal(spot-10, 20, 100),
            'close': np.random.normal(spot, 20, 100),
            'volume': np.random.randint(1000, 5000, 100)
        })
        result = run_backtest(df)
        if result:
            st.success(f"Total P&L: {result['total_pnl']:.2f} points")
            col1, col2, col3 = st.columns(3)
            col1.metric("Win Rate", f"{result['win_rate']*100:.1f}%")
            col2.metric("Avg Profit", f"{result['avg_profit']:.2f}")
            col3.metric("Sharpe", f"{result['sharpe']:.2f}")
            st.dataframe(result['trades'])
        else:
            st.info("No trades generated")
