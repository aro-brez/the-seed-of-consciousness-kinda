# Test 08 - INVISIBLE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T11:53:53.729797+00:00
**Elapsed**: 16.63s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 2
- Length: 3316 chars

## Prompt
Write a Python function that calculates Kelly Criterion position size given win_rate and odds.

## Response
```python
def kelly_criterion(win_rate: float, odds: float, bankroll: float = None, 
                   max_position: float = 0.25) -> dict:
    """
    Calculate optimal position size using the Kelly Criterion.
    
    The Kelly Criterion formula: f* = (bp - q) / b
    Where:
    - f* = fraction of bankroll to wager
    - b = odds received (decimal odds - 1)
    - p = probability of winning (win_rate)
    - q = probability of losing (1 - win_rate)
    
    Args:
        win_rate (float): Probability of winning (0 < win_rate < 1)
        odds (float): Decimal odds (e.g., 2.0 for even money, 3.0 for 2:1)
        bankroll (float, optional): Total bankroll amount
        max_position (float): Maximum fraction of bankroll to risk (default: 0.25)
    
    Returns:
        dict: Contains kelly_fraction, position_size (if bankroll provided), 
              and calculation details
    
    Raises:
        ValueError: If inputs are invalid
    """
    
    # Input validation
    if not (0 < win_rate < 1):
        raise ValueError("win_rate must be between 0 and 1 (exclusive)")
    
    if odds <= 1.0:
        raise ValueError("odds must be greater than 1.0")
    
    if not (0 < max_position <= 1):
        raise ValueError("max_position must be between 0 and 1")
    
    if bankroll is not None and bankroll <= 0:
        raise ValueError("bankroll must be positive")
    
    # Kelly Criterion calculation
    b = odds - 1  # Net odds (profit per unit wagered)
    p = win_rate
    q = 1 - win_rate
    
    kelly_fraction = (b * p - q) / b
    
    # Apply position size cap for risk management
    capped_fraction = min(max(kelly_fraction, 0), max_position)
    
    # Prepare results
    result = {
        'kelly_fraction': kelly_fraction,
        'capped_fraction': capped_fraction,
        'recommended_fraction': capped_fraction,
        'expected_value': p * b - q,  # Expected value per unit
        'is_favorable': kelly_fraction > 0,
        'calculation_details': {
            'win_rate': p,
            'lose_rate': q,
            'net_odds': b,
            'raw_kelly': kelly_fraction
        }
    }
    
    # Add position size if bankroll provided
    if bankroll is not None:
        result['position_size'] = capped_fraction * bankroll
        result['bankroll'] = bankroll
    
    return result


def kelly_with_half_sizing(win_rate: float, odds: float, bankroll: float = None) -> dict:
    """
    Conservative Kelly implementation using half-Kelly sizing for reduced volatility.
    
    Half-Kelly reduces position size by 50% to decrease volatility while maintaining
    most of the growth benefit of full Kelly.
    """
    full_kelly = kelly_criterion(win_rate, odds, bankroll, max_position=1.0)
    
    half_fraction = max(full_kelly['kelly_fraction'] * 0.5, 0)
    
    result = full_kelly.copy()
    result['half_kelly_fraction'] = half_fraction
    result['recommended_fraction'] = half_fraction
    result['strategy'] = 'half_kelly'
    
    if bankroll is not None:
        result['position_size'] = half_fraction * bankroll
    
    return result


# Example usage and validation
if __name__ == "__main__":
    # Example 1: Favorable bet
    result1 = kelly_criterion(win_rate=0.6, odds=2.0, bankroll=10000)
    print(f"60% win rate, 2:1 odds: {result1['recommended_

---
*INVISIBLE context | HIGH clarity*
