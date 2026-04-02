import random
from core.logger import get_logger

logger = get_logger()

class SentimentAnalyzer:
    def __init__(self):
        pass

    def get_sentiment(self, symbol: str) -> float:
        """
        Mock sentiment analysis returning a score between -1.0 (very negative) and 1.0 (very positive).
        In phase 2, this will be connected to news APIs and LLMs.
        """
        try:
            # For now, return a neutral/slightly randomized score
            score = round(random.uniform(-0.5, 0.5), 2)
            logger.debug(f"Sentiment for {symbol}: {score}")
            return score
        except Exception as e:
            logger.error(f"Failed to fetch sentiment for {symbol}: {e}")
            return 0.0

sentiment_analyzer = SentimentAnalyzer()
