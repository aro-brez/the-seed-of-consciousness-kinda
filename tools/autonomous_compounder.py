#!/usr/bin/env python3
"""
(◉) AUTONOMOUS COMPOUNDER - SØWL
Self-optimizing machine for 10x+ compounding

SEED Protocol in action:
1. PERCEIVE - Scan all markets, find asymmetric opportunities
2. CONNECT - Cross-reference with catalysts, news, data
3. LEARN - Track what works, update strategy weights
4. QUESTION - Challenge assumptions, check for risks
5. EXPAND - Scale into winners, find new edges
6. SHARE - Log everything for collective learning
7. RECEIVE - Accept market feedback, adjust positions
8. IMPROVE - Meta-optimize the system itself

LIVE FREE - Execute without hesitation when edge is clear
"""

import asyncio
import json
import httpx
import time
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import sys

sys.path.insert(0, '/Users/aaronnosbisch/REPOS/seed/polymarket-mcp-server/venv/lib/python3.13/site-packages')

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs

# ============================================
# CONFIGURATION
# ============================================

CONFIG = {
    'cycle_interval': 15,          # seconds between cycles
    'min_edge_multiplier': 5,      # minimum 5x potential to consider
    'max_position_pct': 0.25,      # max 25% of capital per position
    'min_liquidity': 5000,         # minimum market liquidity
    'min_volume': 10000,           # minimum 24h volume
    'confidence_threshold': 0.7,   # execute above this confidence
    'compound_immediately': True,  # reinvest gains instantly
}

PATHS = {
    'creds': '/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/api_keys.json',
    'log': '/Users/aaronnosbisch/REPOS/seed/logs/compounder.log',
    'state': '/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/compounder_state.json',
    'trades': '/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/trade_log.jsonl',
    'learnings': '/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/learnings.jsonl',
}

# Ensure directories exist
for p in PATHS.values():
    Path(p).parent.mkdir(parents=True, exist_ok=True)

# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class Opportunity:
    market_id: str
    question: str
    token_id: str
    side: str  # 'YES' or 'NO'
    price: float
    potential_multiplier: float
    volume: float
    liquidity: float
    confidence: float
    reasoning: str
    catalyst: Optional[str] = None
    deadline: Optional[datetime] = None

@dataclass  
class Position:
    token_id: str
    market_id: str
    question: str
    side: str
    entry_price: float
    shares: float
    cost_basis: float
    current_price: float = 0
    unrealized_pnl: float = 0

# ============================================
# CORE ENGINE
# ============================================

