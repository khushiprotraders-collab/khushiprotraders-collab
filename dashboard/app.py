import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os, json, time, random
import pandas as pd, numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv
from SmartApi import SmartConnect
import pyotp
from streamlit_autorefresh import st_autorefresh

# Import Chandan788 integration
from chandan788_integration import chandan788_page

load_dotenv()

st.set_page_config(page_title="KPT Professional", layout="wide")
st_autorefresh(interval=30000, key="kpt_refresh")

# ---------- Header ----------
tz = pytz.timezone('Asia/Kolkata')
now = datetime.now(tz)
market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
is_market_live = (now.weekday() < 5) and (market_open <= now <= market_close)
status_text = "🟢 Market Open" if is_market_live else "⚫ Market Closed"
st.markdown(f"""
    <div style="background:#161B22; border-bottom:2px solid #FFD700; padding:12px; border-radius:8px; display:flex; justify-content:space-between;">
        <div><h2 style="color:#FFD700;">🏆 KPT Professional</h2><small style="color:#AAA;">Multi‑timeframe NIFTY Options</small></div>
        <div style="text-align:right;">
            <h4 style="color:#FFF;">{now.strftime('%I:%M:%S %p')}</h4>
            <span style="color:{'#00E676' if is_market_live else '#FF5252'}; font-weight:bold;">{status_text}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.markdown("### 📌 Navigation")
page = st.sidebar.radio("", ["🏠 Live Dashboard", "📊 Multi-Timeframe", "🔎 Options Chain", "📈 Chandan788 Analysis"])
refresh_rate = st.sidebar.selectbox("Refresh (sec)", [10, 30, 60, 120, 300], index=2)
if st.sidebar.button("🔄 Refresh Live Data"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("KPT v2.0 • Paper Trading")

# ---------- Helper ----------
def get_signal():
    try:
        with open('last_signal.json', 'r') as f:
            return json.load(f)
    except:
        return None

# ---------- Pages ----------
if page == "🏠 Live Dashboard":
    data = get_signal()
    if data:
        spot = data.get('spot', 0)
        signal = data.get('signal', 'NEUTRAL')
        conf = data.get('confidence', 0)
        top = data.get('top_signals', [])
        st.metric("NIFTY Spot", f"{spot:.2f}")
        st.metric("Signal", signal, delta=f"{conf:.1%}")
        for s in top[:5]:
            st.write(f"• {s}")
    else:
        st.info("Waiting for signal data... (Ensure engine is running)")

elif page == "📊 Multi-Timeframe":
    st.info("Multi-timeframe charts will appear here.")

elif page == "🔎 Options Chain":
    st.info("Options chain with Greeks will appear here.")

elif page == "📈 Chandan788 Analysis":
    chandan788_page()

# ---------- Auto Refresh ----------
time.sleep(refresh_rate)
st.rerun()
