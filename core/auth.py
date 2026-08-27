import pyotp
from SmartApi import SmartConnect
from config.settings import ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PASSWORD, ANGEL_TOTP_SECRET

class AngelOneAuth:
    def __init__(self):
        self.obj = None
        self.jwt_token = None
        self.feed_token = None

    def login(self):
        try:
            self.obj = SmartConnect(api_key=ANGEL_API_KEY)
            totp = pyotp.TOTP(ANGEL_TOTP_SECRET).now()
            session = self.obj.generateSession(
                clientCode=ANGEL_CLIENT_ID,
                password=ANGEL_PASSWORD,
                totp=totp
            )
            self.jwt_token = session['data']['jwtToken']
            self.feed_token = self.obj.getfeedToken()
            print("✅ Angel One login successful")
            return True
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

    def get_connection(self):
        if not self.obj:
            self.login()
        return self.obj

    def get_ltp(self, exchange, token):
        try:
            resp = self.obj.ltpData(exchange, "", token)
            return resp['data']['ltp']
        except:
            return None

    def get_candles(self, token, interval, from_date, to_date):
        try:
            params = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date
            }
            resp = self.obj.getCandleData(params)
            return resp.get('data', [])
        except:
            return []

_auth = None

def get_auth():
    global _auth
    if _auth is None:
        _auth = AngelOneAuth()
        _auth.login()
    return _auth
