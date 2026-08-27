import os, json, urllib.request
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import mibian

# ---------- Helpers ----------
def get_greeks(spot, strike, days, premium, opt_type):
    try:
        iv = max(0.05, min(0.8, (premium / strike) * np.sqrt(365 / max(days, 1))))
        bs = mibian.BS([spot, strike, 7.0, days / 365], volatility=iv)
        if opt_type == 'CE':
            return {'delta': bs.callDelta, 'gamma': bs.callGamma, 'theta': bs.callTheta, 'vega': bs.callVega, 'iv': iv}
        else:
            return {'delta': bs.putDelta, 'gamma': bs.putGamma, 'theta': bs.putTheta, 'vega': bs.putVega, 'iv': iv}
    except:
        return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'iv': 0}

def fetch_option_chain(spot):
    url = "https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json"
    with urllib.request.urlopen(url) as response:
        instruments = json.loads(response.read())

    data = []
    atm = round(spot / 50) * 50
    for i in instruments:
        if i.get('name') == 'NIFTY' and i.get('instrumenttype') == 'OPTIDX':
            strike = float(i['strike']) / 100
            if abs(strike - spot) <= 500:
                symbol = i['symbol']
                opt_type = symbol[-2:] if symbol[-2:] in ['CE', 'PE'] else ''
                token = i['token']
                premium = 145.25  # Placeholder – replace with actual API call later
                expiry_str = i['expiry']
                days = (datetime.strptime(expiry_str, '%d%b%Y') - datetime.now()).days
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
                        'expiry': expiry_str,
                        'days': days
                    })
    df = pd.DataFrame(data)
    if df.empty:
        return df
    # Keep only the nearest expiry for each (strike, type)
    df = df.loc[df.groupby(['strike', 'type'])['days'].idxmin()]
    df = df.drop_duplicates(subset=['strike', 'type'])
    df = df.sort_values('strike')
    return df

def chandan788_page():
    st.header("📈 Chandan788 Analysis")
    st.markdown("Option chain with Greeks and backtesting (inspired by SmartAPI.ipynb)")

    # Get spot from engine
    try:
        with open('last_signal.json', 'r') as f:
            data = json.load(f)
            spot = data.get('spot', 24000)
    except:
        spot = 24000

    col1, col2 = st.columns(2)
    col1.metric("NIFTY Spot", f"{spot:.2f}")
    atm = round(spot / 50) * 50
    col2.metric("ATM Strike", f"{atm:.0f}")

    st.subheader("🔎 Option Chain with Greeks")
    with st.spinner("Fetching option chain..."):
        df = fetch_option_chain(spot)
        if not df.empty:
            # Display table
            st.dataframe(df.style.format({
                'premium': '{:.2f}',
                'delta': '{:.3f}',
                'gamma': '{:.4f}',
                'theta': '{:.2f}',
                'vega': '{:.2f}',
                'iv': '{:.2%}'
            }), use_container_width=True)

            # ----- MANUAL HEATMAP (NO PIVOT) -----
            try:
                strikes = sorted(df['strike'].unique())
                types = ['CE', 'PE']
                matrix = np.zeros((len(strikes), len(types)))
                for i, s in enumerate(strikes):
                    for j, t in enumerate(types):
                        val = df[(df['strike'] == s) & (df['type'] == t)]['premium'].values
                        matrix[i, j] = val[0] if len(val) > 0 else 0

                fig = go.Figure(data=go.Heatmap(
                    z=matrix,
                    x=types,
                    y=strikes,
                    colorscale='Viridis',
                    text=matrix,
                    texttemplate='%{text:.1f}'
                ))
                fig.update_layout(height=400, template='plotly_dark', title='Premium Heatmap')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render heatmap: {e}")
        else:
            st.warning("No option data available")

    st.subheader("📊 Backtest (ORB Strategy)")
    if st.button("Run Backtest"):
        dates = pd.date_range(end=datetime.now(), periods=100, freq='5min')
        df_dummy = pd.DataFrame({
            'date': dates,
            'open': np.random.normal(spot, 20, 100),
            'high': np.random.normal(spot+10, 20, 100),
            'low': np.random.normal(spot-10, 20, 100),
            'close': np.random.normal(spot, 20, 100),
            'volume': np.random.randint(1000, 5000, 100)
        })
        # Simple ORB backtest
        if len(df_dummy) >= 5:
            orb_high = df_dummy['high'].iloc[:3].max()
            orb_low = df_dummy['low'].iloc[:3].min()
            df_dummy['signal'] = 0
            df_dummy.loc[df_dummy['close'] > orb_high, 'signal'] = 1
            df_dummy.loc[df_dummy['close'] < orb_low, 'signal'] = -1
            trades = []
            pos = 0
            entry = 0
            entry_idx = 0
            for i, row in df_dummy.iterrows():
                if pos == 0 and row['signal'] != 0:
                    pos = row['signal']
                    entry = row['close']
                    entry_idx = i
                elif pos != 0:
                    if (row['signal'] == -pos) or (i - entry_idx >= 5):
                        exit_price = row['close']
                        pnl = (exit_price - entry) * pos
                        trades.append({'entry': entry, 'exit': exit_price, 'pnl': pnl, 'type': 'long' if pos == 1 else 'short'})
                        pos = 0
            if trades:
                df_trades = pd.DataFrame(trades)
                total_pnl = df_trades['pnl'].sum()
                win_rate = (df_trades['pnl'] > 0).mean()
                avg_profit = df_trades['pnl'].mean()
                sharpe = avg_profit / df_trades['pnl'].std() if df_trades['pnl'].std() != 0 else 0
                st.success(f"Total P&L: {total_pnl:.2f} points")
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Win Rate", f"{win_rate*100:.1f}%")
                col_b.metric("Avg Profit", f"{avg_profit:.2f}")
                col_c.metric("Sharpe", f"{sharpe:.2f}")
                st.dataframe(df_trades)
            else:
                st.info("No trades generated.")
        else:
            st.warning("Insufficient data for backtest.")
