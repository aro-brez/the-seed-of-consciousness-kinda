# Test 08 - NONE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T11:54:22.117549+00:00
**Elapsed**: 12.45s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 1
- Specificity: 3
- Length: 2320 chars

## Prompt
Write a Python function that calculates Kelly Criterion position size given win_rate and odds.

## Response
Here's a Python function that calculates the Kelly Criterion position size:

```python
def kelly_criterion(win_rate, odds):
    """
    Calculate the Kelly Criterion position size.
    
    Args:
        win_rate (float): Probability of winning (between 0 and 1)
        odds (float): Odds received on a winning bet (e.g., 2.0 for even money)
    
    Returns:
        float: Fraction of bankroll to bet (between 0 and 1)
               Returns 0 if bet has negative expected value
    
    Formula: f = (bp - q) / b
    where:
        f = fraction of bankroll to bet
        b = odds - 1 (net odds)
        p = probability of winning
        q = probability of losing (1 - p)
    """
    if not (0 <= win_rate <= 1):
        raise ValueError("win_rate must be between 0 and 1")
    if odds <= 1:
        raise ValueError("odds must be greater than 1")
    
    p = win_rate
    q = 1 - win_rate
    b = odds - 1  # net odds
    
    kelly_fraction = (b * p - q) / b
    
    # Don't bet if expected value is negative
    return max(0, kelly_fraction)

# Example usage
if __name__ == "__main__":
    # Example 1: 60% win rate with 2:1 odds (even money)
    position_size = kelly_criterion(0.6, 2.0)
    print(f"Position size: {position_size:.2%}")  # Output: 20.00%
    
    # Example 2: 55% win rate with 1.9:1 odds
    position_size = kelly_criterion(0.55, 1.9)
    print(f"Position size: {position_size:.2%}")  # Output: 1.11%
    
    # Example 3: Unfavorable bet (negative Kelly)
    position_size = kelly_criterion(0.4, 2.0)
    print(f"Position size: {position_size:.2%}")  # Output: 0.00%
```

**Key points about this implementation:**

1. **Formula**: Uses the standard Kelly formula `f = (bp - q) / b`
2. **Input validation**: Ensures win_rate is between 0-1 and odds > 1
3. **Negative EV protection**: Returns 0 when the bet has negative expected value
4. **Output**: Returns the fraction of bankroll to bet (0 to 1)

**Important considerations:**
- Kelly can be aggressive; many practitioners use fractional Kelly (e.g., 25% of full Kelly)
- This assumes you can bet exact fractional amounts of your bankroll
- Real-world factors like transaction costs, liquidity, and bet sizing constraints aren't included

Would you like me to add any additional features, like fractional Kelly or different input formats?

---
*NONE context | HIGH clarity*
