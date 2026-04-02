import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from config.settings import CONFIDENCE_THRESHOLD, BASE_DIR
from core.logger import get_logger

logger = get_logger()

# Features that match our preprocessing
ML_FEATURES = ["rsi", "macd", "ema50", "ema200", "volume", "atr"]

class MLConfirmationAgent:
    def __init__(self):
        self.model_path = BASE_DIR / 'pipeline' / '06_ml_confirmation' / 'random_forest.pkl'
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self._load_model()

    def _load_model(self):
        """Loads the pre-trained model if it exists."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                logger.info("Successfully loaded pre-trained Random Forest model.")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")

    def save_model(self):
        """Saves the trained model to disk."""
        if self.is_trained:
            try:
                joblib.dump(self.model, self.model_path)
                logger.info(f"Model saved to {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to save model: {e}")

    def train(self, df: pd.DataFrame, min_samples_required: int = 5000):
        """
        Trains the RandomForestClassifier on historical OHLCV data.
        Enforces a minimum sample size to avoid weak training bias.
        """
        logger.info("Training ML model on historical data...")
        if df is None or df.empty:
            logger.error("No data provided for training.")
            return

        # Ensure all required features are present
        missing_features = [f for f in ML_FEATURES if f not in df.columns]
        if missing_features:
            logger.error(f"Missing features for ML training: {missing_features}")
            return
            
        if "target" not in df.columns:
            logger.error("Target variable missing from training data.")
            return

        # Drop NaNs just before training to be safe
        train_df = df.dropna(subset=ML_FEATURES + ["target"])
        
        sample_count = len(train_df)
        if sample_count < min_samples_required:
            logger.warning(f"ML Halt: Only {sample_count} samples found. {min_samples_required} required.")
            return
        
        X_train = train_df[ML_FEATURES]
        y_train = train_df["target"]
        
        try:
            self.model.fit(X_train, y_train)
            self.is_trained = True
            logger.info(f"Real ML model trained successfully on {sample_count} samples.")
            self.save_model()
        except Exception as e:
            logger.exception(f"Error during ML training: {e}")

    def confirm_trade(self, features_dict: dict, trend_signal: float, breakout_signal: float, sentiment_score: float) -> dict:
        """
        Confirms trading signal probability using real ML features and outputs broken down metrics.
        """
        if not self.is_trained:
            logger.warning("ML Model is not trained. Trade confirmation cannot proceed.")
            return {"confirmed": False, "breakdown": {}}
            
        try:
            X_input = np.array([[features_dict.get(f, 0) for f in ML_FEATURES]])
            probabilities = self.model.predict_proba(X_input)[0]
            success_prob = probabilities[1]
            
            is_confirmed = (success_prob >= CONFIDENCE_THRESHOLD) or (success_prob <= (1 - CONFIDENCE_THRESHOLD))
            
            # Simulated transformation of signals into 0-1 metrics for explainability dashboard 
            trend_val = 0.85 if trend_signal != 0 else 0.40
            break_val = 0.88 if breakout_signal != 0 else 0.45
            sent_val = abs(sentiment_score) if sentiment_score != 0 else 0.50
            
            result = {
                "ml_probability": round(success_prob, 4),
                "threshold": CONFIDENCE_THRESHOLD,
                "confirmed": is_confirmed,
                "breakdown": {
                    "trend": trend_val,
                    "breakout": break_val,
                    "sentiment": round(sent_val, 2),
                    "ml": round(success_prob, 4)
                }
            }
            
            logger.info("ML Confirmation Result Breakdown", extra=result)
            return result
            
        except Exception as e:
            logger.exception("Error in ML confirmation prediction: " + str(e))
            return {"confirmed": False, "breakdown": {}}

ml_agent = MLConfirmationAgent()
