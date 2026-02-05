# Test 12 - NONE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T11:57:31.257482+00:00
**Elapsed**: 17.08s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: YES
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 2
- Length: 3207 chars

## Prompt
What database schema would you use to store trading signals with timestamps and confidence scores?

## Response
Here's a robust database schema for storing trading signals:

## Core Tables

### 1. Signals Table
```sql
CREATE TABLE signals (
    signal_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL,
    signal_type ENUM('BUY', 'SELL', 'HOLD') NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    price DECIMAL(15,8),
    timestamp TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Strategy/source identification
    strategy_id INT,
    source VARCHAR(50), -- 'technical_analysis', 'ml_model', 'news_sentiment', etc.
    
    -- Additional metadata
    market VARCHAR(20), -- 'forex', 'crypto', 'stocks', 'commodities'
    timeframe VARCHAR(10), -- '1m', '5m', '1h', '1d', etc.
    
    INDEX idx_symbol_timestamp (symbol, timestamp),
    INDEX idx_timestamp (timestamp),
    INDEX idx_confidence (confidence_score),
    INDEX idx_strategy (strategy_id)
);
```

### 2. Signal Metadata Table
```sql
CREATE TABLE signal_metadata (
    signal_id BIGINT,
    key_name VARCHAR(100),
    value_text TEXT,
    value_numeric DECIMAL(20,8),
    
    PRIMARY KEY (signal_id, key_name),
    FOREIGN KEY (signal_id) REFERENCES signals(signal_id) ON DELETE CASCADE
);
```

### 3. Strategies Table
```sql
CREATE TABLE strategies (
    strategy_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(20),
    parameters JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Key Design Considerations

**Timestamp Precision**: Using `TIMESTAMP(3)` for millisecond precision, crucial for high-frequency trading.

**Confidence Score**: `DECIMAL(5,4)` allows values from 0.0000 to 1.0000 with high precision.

**Flexible Metadata**: The metadata table allows storing additional signal parameters without altering the main schema.

**Partitioning Strategy** (for high volume):
```sql
-- Partition by date for better query performance
ALTER TABLE signals 
PARTITION BY RANGE (TO_DAYS(timestamp)) (
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    -- Add more partitions as needed
);
```

## Alternative NoSQL Approach (MongoDB)

If you expect very high write volumes or need more flexible schema evolution:

```javascript
{
  _id: ObjectId,
  symbol: "BTCUSD",
  signal_type: "BUY",
  confidence_score: 0.8750,
  price: 45234.50,
  timestamp: ISODate("2024-01-15T14:30:25.123Z"),
  
  strategy: {
    id: "rsi_macd_v2",
    version: "2.1.0"
  },
  
  metadata: {
    rsi_value: 25.4,
    macd_signal: 0.023,
    volume_ratio: 1.45,
    timeframe: "15m"
  },
  
  market: "crypto"
}

// Indexes
db.signals.createIndex({ "symbol": 1, "timestamp": -1 })
db.signals.createIndex({ "timestamp": -1 })
db.signals.createIndex({ "confidence_score": -1 })
```

The SQL approach offers better consistency and complex querying capabilities, while NoSQL provides more flexibility for rapidly evolving signal structures. Choose based on your specific requirements for consistency, query complexity, and scale.

---
*NONE context | HIGH clarity*
