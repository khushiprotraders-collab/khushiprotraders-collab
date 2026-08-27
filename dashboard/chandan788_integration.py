import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

def chandan788_page():
    st.header("📈 Chandan788 Analysis")
    st.markdown("Option chain with Greeks and backtesting (inspired by SmartAPI.ipynb)")

    # Get spot from engine (if available)
    try:
        with open('last_signal.json', 'r') as f:
            import json
            data = json.load(f)
            spot = data.get('spot', 24090.85)
    except:
        spot = 24090.85

    atm_strike = round(spot / 50) * 50

    # ---------- Build Synthetic / Live Option Chain ----------
    strikes = [atm_strike + i for i in range(-500, 550, 50)]
    data_list = []
    for strike in strikes:
        # CE data
        data_list.append({
            'strike': strike,
            'type': 'CE',
            'LTP': max(5.0, round(spot - strike + 150 + np.random.normal(0, 5), 2)),
            'IV': round(12.5 + np.random.normal(0, 0.5), 2),
            'Delta': round(0.5 + (spot - strike) / 1000, 2),
            'OI': int(np.random.randint(10000, 500000))
        })
        # PE data
        data_list.append({
            'strike': strike,
            'type': 'PE',
            'LTP': max(5.0, round(strike - spot + 100 + np.random.normal(0, 5), 2)),
            'IV': round(13.0 + np.random.normal(0, 0.5), 2),
            'Delta': round(-0.5 + (spot - strike) / 1000, 2),
            'OI': int(np.random.randint(10000, 500000))
        })

    df_raw = pd.DataFrame(data_list)

    # ---------- Duplicate-safe pivot ----------
    df_clean = df_raw.drop_duplicates(subset=['strike', 'type'])
    df_pivot = df_clean.pivot_table(
        index='strike',
        columns='type',
        values=['LTP', 'IV', 'Delta', 'OI'],
        aggfunc='first'
    )
    # Flatten multi-index columns for clean display
    df_pivot.columns = [f"{col[1]} {col[0]}" for col in df_pivot.columns]
    df_pivot = df_pivot.reset_index()

    st.subheader("🔎 Option Chain Matrix")
    st.dataframe(df_pivot, use_container_width=True)

    # ---------- Premium Heatmap (manual, no pivot) ----------
    try:
        ce_series = df_clean[df_clean['type'] == 'CE'][['strike', 'LTP']].set_index('strike')['LTP']
        pe_series = df_clean[df_clean['type'] == 'PE'][['strike', 'LTP']].set_index('strike')['LTP']
        common_strikes = sorted(set(ce_series.index) & set(pe_series.index))
        if common_strikes:
            matrix = np.array([[ce_series.get(s, 0), pe_series.get(s, 0)] for s in common_strikes])
            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=['CE', 'PE'],
                y=common_strikes,
                colorscale='Viridis',
                text=matrix,
                texttemplate='%{text:.1f}'
            ))
            fig.update_layout(height=400, template='plotly_dark', title='Premium Heatmap')
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Heatmap could not be rendered: {e}")

    st.subheader("📊 Backtest (ORB Strategy)")
    if st.button("Run Backtest"):
        # Dummy historical data (replace with real data)
        dates = pd.date_range(end=datetime.now(), periods=100, freq='5min')
        df_dummy = pd.DataFrame({
            'date': dates,
            'open': np.random.normal(spot, 20, 100),
            'high': np.random.normal(spot+10, 20, 100),
            'low': np.random.normal(spot-10, 20, 100),
            'close': np.random.normal(spot, 20, 100),
            'volume': np.random.randint(1000, 5000, 100)
        })
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
                col1, col2, col3 = st.columns(3)
                col1.metric("Win Rate", f"{win_rate*100:.1f}%")
                col2.metric("Avg Profit", f"{avg_profit:.2f}")
                col3.metric("Sharpe", f"{sharpe:.2f}")
                st.dataframe(df_trades)
            else:
                st.info("No trades generated.")
        else:
            st.warning("Insufficient data for backtest.")

if __name__ == "__main__":
    chandan788_page()
