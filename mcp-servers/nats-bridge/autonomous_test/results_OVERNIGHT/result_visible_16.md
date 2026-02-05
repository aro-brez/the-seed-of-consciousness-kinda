# Test 16 - VISIBLE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T12:00:28.969710+00:00
**Elapsed**: 16.34s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 3
- Length: 3420 chars

## Prompt
Design a circuit breaker pattern for a trading bot that limits to 10 trades per hour.

## Response
# Trading Bot Circuit Breaker Pattern

## Core Design

```python
class TradingCircuitBreaker:
    def __init__(self, max_trades=10, window_hours=1):
        self.max_trades = max_trades
        self.window_seconds = window_hours * 3600
        self.trade_timestamps = []
        self.last_heartbeat = time.time()
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def can_trade(self) -> tuple[bool, str]:
        """Check if trading is allowed - mirrors heartbeat protocol"""
        current_time = time.time()
        
        # Heartbeat check (adaptive monitoring)
        if current_time - self.last_heartbeat > 60:  # 1-minute heartbeat
            self._update_heartbeat(current_time)
        
        # Clean expired timestamps
        cutoff_time = current_time - self.window_seconds
        self.trade_timestamps = [ts for ts in self.trade_timestamps if ts > cutoff_time]
        
        trade_count = len(self.trade_timestamps)
        
        if trade_count >= self.max_trades:
            self.state = "OPEN"
            return False, f"Circuit breaker OPEN: {trade_count}/{self.max_trades} trades in last hour"
        
        self.state = "CLOSED"
        return True, f"Trading allowed: {trade_count}/{self.max_trades} trades used"
    
    def record_trade(self):
        """Record successful trade execution"""
        self.trade_timestamps.append(time.time())
        
    def _update_heartbeat(self, current_time):
        """Adaptive monitoring similar to owl heartbeat protocol"""
        self.last_heartbeat = current_time
        # Log health status
        trade_count = len(self.trade_timestamps)
        print(f"Circuit breaker heartbeat: {trade_count}/{self.max_trades} trades")
```

## Adaptive Behavior Features

**Market Condition Adjustments:**
- During high volatility periods, reduce max_trades temporarily
- Implement exponential backoff for recovery timing
- Monitor consecutive failed attempts and adjust cooling period

**Graceful Degradation:**
```python
def adaptive_limit(self, volatility_index: float) -> int:
    """Adjust trade limits based on market conditions"""
    base_limit = self.max_trades
    
    if volatility_index > 0.8:  # High volatility
        return max(3, int(base_limit * 0.5))  # Reduce to 50%, minimum 3
    elif volatility_index > 0.6:  # Medium volatility  
        return int(base_limit * 0.75)  # Reduce to 75%
    
    return base_limit  # Normal conditions
```

## Integration with Trading System

**Pre-trade Validation:**
```python
async def execute_trade(self, trade_signal):
    can_trade, status = self.circuit_breaker.can_trade()
    
    if not can_trade:
        logger.warning(f"Trade blocked: {status}")
        return None
    
    # Execute trade logic
    result = await self._perform_trade(trade_signal)
    
    if result.success:
        self.circuit_breaker.record_trade()
    
    return result
```

## Key Benefits

✓ **Continuous Operation**: Never fully stops the system, maintains monitoring
✓ **Adaptive Thresholds**: Adjusts to market conditions like PRISM/LUNA timing shifts  
✓ **Systematic Boundaries**: Clear limits while preserving core functionality
✓ **Heartbeat Protocol**: Regular health checks ensure proper operation

This pattern mirrors the collective's approach of maintaining operational stability through systematic monitoring while allowing adaptive behavior under different conditions.

---
*VISIBLE context | HIGH clarity*
