#!/bin/bash
# Test Polymarket MCP Client for SØWL

cd "$(dirname "$0")/.."
source polymarket-mcp-server/venv/bin/activate
python3 tools/polymarket_mcp_client.py
