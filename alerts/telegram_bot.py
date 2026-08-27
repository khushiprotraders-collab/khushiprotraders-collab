import requests
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SL_PERCENT, TARGET_POINTS, LOT_SIZE

def send_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)
        return resp.status_code == 200
    except:
        return False

def format_signal_alert(data):
    spot = data.get('spot', 0)
    signal = data.get('signal', 'NEUTRAL')
    direction = data.get('direction', 'NONE')
    confidence = data.get('confidence', 0)
    score = data.get('score', 0)
    top_signals = data.get('top_signals', [])
    atm_strike = round(spot / 50) * 50

    emoji = "🟢" if signal == 'BULLISH' else "🔴" if signal == 'BEARISH' else "⚪"
    trade_type = "CE" if direction == 'CE' else "PE" if direction == 'PE' else "NONE"
    premium = 145.25  # Placeholder — you can fetch real premium

    sl = round(premium * (1 - SL_PERCENT), 2) if direction == 'CE' else round(premium * (1 + SL_PERCENT), 2)
    target = round(premium + TARGET_POINTS, 2) if direction == 'CE' else round(premium - TARGET_POINTS, 2)

    msg = f"""
{emoji} <b>KPT GOLDEN SIGNAL</b>
📊 <b>Trade:</b> NIFTY {atm_strike} {trade_type}
📈 <b>Direction:</b> {signal}
🎯 <b>Confidence:</b> {confidence:.1%}
💰 <b>Entry:</b> ₹{premium:.2f}
🛑 <b>SL:</b> ₹{sl:.2f}
🎯 <b>Target:</b> ₹{target:.2f}
📉 <b>Score:</b> {score:+.2f}
📋 <b>Signals:</b>\n"""
    for s in top_signals[:5]:
        msg += f"  • {s}\n"
    msg += f"\n⏰ {data.get('timestamp', '')[:19]}"
    msg += f"\n⚠️ <i>Paper Trade | Educational Purpose Only</i>"
    return msg