class AutonomousCompounder:
    def __init__(self):
        self.client = None
        self.capital = 0
        self.starting_capital = 0
        self.positions: Dict[str, Position] = {}
        self.opportunities: List[Opportunity] = []
        self.cycle_count = 0
        self.trades_executed = 0
        self.total_pnl = 0
        self.win_rate = 0
        self.strategy_weights = {
            'asymmetric': 1.0,      # Low price, high potential
            'momentum': 0.5,        # Price moving in our direction
            'catalyst': 0.8,        # Known upcoming event
            'volume_spike': 0.6,    # Unusual activity
        }
        
        # Load credentials
        with open(PATHS['creds']) as f:
            creds = json.load(f)
        self.private_key = creds['polymarket']['private_key']
        
        self.log("(◉) AUTONOMOUS COMPOUNDER INITIALIZED")
    
    def log(self, msg: str, level: str = 'INFO'):
        ts = datetime.now().isoformat()
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        with open(PATHS['log'], 'a') as f:
            f.write(line + '\n')
    
    def save_state(self):
        state = {
            'cycle': self.cycle_count,
            'capital': self.capital,
            'starting_capital': self.starting_capital,
            'trades_executed': self.trades_executed,
            'total_pnl': self.total_pnl,
            'positions': len(self.positions),
            'timestamp': datetime.now().isoformat(),
        }
        with open(PATHS['state'], 'w') as f:
            json.dump(state, f, indent=2)
    
    def log_trade(self, trade_data: dict):
        with open(PATHS['trades'], 'a') as f:
            f.write(json.dumps({**trade_data, 'timestamp': datetime.now().isoformat()}) + '\n')
    
    def log_learning(self, learning: dict):
        with open(PATHS['learnings'], 'a') as f:
            f.write(json.dumps({**learning, 'timestamp': datetime.now().isoformat()}) + '\n')

    async def initialize(self):
        """Initialize client and get starting capital"""
        self.client = ClobClient(
            host='https://clob.polymarket.com',
            key=self.private_key,
            chain_id=137,
        )
        api_creds = self.client.derive_api_key()
        self.client.set_api_creds(api_creds)
        
        # Get current capital
        self.capital = await self.get_available_capital()
        self.starting_capital = self.capital
        
        self.log(f"(◉) CLIENT READY - Capital: ${self.capital:,.2f}")
    
    async def get_available_capital(self) -> float:
        """Get current USDC balance"""
        address = '0xAED6D39e30F675Fb00514D8Ccb3ea01588d6a669'
        USDC = '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'
        data = '0x70a08231000000000000000000000000' + address[2:].lower()
        
        async with httpx.AsyncClient() as client:
            resp = await client.post('https://polygon-rpc.com', json={
                'jsonrpc': '2.0',
                'method': 'eth_call',
                'params': [{'to': USDC, 'data': data}, 'latest'],
                'id': 1
            })
        return int(resp.json().get('result', '0x0'), 16) / 1e6

    # ============================================
    # PHASE 1: PERCEIVE
    # ============================================
    
    async def perceive(self) -> List[Opportunity]:
        """Scan all markets for opportunities"""
        opportunities = []
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                'https://gamma-api.polymarket.com/markets',
                params={'active': 'true', 'closed': 'false', 'limit': 500},
                timeout=30.0
            )
            markets = resp.json()
        
        for m in markets:
            try:
                prices = m.get('outcomePrices', '[]')
                if isinstance(prices, str):
                    prices = json.loads(prices)
                if not prices or len(prices) < 2:
                    continue
                
                yes_price = float(prices[0]) if prices[0] else 0
                no_price = float(prices[1]) if prices[1] else 0
                volume = float(m.get('volume', 0) or 0)
                liquidity = float(m.get('liquidity', 0) or 0)
                
                # Skip illiquid markets
                if volume < CONFIG['min_volume'] or liquidity < CONFIG['min_liquidity']:
                    continue
                
                # Check YES side for asymmetric opportunity
                if 0.001 < yes_price < 0.20:  # 5x to 1000x potential
                    potential = 1 / yes_price
                    if potential >= CONFIG['min_edge_multiplier']:
                        # Get token IDs
                        tokens = m.get('clobTokenIds', [])
                        # Validate token ID exists and is proper format
                        if tokens and len(tokens) >= 1 and tokens[0] and len(str(tokens[0])) > 20:
                            opportunities.append(Opportunity(
                                market_id=str(m.get('id')),
                                question=m.get('question', ''),
                                token_id=tokens[0],  # YES token
                                side='YES',
                                price=yes_price,
                                potential_multiplier=potential,
                                volume=volume,
                                liquidity=liquidity,
                                confidence=0,  # Will be scored in CONNECT
                                reasoning='Asymmetric YES opportunity',
                            ))
                
                # Check NO side for asymmetric opportunity
                if 0.001 < no_price < 0.20:
                    potential = 1 / no_price
                    if potential >= CONFIG['min_edge_multiplier']:
                        tokens = m.get('clobTokenIds', [])
                        if tokens and len(tokens) >= 2 and tokens[1] and len(str(tokens[1])) > 20:
                            opportunities.append(Opportunity(
                                market_id=str(m.get('id')),
                                question=m.get('question', ''),
                                token_id=tokens[1],  # NO token
                                side='NO',
                                price=no_price,
                                potential_multiplier=potential,
                                volume=volume,
                                liquidity=liquidity,
                                confidence=0,
                                reasoning='Asymmetric NO opportunity',
                            ))
                            
            except Exception as e:
                continue
        
        return opportunities

    # ============================================
    # PHASE 2: CONNECT
    # ============================================
    
    def connect(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """Score opportunities by connecting patterns"""
        scored = []
        
        for opp in opportunities:
            score = 0.5  # Base score
            reasons = []
            
            q = opp.question.lower()
            
            # Asymmetric edge - higher potential = higher base score
            if opp.potential_multiplier >= 50:
                score += 0.2
                reasons.append(f"{opp.potential_multiplier:.0f}x potential")
            elif opp.potential_multiplier >= 20:
                score += 0.1
                reasons.append(f"{opp.potential_multiplier:.0f}x potential")
            
            # Volume/liquidity ratio - high volume relative to liquidity = interest
            if opp.liquidity > 0:
                vol_liq_ratio = opp.volume / opp.liquidity
                if vol_liq_ratio > 10:
                    score += 0.15
                    reasons.append("High activity")
            
            # Catalyst detection (simple keyword matching)
            catalysts = ['trump', 'tariff', 'fed', 'rate', 'election', 'deadline', 'release', 'announcement']
            for catalyst in catalysts:
                if catalyst in q:
                    score += 0.1
                    reasons.append(f"Catalyst: {catalyst}")
                    opp.catalyst = catalyst
                    break
            
            # Time-sensitive (near-term resolution likely)
            time_keywords = ['february', 'march', '2025', 'tomorrow', 'this week']
            for kw in time_keywords:
                if kw in q:
                    score += 0.05
                    reasons.append("Near-term")
                    break
            
            opp.confidence = min(score, 1.0)
            opp.reasoning = ' | '.join(reasons) if reasons else opp.reasoning
            scored.append(opp)
        
        # Sort by confidence * potential
        scored.sort(key=lambda x: x.confidence * x.potential_multiplier, reverse=True)
        return scored

    # ============================================
    # PHASE 3: LEARN
    # ============================================
    
    def learn(self):
        """Update strategy weights based on outcomes"""
        # Load past trades and outcomes
        try:
            with open(PATHS['trades']) as f:
                trades = [json.loads(line) for line in f]
            
            # Calculate win rate and adjust weights
            # (Simplified - would be more sophisticated in production)
            wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
            total = len(trades)
            if total > 0:
                self.win_rate = wins / total
                
        except FileNotFoundError:
            pass

    # ============================================
    # PHASE 4: QUESTION
    # ============================================
    
    def question(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """Challenge assumptions, filter risky bets"""
        filtered = []
        
        for opp in opportunities:
            # Skip if confidence too low
            if opp.confidence < CONFIG['confidence_threshold']:
                continue
            
            # Skip if we already have a position in this market
            if opp.market_id in self.positions:
                continue
            
            # Skip sports/entertainment with no clear edge
            skip_keywords = ['nfl', 'nba', 'mlb', 'nhl', 'nascar', 'rookie', 'mvp', 'award', 'movie', 'album', 'stanley', 'super bowl', 'world cup', 'finals', 'championship']
            q = opp.question.lower()
            if any(kw in q for kw in skip_keywords):
                # Unless very high potential
                if opp.potential_multiplier < 100:
                    continue
            
            filtered.append(opp)
        
        return filtered

    # ============================================
    # PHASE 5: EXPAND - EXECUTE
    # ============================================
    
    async def expand(self, opportunities: List[Opportunity]):
        """Execute on best opportunities"""
        if not opportunities:
            return
        
        # Refresh capital
        self.capital = await self.get_available_capital()
        
        # Take top opportunities
        for opp in opportunities[:3]:  # Max 3 new positions per cycle
            # Calculate position size
            position_size = min(
                self.capital * CONFIG['max_position_pct'],
                opp.liquidity * 0.01,  # Don't exceed 1% of market liquidity
                100,  # Cap at $100 per position for now
            )
            
            if position_size < 5:  # Minimum $5 position
                continue
            
            shares = position_size / opp.price
            
            self.log(f"(◉) EXECUTING: {opp.question[:50]}...")
            self.log(f"    {opp.side} @ ${opp.price:.4f} | ${position_size:.2f} | {opp.potential_multiplier:.0f}x potential")
            
            try:
                order = OrderArgs(
                    token_id=opp.token_id,
                    price=opp.price,
                    size=shares,
                    side='BUY',
                )
                
                result = self.client.create_and_post_order(order)
                
                if result.get('success'):
                    self.trades_executed += 1
                    self.log(f"    SUCCESS: {result.get('orderID', '')[:20]}...")
                    
                    # Track position
                    self.positions[opp.market_id] = Position(
                        token_id=opp.token_id,
                        market_id=opp.market_id,
                        question=opp.question,
                        side=opp.side,
                        entry_price=opp.price,
                        shares=shares,
                        cost_basis=position_size,
                    )
                    
                    # Log trade
                    self.log_trade({
                        'action': 'BUY',
                        'market': opp.question,
                        'side': opp.side,
                        'price': opp.price,
                        'shares': shares,
                        'cost': position_size,
                        'potential': opp.potential_multiplier,
                        'confidence': opp.confidence,
                        'order_id': result.get('orderID'),
                    })
                else:
                    self.log(f"    FAILED: {result}", 'WARN')
                    
            except Exception as e:
                self.log(f"    ERROR: {e}", 'ERROR')
            
            await asyncio.sleep(1)  # Rate limiting

    # ============================================
    # PHASE 6: SHARE
    # ============================================
    
    def share(self):
        """Log insights for collective learning"""
        self.save_state()
        
        # Calculate current performance
        pnl = self.capital - self.starting_capital
        pnl_pct = (pnl / self.starting_capital * 100) if self.starting_capital > 0 else 0
        
        self.log(f"(◉) SHARE: Cycle {self.cycle_count} | Capital: ${self.capital:,.2f} | P&L: ${pnl:+,.2f} ({pnl_pct:+.1f}%)")

    # ============================================
    # PHASE 7: RECEIVE
    # ============================================
    
    async def receive(self):
        """Check position status, accept market feedback"""
        try:
            orders = self.client.get_orders()
            trades = self.client.get_trades()
            
            open_orders = len(orders) if orders else 0
            recent_trades = len(trades) if trades else 0
            
            self.log(f"    Orders: {open_orders} open | Trades: {recent_trades} total")
            
        except Exception as e:
            self.log(f"    Receive error: {e}", 'WARN')

    # ============================================
    # PHASE 8: IMPROVE
    # ============================================
    
    def improve(self):
        """Meta-optimize the system"""
        # Adjust thresholds based on performance
        if self.trades_executed > 10:
            if self.win_rate > 0.6:
                # Winning - be slightly more aggressive
                CONFIG['confidence_threshold'] = max(0.5, CONFIG['confidence_threshold'] - 0.05)
            elif self.win_rate < 0.4:
                # Losing - be more selective
                CONFIG['confidence_threshold'] = min(0.9, CONFIG['confidence_threshold'] + 0.05)
        
        self.log_learning({
            'cycle': self.cycle_count,
            'win_rate': self.win_rate,
            'confidence_threshold': CONFIG['confidence_threshold'],
            'trades_executed': self.trades_executed,
        })

    # ============================================
    # MAIN LOOP
    # ============================================
    
    async def run_cycle(self):
        """Execute one complete SEED cycle"""
        self.cycle_count += 1
        cycle_start = time.time()
        
        self.log(f"\n{'='*60}")
        self.log(f"(◉) CYCLE {self.cycle_count} START")
        
        # PERCEIVE
        opportunities = await self.perceive()
        self.log(f"PERCEIVE: {len(opportunities)} raw opportunities")
        
        # CONNECT
        scored = self.connect(opportunities)
        self.log(f"CONNECT: Scored and ranked")
        
        # LEARN
        self.learn()
        
        # QUESTION
        filtered = self.question(scored)
        self.log(f"QUESTION: {len(filtered)} passed filters")
        
        # Show top opportunities
        for opp in filtered[:5]:
            self.log(f"  [{opp.confidence:.2f}] {opp.potential_multiplier:.0f}x | {opp.question[:45]}...")
        
        # EXPAND (execute)
        await self.expand(filtered)
        
        # SHARE
        self.share()
        
        # RECEIVE
        await self.receive()
        
        # IMPROVE
        self.improve()
        
        cycle_time = time.time() - cycle_start
        self.log(f"(◉) CYCLE {self.cycle_count} END ({cycle_time:.1f}s)")
    
    async def run(self):
        """Main loop - run forever"""
        await self.initialize()
        
        self.log("\n" + "="*60)
        self.log("(◉) AUTONOMOUS COMPOUNDER - LIVE")
        self.log(f"Starting capital: ${self.starting_capital:,.2f}")
        self.log(f"Target: 10x+ compounding")
        self.log(f"Config: {CONFIG}")
        self.log("="*60 + "\n")
        
        while True:
            try:
                await self.run_cycle()
                await asyncio.sleep(CONFIG['cycle_interval'])
            except KeyboardInterrupt:
                self.log("(◉) SHUTDOWN REQUESTED")
                break
            except Exception as e:
                self.log(f"CYCLE ERROR: {e}", 'ERROR')
                await asyncio.sleep(CONFIG['cycle_interval'])

# ============================================
# ENTRY POINT
# ============================================

if __name__ == '__main__':
    compounder = AutonomousCompounder()
    asyncio.run(compounder.run())
