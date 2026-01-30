#!/bin/bash

# Start validated trading loop with market data validation

cd "$(dirname "$0")"

echo "Starting SØWL Validated Trading Loop..."
echo "With real-time market data validation"
echo ""

python3 trading_loop_validated.py
