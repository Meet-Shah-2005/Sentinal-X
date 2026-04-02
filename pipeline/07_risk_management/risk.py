from config import settings
from core.logger import get_logger

logger = get_logger()

class RiskManager:
    def __init__(self):
        self.max_position_percent = settings.MAX_POSITION_SIZE_PERCENT
        self.max_drawdown_percent = settings.MAX_DAILY_DRAWDOWN_PERCENT
        
        # Mock active stats for paper trading memory
        self.starting_balance = 500000.0  # e.g., 5 Lakh starting margin
        self.current_balance = 500000.0
        self.daily_pnl = 0.0
        
    def check_risk_limits(self, price: float) -> dict:
        """
        Validates if a new trade adheres to risk guidelines.
        Returns {"approved": bool, "quantity": int, "reason": str}
        """
        # 1. Check Drawdown Halts
        drawdown_pct = self.daily_pnl / self.starting_balance
        if drawdown_pct <= -self.max_drawdown_percent:
            logger.warning(f"RISK HALT: Daily drawdown of {drawdown_pct*100:.2f}% breached maximum {self.max_drawdown_percent*100}% limite.")
            return {"approved": False, "quantity": 0, "reason": "Max Drawdown Breached"}
            
        # 2. Determine Position Size (Max 5% of Portfolio)
        max_capital_per_trade = self.current_balance * self.max_position_percent
        quantity = int(max_capital_per_trade // price)
        
        if quantity <= 0:
            logger.warning("RISK REJECT: Not enough margin to buy 1 share based on 5% rule.")
            return {"approved": False, "quantity": 0, "reason": "Insufficient Risk Capital"}
            
        logger.info(f"RISK APPROVED: Proceeding with {quantity} shares.", extra={"capital_allocated": quantity*price})
        return {"approved": True, "quantity": quantity, "reason": "Passes risk checks"}
        
    def update_pnl(self, realized_pnl: float):
        self.daily_pnl += realized_pnl
        self.current_balance += realized_pnl

risk_manager = RiskManager()
