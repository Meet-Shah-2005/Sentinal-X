from core.logger import get_logger
import importlib
execution_engine = importlib.import_module("pipeline.09_execution_engine.executor").execution_engine
trade_auditor = importlib.import_module("pipeline.12_post_trade_audit.audit").trade_auditor

logger = get_logger()

class ExitManager:
    def __init__(self):
        pass

    def execute_exit(self, symbol: str, token: str, direction_held: str, quantity: int, exit_price: float, pnl: float, reason: str = "T-SL Triggered"):
        """
        Coordinates the closing of an active position.
        """
        inverse_direction = "SELL" if direction_held == "BUY" else "BUY"
        logger.info(f"EXIT MANAGER: Closing {direction_held} position on {symbol}. Reason: {reason}")
        
        # 1. Fire Execution to Square Off
        execution_response = execution_engine.execute_order(symbol, token, inverse_direction, quantity, price=0.0)
        
        if execution_response['status']:
            # 2. Log to Audit Database
            trade_auditor.log_trade(
                symbol=symbol,
                side=direction_held,
                exit_price=exit_price,
                pnl=pnl,
                reason=reason
            )
            logger.info(f"Successfully closed {symbol} position.")
            return True
        else:
            logger.error(f"FATAL: Exit execution failed for {symbol}.")
            return False

exit_manager = ExitManager()
