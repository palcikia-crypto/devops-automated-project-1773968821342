"""
Polymarket Crypto Lab - FastAPI Application
Main application file with all API endpoints
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Optional
import logging
import asyncio
from datetime import datetime
import uvicorn

from config import settings
from .api import markets, signals, trading, dashboard, paper_trading
from .models import schemas
from .utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Polymarket Crypto Lab",
        description="Automated prediction market trading laboratory for crypto markets",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.FRONTEND_URL,
            "http://localhost:3000",
            "http://localhost:8000",
            "*"  # For development
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(markets.router, prefix="/api/markets", tags=["Markets"])
    app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])
    app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])
    app.include_router(paper_trading.router, prefix="/api/paper", tags=["Paper Trading"])
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
    
    # WebSocket endpoint for real-time updates
    @app.websocket("/ws/realtime")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time market updates"""
        await websocket.accept()
        try:
            while True:
                # Send market updates every 30 seconds
                data = {
                    "type": "market_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": await markets.get_latest_markets(limit=10)
                }
                await websocket.send_json(data)
                await asyncio.sleep(30)
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
    
    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0"
        }
    
    # Root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Root endpoint with basic info"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Polymarket Crypto Lab</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #2b5bff; }
                a { color: #2b5bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .container { max-width: 800px; margin: 0 auto; }
                .button { display: inline-block; padding: 10px 20px; background: #2b5bff; color: white; border-radius: 5px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Polymarket Crypto Lab</h1>
                <p>Automated prediction market trading laboratory for crypto markets.</p>
                <p>
                    <a href="/api/docs" class="button">📖 API Documentation</a>
                </p>
                <p>
                    <a href="/dashboard" class="button">📊 Dashboard</a>
                </p>
                <p>
                    <strong>Features:</strong>
                    <ul>
                        <li>✅ Real-time market data from Polymarket</li>
                        <li>✅ Automated signal generation (10+ strategies)</li>
                        <li>✅ Paper trading with virtual balance</li>
                        <li>✅ Beautiful dashboard with charts</li>
                        <li>✅ WebSocket for real-time updates</li>
                        <li>✅ Telegram/Discord notifications</li>
                    </ul>
                </p>
            </div>
        </body>
        </html>
        """
    
    # Serve static files (frontend build)
    app.mount("/static", StaticFiles(directory="src/frontend/public"), name="static")
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.backend.app:app",
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
