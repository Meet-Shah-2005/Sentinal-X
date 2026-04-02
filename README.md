# Sentinel-X 🚀

**Sentinel-X** is a professional-grade, highly modular, quant-level algorithmic trading engine tailored for the Indian Equity and F&O markets. Built entirely in Python, it interfaces natively with the **Angel One SmartAPI**, leveraging Machine Learning guardrails, dynamic volatility-based strategies, and strict institutional-grade risk management.

## 🧠 Architecture Overview

Sentinel-X abandons monolithic "if/else" trading scripts in favor of a strictly enforced, independently testable **12-Stage Pipeline** architecture:

### Signal Generation Phase
1. **`01_data_ingestion`**: Polling real-time historical 1-minute tick/candle data.
2. **`02_preprocessing`**: Dynamic feature engineering (EMA, MACD, RSI, ATR).
3. **`03_trend_analysis`**: Measuring structural dominance using ATR-scaled EMAs.
4. **`04_breakout_detect`**: Confirming rapid momentum moves via rolling volatility bounds.

### Confirmation Phase
5. **`05_sentiment_analysis`**: External sentiment hooks overlay.
6. **`06_ml_confirmation`**: **Random Forest Classifier** assessing features natively. Evaluates a strict **`> 90% confidence threshold`** block before allowing trade propagation. Automatically halts if training data bias is detected (< 5,000 samples).

### Safety & Execution Phase
7. **`07_risk_management`**: Restricts position sizing (max 5%) and enforces absolute daily drawdown limits (2% DD cap).
8. **`08_pretrade_validation`**: 10-minute cooldown loops and strict duplicate-exposure rejections.
9. **`09_execution_engine`**: API Wrapper natively handling Order deployment with **0.2% Slippage Controls** and Ghost-Trade prevention cancellation loops. 

### Management & Audit Phase
10. **`10_monitoring`**: Trailing Stop-Loss (`T-SL`) engine dynamically scaling with tick-by-tick profits.
11. **`11_exit_management`**: Inverse coordination engine immediately flattening positions when limits hit.
12. **`12_post_trade_audit`**: Immediate immutable writes of `Entry`, `Exit`, `PnL`, and `Reason` into an SQLite Database for deep history UI generation.

## 🛡️ Critical Guardrails
- **The Global Kill Switch**: Catch-all mechanism safely sweeping `Trailing SL` engines and flattening your entire active portfolio instantly upon consecutive unhandled network exceptions or API drops.
- **Explainable AI Matrix**: `predict_proba()` doesn't just pass/fail. It decomposes the probability into `{trend, breakout, sentiment, ml}` for dashboard visualizations.

---

## 🏗️ Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Meet-Shah-2005/Sentinal-X.git
cd Sentinal-X
```

### 2. Environment Setup
Construct a dedicated python environment so Sentinel's dependencies don't overwrite your master Python path.
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. API Key Injection (.env)
Sentinel relies on heavily restricted configurations. Create a `.env` file at the exact root of your directory with your Angel One parameters:
```env
API_KEY=your_angel_one_api_key
CLIENT_ID=your_angel_one_client_id
PASSWORD=your_angel_one_pin_or_pass
TOTP_SECRET=your_auth_app_totp_seed
```
*(Note: `.env` is comprehensively blocked via `.gitignore`. Your keys will never leak into version history).*

## ⚡ Deployment
Once configured, simply launch the command orchestrator. It will begin polling 1-minute iterations and open the monitoring dashboard locally.

```bash
python main.py
```
> **Trading Safety**: Sentinel-X ships natively set to `MODE = "PAPER"` inside `config/settings.py`. Flip this entirely at your own risk when live parameters are verified.

---
*Built for absolute execution efficiency and fail-safe capital protection.*
