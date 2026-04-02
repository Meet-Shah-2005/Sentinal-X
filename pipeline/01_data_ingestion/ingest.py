import pandas as pd
from datetime import datetime, timedelta
from core.angel_api import angel_api
from core.logger import get_logger
from config import settings

logger = get_logger()

class DataIngestion:
    def __init__(self):
        self.api = angel_api.smart_api
        self.interval = settings.CANDLE_INTERVAL

    def fetch_historical_data(self, symbol, token, exchange="NSE", days_back=5):
        """
        Fetch historical 1-minute candle data for a given symbol.
        """
        if not self.api:
            logger.error("Angel One API not initialized.")
            return None

        # To fetch 1-min candles, Angel One allows up to 30 days of data, 
        # but it's best to fetch fewer days per call and paginate if needed.
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        historic_param = {
            "exchange": exchange,
            "symboltoken": token,
            "interval": self.interval,
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M")
        }

        try:
            logger.info("Fetching historical data", extra={"symbol": symbol, "from": historic_param["fromdate"], "to": historic_param["todate"]})
            response = self.api.getCandleData(historic_param)
            
            if response['status'] and response['data']:
                columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                df = pd.DataFrame(response['data'], columns=columns)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # Convert appropriate columns to numeric
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                logger.info(f"Successfully fetched {len(df)} candles for {symbol}")
                return df
            else:
                logger.warning(f"No data returned for {symbol}: {response.get('message', '')}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.exception(f"Error fetching historical data for {symbol}: {e}")
            return None

data_ingestion = DataIngestion()
