from core.logger import get_logger
from datetime import datetime, timedelta
from config.settings import COOLDOWN_MINUTES
import importlib
trailing_sl_engine = importlib.import_module("pipeline.10_monitoring.trailing_sl").trailing_sl_engine

logger = get_logger()

class PreTradeValidator:
    def __init__(self):
        self.last_traded = {}

    def log_trade_exit(self, symbol: str):
        """Called by exit manager when a trade finishes to start the cooldown"""
        self.last_traded[symbol] = datetime.now()

    def validate(self, symbol: str, direction: str) -> bool:
        """
        Ensures safety preconditions before hitting placing order APIs.
        """
        # 1. Double Exposure Check
        if symbol in trailing_sl_engine.active_trades:
            active_trade = trailing_sl_engine.active_trades[symbol]
            logger.debug(f"VALIDATION FAILED: Trade already open for {symbol} ({active_trade['direction']}). Preventing double exposure.")
            return False
            
        # 2. Cooldown Check
        if symbol in self.last_traded:
            time_since_last_trade = datetime.now() - self.last_traded[symbol]
            if time_since_last_trade < timedelta(minutes=COOLDOWN_MINUTES):
                logger.debug(f"VALIDATION FAILED: {symbol} is in a {COOLDOWN_MINUTES}-minute cooldown. Prevented overtrading.")
                return False
            
        # 3. Add restricted lists check (penny stocks, suspended F&Os)
        restricted_list = ["SUSPENDED-EQ", "BANNED-OPT"]
        if symbol in restricted_list:
            logger.debug(f"VALIDATION FAILED: {symbol} is on restricted/banned list.")
            return False

        logger.info(f"Pre-Trade Validation PASSED for {symbol}.")
        return True

validator = PreTradeValidator()
