"""
Sentiment Strategy for Polymarket Crypto Lab
Analyzes sentiment from news and social media to generate signals
"""
from typing import List, Dict, Optional, Any, Tuple, Tuple
import logging
import aiohttp
import json

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class SentimentStrategy(BaseStrategy):
    """
    Strategy that analyzes sentiment from news and social media
    
    Uses:
    1. Twitter API for social media sentiment
    2. News API for news sentiment
    3. NLP models for sentiment analysis
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.SENTIMENT
    
    @property
    def name(self) -> str:
        return "Sentiment Analysis"
    
    @property
    def description(self) -> str:
        return "Analyzes sentiment from news and social media to predict market movements"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        twitter_bearer_token: Optional[str] = None,
        newsapi_key: Optional[str] = None,
        min_sentiment: float = 0.6,  # Minimum sentiment score
        max_sentiment: float = 0.9,  # Maximum sentiment score
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.twitter_bearer_token = twitter_bearer_token or settings.TWITTER_BEARER_TOKEN
        self.newsapi_key = newsapi_key or settings.NEWSAPI_KEY
        self.min_sentiment = min_sentiment
        self.max_sentiment = max_sentiment
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate sentiment signals
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        if not self.twitter_bearer_token and not self.newsapi_key:
            logger.warning("⚠️ No API keys for sentiment analysis. Skipping.")
            return signals
        
        # Filter markets
        filtered_markets = self._filter_markets(markets)
        
        for market in filtered_markets:
            try:
                # Analyze sentiment for this market
                sentiment_score, sentiment_text = await self._analyze_sentiment(market)
                
                if sentiment_score is None:
                    continue
                
                # Generate signal based on sentiment
                market_signals = await self._generate_sentiment_signals(market, sentiment_score, sentiment_text)
                signals.extend(market_signals)
            except Exception as e:
                logger.error(f"❌ Error analyzing sentiment for {market.get('title')}: {e}")
        
        return signals
    
    async def _analyze_sentiment(
        self,
        market: Dict[str, Any]
    ) -> Tuple[Optional[float], str]:
        """
        Analyze sentiment for a market
        
        Args:
            market: Market dictionary
            
        Returns:
            Tuple of (sentiment_score, sentiment_text)
        """
        title = market.get("title", "")
        slug = market.get("slug", "")
        
        sentiment_score = 0.5  # Neutral by default
        sentiment_text = ""
        
        # Extract keywords for sentiment analysis
        keywords = self._extract_keywords(title)
        
        # Get sentiment from Twitter
        if self.twitter_bearer_token:
            twitter_sentiment, twitter_text = await self._get_twitter_sentiment(keywords)
            if twitter_sentiment is not None:
                sentiment_score = twitter_sentiment
                sentiment_text += f"Twitter: {twitter_text}\n"
        
        # Get sentiment from News API
        if self.newsapi_key:
            news_sentiment, news_text = await self._get_news_sentiment(keywords)
            if news_sentiment is not None:
                # Average with Twitter sentiment
                if sentiment_score != 0.5:
                    sentiment_score = (sentiment_score + news_sentiment) / 2
                else:
                    sentiment_score = news_sentiment
                sentiment_text += f"News: {news_text}\n"
        
        return sentiment_score, sentiment_text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from market title
        
        Args:
            text: Market title
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction
        keywords = []
        
        # Common crypto keywords
        crypto_keywords = [
            "bitcoin", "btc", "ethereum", "eth", "solana", "sol",
            "cardano", "ada", "xrp", "ripple", "dogecoin", "doge",
            "litecoin", "ltc", "binance", "bnb", "polkadot", "dot",
            "avalanche", "avax", "chainlink", "link", "uniswap", "uni",
            "price", "up", "down", "rise", "fall", "increase", "decrease",
            "halving", "etf", "sec", "approved", "rejected"
        ]
        
        text_lower = text.lower()
        for keyword in crypto_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # If no keywords found, use the whole title
        if not keywords:
            keywords = [text.lower()]
        
        return keywords
    
    async def _get_twitter_sentiment(
        self,
        keywords: List[str]
    ) -> Tuple[Optional[float], str]:
        """
        Get sentiment from Twitter
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            Tuple of (sentiment_score, sentiment_text)
        """
        if not self.twitter_bearer_token or not self.session:
            return None, ""
        
        try:
            # Build query
            query = " OR ".join(keywords)
            url = f"https://api.twitter.com/2/tweets/search/recent"
            
            headers = {
                "Authorization": f"Bearer {self.twitter_bearer_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "query": query,
                "max_results": 50,
                "tweet_fields": "text,created_at"
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tweets = data.get("data", [])
                    
                    if not tweets:
                        return None, "No tweets found"
                    
                    # Analyze sentiment of tweets
                    positive = 0
                    negative = 0
                    neutral = 0
                    
                    for tweet in tweets:
                        text = tweet.get("text", "").lower()
                        sentiment = self._analyze_tweet_sentiment(text)
                        
                        if sentiment > 0.1:
                            positive += 1
                        elif sentiment < -0.1:
                            negative += 1
                        else:
                            neutral += 1
                    
                    total = positive + negative + neutral
                    if total == 0:
                        return None, "No sentiment data"
                    
                    # Calculate sentiment score (0-1)
                    sentiment_score = (positive - negative) / total
                    sentiment_score = (sentiment_score + 1) / 2  # Convert to 0-1 range
                    
                    sentiment_text = f"{positive} positive, {negative} negative, {neutral} neutral tweets"
                    
                    return sentiment_score, sentiment_text
                else:
                    logger.error(f"Twitter API error: {response.status}")
                    return None, f"API error: {response.status}"
        
        except Exception as e:
            logger.error(f"Error getting Twitter sentiment: {e}")
            return None, f"Error: {str(e)}"
    
    def _analyze_tweet_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of a tweet text
        
        Args:
            text: Tweet text
            
        Returns:
            Sentiment score (-1 to 1)
        """
        # Simple sentiment analysis based on keywords
        positive_words = [
            "up", "rise", "rising", "increase", "increasing", "bullish",
            "positive", "good", "great", "excellent", "amazing", "awesome",
            "approved", "accept", "yes", "buy", "long", "pump"
        ]
        
        negative_words = [
            "down", "fall", "falling", "decrease", "decreasing", "bearish",
            "negative", "bad", "terrible", "horrible", "awful", "suck",
            "rejected", "deny", "no", "sell", "short", "dump"
        ]
        
        score = 0
        text_lower = text.lower()
        
        for word in positive_words:
            if word in text_lower:
                score += 1
        
        for word in negative_words:
            if word in text_lower:
                score -= 1
        
        return score
    
    async def _get_news_sentiment(
        self,
        keywords: List[str]
    ) -> Tuple[Optional[float], str]:
        """
        Get sentiment from News API
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            Tuple of (sentiment_score, sentiment_text)
        """
        if not self.newsapi_key or not self.session:
            return None, ""
        
        try:
            # Build query
            query = " OR ".join(keywords)
            url = "https://newsapi.org/v2/everything"
            
            params = {
                "q": query,
                "apiKey": self.newsapi_key,
                "pageSize": 20,
                "sortBy": "publishedAt",
                "language": "en"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get("articles", [])
                    
                    if not articles:
                        return None, "No articles found"
                    
                    # Analyze sentiment of articles
                    positive = 0
                    negative = 0
                    neutral = 0
                    
                    for article in articles:
                        title = article.get("title", "").lower()
                        description = article.get("description", "").lower()
                        text = f"{title} {description}"
                        sentiment = self._analyze_article_sentiment(text)
                        
                        if sentiment > 0.1:
                            positive += 1
                        elif sentiment < -0.1:
                            negative += 1
                        else:
                            neutral += 1
                    
                    total = positive + negative + neutral
                    if total == 0:
                        return None, "No sentiment data"
                    
                    # Calculate sentiment score (0-1)
                    sentiment_score = (positive - negative) / total
                    sentiment_score = (sentiment_score + 1) / 2  # Convert to 0-1 range
                    
                    sentiment_text = f"{positive} positive, {negative} negative, {neutral} neutral articles"
                    
                    return sentiment_score, sentiment_text
                else:
                    logger.error(f"News API error: {response.status}")
                    return None, f"API error: {response.status}"
        
        except Exception as e:
            logger.error(f"Error getting news sentiment: {e}")
            return None, f"Error: {str(e)}"
    
    def _analyze_article_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of an article text
        
        Args:
            text: Article text
            
        Returns:
            Sentiment score (-1 to 1)
        """
        # Use the same keyword-based approach as for tweets
        return self._analyze_tweet_sentiment(text)
    
    async def _generate_sentiment_signals(
        self,
        market: Dict[str, Any],
        sentiment_score: float,
        sentiment_text: str
    ) -> List[Signal]:
        """
        Generate signals based on sentiment score
        
        Args:
            market: Market dictionary
            sentiment_score: Sentiment score (0-1)
            sentiment_text: Sentiment text description
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        current_price = market.get("outcomePrices", [0.5])[0]
        outcomes = market.get("outcomes", [])
        
        # If sentiment is very positive, look for "Yes" opportunities
        if sentiment_score >= self.max_sentiment:
            for i, outcome in enumerate(outcomes):
                if outcome == "Yes":
                    signal = self._create_signal(
                        market=market,
                        outcome=outcome,
                        outcome_index=i,
                        entry_price=current_price,
                        current_price=current_price,
                        sentiment_score=sentiment_score,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market.get("liquidity", 1000) * 0.1
                        ),
                        target_price=min(0.99, current_price * 1.1),  # 10% target
                        stop_loss=max(0.01, current_price * 0.95)  # 5% stop loss
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"😊 Positive sentiment: {market['title']} | "
                        f"Score: {sentiment_score:.2%} | Outcome: {outcome}"
                    )
        
        # If sentiment is very negative, look for "No" opportunities
        elif sentiment_score <= (1 - self.max_sentiment):
            for i, outcome in enumerate(outcomes):
                if outcome == "No":
                    signal = self._create_signal(
                        market=market,
                        outcome=outcome,
                        outcome_index=i,
                        entry_price=current_price,
                        current_price=current_price,
                        sentiment_score=sentiment_score,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market.get("liquidity", 1000) * 0.1
                        ),
                        target_price=min(0.99, current_price * 1.1),  # 10% target
                        stop_loss=max(0.01, current_price * 0.95)  # 5% stop loss
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"😠 Negative sentiment: {market['title']} | "
                        f"Score: {sentiment_score:.2%} | Outcome: {outcome}"
                    )
        
        # If sentiment is neutral, no signal
        
        return signals
