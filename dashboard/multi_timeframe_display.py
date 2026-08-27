import streamlit as st
import pandas as pd
import plotly.express as px
import json

def multi_timeframe_page():
    st.header("📊 Multi-Timeframe Analysis")
    st.markdown("Weighted scoring across timeframes (1m to 1D)")

    try:
        with open('last_signal.json', 'r') as f:
            data = json.load(f)
    except:
        st.warning("No signal data available. Please ensure the KPT engine is running.")
        return

    # Overall signal
    signal = data.get('signal', 'NEUTRAL')
    confidence = data.get('confidence', 0)
    score = data.get('score', 0)
    top_signals = data.get('top_signals', [])
    tf_results = data.get('tf_results', {})

    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Signal", signal, delta=f"{confidence:.1%}")
    col2.metric("Score", f"{score:+.2f}")
    col3.metric("Timeframes Analyzed", len(tf_results))

    if top_signals:
        st.markdown("#### 🔍 Top Indicator Signals")
        for s in top_signals[:5]:
            st.write(f"• {s}")

    if tf_results:
        # Build dataframe
        rows = []
        for tf, result in tf_results.items():
            rows.append({
                'Timeframe': tf,
                'Score': result.get('score', 0),
                'Signals': ', '.join(result.get('signals', [])[:2])
            })
        df = pd.DataFrame(rows)
        
        st.subheader("📋 Timeframe Breakdown")
        st.dataframe(df, use_container_width=True)

        # Bar chart of scores
        fig = px.bar(
            df,
            x='Timeframe',
            y='Score',
            title='Score per Timeframe',
            color='Score',
            color_continuous_scale=['red', 'yellow', 'green'],
            template='plotly_dark'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeframe data available.")

    st.caption(f"Last updated: {data.get('timestamp', 'N/A')[:19]}")

if __name__ == "__main__":
    multi_timeframe_page()
