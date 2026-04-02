import pandas as pd
from ta.trend import EMAIndicator, ADXIndicator
from core.logger import get_logger

logger = get_logger()

class TrendAnalyzer:
    def __init__(self, adx_window=14):
        self.adx_window = adx_window

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adaptive Trend Analysis
        - EMA windows adapt based on historical Volatility (ATR).
        - ADX > 25 ensures we only take trades in trending environments.
        """
        if df is None or df.empty or 'atr' not in df.columns:
            logger.warning("Trend Analyzer needs 'atr' feature from preprocessing.")
            return df
            
        try:
            # Determine Volatility state: High Volatility = ATR > 20-period average ATR
            df['atr_ma'] = df['atr'].rolling(window=20).mean()
            df['is_high_volatility'] = df['atr'] > df['atr_ma']
            
            # We don't want to calculate rolling EMA dynamically per row in pandas cleanly,
            # so we calculate both sets and use np.where or loc to choose the signal.
            
            # Short windows
            ema20 = EMAIndicator(close=df['close'], window=20).ema_indicator()
            ema50 = EMAIndicator(close=df['close'], window=50).ema_indicator()
            
            # Long windows
            ema100 = EMAIndicator(close=df['close'], window=100).ema_indicator()
            ema200 = EMAIndicator(close=df['close'], window=200).ema_indicator()
            
            df['ema_short'] = 0.0
            df['ema_long'] = 0.0
            
            # If high volatility, use shorter windows (faster response)
            df.loc[df['is_high_volatility'], 'ema_short'] = ema20
            df.loc[df['is_high_volatility'], 'ema_long'] = ema100
            
            # If low volatility, use longer windows (avoid chop)
            df.loc[~df['is_high_volatility'], 'ema_short'] = ema50
            df.loc[~df['is_high_volatility'], 'ema_long'] = ema200
            
            # ADX filtering
            adx = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=self.adx_window)
            df['adx'] = adx.adx()
            
            # Generate Signals
            df['ema_crossover'] = 0
            df.loc[df['ema_short'] > df['ema_long'], 'ema_crossover'] = 1
            df.loc[df['ema_short'] < df['ema_long'], 'ema_crossover'] = -1
            
            # FINAL FILTER: ADX MUST be > 25
            df['trend_signal'] = 0
            df.loc[(df['ema_crossover'] == 1) & (df['adx'] > 25), 'trend_signal'] = 1
            df.loc[(df['ema_crossover'] == -1) & (df['adx'] > 25), 'trend_signal'] = -1
            
            logger.info("Adaptive Trend analysis completed", extra={"signals_generated": len(df[df['trend_signal'] != 0])})
            return df
        except Exception as e:
            logger.exception("Error during trend analysis: " + str(e))
            return df

trend_analyzer = TrendAnalyzer()
