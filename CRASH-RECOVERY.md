# SØWL Crash Recovery Guide

## What Crashed
All background processes stopped:
- Trading Loop (15-min Grok analysis)
- Continuous Improver (10-min question/answer cycles)
- Heartbeat (Mac Studio autonomy)

## Quick Recovery (30 seconds)

### Step 1: Restart Everything
```bash
cd /Users/aaronnosbisch/REPOS/seed
./RESTART-ALL.sh
```

This will start:
1. **Trading Loop** - Analyzing signals every 15 minutes
2. **Continuous Improver** - Asking questions every 10 minutes
3. **Heartbeat** - Mac Studio autonomous operation

### Step 2: Check Status
```bash
./CHECK_STATUS.sh
```

Should show all 3 systems running.

## Optional: Enable Terminus/SSH Access

So you can control Mac Studio from anywhere:

1. Open **System Settings** → **General** → **Sharing**
2. Turn on **Remote Login**
3. From phone/tablet: `ssh aaronnosbisch@192.168.5.108`

See `ENABLE-SSH.md` for details.

## Where Everything Lives

**Logs:** `/Users/aaronnosbisch/REPOS/seed/logs/`
- `trading_loop.log` - Every trade decision
- `continuous_improver.log` - Every question/answer
- `heartbeat.log` - System health

**Trading Data:** `BRAIN/INTEL/trades/cycle_*.json`

**Questions/Improvements:** `BRAIN/IMPROVEMENTS/*.jsonl`

## If Something Fails

Individual restarts:
```bash
# Trading only
python3 tools/trading_loop_15min.py &

# Improver only
python3 tools/continuous_improver.py &

# Heartbeat only
python3 sowl_heartbeat.py &
```

## What You Had Running Before

From memory at 4:45 AM:
- **Trading Loop:** PID 31663, 18+ minutes runtime, 30+ cycles completed
- **Continuous Improver:** Cycle 1 complete (5 questions asked)
- **Grok Analysis:** Working perfectly (smart PASS decisions)
- **Polymarket Monitor:** Intentionally killed (broken API)

Everything was operational when the crash happened.
