import time
import json
from datetime import datetime
from core.logger import get_logger
from core.angel_api import angel_api
from config import settings
from config.settings import BASE_DIR, LOG_DIR

# Pipeline Modules
import importlib
data_ingestion = importlib.import_module("pipeline.01_data_ingestion.ingest").data_ingestion
data_preprocessor = importlib.import_module("pipeline.02_preprocessing.clean").data_preprocessor
trend_analyzer = importlib.import_module("pipeline.03_trend_analysis.trend").trend_analyzer
breakout_detector = importlib.import_module("pipeline.04_breakout_detect.breakout").breakout_detector
sentiment_analyzer = importlib.import_module("pipeline.05_sentiment_analysis.sentiment").sentiment_analyzer
ml_agent = importlib.import_module("pipeline.06_ml_confirmation.model").ml_agent
trailing_sl_engine = importlib.import_module("pipeline.10_monitoring.trailing_sl").trailing_sl_engine
risk_manager = importlib.import_module("pipeline.07_risk_management.risk").risk_manager
validator = importlib.import_module("pipeline.08_pretrade_validation.validator").validator
execution_engine = importlib.import_module("pipeline.09_execution_engine.executor").execution_engine
exit_manager = importlib.import_module("pipeline.11_exit_management.exit").exit_manager
trade_auditor = importlib.import_module("pipeline.12_post_trade_audit.audit").trade_auditor

logger = get_logger()

