import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Ensure directories exist
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Angel One API Credentials
API_KEY = os.getenv("API_KEY", "")
CLIENT_ID = os.getenv("CLIENT_ID", "")
PASSWORD = os.getenv("PASSWORD", "")
TOTP_SECRET = os.getenv("TOTP_SECRET", "")

# Risk Management Parameters
MAX_POSITION_SIZE_PERCENT = 0.05  # 5% of portfolio per trade
MAX_DAILY_DRAWDOWN_PERCENT = 0.02 # Halt trading if 2% down for the day
CONFIDENCE_THRESHOLD = 0.90       # 90% strict confidence threshold for ML
TRAILING_SL_PERCENT = 0.01        # 1% trailing stoploss

# Trading Parameters
MODE = "PAPER"                    # "PAPER" or "LIVE"
CANDLE_INTERVAL = "ONE_MINUTE"    # Phase 1: 1-minute candles
RETRY_DELAY_SECONDS = 3           # API rate limit delay
COOLDOWN_MINUTES = 10             # Minutes to wait before re-entering same symbol
MAX_SLIPPAGE_PERCENT = 0.002      # 0.2% max acceptable slippage between expected vs execution
