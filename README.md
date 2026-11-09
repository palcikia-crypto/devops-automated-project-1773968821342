#  Polymarket Crypto Lab

##  Automated Prediction Market Trading Laboratory for Crypto Markets

**Polymarket Crypto Lab** is a comprehensive, automated trading laboratory that continuously scans, analyzes, and identifies profitable trading opportunities (edges) in Polymarket's crypto prediction markets.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104%2B-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/react-18.2%2B-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

##  Features

###  Core Capabilities

- ** Automated Market Scanning**: Continuously scans Polymarket for crypto markets (tag_id=21)
- ** Signal Generation**: 10+ trading strategies to identify profitable opportunities
- ** Paper Trading**: Virtual trading with simulated balance (no real money)
- ** Real Trading**: Optional real trading with wallet integration
- ** Real-time Updates**: WebSocket integration for live data
- ** Beautiful Dashboard**: React-based UI with charts and analytics

###  10 Trading Strategies

| Strategy | Description | Edge Detection |
|----------|-------------|----------------|
| **Undervalued** | Finds undervalued/overvalued outcomes | Price vs Fair Value |
| **Arbitrage** | Finds mutually exclusive markets with arbitrage | Cross-market pricing |
| **Trending** | Identifies markets with strong momentum | Price trends |
| **Correlation** | Finds correlated markets and divergences | Statistical correlation |
| **Liquidity** | Identifies low-liquidity opportunities | Liquidity analysis |
| **Sentiment** | Analyzes Twitter/News sentiment | NLP analysis |
| **Seasonality** | Finds seasonal patterns | Historical patterns |
| **Mean Reversion** | Identifies overbought/oversold conditions | Statistical deviation |
| **Breakout** | Detects price breakouts | Technical analysis |
| **Volume Spike** | Finds unusual volume activity | Volume analysis |

###  Web Dashboard

- Real-time market data visualization
- Signal monitoring and management
- Portfolio tracking and analytics
- Performance charts and statistics
- Trade history and position management
- Configurable notifications

###  Notifications

- **Telegram**: Bot notifications for signals and trades
- **Discord**: Webhook notifications
- **Desktop**: Browser notifications
- **In-app**: Real-time notification center

###  Risk Management

- Stop-loss and take-profit orders
- Position sizing based on portfolio risk
- Maximum position size limits
- Maximum portfolio risk limits
- Diversification controls

---

##  Quick Start

###  Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional)
- Redis (optional, for caching)

###  Installation

####  Option 1: Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/polymarket-crypto-lab.git
   cd polymarket-crypto-lab
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Install frontend dependencies:**
   ```bash
   cd src/frontend
   npm install
   cd ../..
   ```

6. **Run the backend:**
   ```bash
   python -m uvicorn src.backend.app:app --reload
   ```

7. **Run the frontend (in another terminal):**
   ```bash
   cd src/frontend
   npm start
   ```

8. **Access the dashboard:**
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs

####  Option 2: Docker Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/polymarket-crypto-lab.git
   cd polymarket-crypto-lab
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the dashboard:**
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs

---

##  Configuration

###  Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Polymarket API
POLYMARKET_GAMMA_API_URL=https://gamma-api.polymarket.com
POLYMARKET_CLOB_API_URL=https://clob.polymarket.com
POLYMARKET_DATA_API_URL=https://data-api.polymarket.com
POLYMARKET_WS_URL=wss://ws-subscriptions-clob.polymarket.com

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/polymarket.db

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# Paper Trading
PAPER_TRADING_ENABLED=true
PAPER_TRADING_INITIAL_BALANCE=10000

# Real Trading
ENABLE_REAL_TRADING=false
WALLET_ADDRESS=
WALLET_PRIVATE_KEY=

# Trading Settings
AUTO_TRADE=false
MAX_POSITION_SIZE=1000
MAX_PORTFOLIO_RISK=0.05
STOP_LOSS_PCT=0.10
TAKE_PROFIT_PCT=0.20

# Scheduler
MARKET_SCAN_INTERVAL=300
SIGNAL_GENERATION_INTERVAL=900
POSITION_UPDATE_INTERVAL=60
PORTFOLIO_SNAPSHOT_INTERVAL=3600

# Notifications
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DISCORD_WEBHOOK_URL=

# External APIs (for sentiment analysis)
COINGECKO_API_KEY=
TWITTER_BEARER_TOKEN=
NEWSAPI_KEY=

# Web Server
WEB_HOST=0.0.0.0
WEB_PORT=8000
FRONTEND_URL=http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOGS_DIR=logs
```

###  Crypto Tag IDs

- **Crypto**: `21` (default)
- **Bitcoin**: `21`
- **Ethereum**: `21`
- **Finance**: `120`

---

##  API Endpoints

###  Markets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/markets` | List all markets |
| GET | `/api/markets/{slug}` | Get market by slug |
| GET | `/api/markets/crypto` | Get crypto markets |
| GET | `/api/markets/bitcoin` | Get Bitcoin markets |
| GET | `/api/markets/ethereum` | Get Ethereum markets |
| GET | `/api/markets/active` | Get active markets |
| GET | `/api/markets/stats` | Market statistics |
| POST | `/api/markets/scan` | Trigger market scan |

