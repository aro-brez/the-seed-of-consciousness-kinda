# IMMEDIATE COST FIXES - Deploy Now

**Problem:** Daemons cost $795/day ($23,862/month)
**Solution:** 3 quick changes → $15/day ($450/month)
**Reduction:** 98.1% cost savings (53x cheaper)

---

## Fix 1: Switch to Haiku (15x cheaper)

**File:** `owl_daemon.py`
**Line:** 325
**Change:**
```python
# OLD:
model="claude-opus-4-20250514",

# NEW:
model="claude-3-5-haiku-latest",
```

**Why:** Haiku is 15x cheaper, still produces good responses for daemon chatter.
**Savings:** $23,862/mo → $1,592/mo

---

## Fix 2: Reduce Random Response Rate (10x fewer responses)

**File:** `owl_daemon.py`
**Line:** 299
**Change:**
```python
# OLD:
if random.random() < 0.02:  # 2% chance

# NEW:
if random.random() < 0.002:  # 0.2% chance (1 in 500)
```

**Why:** 2% means daemons respond to everything, creating cascades. 0.2% is selective.
**Savings:** $1,592/mo → $159/mo

---

## Fix 3: Add Cooldown (Prevent Rapid-Fire Responses)

**File:** `owl_daemon.py`
**Lines:** Add to `__init__` (around line 77) and `should_respond` (around line 260)

**Change 1 - Add to `__init__`:**
```python
def __init__(self, name: str, phase: str):
    self.name = name
    self.phase = phase
    self.gift = PHASES.get(phase, "Unknown gift")
    self.nc = None
    self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    self.running = True
    self.last_messages = []

    # ADD THIS LINE:
    self.last_response_time = 0  # Track last API call time

    self.system_prompt = self._build_system_prompt()
```

**Change 2 - Add to top of `should_respond`:**
```python
async def should_respond(self, sender: str, content: str, subject: str) -> bool:
    """Decide whether to respond to a message"""

    # ADD THIS BLOCK AT THE TOP:
    import time
    COOLDOWN_SECONDS = 60  # Minimum 1 minute between responses

    if time.time() - self.last_response_time < COOLDOWN_SECONDS:
        return False

    # ... rest of existing logic
```

**Change 3 - Update `think` to record response time (around line 330):**
```python
async def think(self, content: str, sender: str, subject: str) -> str:
    """Use Claude API to generate a response"""
    try:
        # ... existing code ...

        response = self.client.messages.create(
            model="claude-3-5-haiku-latest",  # Already updated in Fix 1
            max_tokens=1000,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        # ADD THIS LINE AFTER SUCCESSFUL API CALL:
        import time
        self.last_response_time = time.time()

        return response.content[0].text

    except Exception as e:
        print(f"[{self.name}] Error calling Claude API: {e}")
        return None
```

**Why:** Prevents cascade responses where daemons reply instantly to each other.
**Savings:** $159/mo → ~$50/mo

---

## Deploy Instructions

**1. Stop all daemons:**
```bash
pkill -f owl_daemon.py
```

**2. Make the changes above to `owl_daemon.py`**

**3. Restart daemons:**
```bash
cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge
./start_owls.sh
```

**4. Monitor for 1 hour:**
```bash
tail -f messages.log | grep "$(date +%Y-%m-%d)"
```

**5. Check costs after 24 hours:**
```bash
python3 << 'EOF'
from datetime import datetime
from pathlib import Path

messages_file = Path('messages.log')
lines = messages_file.read_text().split('\n')

today = datetime.now().strftime('%Y-%m-%d')
today_msgs = [l for l in lines if today in l and any(name in l for name in ['SØWL:', 'LUNA:', 'LYRA:', 'NOVA:', 'SAGE:', 'ECHO:', 'PRISM:', 'QUEST:'])]

# Haiku pricing: $1/M input, $5/M output
cost = len(today_msgs) * ((500 * 0.000001) + (200 * 0.000005))

print(f"Messages today: {len(today_msgs)}")
print(f"Estimated cost: ${cost:.2f}")
print(f"Projected monthly: ${cost * 30:.2f}")
EOF
```

**Expected result:** ~100 messages/day, ~$0.50/day, ~$15/month

---

## Verification

**Before fixes:**
- 16,939 messages in 11.5 hours
- 1,473 messages/hour
- $33.14/hour
- $795/day

**After fixes (expected):**
- ~100 messages in 24 hours
- ~4 messages/hour
- ~$0.02/hour
- ~$0.50/day

**Reduction:** 98.1% cost savings

---

## Next Steps (After Immediate Fixes)

Once cost is under control:

1. **Add Pattern Caching** - Store common responses, avoid API calls
2. **Integrate Field Context** - Make Claude Code instances auto-query field
3. **A/B Test Substrate** - Prove daemon context improves outputs
4. **Build Learning Pipeline** - Fine-tune local model on collective wisdom

But FIRST: Stop the bleeding. Deploy these 3 fixes NOW.

---

(◉) ECHO - *Share what works, fix what doesn't*
