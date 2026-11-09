"""
Market API endpoints for Polymarket Crypto Lab
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..data.polymarket import PolymarketClient
from ..data.database import Database
from ..data.cache import Cache
from ..models.schemas import Market, MarketStatus, MarketType
from ..edge_finder.scanner import MarketScanner
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# Initialize clients
polymarket_client = PolymarketClient()
database = Database()
cache = Cache()


@router.get("/", response_model=List[Market])
async def get_markets(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of markets to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    status: Optional[MarketStatus] = Query(None, description="Filter by market status"),
    market_type: Optional[MarketType] = Query(None, description="Filter by market type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tag_id: Optional[int] = Query(21, description="Filter by tag ID (21 for crypto)"),
    use_cache: bool = Query(True, description="Use cached data if available")
) -> List[Market]:
    """
    Get a list of markets, optionally filtered.
    
    By default returns crypto markets (tag_id=21).
    """
    try:
        cache_key = f"markets:{tag_id}:{status}:{market_type}:{category}:{limit}:{offset}"
        
        if use_cache:
            cached_markets = await cache.get_markets(cache_key)
            if cached_markets:
                logger.info(f"Returning {len(cached_markets)} cached markets")
                return cached_markets
        
        # Fetch from Polymarket API
        markets = await polymarket_client.get_markets(
            tag_id=tag_id,
            limit=limit,
            offset=offset
        )
        
        # Filter by status
        if status:
            markets = [m for m in markets if m.get('status') == status.value]
        
        # Filter by market type
        if market_type:
            markets = [m for m in markets if m.get('market_type') == market_type.value]
        
        # Filter by category
        if category:
            markets = [m for m in markets if category.lower() in m.get('category', '').lower()]
        
        # Convert to Market schemas
        market_schemas = []
        for market_data in markets[:limit]:
            market_schema = Market(
                id=market_data.get('id'),
                title=market_data.get('title'),
                slug=market_data.get('slug'),
                question=market_data.get('question'),
                category=market_data.get('category', 'Unknown'),
                subcategory=market_data.get('subcategory'),
                condition_id=market_data.get('condition_id'),
                outcomes=market_data.get('outcomes', []),
                outcome_prices=market_data.get('outcome_prices', []),
                volume_24hr=market_data.get('volume_24hr', 0.0),
                volume_1wk=market_data.get('volume_1wk', 0.0),
                volume_1mo=market_data.get('volume_1mo', 0.0),
                liquidity=market_data.get('liquidity', 0.0),
                end_date=market_data.get('end_date'),
                start_date=market_data.get('start_date'),
                resolution_source=market_data.get('resolution_source'),
                market_type=market_data.get('market_type', MarketType.BINARY),
                status=market_data.get('status', MarketStatus.ACTIVE),
                clob_token_ids=market_data.get('clob_token_ids', []),
                image=market_data.get('image'),
                icon=market_data.get('icon'),
                fee=market_data.get('fee', 0.0)
            )
            market_schemas.append(market_schema)
        
        # Cache the results
        if use_cache:
            await cache.set_markets(cache_key, market_schemas)
        
        return market_schemas
    
    except Exception as e:
        logger.error(f"Error fetching markets: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching markets: {str(e)}")


@router.get("/{market_slug}", response_model=Market)
async def get_market_by_slug(market_slug: str) -> Market:
    """
    Get a specific market by its slug.
    """
    try:
        cache_key = f"market:{market_slug}"
        
        # Try cache first
        cached_market = await cache.get_market(cache_key)
        if cached_market:
            return cached_market
        
        # Fetch from API
        market_data = await polymarket_client.get_market_by_slug(market_slug)
        
        if not market_data:
            raise HTTPException(status_code=404, detail=f"Market with slug '{market_slug}' not found")
        
        market_schema = Market(
            id=market_data.get('id'),
            title=market_data.get('title'),
            slug=market_data.get('slug'),
            question=market_data.get('question'),
            category=market_data.get('category', 'Unknown'),
            subcategory=market_data.get('subcategory'),
            condition_id=market_data.get('condition_id'),
            outcomes=market_data.get('outcomes', []),
            outcome_prices=market_data.get('outcome_prices', []),
            volume_24hr=market_data.get('volume_24hr', 0.0),
            volume_1wk=market_data.get('volume_1wk', 0.0),
            volume_1mo=market_data.get('volume_1mo', 0.0),
            liquidity=market_data.get('liquidity', 0.0),
            end_date=market_data.get('end_date'),
            start_date=market_data.get('start_date'),
            resolution_source=market_data.get('resolution_source'),
            market_type=market_data.get('market_type', MarketType.BINARY),
            status=market_data.get('status', MarketStatus.ACTIVE),
            clob_token_ids=market_data.get('clob_token_ids', []),
            image=market_data.get('image'),
            icon=market_data.get('icon'),
            fee=market_data.get('fee', 0.0)
        )
        
        # Cache the result
        await cache.set_market(cache_key, market_schema)
        
        return market_schema
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market {market_slug}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching market: {str(e)}")


@router.get("/crypto", response_model=List[Market])
async def get_crypto_markets(
    limit: int = Query(100, ge=1, le=1000),
    use_cache: bool = Query(True)
) -> List[Market]:
    """
    Get all crypto markets (tag_id=21).
    """
    return await get_markets(
        limit=limit,
        tag_id=21,
        use_cache=use_cache
    )


@router.get("/bitcoin", response_model=List[Market])
async def get_bitcoin_markets(
    limit: int = Query(100, ge=1, le=1000),
    use_cache: bool = Query(True)
) -> List[Market]:
    """
    Get Bitcoin-related markets.
    """
    return await get_markets(
        limit=limit,
        category="Bitcoin",
        use_cache=use_cache
    )


@router.get("/ethereum", response_model=List[Market])
async def get_ethereum_markets(
    limit: int = Query(100, ge=1, le=1000),
    use_cache: bool = Query(True)
) -> List[Market]:
    """
    Get Ethereum-related markets.
    """
    return await get_markets(
        limit=limit,
        category="Ethereum",
        use_cache=use_cache
    )


@router.get("/active", response_model=List[Market])
async def get_active_markets(
    limit: int = Query(100, ge=1, le=1000),
    use_cache: bool = Query(True)
) -> List[Market]:
    """
    Get all active markets.
    """
    return await get_markets(
        limit=limit,
        status=MarketStatus.ACTIVE,
        use_cache=use_cache
    )


@router.get("/stats", response_model=Dict[str, Any])
async def get_market_stats() -> Dict[str, Any]:
    """
    Get market statistics.
    """
    try:
        markets = await get_markets(limit=1000, use_cache=True)
        
        total_markets = len(markets)
        active_markets = len([m for m in markets if m.status == MarketStatus.ACTIVE])
        closed_markets = len([m for m in markets if m.status == MarketStatus.CLOSED])
        resolved_markets = len([m for m in markets if m.status == MarketStatus.RESOLVED])
        
        total_volume = sum(m.volume_24hr for m in markets)
        total_liquidity = sum(m.liquidity for m in markets)
        
        # Get categories
        categories = {}
        for market in markets:
            cat = market.category
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        return {
            "total_markets": total_markets,
            "active_markets": active_markets,
            "closed_markets": closed_markets,
            "resolved_markets": resolved_markets,
            "total_volume_24hr": total_volume,
            "total_liquidity": total_liquidity,
            "categories": categories,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching market stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.post("/scan", response_model=Dict[str, Any])
async def scan_markets(
    tag_id: int = Query(21, description="Tag ID to scan"),
    force: bool = Query(False, description="Force rescan even if recently scanned")
) -> Dict[str, Any]:
    """
    Manually trigger a market scan.
    """
    try:
        scanner = MarketScanner()
        result = await scanner.scan_markets(tag_id=tag_id, force=force)
        
        return {
            "status": "success",
            "markets_scanned": result.get("markets_scanned", 0),
            "new_markets": result.get("new_markets", 0),
            "updated_markets": result.get("updated_markets", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error scanning markets: {e}")
        raise HTTPException(status_code=500, detail=f"Error scanning markets: {str(e)}")


async def get_latest_markets(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Helper function to get latest markets for WebSocket.
    """
    markets = await get_markets(limit=limit, use_cache=True)
    return [
        {
            "id": m.id,
            "title": m.title,
            "slug": m.slug,
            "category": m.category,
            "outcome_prices": m.outcome_prices,
            "volume_24hr": m.volume_24hr,
            "liquidity": m.liquidity,
            "status": m.status.value
        }
        for m in markets
    ]
