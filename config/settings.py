import os
from dotenv import load_dotenv
load_dotenv()

ANGEL_API_KEY = os.getenv('ANGEL_API_KEY')
ANGEL_CLIENT_ID = os.getenv('ANGEL_CLIENT_ID')
ANGEL_PASSWORD = os.getenv('ANGEL_PASSWORD')
ANGEL_TOTP_SECRET = os.getenv('ANGEL_TOTP_SECRET')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

LOT_SIZE = 65
PAPER_TRADING = True
SL_PERCENT = 0.40
TARGET_POINTS = 12

TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1D']
TIMEFRAME_INTERVALS = {
    '1m': 'ONE_MINUTE', '5m': 'FIVE_MINUTE', '15m': 'FIFTEEN_MINUTE',
    '30m': 'THIRTY_MINUTE', '1h': 'ONE_HOUR', '4h': 'FOUR_HOUR', '1D': 'ONE_DAY'
}
TIMEFRAME_DAYS = {
    '1m': 1, '5m': 2, '15m': 5, '30m': 7, '1h': 10, '4h': 20, '1D': 30
}
TIMEFRAME_WEIGHTS = {
    '1m': 0.05, '5m': 0.10, '15m': 0.20, '30m': 0.15,
    '1h': 0.20, '4h': 0.15, '1D': 0.15
}
CONFIDENCE_THRESHOLD = 0.65
NIFTY_TOKEN = '99926000'
MARKET_OPEN = (9, 15)
MARKET_CLOSE = (15, 30)
