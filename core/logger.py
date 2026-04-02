import sys
import json
from loguru import logger
from datetime import datetime
from config.settings import LOG_DIR

# Remove default logger
logger.remove()

# Formatter for JSON structured logs
def json_formatter(record):
    log_record = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "extra": record["extra"]
    }
    return json.dumps(log_record) + "\n"

# Add standard console output for readability during dev
logger.add(
    sys.stdout, 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add JSON structured log file for production/audit
log_file = LOG_DIR / f"sentinel_x_{datetime.now().strftime('%Y%m%d')}.jsonl"
logger.add(
    log_file,
    format="{message}", # message is already serialized by json_formatter? No, loguru's serialize=True is better.
    serialize=True,     # Using loguru's built-in JSON serialization instead of custom formatter
    level="DEBUG",
    rotation="00:00",   # New log file every day
    retention="30 days",# Keep logs for 30 days
    compression="zip"   # Compress old logs
)

def get_logger():
    return logger
