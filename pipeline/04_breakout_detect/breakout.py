import pandas as pd
from ta.volatility import BollingerBands
from core.logger import get_logger

logger = get_logger()

class BreakoutDetector:
    def __init__(self, num_std=2):
        self.num_std = num_std

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adaptive Breakout Detection
        - Lookback window changes from 20 to 50 based on Volatility (ATR).
        """
        if df is None or df.empty or 'atr' not in df.columns:
            logger.warning("Breakout Detector needs 'atr' feature from preprocessing.")
            return df
            
        try:
            # We already have atr scaling logic in df if trend analyzer ran, but let's recalculate safely
            if 'atr_ma' not in df.columns:
                df['atr_ma'] = df['atr'].rolling(window=20).mean()
                df['is_high_volatility'] = df['atr'] > df['atr_ma']
                
            df['breakout_signal'] = 0
            
            # High Volatility -> Use 50 candle lookback (prevent getting wicked out)
            # Low Volatility -> Use 20 candle lookback (tighter entry)
            
            # Fast Rolling (20)
            roll_high_20 = df['high'].rolling(window=20).max()
            roll_low_20 = df['low'].rolling(window=20).min()
            
            # Slow Rolling (50)
            roll_high_50 = df['high'].rolling(window=50).max()
            roll_low_50 = df['low'].rolling(window=50).min()
            
            df['rolling_high'] = roll_high_20
            df['rolling_low'] = roll_low_20
            
            df.loc[df['is_high_volatility'], 'rolling_high'] = roll_high_50
            df.loc[df['is_high_volatility'], 'rolling_low'] = roll_low_50
            
            # Buy Breakout
            buy_condition = (df['close'] >= df['rolling_high'].shift(1))
            
            # Sell Breakout
            sell_condition = (df['close'] <= df['rolling_low'].shift(1))
            
            df.loc[buy_condition, 'breakout_signal'] = 1
            df.loc[sell_condition, 'breakout_signal'] = -1
            
            logger.info("Adaptive Breakout detection completed", extra={"signals_generated": len(df[df['breakout_signal'] != 0])})
            return df
        except Exception as e:
            logger.exception("Error during adaptive breakout detection: " + str(e))
            return df

breakout_detector = BreakoutDetector()