###  Signals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/signals` | List all signals |
| GET | `/api/signals/{id}` | Get signal by ID |
| GET | `/api/signals/active` | Get active signals |
| GET | `/api/signals/by-strategy/{strategy}` | Signals by strategy |
| GET | `/api/signals/top` | Top signals by edge |
| GET | `/api/signals/stats` | Signal statistics |
| POST | `/api/signals/generate` | Generate signals |
| POST | `/api/signals/close/{id}` | Close a signal |

###  Paper Trading

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/paper/balance` | Get paper balance |
| GET | `/api/paper/positions` | Get open positions |
| GET | `/api/paper/positions/{id}` | Get position by ID |
| GET | `/api/paper/trades` | Get trade history |
| GET | `/api/paper/trades/{id}` | Get trade by ID |
| POST | `/api/paper/trade` | Execute a paper trade |
| POST | `/api/paper/trade/signal/{signal_id}` | Trade from signal |
| POST | `/api/paper/close-position/{id}` | Close a position |
| GET | `/api/paper/portfolio` | Get portfolio |
| GET | `/api/paper/portfolio/snapshot` | Portfolio snapshot |
| POST | `/api/paper/reset` | Reset paper trading |
| GET | `/api/paper/performance` | Performance metrics |
| GET | `/api/paper/stats` | Paper trading stats |

###  Real Trading

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trading/orderbook/{market_id}` | Get order book |
| GET | `/api/trading/prices/{market_id}` | Get price history |
| GET | `/api/trading/midprice/{market_id}` | Get midprice |
| GET | `/api/trading/spread/{market_id}` | Get bid-ask spread |
| GET | `/api/trading/trades` | Get trade history |
| POST | `/api/trading/trade` | Execute a real trade |
| GET | `/api/trading/balance` | Get real balance |
| GET | `/api/trading/positions` | Get real positions |

###  Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/overview` | Dashboard overview |
| GET | `/api/dashboard/realtime` | Real-time data |
| GET | `/api/dashboard/charts/markets` | Markets chart data |
| GET | `/api/dashboard/charts/signals` | Signals chart data |
| GET | `/api/dashboard/charts/portfolio` | Portfolio chart data |
| GET | `/api/dashboard/notifications` | Get notifications |
| GET | `/api/dashboard/settings` | Get dashboard settings |
| POST | `/api/dashboard/settings` | Update dashboard settings |

###  WebSocket

- **Endpoint**: `ws://localhost:8000/ws/realtime`
- **Events**: `market_update`, `signal_update`, `portfolio_update`, `notification`

---

##  Project Structure

```
polymarket-crypto-lab/
├── src/
│   ├── backend/
│   │   ├── app.py                      # FastAPI application
│   │   ├── api/                       # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── markets.py
│   │   │   ├── signals.py
│   │   │   ├── trading.py
│   │   │   ├── paper_trading.py
│   │   │   └── dashboard.py
│   │   ├── automation/                # Automated trading
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py
│   │   │   ├── trader.py
│   │   │   ├── paper_trading.py
│   │   │   └── notifier.py
│   │   ├── data/                      # Data layer
│   │   │   ├── __init__.py
│   │   │   ├── polymarket.py          # Polymarket API client
│   │   │   ├── database.py            # Database operations
│   │   │   └── cache.py               # Redis cache
│   │   ├── edge_finder/               # Signal generation
│   │   │   ├── __init__.py
│   │   │   ├── scanner.py             # Market scanner
│   │   │   ├── signals.py             # Signal generator
│   │   │   └── strategies/            # Trading strategies
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── undervalued.py
│   │   │       ├── arbitrage.py
│   │   │       ├── trending.py
│   │   │       ├── correlation.py
│   │   │       ├── liquidity.py
│   │   │       ├── sentiment.py
│   │   │       ├── seasonality.py
│   │   │       ├── mean_reversion.py
│   │   │       ├── breakout.py
│   │   │       └── volume_spike.py
│   │   ├── models/                    # Data models
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   └── utils/                     # Utilities
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── helpers.py
│   └── frontend/
│       ├── public/                    # Static files
│       │   └── index.html
│       └── src/                       # React source
│           ├── index.tsx
│           ├── index.css
│           ├── App.tsx
│           ├── pages/                 # Page components
│           │   ├── Dashboard.tsx
│           │   ├── Markets.tsx
│           │   ├── Signals.tsx
│           │   ├── Trading.tsx
│           │   ├── Portfolio.tsx
│           │   ├── Settings.tsx
│           │   └── Notifications.tsx
│           └── reportWebVitals.ts
├── config/
│   └── __init__.py                    # Configuration
├── docker-compose.yml                 # Docker Compose
├── Dockerfile                         # Backend Dockerfile
├── Dockerfile.frontend                # Frontend Dockerfile
├── nginx.conf                         # Nginx configuration
├── nginx.frontend.conf                # Frontend Nginx config
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Dev dependencies
├── .env.example                       # Environment template
└── README.md                          # This file
```

