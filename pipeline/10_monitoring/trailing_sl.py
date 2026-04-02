from core.logger import get_logger

logger = get_logger()

class TrailingStopLossEngine:
    def __init__(self, default_trailing_pct=0.01):
        self.default_trailing_pct = default_trailing_pct
        self.active_trades = {}

    def register_trade(self, symbol: str, direction: str, entry_price: float, quantity: int = 1):
        """
        Registers a new trade for SL monitoring.
        """
        initial_sl = entry_price * (1 - self.default_trailing_pct) if direction == "BUY" else entry_price * (1 + self.default_trailing_pct)
        
        self.active_trades[symbol] = {
            "direction": direction,
            "entry_price": entry_price,
            "highest_price": entry_price if direction == "BUY" else float('inf'), # For short, lowest price is tracked
            "lowest_price": entry_price if direction == "SELL" else float('-inf'),
            "stop_loss": initial_sl,
            "quantity": quantity,
            "risk_free": False
        }
        logger.info(f"Trade registered for Trailing SL", extra={"symbol": symbol, "entry_price": entry_price, "initial_sl": initial_sl})

    def update(self, symbol: str, current_price: float) -> dict:
        """
        Updates the trailing stop loss dynamically as price moves in favor.
        Returns a dict indicating if the stop loss was triggered.
        """
        if symbol not in self.active_trades:
            return {"triggered": False}

        trade = self.active_trades[symbol]
        direction = trade["direction"]

        if direction == "BUY":
            # Update SL if we reached a new high
            if current_price > trade["highest_price"]:
                trade["highest_price"] = current_price
                new_sl = current_price * (1 - self.default_trailing_pct)
                if new_sl > trade["stop_loss"]:
                    trade["stop_loss"] = new_sl
                    logger.debug(f"Trailing SL adjusted UP for {symbol}: {new_sl:.2f}")

            # Check Risk-Free status
            if not trade["risk_free"] and trade["stop_loss"] > trade["entry_price"]:
                trade["risk_free"] = True
                logger.info(f"Trade {symbol} is now RISK-FREE! Stop loss locked above entry.")

            # Check if triggered
            if current_price <= trade["stop_loss"]:
                logger.warning(f"Stop Loss TRIGGERED for {symbol} at {current_price:.2f} (SL: {trade['stop_loss']:.2f})")
                return {"triggered": True, "exit_price": current_price, "pnl": current_price - trade["entry_price"]}

        elif direction == "SELL":
            # Update SL if we reached a new low
            if current_price < trade["lowest_price"]:
                trade["lowest_price"] = current_price
                new_sl = current_price * (1 + self.default_trailing_pct)
                if new_sl < trade["stop_loss"]:
                    trade["stop_loss"] = new_sl
                    logger.debug(f"Trailing SL adjusted DOWN for {symbol}: {new_sl:.2f}")

            # Check Risk-Free status
            if not trade["risk_free"] and trade["stop_loss"] < trade["entry_price"]:
                trade["risk_free"] = True
                logger.info(f"Trade {symbol} is now RISK-FREE! Stop loss locked below entry.")

            # Check if triggered
            if current_price >= trade["stop_loss"]:
                logger.warning(f"Stop Loss TRIGGERED for {symbol} at {current_price:.2f} (SL: {trade['stop_loss']:.2f})")
                return {"triggered": True, "exit_price": current_price, "pnl": trade["entry_price"] - current_price}

        return {"triggered": False}

    def remove_trade(self, symbol: str):
        if symbol in self.active_trades:
            del self.active_trades[symbol]

trailing_sl_engine = TrailingStopLossEngine()
