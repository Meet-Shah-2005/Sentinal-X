import sqlite3
from datetime import datetime
from config.settings import BASE_DIR
from core.logger import get_logger

logger = get_logger()

class TradeAuditor:
    def __init__(self):
        self.db_path = BASE_DIR / 'trade_history.sqlite'
        self._initialize_db()

    def _initialize_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completed_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    side TEXT,
                    exit_price REAL,
                    total_pnl REAL,
                    reason TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize trade history DB: {e}")

    def log_trade(self, symbol: str, side: str, exit_price: float, pnl: float, reason: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO completed_trades (timestamp, symbol, side, exit_price, total_pnl, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, symbol, side, exit_price, pnl, reason))
            
            conn.commit()
            conn.close()
            logger.info("Trade successfully committed to SQLite Audit log.")
        except Exception as e:
            logger.error(f"Failed to log trade to DB: {e}")

trade_auditor = TradeAuditor()
