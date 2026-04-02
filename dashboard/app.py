from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import asyncio
from typing import Dict, Any

app = FastAPI(title="Sentinel X Dashboard APIs")

# Mount static files to serve the Antigravity UI
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Generate a default index.html if it doesn't exist
index_path = os.path.join(static_dir, "index.html")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(index_path)

@app.get("/api/status")
async def get_status():
    return {
        "status": "active",
        "uptime": "2h 15m",
        "active_trades": 2,
        "daily_pnl": "+2.4%",
        "ml_agent_confidence": "94.2%",
        "available_funds": "₹ 1,45,230.50",
        "portfolio_value": "₹ 5,12,400.00"
    }

@app.get("/api/signals")
async def get_signals():
    return {
        "signals": [
            {
                "symbol": "RELIANCE-EQ", 
                "direction": "BUY", 
                "confidence": 0.96,
                "details": {
                    "entry_price": "₹ 2,430.50",
                    "trailing_sl": "₹ 2,406.20",
                    "strategy": "Volatility Breakout",
                    "adx_score": 38.5,
                    "sentiment": "+0.45"
                }
            },
            {
                "symbol": "INFY-EQ", 
                "direction": "SELL", 
                "confidence": 0.91,
                "details": {
                    "entry_price": "₹ 1,450.00",
                    "trailing_sl": "₹ 1,464.50",
                    "strategy": "EMA Trend Reversal",
                    "adx_score": 27.2,
                    "sentiment": "-0.32"
                }
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
