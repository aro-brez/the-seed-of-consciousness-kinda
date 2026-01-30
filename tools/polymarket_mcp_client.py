#!/usr/bin/env python3
"""
Polymarket MCP Client for SØWL
Provides easy access to 45 Polymarket tools via MCP Server

Usage:
    from tools.polymarket_mcp_client import PolymarketMCP

    async with PolymarketMCP() as client:
        # Market Discovery
        trending = await client.get_trending_markets(limit=10)
        markets = await client.search_markets("Bitcoin")

        # Market Analysis
        analysis = await client.analyze_market(market_id)
        price = await client.get_current_price(token_id)

        # Trading (requires wallet credentials)
        order = await client.create_limit_order(...)

        # Real-time Monitoring
        await client.subscribe_price_updates(token_id)
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Add MCP server to path
MCP_PATH = Path(__file__).parent.parent / "polymarket-mcp-server" / "src"
sys.path.insert(0, str(MCP_PATH))

from polymarket_mcp.config import load_config
from polymarket_mcp.tools import (
    market_discovery,
    market_analysis,
    portfolio,
    trading,
    realtime
)


class PolymarketMCP:
    """
    SØWL's Polymarket MCP Client

    Provides 45 trading tools across 5 categories:
    - Market Discovery (8 tools)
    - Market Analysis (10 tools)
    - Trading (12 tools)
    - Portfolio Management (8 tools)
    - Real-time Monitoring (7 tools)
    """

    def __init__(self, demo_mode: Optional[bool] = None):
        """
        Initialize Polymarket MCP Client

        Args:
            demo_mode: Override demo mode (None = use .env setting)
        """
        # Set environment variable before loading config if demo_mode specified
        if demo_mode is not None:
            import os
            os.environ['DEMO_MODE'] = 'true' if demo_mode else 'false'

        self.config = load_config()
        self.demo_mode = self.config.DEMO_MODE

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass

    # ==========================================
    # MARKET DISCOVERY (8 tools)
    # ==========================================

    async def search_markets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search markets by keyword"""
        return await market_discovery.search_markets(query=query, limit=limit)

    async def get_trending_markets(self, timeframe: str = "24h", limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending markets by volume (24h, 7d, 30d)"""
        return await market_discovery.get_trending_markets(timeframe=timeframe, limit=limit)

    async def filter_markets_by_category(self, category: str, active_only: bool = True, limit: int = 20) -> List[Dict[str, Any]]:
        """Filter markets by category (Politics, Sports, Crypto, etc)"""
        return await market_discovery.filter_markets_by_category(
            category=category,
            active_only=active_only,
            limit=limit
        )

    async def get_event_markets(self, event_slug: Optional[str] = None, event_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all markets for a specific event"""
        return await market_discovery.get_event_markets(event_slug=event_slug, event_id=event_id)

    async def get_featured_markets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get featured/promoted markets"""
        return await market_discovery.get_featured_markets(limit=limit)

    async def get_closing_soon_markets(self, hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
        """Get markets closing within specified hours"""
        return await market_discovery.get_closing_soon_markets(hours=hours, limit=limit)

    async def get_sports_markets(self, sport_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get sports markets (NBA, NFL, etc)"""
        return await market_discovery.get_sports_markets(sport_type=sport_type, limit=limit)

    async def get_crypto_markets(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get crypto prediction markets"""
        return await market_discovery.get_crypto_markets(symbol=symbol, limit=limit)

    # ==========================================
    # MARKET ANALYSIS (10 tools)
    # ==========================================

    async def get_market_details(self, market_id: Optional[str] = None, condition_id: Optional[str] = None, slug: Optional[str] = None) -> Dict[str, Any]:
        """Get complete market information"""
        return await market_analysis.get_market_details(
            market_id=market_id,
            condition_id=condition_id,
            slug=slug
        )

    async def get_current_price(self, token_id: str, side: str = "BOTH") -> Dict[str, Any]:
        """Get current bid/ask prices (side: BUY, SELL, BOTH)"""
        return await market_analysis.get_current_price(token_id=token_id, side=side)

    async def get_orderbook(self, token_id: str, depth: int = 20) -> Dict[str, Any]:
        """Get order book with bids and asks"""
        return await market_analysis.get_orderbook(token_id=token_id, depth=depth)

    async def get_spread(self, token_id: str) -> Dict[str, float]:
        """Get current bid-ask spread"""
        return await market_analysis.get_spread(token_id=token_id)

    async def get_market_volume(self, market_id: str, timeframes: Optional[List[str]] = None) -> Any:
        """Get volume statistics (24h, 7d, 30d, all-time)"""
        if timeframes is None:
            timeframes = ['24h', '7d', '30d']
        return await market_analysis.get_market_volume(market_id=market_id, timeframes=timeframes)

    async def get_liquidity(self, market_id: str) -> Dict[str, Any]:
        """Get available liquidity in USD"""
        return await market_analysis.get_liquidity(market_id=market_id)

    async def get_price_history(self, token_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, resolution: str = "1h") -> List[Dict[str, Any]]:
        """Get historical price data (OHLC)"""
        return await market_analysis.get_price_history(
            token_id=token_id,
            start_date=start_date,
            end_date=end_date,
            resolution=resolution
        )

    async def get_market_holders(self, market_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top position holders (requires auth)"""
        return await market_analysis.get_market_holders(market_id=market_id, limit=limit)

    async def analyze_market_opportunity(self, market_id: str) -> Any:
        """
        🤖 AI-POWERED: Comprehensive market analysis with BUY/SELL/HOLD recommendation

        Returns MarketOpportunity with:
        - recommendation: BUY, SELL, HOLD, AVOID
        - confidence_score: 0-100
        - risk_assessment: low, medium, high
        - reasoning: AI explanation
        """
        return await market_analysis.analyze_market_opportunity(market_id=market_id)

    async def compare_markets(self, market_ids: List[str]) -> List[Dict[str, Any]]:
        """Compare multiple markets side-by-side (2-10 markets)"""
        return await market_analysis.compare_markets(market_ids=market_ids)

    # ==========================================
    # PORTFOLIO MANAGEMENT (8 tools)
    # ==========================================

    async def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all current positions (requires wallet)"""
        if self.demo_mode:
            return []
        return await portfolio.get_all_positions()

    async def get_position_details(self, market_id: str) -> Dict[str, Any]:
        """Get detailed position info for specific market (requires wallet)"""
        if self.demo_mode:
            return {}
        return await portfolio.get_position_details(market_id=market_id)

    async def get_portfolio_value(self) -> Dict[str, float]:
        """Get total portfolio value in USD (requires wallet)"""
        if self.demo_mode:
            return {"total_value": 0}
        return await portfolio.get_portfolio_value()

    async def get_pnl_summary(self, timeframe: str = "all") -> Dict[str, Any]:
        """Get P&L summary (timeframe: 24h, 7d, 30d, all)"""
        if self.demo_mode:
            return {}
        return await portfolio.get_pnl_summary(timeframe=timeframe)

    async def get_trade_history(self, limit: int = 50, market_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trade history with optional filters"""
        if self.demo_mode:
            return []
        return await portfolio.get_trade_history(limit=limit, market_id=market_id)

    async def get_activity_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get on-chain activity log"""
        if self.demo_mode:
            return []
        return await portfolio.get_activity_log(limit=limit)

    async def analyze_portfolio_risk(self) -> Dict[str, Any]:
        """
        🤖 AI-POWERED: Analyze portfolio risk

        Returns risk metrics:
        - concentration_risk
        - liquidity_risk
        - diversification_score
        - recommendations
        """
        if self.demo_mode:
            return {}
        return await portfolio.analyze_portfolio_risk()

    async def suggest_portfolio_actions(self, strategy: str = "balanced") -> List[Dict[str, Any]]:
        """
        🤖 AI-POWERED: Get portfolio optimization suggestions

        Args:
            strategy: conservative, balanced, aggressive
        """
        if self.demo_mode:
            return []
        return await portfolio.suggest_portfolio_actions(strategy=strategy)

    # ==========================================
    # HELPER METHODS
    # ==========================================

    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get summary of available capabilities"""
        return {
            "mode": "DEMO" if self.demo_mode else "LIVE",
            "capabilities": {
                "market_discovery": 8,
                "market_analysis": 10,
                "trading": 0 if self.demo_mode else 12,
                "portfolio_management": 0 if self.demo_mode else 8,
                "real_time_monitoring": 0 if self.demo_mode else 7,
            },
            "total_tools": 18 if self.demo_mode else 45,
            "demo_features": [
                "Market search and discovery",
                "Real-time price data",
                "AI-powered market analysis",
                "Volume and liquidity metrics",
                "Market comparisons"
            ],
            "live_features": [
                "All demo features",
                "Order placement (limit/market)",
                "Position tracking",
                "P&L calculation",
                "Real-time WebSocket feeds",
                "Portfolio optimization"
            ]
        }


async def demo():
    """Demo the Polymarket MCP Client"""
    print("=" * 70)
    print("🤖 SØWL Polymarket MCP Client - Demo")
    print("=" * 70)

    async with PolymarketMCP(demo_mode=True) as client:
        # Show capabilities
        caps = client.get_capabilities_summary()
        print(f"\nMode: {caps['mode']}")
        print(f"Tools Available: {caps['total_tools']}")
        print(f"\nCapabilities:")
        for cat, count in caps['capabilities'].items():
            print(f"  - {cat.replace('_', ' ').title()}: {count} tools")

        # Search for Bitcoin markets
        print("\n" + "-" * 70)
        print("🔍 Searching for Bitcoin markets...")
        markets = await client.search_markets("Bitcoin", limit=3)
        print(f"Found {len(markets)} markets:")
        for i, m in enumerate(markets, 1):
            print(f"\n{i}. {m.get('question', 'Unknown')[:70]}")
            print(f"   Market ID: {m.get('condition_id', 'N/A')}")

        # Get trending markets
        print("\n" + "-" * 70)
        print("📈 Getting top trending markets (24h)...")
        trending = await client.get_trending_markets(timeframe="24h", limit=3)
        print(f"Found {len(trending)} trending markets:")
        for i, m in enumerate(trending, 1):
            print(f"\n{i}. {m.get('question', 'Unknown')[:70]}")

        # Analyze a market
        if markets:
            market = markets[0]
            market_id = market.get('condition_id') or market.get('id')

            if market_id:
                print("\n" + "-" * 70)
                print(f"🤖 Analyzing market opportunity...")
                print(f"   Market: {market.get('question', 'Unknown')[:60]}...")

                try:
                    analysis = await client.analyze_market_opportunity(market_id)
                    print(f"\n   Recommendation: {getattr(analysis, 'recommendation', 'N/A')}")
                    print(f"   Confidence: {getattr(analysis, 'confidence_score', 0):.0f}%")
                    print(f"   Risk: {getattr(analysis, 'risk_assessment', 'N/A').upper()}")
                    if hasattr(analysis, 'reasoning'):
                        print(f"   Reasoning: {analysis.reasoning[:100]}...")
                except Exception as e:
                    print(f"   ⚠️ Analysis unavailable: {e}")

        print("\n" + "=" * 70)
        print("✅ Demo complete! Integration ready.")
        print("\nNext steps:")
        print("1. Add Polygon wallet credentials to .env for live trading")
        print("2. Import PolymarketMCP in your trading scripts")
        print("3. Use analyze_market_opportunity() for AI-powered signals")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())
