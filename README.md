# 🔮 Polymarket Crypto Lab v1.5

## Automated Prediction Market Trading Laboratory for Crypto Markets

**Polymarket Crypto Lab** is a comprehensive, automated trading laboratory that continuously scans, analyzes, and identifies profitable trading opportunities (edges) in Polymarket's crypto prediction markets.

## ✅ Features

- **10 Trading Strategies**: Undervalued, Arbitrage, Trending, Correlation, Liquidity, Sentiment, Seasonality, Mean Reversion, Breakout, Volume Spike
- **Paper Trading**: Virtual trading with simulated balance (no real money)
- **Real Trading**: Optional real trading with wallet integration
- **Beautiful Dashboard**: HTML dashboard with real-time data
- **Real-time Updates**: JavaScript-based live updates
- **Notifications**: Telegram, Discord, Desktop, In-app

## 🚀 Quick Start

### Development Setup

```bash
git clone https://github.com/palcikia-crypto/devops-automated-project-1773968821342.git
cd devops-automated-project-1773968821342

# Install dependencies
pip install -r requirements.txt

# Run backend
python -m uvicorn src.backend.app:app --reload
```

### Docker Setup

```bash
docker-compose up -d
```

## 🌐 Access

- **Backend API**: http://localhost:8000
- **Dashboard**: Open dashboard/index.html in browser

## 📊 Live Dashboard

**Working Dashboard:** [https://palcikia-crypto.github.io/devops-automated-project-1773968821342/](https://palcikia-crypto.github.io/devops-automated-project-1773968821342/)

To enable GitHub Pages:
1. Go to Settings → Pages
2. Select branch: `main`
3. Select folder: `/dashboard`
4. Save

## 🎯 Original Project

This is a copy of: [davletovaalmira11-creator/polymarket-lab](https://github.com/davletovaalmira11-creator/polymarket-lab)

## 📜 License

MIT License
