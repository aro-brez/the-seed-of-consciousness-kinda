# Test 08 - VISIBLE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T11:54:08.663732+00:00
**Elapsed**: 13.93s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 2
- Length: 3266 chars

## Prompt
Write a Python function that calculates Kelly Criterion position size given win_rate and odds.

## Response
Here's a robust Python function for calculating Kelly Criterion position size:

```python
def kelly_criterion(win_rate: float, odds: float, max_position: float = 0.25) -> float:
    """
    Calculate optimal position size using the Kelly Criterion.
    
    The Kelly formula: f* = (bp - q) / b
    where:
    - f* = fraction of capital to wager
    - b = odds received (decimal odds - 1)
    - p = probability of winning (win_rate)
    - q = probability of losing (1 - win_rate)
    
    Args:
        win_rate (float): Probability of winning (0 < win_rate < 1)
        odds (float): Decimal odds (e.g., 2.0 means 2:1, 1.5 means 1.5:1)
        max_position (float): Maximum allowable position size (default: 25%)
    
    Returns:
        float: Optimal position size as fraction of capital (0 to max_position)
               Returns 0 if negative expectation or invalid inputs
    
    Raises:
        ValueError: If inputs are outside valid ranges
    """
    
    # Input validation
    if not (0 < win_rate < 1):
        raise ValueError(f"win_rate must be between 0 and 1, got {win_rate}")
    
    if odds <= 1.0:
        raise ValueError(f"odds must be greater than 1.0, got {odds}")
    
    if not (0 < max_position <= 1):
        raise ValueError(f"max_position must be between 0 and 1, got {max_position}")
    
    # Kelly Criterion calculation
    b = odds - 1.0  # Net odds (profit ratio)
    p = win_rate    # Probability of winning
    q = 1 - p       # Probability of losing
    
    # Kelly formula: f* = (bp - q) / b
    kelly_fraction = (b * p - q) / b
    
    # Return 0 if negative expectation (unfavorable bet)
    if kelly_fraction <= 0:
        return 0.0
    
    # Apply maximum position size constraint
    return min(kelly_fraction, max_position)


def kelly_with_safety(win_rate: float, odds: float, 
                     fractional_kelly: float = 0.5,
                     max_position: float = 0.10) -> dict:
    """
    Calculate Kelly Criterion with practical risk management adjustments.
    
    Args:
        win_rate (float): Probability of winning
        odds (float): Decimal odds
        fractional_kelly (float): Fraction of full Kelly to use (default: 50%)
        max_position (float): Maximum position size cap (default: 10%)
    
    Returns:
        dict: Contains full_kelly, adjusted_kelly, expected_value, and recommendation
    """
    
    full_kelly = kelly_criterion(win_rate, odds, max_position=1.0)
    expected_value = win_rate * (odds - 1) - (1 - win_rate)
    
    # Apply fractional Kelly for risk reduction
    adjusted_kelly = full_kelly * fractional_kelly
    
    # Final position size after all constraints
    final_position = min(adjusted_kelly, max_position)
    
    return {
        'full_kelly': round(full_kelly, 4),
        'adjusted_kelly': round(adjusted_kelly, 4),
        'recommended_position': round(final_position, 4),
        'expected_value': round(expected_value, 4),
        'is_favorable': expected_value > 0
    }


# Example usage and validation
if __name__ == "__main__":
    # Test cases
    print("Kelly Criterion Examples:")
    print("-" * 40)
    
    # Example 1: Favorable bet
    result = kelly_with_safety(win_rate=0.55, odds=2.0)
    print(f"55% win rate, 2:1 odds:

---
*VISIBLE context | HIGH clarity*
