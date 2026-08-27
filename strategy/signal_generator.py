import json, time
from datetime import datetime
from core.auth import get_auth
from core.websocket_client import LiveMarketStreamer
from strategy.multi_timeframe import MultiTimeframeAnalyzer
from alerts.telegram_bot import send_alert, format_signal_alert
from config.settings import CONFIDENCE_THRESHOLD, NIFTY_TOKEN

class SignalEngine:
    def __init__(self):
        self.auth = get_auth()
        self.streamer = LiveMarketStreamer()
        self.analyzer = MultiTimeframeAnalyzer()
        self.spot = None
        self.last_signal = None
        self.last_alert_time = 0
        self.alert_cooldown = 300

    def on_price(self, token, price):
        if token == NIFTY_TOKEN:
            self.spot = price

    def run(self):
        print("🚀 Signal Engine starting...")
        self.streamer.connect(callback=self.on_price)
        while True:
            try:
                if self.spot is not None:
                    analysis = self.analyzer.analyze()
                    analysis['spot'] = self.spot
                    analysis['timestamp'] = datetime.now().isoformat()
                    with open('last_signal.json', 'w') as f:
                        json.dump(analysis, f, indent=2)
                    signal = analysis['signal']
                    confidence = analysis['confidence']
                    if signal != 'NEUTRAL' and confidence >= CONFIDENCE_THRESHOLD:
                        now = time.time()
                        if now - self.last_alert_time >= self.alert_cooldown:
                            msg = format_signal_alert(analysis)
                            send_alert(msg)
                            self.last_alert_time = now
                    print(f"📊 Signal: {signal} | Confidence: {confidence:.1%} | Spot: {self.spot:.2f}")
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
                break
            except Exception as e:
                print(f"❌ Engine error: {e}")
                time.sleep(5)