class SentinelXBot:
    def __init__(self):
        self.symbols = self._load_symbols()
        self.is_running = False

    def _load_symbols(self):
        try:
            with open(BASE_DIR / 'config' / 'symbols.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load symbols: {e}")
            return {"equities": [], "futures_options": []}

    def start(self):
        self.is_running = True
        logger.info("Starting Sentinel X Bot in Paper Trading Mode...")
        
        # We don't train random mock data anymore, we let the user train real data later.
        if not settings.API_KEY or settings.API_KEY == 'YOUR_ANGEL_ONE_API_KEY':
            logger.warning("Angel One credentials missing. Running in dry-run mocked data mode.")
        else:
            connected = angel_api.connect()
            if not connected:
                logger.error("Failed to connect to Angel One. Exiting.")
                return

        try:
            self.main_loop()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.exception(f"Fatal error in main loop: {e}")
            self.stop()

    def stop(self):
        self.is_running = False
        logger.info("Stopping Sentinel X Bot. Flattening positions logic goes here.")
        if angel_api.smart_api:
            angel_api.logout()

    def process_symbol(self, symbol, token="dummy_token"):
        """
        Executes the 12-stage pipeline for a single symbol.
        """
        logger.info(f"Processing symbol: {symbol}")
        
        # Stage 01: Ingestion
        df = data_ingestion.fetch_historical_data(symbol, token, days_back=1)
        if df is None or df.empty:
            logger.debug(f"Skipping {symbol} due to no data.")
            return

        # Stage 02: Preprocessing
        df = data_preprocessor.preprocess(df)
        if df is None or df.empty:
            return
            
        current_price = df.iloc[-1]['close']
        
        # --- Stage 10: Monitoring Active Trades ---
        # If we have an active trade, check trailing stop loss
        if symbol in trailing_sl_engine.active_trades:
            sl_result = trailing_sl_engine.update(symbol, current_price)
            if sl_result["triggered"]:
                logger.warning(f"Stop loss triggered for {symbol}. PnL: {sl_result['pnl']}")
                # Fire Phase 11 & 12: Exit & Audit
                direction_held = trailing_sl_engine.active_trades[symbol]["direction"]
                qty = trailing_sl_engine.active_trades[symbol]["quantity"]
                exit_manager.execute_exit(symbol, token, direction_held, qty, sl_result["exit_price"], sl_result["pnl"], "T-SL Triggered")
                validator.log_trade_exit(symbol)
                trailing_sl_engine.remove_trade(symbol)
            return # Skip new signals while we have an active trade

        # --- Stages 03 & 04: Strategy Signals ---
        df = trend_analyzer.analyze(df)
        df = breakout_detector.detect(df)
        
        latest = df.iloc[-1]
        trend_sig = latest.get('trend_signal', 0)
        breakout_sig = latest.get('breakout_signal', 0)
        
        if trend_sig == 0 and breakout_sig == 0:
            logger.debug(f"No signal for {symbol}.")
            return
            
        direction = "BUY" if (trend_sig > 0 or breakout_sig > 0) else "SELL"
        logger.info(f"Signal detected for {symbol}: {direction}")

        # Stage 05: Sentiment
        sentiment_score = sentiment_analyzer.get_sentiment(symbol)
        
        # Stage 06: ML Confirmation (Strict 90% confidence)
        features_dict = {
            "rsi": latest.get('rsi', 50),
            "macd": latest.get('macd', 0),
            "ema50": latest.get('ema50', current_price),
            "ema200": latest.get('ema200', current_price),
            "volume": latest.get('volume', 0),
            "atr": latest.get('atr', 0)
        }
        
        ml_result = ml_agent.confirm_trade(features_dict, trend_sig, breakout_sig, sentiment_score)
        
        if not ml_result['confirmed']:
            logger.info(f"Trade rejected by ML Agent. Confidence: {ml_result.get('ml_probability', 0)*100:.2f}%")
            return
            
        logger.info(f"Trade CONFIRMED by ML Agent! Breakdowns:", extra=ml_result.get('breakdown', {}))

        # Stage 07: Risk Management
        risk_result = risk_manager.check_risk_limits(current_price)
        if not risk_result["approved"]:
            return
            
        quantity = risk_result["quantity"]
        
        # Stage 08: Pre-Trade Validation
        if not validator.validate(symbol, direction):
            return

        # Stage 09: Execution Engine
        exec_result = execution_engine.execute_order(symbol, token, direction, quantity, price=current_price)
        
        if not exec_result["status"]:
            return
            
        logger.info(f"Successfully executed {direction} order for {symbol} at {current_price}")
            
        # Register to Trailing Stop-Loss Engine
        trailing_sl_engine.register_trade(symbol, direction, current_price, quantity=quantity)

    def trigger_global_kill_switch(self):
        """
        Emergency routine flattening all open trades when system/API goes offline.
        """
        logger.critical("GLOBAL KILL SWITCH ACTIVATED. System Error/API disconnected.")
        open_symbols = list(trailing_sl_engine.active_trades.keys())
        for symbol in open_symbols:
            trade = trailing_sl_engine.active_trades[symbol]
            logger.warning(f"Emergency Flattening: {symbol}")
            # We mock the current price as the SL exit for flattening logic sake
            exit_manager.execute_exit(symbol, "dummy_token", trade["direction"], trade["quantity"], trade["stop_loss"], 0.0, "KILL SWITCH")
            validator.log_trade_exit(symbol)
            
        trailing_sl_engine.active_trades.clear()
        import sys
        sys.exit(1)

    def main_loop(self):
        """
        Continuous run loop polling 1-min candles.
        """
        logger.info("Starting new polling cycle...")
        error_count = 0
        
        while self.is_running:
            try:
                start_time = time.time()
                
                for symbol in self.symbols.get('equities', []):
                    self.process_symbol(symbol)
                    
                elapsed = time.time() - start_time
                sleep_time = max(10, 60 - elapsed)
                time.sleep(sleep_time)
                # Reset error counter on successful loops
                error_count = 0
                
            except Exception as e:
                error_count += 1
                logger.error(f"Fatal unhandled exception in main loop: {e}")
                if error_count >= 3:
                    self.trigger_global_kill_switch()
                time.sleep(10)

if __name__ == "__main__":
    bot = SentinelXBot()
    bot.start()
