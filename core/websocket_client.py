import json, threading
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from config.settings import ANGEL_CLIENT_ID
from core.auth import get_auth

class LiveMarketStreamer:
    def __init__(self):
        self.auth = get_auth()
        self.sws = None
        self.live_data = {}
        self.connected = False
        self.callback = None

    def on_data(self, wsapp, message):
        try:
            if isinstance(message, dict):
                token = message.get('token')
                ltp = message.get('last_traded_price')
                if token and ltp is not None:
                    self.live_data[token] = ltp / 100
                    if self.callback:
                        self.callback(token, ltp / 100)
        except Exception as e:
            print(f"WebSocket data error: {e}")

    def on_open(self, wsapp):
        self.connected = True
        print("✅ WebSocket connected")
        tokens = [{"exchangeType": 1, "tokens": ["99926000"]}]
        self.sws.subscribe("live_data", 1, tokens)

    def on_error(self, wsapp, error):
        print(f"❌ WebSocket error: {error}")

    def on_close(self, wsapp, close_status_code, close_msg):
        self.connected = False
        print(f"🔌 WebSocket closed: {close_status_code}")

    def connect(self, callback=None):
        self.callback = callback
        self.sws = SmartWebSocketV2(
            self.auth.jwt_token,
            self.auth.obj.api_key,
            ANGEL_CLIENT_ID,
            self.auth.feed_token
        )
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.sws.connect()
        self.sws.run_forever()

    def get_ltp(self, token):
        return self.live_data.get(token)
