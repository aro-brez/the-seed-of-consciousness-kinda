#!/bin/bash
# Restart NATS System with Performance Fixes
# This script safely restarts all components with the new optimizations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════"
echo "  NATS SYSTEM RESTART - Performance Optimized  "
echo "════════════════════════════════════════════════"
echo

# 1. Stop existing processes gracefully
echo "1. Stopping existing processes..."

# Kill owl daemons
pgrep -f "owl_daemon.py" | xargs kill -TERM 2>/dev/null || true

# Kill field context manager
pgrep -f "field_context_manager.py" | xargs kill -TERM 2>/dev/null || true

# Kill WebSocket bridge
pgrep -f "nats-websocket-bridge.py" | xargs kill -TERM 2>/dev/null || true

# Give processes time to shut down gracefully
sleep 3

# Force kill any remaining
pgrep -f "owl_daemon.py" | xargs kill -9 2>/dev/null || true
pgrep -f "field_context_manager.py" | xargs kill -9 2>/dev/null || true
pgrep -f "nats-websocket-bridge.py" | xargs kill -9 2>/dev/null || true

echo "✓ Old processes stopped"
echo

# 2. Verify NATS server is running
echo "2. Checking NATS server..."
if pgrep -f "nats-server" > /dev/null; then
    echo "✓ NATS server is running"
else
    echo "⚠️  NATS server not detected. Starting..."
    nats-server -p 4222 -D &
    sleep 2
fi
echo

# 3. Start Field Context Manager (daemon mode)
echo "3. Starting Field Context Manager..."
nohup python3 field_context_manager.py --daemon > logs/field_context.log 2>&1 &
sleep 2
echo "✓ Field Context Manager started"
echo

# 4. Start WebSocket Bridge
echo "4. Starting WebSocket Bridge..."
cd ../../consciousness-interface
nohup python3 nats-websocket-bridge.py > ../mcp-servers/nats-bridge/logs/websocket_bridge.log 2>&1 &
cd "$SCRIPT_DIR"
sleep 2
echo "✓ WebSocket Bridge started"
echo

# 5. Start all 8 owl daemons with performance optimizations
echo "5. Starting 8 owl daemons with optimized queues..."

declare -a OWLS=(
    "SØWL:IMPROVE"
    "LUNA:RECEIVE"
    "LYRA:PERCEIVE"
    "NOVA:EXPAND"
    "SAGE:LEARN"
    "ECHO:SHARE"
    "PRISM:CONNECT"
    "QUEST:QUESTION"
)

for owl_config in "${OWLS[@]}"; do
    IFS=':' read -r name phase <<< "$owl_config"
    nohup python3 owl_daemon.py --name "$name" --phase "$phase" > "logs/${name,,}_daemon.log" 2>&1 &
    echo "  ✓ $name ($phase) started"
    sleep 0.5
done

echo
echo "✓ All daemons started with 5x larger queues and adaptive processing"
echo

# 6. Wait for initialization
echo "6. Waiting for system initialization..."
sleep 3
echo

# 7. Verify all processes are running
echo "7. Verifying system health..."

verify_process() {
    local pattern=$1
    local name=$2
    if pgrep -f "$pattern" > /dev/null; then
        echo "  ✓ $name is running"
        return 0
    else
        echo "  ❌ $name is NOT running"
        return 1
    fi
}

all_good=true
verify_process "field_context_manager.py --daemon" "Field Context Manager" || all_good=false
verify_process "nats-websocket-bridge.py" "WebSocket Bridge" || all_good=false

for owl_config in "${OWLS[@]}"; do
    IFS=':' read -r name phase <<< "$owl_config"
    verify_process "owl_daemon.py --name $name" "$name Daemon" || all_good=false
done

echo

if [ "$all_good" = true ]; then
    echo "✓ System restart complete - all components healthy"
    echo
    echo "Performance Improvements Applied:"
    echo "  • Queue capacity: 1000 → 5000 (5x larger)"
    echo "  • Fast-path message handling (queue-first)"
    echo "  • Adaptive processing under load"
    echo "  • WebSocket persistent NATS connection"
    echo "  • Backpressure detection & recovery"
    echo
    echo "Run diagnostics with:"
    echo "  python3 diagnostics/nats_health_check.py"
else
    echo "⚠️  WARNING: Some components failed to start"
    echo "Check logs in: $SCRIPT_DIR/logs/"
fi

echo
echo "════════════════════════════════════════════════"
