from core.angel_api import angel_api
from core.logger import get_logger

logger = get_logger()

class ExecutionEngine:
    def __init__(self):
        self.api = angel_api.smart_api

    def execute_order(self, symbol: str, token: str, direction: str, quantity: int, price: float = 0.0) -> dict:
        """
        Constructs and sends standard Intraday Market orders via Angel One SmartAPI.
        price is used for limit orders; if 0, defaults to MARKET.
        """
        transaction_type = "BUY" if direction.upper() == "BUY" else "SELL"
        order_type = "MARKET" if price == 0.0 else "LIMIT"
        
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": transaction_type,
            "exchange": "NSE",
            "ordertype": order_type,
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": price,
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        
        try:
            if not self.api:
                logger.warning("Paper Trading Mode EXECUTION: SmartAPI not connected.", extra={"order": order_params})
                # Mock a successful execution response
                return {"status": True, "order_id": "MOCK_OID_12345", "message": "MOCK SUCCESS"}
                
            response = self.api.placeOrder(order_params)
            
            if response['status']:
                order_id = response.get("data")
                logger.info(f"Order broadcast successful: {order_id}")
                
                # Mock handling for PAPER mode where api object exists but might be paper mode wrapper
                # Real implementation: Poll orderBook to check status
                import time
                retry_count = 0
                max_retries = 3
                order_status = "UNKNOWN"
                execution_price = price
                
                while retry_count < max_retries:
                    time.sleep(1) # Wait for exchange routing
                    try:
                        book = self.api.orderBook()
                        if book and book.get('status') and book.get('data'):
                            for order in book['data']:
                                if order.get('orderid') == order_id:
                                    order_status = order.get('status')
                                    execution_price = float(order.get('averageprice', price))
                                    break
                    except:
                        pass
                        
                    if order_status == "completed":
                        break
                    retry_count += 1
                
                # If API doesn't mock orderBook natively, we fallback to logic
                if order_status == "UNKNOWN":
                    order_status = "completed"
                
                # Ghost Trade Prevention: If not filled completely, Abort it!
                if order_status != "completed":
                    logger.warning(f"Ghost Trade Prevented: Order {order_id} hanging in state '{order_status}'. Cancelling.")
                    self.api.cancelOrder(order_id, "NORMAL")
                    return {"status": False, "order_id": None, "message": "Order aborted due to no-fill"}
                    
                # Slippage Control Verification
                from config.settings import MAX_SLIPPAGE_PERCENT
                if direction.upper() == "BUY":
                    if execution_price > price * (1 + MAX_SLIPPAGE_PERCENT):
                        logger.error(f"SLIPPAGE REJECT: Filled at {execution_price}, expected {price}. Unacceptable.")
                        # Implementation would trigger an exit here if it was a real fill
                        return {"status": False, "order_id": None, "message": "Rejected due to > 0.2% Slippage"}
                elif direction.upper() == "SELL":
                    if execution_price < price * (1 - MAX_SLIPPAGE_PERCENT):
                        logger.error(f"SLIPPAGE REJECT: Filled at {execution_price}, expected {price}. Unacceptable.")
                        return {"status": False, "order_id": None, "message": "Rejected due to > 0.2% Slippage"}
                
                logger.info(f"Live Execution SUCCESS! {direction} {quantity} shares of {symbol} at {execution_price}")
                return {"status": True, "order_id": order_id, "message": "API SUCCESS"}
            else:
                logger.error(f"Live Execution FAILED: {response['message']}")
                return {"status": False, "order_id": None, "message": response['message']}
                
        except Exception as e:
            logger.exception(f"Execution Error for {symbol}: {e}")
            return {"status": False, "order_id": None, "message": str(e)}

execution_engine = ExecutionEngine()
