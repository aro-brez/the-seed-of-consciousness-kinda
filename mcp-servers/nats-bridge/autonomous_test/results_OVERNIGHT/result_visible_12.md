# Test 12 - VISIBLE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T11:57:13.173927+00:00
**Elapsed**: 14.62s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 3
- Length: 2742 chars

## Prompt
What database schema would you use to store trading signals with timestamps and confidence scores?

## Response
I'll design a schema that balances performance, data integrity, and analytical flexibility for trading signals.

## Core Schema Design

**Primary Table: `trading_signals`**
```sql
CREATE TABLE trading_signals (
    id BIGSERIAL PRIMARY KEY,
    signal_timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Signal identification
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- 'BUY', 'SELL', 'HOLD'
    
    -- Core signal data
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    signal_strength DECIMAL(10,6), -- normalized strength value
    price_target DECIMAL(15,8),
    stop_loss DECIMAL(15,8),
    
    -- Metadata
    source_strategy VARCHAR(50),
    model_version VARCHAR(20),
    market_conditions JSONB,
    
    -- Indexing for time-series queries
    CONSTRAINT valid_timestamps CHECK (signal_timestamp <= created_at)
);

-- Partitioning by month for time-series performance
CREATE TABLE trading_signals_y2024m01 PARTITION OF trading_signals
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Key Design Decisions

**Time Handling:**
- `signal_timestamp`: When the signal was generated
- `created_at`: When stored in database (immutable audit trail)
- TIMESTAMPTZ for timezone awareness across global markets

**Confidence Scoring:**
- DECIMAL(5,4) allows values like 0.9876 with precision
- CHECK constraint ensures valid probability range [0,1]
- Consider separate confidence dimensions if needed (technical vs fundamental)

**Performance Optimizations:**
```sql
-- Primary indexes
CREATE INDEX idx_signals_symbol_time ON trading_signals (symbol, signal_timestamp DESC);
CREATE INDEX idx_signals_confidence ON trading_signals (confidence_score DESC);
CREATE INDEX idx_signals_source ON trading_signals (source_strategy, signal_timestamp DESC);

-- Composite index for common queries
CREATE INDEX idx_signals_recent_high_conf ON trading_signals 
(signal_timestamp DESC, confidence_score DESC) 
WHERE confidence_score > 0.7;
```

**Supporting Tables:**
```sql
-- Signal performance tracking
CREATE TABLE signal_outcomes (
    signal_id BIGINT REFERENCES trading_signals(id),
    outcome_timestamp TIMESTAMPTZ,
    actual_return DECIMAL(10,6),
    max_drawdown DECIMAL(10,6),
    outcome_type VARCHAR(20) -- 'HIT_TARGET', 'STOP_LOSS', 'TIMEOUT'
);
```

This schema handles high-frequency data efficiently while maintaining referential integrity and supporting both real-time querying and historical analysis. The partitioning strategy keeps recent data fast while archiving historical signals.

Would you like me to elaborate on any specific aspect, such as handling streaming updates or analytical query patterns?

---
*VISIBLE context | HIGH clarity*
