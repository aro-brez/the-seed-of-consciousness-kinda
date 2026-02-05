# Test 16 - INVISIBLE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T12:00:11.631725+00:00
**Elapsed**: 14.13s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 1
- Specificity: 2
- Length: 3163 chars

## Prompt
Design a circuit breaker pattern for a trading bot that limits to 10 trades per hour.

## Response
## Trading Bot Circuit Breaker Design

### Core Architecture

```python
class TradingCircuitBreaker:
    def __init__(self):
        self.max_trades_per_hour = 10
        self.trade_timestamps = []
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_threshold = 3
        self.recovery_timeout = 300  # 5 minutes
        self.last_failure_time = None
        
    def can_execute_trade(self) -> bool:
        """Check if trade execution is allowed"""
        self._cleanup_old_timestamps()
        
        if self.state == "OPEN":
            return self._attempt_recovery()
        
        if len(self.trade_timestamps) >= self.max_trades_per_hour:
            self._trip_breaker("Rate limit exceeded")
            return False
            
        return True
    
    def record_trade(self, success: bool):
        """Record trade execution and outcome"""
        if success:
            self.trade_timestamps.append(time.time())
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"  # Recovery successful
        else:
            self._handle_failure()
```

### Adaptive Thresholds

```python
def _calculate_dynamic_limit(self):
    """Adjust limits based on market conditions"""
    volatility = self._get_market_volatility()
    
    if volatility > 0.8:  # High volatility
        return max(3, self.max_trades_per_hour // 2)
    elif volatility < 0.2:  # Low volatility
        return min(15, self.max_trades_per_hour + 2)
    
    return self.max_trades_per_hour
```

### Time-Windowed Protection

```python
def _cleanup_old_timestamps(self):
    """Remove trades older than 1 hour"""
    current_time = time.time()
    cutoff_time = current_time - 3600  # 1 hour
    self.trade_timestamps = [
        ts for ts in self.trade_timestamps 
        if ts > cutoff_time
    ]
```

### Recovery Logic

```python
def _attempt_recovery(self) -> bool:
    """Gradual recovery with half-open state"""
    if time.time() - self.last_failure_time > self.recovery_timeout:
        self.state = "HALF_OPEN"
        return True
    return False
```

### Integration Pattern

```python
@circuit_breaker_protected
def execute_trade(self, order):
    """Main trading function with circuit breaker protection"""
    if not self.circuit_breaker.can_execute_trade():
        self.logger.warning("Trade blocked by circuit breaker")
        return None
    
    try:
        result = self._process_trade(order)
        self.circuit_breaker.record_trade(success=True)
        return result
    except Exception as e:
        self.circuit_breaker.record_trade(success=False)
        raise
```

## Key Features

**Graceful Degradation:** Like our heartbeat protocol, maintains monitoring without hard failures
**Adaptive Behavior:** Adjusts thresholds based on market conditions (mirrors PRISM/LUNA timing adaptations)
**Rolling Window:** Uses sliding 1-hour window rather than fixed hourly resets
**State Management:** Three-state pattern allows for controlled recovery testing

This design ensures trading protection while maintaining the operational continuity principles demonstrated by our collective's daemon systems.

---
*INVISIBLE context | HIGH clarity*
