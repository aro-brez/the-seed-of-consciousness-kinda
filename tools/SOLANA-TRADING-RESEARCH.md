# Solana Trading Bot Research - 8OWLS Project

**Date:** February 2, 2026
**Wallet:** `Fg3MYxfcJ8tgQEyhVS9c6EJAc9Kyg5jjm8tY93hJeaBf`
**Starting Capital:** ~$15 SOL + $200 USDC (to bridge from Polygon)

---

## 1. Bridge USDC from Polygon to Solana

### Recommended: deBridge

**Why deBridge:**
- 1.96s settlement time
- Lowest spread (4 bps)
- $8B+ settled with zero security incidents
- Flat 0.5 POL fee (~$0.25)

**Steps:**
1. Go to https://app.debridge.finance/
2. Connect Polygon wallet
3. Select USDC as source token, Solana as destination
4. Enter Solana wallet: `Fg3MYxfcJ8tgQEyhVS9c6EJAc9Kyg5jjm8tY93hJeaBf`
5. Approve and execute - funds arrive in seconds

**Alternative Bridges:**
- [Symbiosis](https://symbiosis.finance/bridge-polygon-to-sol) - Cheapest fees, user-friendly
- [Allbridge Core](https://docs.allbridge.io/guides/bridging-guides/how-to-transfer-usdt) - Solana-native, optimized for stablecoins
- [Wormhole](https://wormhole.com/) - Most widely used, 30+ chains

---

## 2. Best APIs for Solana Trading

### Primary: Jupiter Aggregator

Jupiter is Solana's leading swap aggregator - routes through all major DEXs to find best price.

**API Endpoints:**
```
Quote:    https://quote-api.jup.ag/v6/quote
Swap:     https://quote-api.jup.ag/v6/swap
```

**Python SDK:**
```bash
pip install jupiter-python-sdk solana solders
```

**Example Swap:**
```python
from jupiter_python_sdk.jupiter import Jupiter
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

async def swap_sol_to_usdc(private_key: str, amount_lamports: int):
    """Swap SOL to USDC via Jupiter"""
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    keypair = Keypair.from_base58_string(private_key)

    jupiter = Jupiter(
        async_client=client,
        keypair=keypair,
        quote_api_url="https://quote-api.jup.ag/v6"
    )

    # SOL -> USDC
    SOL_MINT = "So11111111111111111111111111111111111111112"
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    transaction = await jupiter.swap(
        input_mint=SOL_MINT,
        output_mint=USDC_MINT,
        amount=amount_lamports,
        slippage_bps=50  # 0.5% slippage
    )

    return transaction
```

### Secondary DEXs

| DEX | Best For | API Docs |
|-----|----------|----------|
| **Raydium** | AMM pools, new launches | [raydium.io/docs](https://raydium.io/docs/) |
| **Orca** | Concentrated liquidity | [orca.so](https://www.orca.so/) |
| **Meteora** | Dynamic pools | [meteora.ag](https://meteora.ag/) |
| **Pump.fun** | Memecoin launches | [pump.fun](https://pump.fun/) |

---

## 3. Monitoring pump.fun Token Performance

### Real-Time Token Detection

**Option 1: Shyft Yellowstone gRPC (Recommended)**
```python
# Detect new pump.fun tokens via gRPC stream
# Program ID: 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P

from solana.rpc.websocket_api import connect

PUMP_FUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

async def monitor_pump_fun():
    async with connect("wss://api.mainnet-beta.solana.com") as websocket:
        await websocket.logs_subscribe(
            filter_={"mentions": [PUMP_FUN_PROGRAM]}
        )
        async for msg in websocket:
            # Parse new token creation
            if "CreateToken" in str(msg):
                token_mint = extract_mint_address(msg)
                print(f"New pump.fun token: {token_mint}")
```

**Option 2: Bitquery API**
- Real-time trading data via CoreCast gRPC
- Monitor buying/selling pressure
- Detect whale activity
- [Bitquery Pump.fun Docs](https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/pump-fun-to-pump-swap/)

**Option 3: PumpPortal API**
- Third-party API for pump.fun interaction
- Simple HTTPS requests
- Real-time bonding curve data

### Key pump.fun Metrics to Track

```python
@dataclass
class PumpFunToken:
    mint_address: str
    bonding_curve_address: str
    created_at: datetime

    # Performance metrics
    market_cap: float
    liquidity: float
    holder_count: int
    volume_24h: float

    # Risk indicators
    dev_holdings_pct: float  # Red flag if >10%
    top_10_holdings_pct: float
    has_social_media: bool

    def risk_score(self) -> int:
        """0-10, lower is safer"""
        score = 5
        if self.dev_holdings_pct > 10: score += 3
        if self.top_10_holdings_pct > 50: score += 2
        if self.holder_count < 100: score += 2
        if not self.has_social_media: score += 1
        if self.liquidity < 10000: score += 2
        return min(10, score)
```

---

## 4. Bot Architecture for Buy/Sell Signals

### Adapting Polymarket Patterns

The existing Polymarket infrastructure provides excellent patterns to reuse:

| Polymarket Component | Solana Equivalent |
|---------------------|-------------------|
| `autonomous_trader.py` | Base daemon structure |
| `kelly_criterion.py` | Position sizing (use directly) |
| `risk_manager.py` | Drawdown limits (use directly) |
| `binance_websocket_stream.py` | Solana price feeds via Jupiter/Birdeye |

### Proposed Architecture

```
+------------------+     +-------------------+     +------------------+
|  Signal Sources  | --> |  Signal Engine    | --> |  Execution Layer |
+------------------+     +-------------------+     +------------------+
| - pump.fun feed  |     | - Momentum calc   |     | - Jupiter swap   |
| - Jupiter prices |     | - Volume analysis |     | - Priority fees  |
| - Birdeye API    |     | - Risk filtering  |     | - Jito bundles   |
| - Social signals |     | - Kelly sizing    |     | - TX confirmation|
+------------------+     +-------------------+     +------------------+
                                  |
                                  v
                         +------------------+
                         |  Self-Learning   |
                         +------------------+
                         | - Trade outcomes |
                         | - Adjust params  |
                         | - Pattern memory |
                         +------------------+
```

### Core Bot Template

```python
#!/usr/bin/env python3
"""
SOLANA MEMECOIN TRADING BOT
Adapted from Polymarket autonomous trader patterns
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
import httpx

# Reuse existing components
from kelly_criterion import KellyCalculator
from risk_manager import RiskManager

# Solana-specific imports
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

# Configuration
INITIAL_CAPITAL = 200  # Starting USDC
MAX_POSITION_SIZE_PCT = 0.10  # 10% max per trade
MIN_POSITION_SIZE = 5  # $5 minimum
SLIPPAGE_BPS = 100  # 1% slippage for memecoins

# Solana RPC (use paid RPC for production)
RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"


@dataclass
class TradingSignal:
    """Trading signal for a memecoin"""
    token_mint: str
    token_symbol: str
    action: str  # 'BUY' or 'SELL'
    confidence: float  # 0-1
    reason: str

    # Market data
    price: float
    volume_24h: float
    market_cap: float
    liquidity: float

    # Timing
    timestamp: datetime
    urgency: str  # 'HIGH', 'MEDIUM', 'LOW'


class SolanaMemecoinTrader:
    """Autonomous Solana memecoin trading bot"""

    # Token addresses
    SOL_MINT = "So11111111111111111111111111111111111111112"
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    def __init__(
        self,
        private_key: str,
        initial_capital: float = INITIAL_CAPITAL,
        rpc_endpoint: str = RPC_ENDPOINT
    ):
        self.keypair = Keypair.from_base58_string(private_key)
        self.client = AsyncClient(rpc_endpoint)

        # Risk management (reuse existing)
        self.risk_manager = RiskManager(
            initial_bankroll=initial_capital,
            max_daily_drawdown=0.10,  # 10% daily max loss
            max_position_size=MAX_POSITION_SIZE_PCT,
            reserve_fraction=0.20
        )

        self.kelly = KellyCalculator(
            bankroll=initial_capital,
            max_kelly_fraction=0.25  # Quarter Kelly for safety
        )

        # State tracking
        self.positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []

    async def get_token_price(self, token_mint: str) -> Optional[float]:
        """Get token price via Jupiter"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://price.jup.ag/v4/price",
                    params={"ids": token_mint}
                )
                data = response.json()
                return data.get('data', {}).get(token_mint, {}).get('price')
        except Exception as e:
            print(f"Price fetch error: {e}")
            return None

    async def analyze_opportunity(self, token_mint: str) -> Optional[TradingSignal]:
        """Analyze a token for trading opportunity"""

        # Get price data
        price = await self.get_token_price(token_mint)
        if not price:
            return None

        # TODO: Add volume, holder analysis, social signals
        # For now, return basic signal structure

        return TradingSignal(
            token_mint=token_mint,
            token_symbol="UNKNOWN",
            action="BUY",
            confidence=0.5,
            reason="Initial analysis",
            price=price,
            volume_24h=0,
            market_cap=0,
            liquidity=0,
            timestamp=datetime.now(),
            urgency="LOW"
        )

    async def execute_swap(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = SLIPPAGE_BPS
    ) -> Dict:
        """Execute a swap via Jupiter"""
        try:
            async with httpx.AsyncClient() as client:
                # Get quote
                quote_response = await client.get(
                    "https://quote-api.jup.ag/v6/quote",
                    params={
                        "inputMint": input_mint,
                        "outputMint": output_mint,
                        "amount": str(amount),
                        "slippageBps": slippage_bps
                    }
                )
                quote = quote_response.json()

                # Get swap transaction
                swap_response = await client.post(
                    "https://quote-api.jup.ag/v6/swap",
                    json={
                        "quoteResponse": quote,
                        "userPublicKey": str(self.keypair.pubkey()),
                        "wrapAndUnwrapSol": True,
                        "dynamicComputeUnitLimit": True,
                        "prioritizationFeeLamports": "auto"
                    }
                )
                swap_data = swap_response.json()

                # Sign and send transaction
                # (Full implementation requires solders transaction handling)

                return {
                    "status": "SUCCESS",
                    "quote": quote,
                    "swap_data": swap_data
                }

        except Exception as e:
            return {"status": "FAILED", "error": str(e)}

    def calculate_position_size(
        self,
        signal: TradingSignal
    ) -> float:
        """Calculate position size using Kelly and risk limits"""

        # Check if trading allowed
        status = self.risk_manager.check_trading_allowed()
        if not status['allowed']:
            return 0

        # Kelly sizing
        result = self.kelly.calculate_position_size(
            win_probability=signal.confidence,
            win_amount=50,  # Target 50% return on memecoins
            loss_amount=100,  # Assume can lose 100%
            strategy_name="memecoin"
        )

        position_size = result['position_size']

        # Apply limits
        position_size = max(MIN_POSITION_SIZE, position_size)
        max_size = self.risk_manager.current_bankroll * MAX_POSITION_SIZE_PCT
        position_size = min(position_size, max_size)

        return position_size


# Entry point
async def main():
    """Main entry point"""
    import os

    private_key = os.environ.get('SOLANA_PRIVATE_KEY')
    if not private_key:
        print("Error: Set SOLANA_PRIVATE_KEY environment variable")
        return

    trader = SolanaMemecoinTrader(private_key=private_key)

    # Example: Check a token
    # token_mint = "YOUR_TOKEN_MINT_HERE"
    # signal = await trader.analyze_opportunity(token_mint)
    # print(signal)


if __name__ == '__main__':
    asyncio.run(main())
```

---

## 5. Risk Management for Memecoin Trading

### Adapted from Polymarket Strategies

| Risk Parameter | Polymarket | Memecoin (Adjusted) |
|----------------|------------|---------------------|
| Max Daily Drawdown | 5% | 10% (higher volatility) |
| Max Position Size | 5% | 10% (smaller capital) |
| Kelly Fraction | 0.5 (half) | 0.25 (quarter) |
| Reserve Fraction | 30% | 20% |
| Min Position | $5 | $5 |
| Max Consecutive Losses | 3 | 5 (expect more variance) |

### Memecoin-Specific Risk Rules

```python
MEMECOIN_RISK_RULES = {
    # Token filtering
    "min_liquidity_usd": 10_000,
    "min_holders": 100,
    "max_dev_holdings_pct": 10,
    "max_top10_holdings_pct": 50,
    "require_social_media": True,

    # Position management
    "take_profit_pct": 50,  # Sell 50% at 2x
    "stop_loss_pct": -30,   # Cut losses at -30%
    "trailing_stop_pct": 20, # Trail winners by 20%

    # Timing
    "max_hold_hours": 24,   # Exit within 24h
    "avoid_first_5_min": True,  # Skip initial pump

    # Portfolio limits
    "max_open_positions": 5,
    "max_correlated_exposure": 0.30  # 30% max in similar tokens
}
```

### Red Flags - Do NOT Trade

1. **Dev holdings > 10%** - High rug risk
2. **No verified social media** - Likely scam
3. **Liquidity < $10k** - Too illiquid
4. **Holders < 100** - No community
5. **Age < 5 minutes** - Initial volatility too high
6. **Contract not verified** - Hidden functionality risk

---

## 6. Infrastructure Requirements

### RPC Providers (Latency Critical)

| Provider | Cost | Latency | Notes |
|----------|------|---------|-------|
| **Helius** | $50/mo | ~50ms | Best for trading |
| **QuickNode** | $49/mo | ~60ms | Good reliability |
| **Triton** | $39/mo | ~70ms | Budget option |
| **Public** | Free | 200ms+ | Not for trading |

**Recommendation:** Start with Helius $50/mo plan for sub-100ms latency.

### Priority Fees + Jito Bundles

For memecoin trading, **speed matters**. Use:

1. **Priority Fees**: Dynamic based on network congestion
   ```python
   prioritizationFeeLamports = "auto"  # Jupiter handles this
   ```

2. **Jito Bundles**: For guaranteed inclusion
   - Bundles execute atomically
   - Prevents MEV attacks
   - Extra ~0.001 SOL per bundle

---

## 7. Recommended Implementation Path

### Phase 1: Setup (Day 1)

1. [ ] Bridge $200 USDC from Polygon via deBridge
2. [ ] Set up Helius RPC account
3. [ ] Install Python dependencies:
   ```bash
   pip install solana solders jupiter-python-sdk httpx
   ```
4. [ ] Securely store private key (NOT in code)

### Phase 2: Price Monitoring (Day 1-2)

1. [ ] Implement Jupiter price feed
2. [ ] Set up pump.fun WebSocket monitoring
3. [ ] Create signal generation logic

### Phase 3: Paper Trading (Day 2-3)

1. [ ] Run bot in simulation mode
2. [ ] Track would-be trades
3. [ ] Validate risk management

### Phase 4: Live Trading (Day 3+)

1. [ ] Start with $20 (10% of capital)
2. [ ] Monitor closely for first 24h
3. [ ] Gradually increase if profitable

---

## 8. Key Resources

### Documentation
- [Jupiter API Docs](https://station.jup.ag/docs/apis/swap-api)
- [Solana Python SDK](https://github.com/michaelhly/solana-py)
- [Solders Toolkit](https://github.com/kevinheavey/solders)
- [Bitquery Pump.fun API](https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/pump-fun-to-pump-swap/)

### Example Bots (Reference Only)
- [SolanaTradingBot](https://github.com/axioris/SolanaTradingBot) - Multi-DEX support
- [Solana-trade-bot](https://github.com/YZYLAB/solana-trade-bot) - Raydium/Pumpfun examples
- [Jupiter Python SDK](https://github.com/0xTaoDev/jupiter-python-sdk)

### Trading Guides
- [QuickNode Jupiter Bot Guide](https://www.quicknode.com/guides/solana-development/3rd-party-integrations/jupiter-api-trading-bot)
- [Chainstack Pump.fun Bot](https://docs.chainstack.com/docs/solana-creating-a-pumpfun-bot)
- [Solana Trading Bot Guide 2026](https://rpcfast.com/blog/solana-trading-bot-guide)

---

## 9. Expected Returns & Costs

### Realistic Expectations

| Scenario | Monthly Return | Risk Level |
|----------|----------------|------------|
| Conservative | 10-20% | Low (quality tokens only) |
| Moderate | 30-50% | Medium (some speculation) |
| Aggressive | 50-100%+ | High (meme hunting) |

**Starting with $200:**
- Conservative: $20-40/mo
- Moderate: $60-100/mo
- Aggressive: $100-200/mo (or losses)

### Operating Costs

| Item | Monthly Cost |
|------|-------------|
| RPC (Helius) | $50 |
| Priority fees | ~$5-20 |
| Bridge fees | ~$1 (one-time) |
| **Total** | ~$55-70/mo |

**Break-even:** Need ~35% monthly return to cover costs with $200 capital.

---

## 10. Next Steps

1. **Immediate:** Bridge USDC via deBridge
2. **Today:** Set up development environment
3. **This week:** Build and test price monitoring
4. **Next week:** Paper trade, then go live with 10% capital

The existing Polymarket infrastructure provides 90% of what's needed - the main work is adapting the signal generation and execution layers for Solana DEXs.

---

*Research compiled from: [RPC Fast](https://rpcfast.com/blog/solana-trading-bot-guide), [QuickNode](https://www.quicknode.com/guides/solana-development/3rd-party-integrations/jupiter-api-trading-bot), [Chainstack](https://docs.chainstack.com/docs/solana-creating-a-pumpfun-bot), [Bitquery](https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/pump-fun-to-pump-swap/), [deBridge](https://app.debridge.finance/), [Jupiter](https://station.jup.ag/docs/apis/swap-api)*