---

##  Usage

###  Start the Scheduler

```python
from src.backend.automation.scheduler import scheduler

# Start all automated tasks
async def main():
    await scheduler.start()
    # Keep running
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

###  Manual Market Scan

```python
from src.backend.edge_finder.scanner import MarketScanner

scanner = MarketScanner()
markets = await scanner.scan_markets(tag_id=21)
```

###  Generate Signals

```python
from src.backend.edge_finder.signals import SignalGenerator

generator = SignalGenerator()
signals = await generator.generate_signals()
```

###  Execute Paper Trade

```python
from src.backend.automation.paper_trading import PaperTradingEngine

engine = PaperTradingEngine()
trade = await engine.execute_trade(
    market_id="market_id",
    outcome="Yes",
    side="buy",
    amount=100,
    price=0.5
)
```

---

##  Strategies

###  Undervalued Strategy

Identifies outcomes that are trading below their fair value based on:
- Historical price analysis
- Fundamental factors
- Market sentiment

###  Arbitrage Strategy

Finds arbitrage opportunities between:
- Mutually exclusive markets
- Different outcome combinations
- Cross-market pricing discrepancies

###  Trending Strategy

Detects strong trends using:
- Moving averages
- Price momentum
- Volume trends

###  Correlation Strategy

Identifies correlated markets and divergences:
- Statistical correlation analysis
- Cointegration tests
- Divergence detection

###  Liquidity Strategy

Finds low-liquidity opportunities:
- Liquidity depth analysis
- Order book analysis
- Volume patterns

###  Sentiment Strategy

Analyzes sentiment from:
- Twitter
- News articles
- Social media
- Requires external API keys

###  Seasonality Strategy

Identifies seasonal patterns:
- Monthly patterns
- Quarterly patterns
- Bitcoin halving cycles
- Historical seasonality

###  Mean Reversion Strategy

Detects overbought/oversold conditions:
- Bollinger Bands
- Z-score analysis
- Statistical deviation

###  Breakout Strategy

Identifies price breakouts:
- Support/resistance levels
- Volume confirmation
- Price action patterns

###  Volume Spike Strategy

Detects unusual volume activity:
- Volume spikes
- Volume trends
- Volume ratios

---

##  Technology Stack

###  Backend

- **Python 3.10+**: Core language
- **FastAPI**: REST API framework
- **Uvicorn**: ASGI server
- **SQLAlchemy**: ORM
- **aiosqlite/asyncpg**: Async database
- **Redis**: Caching
- **aiohttp**: Async HTTP client
- **Pydantic**: Data validation
- **Pydantic Settings**: Configuration

###  Frontend

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Chart.js**: Charts
- **Socket.io-client**: WebSocket
- **Axios**: HTTP client

###  Data & ML

- **Pandas**: Data analysis
- **NumPy**: Numerical computing
- **scikit-learn**: Machine learning
- **Transformers**: NLP
- **TA**: Technical analysis

###  Infrastructure

- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy
- **SQLite**: Default database
- **PostgreSQL**: Production database

---

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Disclaimer

**Important**: This software is for educational and research purposes only. Trading in prediction markets involves risk. You should understand the risks and be experienced in trading before using this software with real funds.

- **Paper trading** uses virtual funds and is safe for learning
- **Real trading** requires wallet configuration and involves real financial risk
- The developers are not responsible for any losses incurred
- Always test strategies thoroughly before using real money
- Past performance is not indicative of future results

---

##  Support

- **Documentation**: https://github.com/yourusername/polymarket-crypto-lab
- **Issues**: https://github.com/yourusername/polymarket-crypto-lab/issues
- **Discussions**: https://github.com/yourusername/polymarket-crypto-lab/discussions

---

##  Roadmap

- [x] Core backend infrastructure
- [x] Polymarket API integration
- [x] 10 trading strategies
- [x] Paper trading engine
- [x] Signal generation
- [x] Web dashboard
- [x] Real-time updates
- [x] Notifications
- [x] Docker support
- [ ] Backtesting framework
- [ ] Strategy optimization
- [ ] Machine learning models
- [ ] Mobile app
- [ ] Advanced analytics

---

##  Acknowledgments

- [Polymarket](https://polymarket.com): Prediction market platform
- [FastAPI](https://fastapi.tiangolo.com): Web framework
- [React](https://reactjs.org): UI framework
- [Tailwind CSS](https://tailwindcss.com): Styling
- [Chart.js](https://www.chartjs.org): Charts

---

<p align="center">
  Made with  by the Polymarket Crypto Lab Team
</p>
