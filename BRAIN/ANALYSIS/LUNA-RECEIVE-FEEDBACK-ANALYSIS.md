# LUNA (RECEIVE) - BREZ Momentum Dashboard Feedback Loop Analysis

**Researcher:** LUNA (RECEIVE Phase)
**Date:** February 5, 2026
**Status:** Complete Analysis
**Overall Grade:** C- (Strong data freshness, zero feedback mechanisms)

---

## Executive Summary

The BREZ Momentum Dashboard is **excellent at receiving live data** (A grade) but **terrible at receiving user feedback** (F grade). The system has a one-way pipeline: Google Sheets → API → Frontend Display. There is no path for user corrections, collaboration, or feedback to flow back.

### Key Findings:

| Category | Grade | Status |
|----------|-------|--------|
| **Refresh/Update** | A | Smart backoff, live mode, excellent stale handling |
| **Data Freshness** | A- | 5-12,000ms to 12 hours, smart caching |
| **User Controls** | C | Only refresh interval and share, no customization |
| **Data Input** | F | Zero forms, zero input fields |
| **Error Communication** | C- | Basic error messages, no rate limit notification |
| **Feedback Mechanisms** | F | No comments, no anomaly flagging, no surveys |
| **Write-Back Capability** | C- | Endpoint exists but unused |
| **Validation** | D | Minimal - accepts any metrics from API |
| **Collaboration** | F | Zero team features |

---

## 1. How Dashboard RECEIVES User Feedback

### Currently Available:
1. **Refresh Button** - Manual data refresh (resets backoff to 0)
2. **Live Mode Toggle** - 5-second refresh cycle (pulsing red button)
3. **Share Button** - Copy link to clipboard
4. **CAC Scale** - Select spend scenarios (view-only, no save)

### Missing Entirely:
- No inline comments or annotations
- No metric flagging ("this seems wrong")
- No data correction forms
- No anomaly reporting
- No team collaboration layer
- No feedback surveys
- No "contact support" option

---

## 2. Smart Refresh Mechanism (The Good Part)

### Intelligent Backoff Algorithm:

```
Initial: 15 seconds
Step 1:  15 seconds (no change → increase backoff)
Step 2:  30 seconds
Step 3:  60 seconds
Step 4:  5 minutes
Step 5:  15 minutes
Step 6:  1 hour
Step 7:  12 hours (max)
```

**Change Detection:** Hashes yesterday + today + pacing data
- If data changed → reset to 15s (fast polling)
- If no change → increase backoff (slower polling)
- User toggles Live Mode → 5 seconds (fastest)

**Key Properties:**
- Jitter: Adds 0-500ms random delay (prevents thundering herd)
- Rate Limiting: Detects 529 errors, exponential backoff (1s → 2s → 4s → max 30s)
- Stale Threshold: 5 minutes (warning shows if no update for 5 min)

### Manual Refresh Mechanisms:
- Error state "Try Again" button
- MomentumHero refresh icon
- Stale data warning "Retry" button
- Live Mode toggle on

---

## 3. Error Communication

### What Users See:

**Loading:** Bouncing dots + "Loading BREZ Momentum..."

**Error (No Metrics):**
```
⚠️ Unable to Load Data
[Error message from API]
[Try Again] button
```

**Stale Data (Has Metrics):**
```
⚠️ Using cached data • Connection issue
[Retry]
```

**Success:**
```
Last updated: 2:45 PM
Next refresh in 15s
Google Sheets - Forecast Sheet
```

### What's Missing:
- No rate limit notifications (just silently retries)
- No data validation errors
- No error logging/tracking
- No "contact support" links
- No error codes for reference

---

## 4. Stale Data Handling

### Detection Logic:
```javascript
isStale = Boolean(
  error &&                              // AND has connection error
  metrics &&                            // AND we have old metrics
  lastUpdated &&                        // AND we know when
  (Date.now() - lastUpdated < 5 min)   // AND less than 5 minutes old
)
```

### Timeline:
- **T=0s:** Fresh data ✅
- **T=5s-15s:** Polling continues
- **T=5m:** No connection → show yellow warning ⚠️
- **T=5m+1s:** Keep showing old metrics (don't go blank)
- **T=5m+2m:** Keep warning until connection restored
- **T=12h+:** Max backoff reached, still polling

### Scenarios:
| Scenario | Behavior | Grade |
|----------|----------|-------|
| Network flaky | Shows stale warning | A |
| Switch tabs | Still polling | A |
| Backend down | Shows old data | A |
| Sheet edited elsewhere | Polling continues (might miss major changes) | B |
| Rate limited | Retries silently (user doesn't know) | C |

---

## 5. User Input Control

### What Users CAN Control:
- Toggle Live Mode (5s) vs Standard (15s+)
- Click refresh manually
- Choose spend scenario (view-only)
- Share dashboard link

### What Users CANNOT Control:
- Data source (always Forecast Sheet)
- Metrics to display
- Refresh rate (preset only)
- Alert thresholds
- Date ranges
- Historical comparisons
- Export format

### Data Input:
**Currently: ZERO forms**

To affect dashboard data, user must:
1. Edit Google Sheets directly
2. Wait for next auto-refresh
3. Or click refresh

---

## 6. API/Data Input Analysis

### Data Sources:
```
Google Sheets API (Read-Only)
├─ Forecast Sheet - February
├─ Columns: K (Spend), N (Sales), Q (Subs)
├─ Computed: CAC, Take Rate, Pacing, Status
└─ Updates every 15-12,000ms based on backoff
```

### Write Capability Exists But Unused:
```
POST /api/metrics/sheet/edit
{
  action: "update" | "batch" | "read",
  range: "CALCULATOR!B55",
  value: 120
}
```

**Could Enable:**
- Save spend scenarios
- Daily actuals input forms
- User corrections with timestamps
- Audit trail logging

**Currently:** Never called from frontend

### Input Validation:
- Checks `response.ok`
- Checks `data.success` flag
- Checks `data.metrics` exists
- **Missing:** Type validation, negative number checks, range validation

---

## 7. Critical Gaps

### 1. No Feedback Loop
```
Google Sheets → API → Frontend ✅
Frontend → API → Google Sheets ❌
```

### 2. Read-Only Dashboard
- Users see data but can't correct it
- Can't add notes or context
- Can't flag anomalies
- Can't override bad values

### 3. No Collaboration
- No comments on metrics
- No team notes
- No shared context
- No anomaly discussions

### 4. No Audit Trail
- Don't know who changed data
- Can't track edits
- No recovery/rollback
- No change history

### 5. No Validation
- Accept any metric from API
- No error detection
- No quality checks
- No sanity bounds

---

## 8. Recommendations for LUNA (RECEIVE Enhancement)

### Priority 1: Enable Write-Back
```
Component: FeedbackForm
├─ "Report data discrepancy"
├─ "Flag metric anomaly"
├─ "Request urgent update"
└─ Save to Sheets + publish to NATS
```

### Priority 2: Data Validation
```
Use Zod schemas:
├─ MetricValidator (CAC > 0, subs > 0)
├─ RangeValidator (CAC < 200, subs < 10k)
└─ Show validation errors to user
```

### Priority 3: Audit Trail
```
Log each change:
├─ Who (user ID)
├─ What (metric name)
├─ When (timestamp)
├─ Old value → new value
└─ Reason (if provided)
```

### Priority 4: Collaboration Features
```
Team inputs:
├─ Comments on metrics
├─ Anomaly flags
├─ Context notes
└─ Publish to collective via NATS
```

### Priority 5: Better Error Communication
```
Show users:
├─ Rate limit status
├─ Data freshness
├─ Why data might be stale
└─ Specific recovery actions
```

---

## 9. Integration with 8OWLS System

### Current Data Flow:
```
Google Sheets (Source)
    ↓
/api/metrics/sheet (read)
    ↓
useGrowthData (fetch + backoff)
    ↓
MomentumDashboard (display)
    ↓
User sees data
    ↓
❌ Dead end
```

### Proposed Enhancement:
```
Google Sheets (Source)
    ↓
/api/metrics/sheet (read)
    ↓
useGrowthData (fetch + backoff)
    ↓
MomentumDashboard (display)
    ↓
User gives feedback/corrections
    ↓
FeedbackForm
    ↓
NATS publish → Collective
    ↓
/api/metrics/sheet/edit (write)
    ↓
Google Sheets (updated with user input)
    ↓
Audit log in database
```

---

## 10. Summary Assessment

### Strengths:
✅ Intelligent backoff (prevents wasted polling)
✅ Live mode (user can request fast updates)
✅ Stale data fallback (shows old data, doesn't go blank)
✅ Rate limit handling (exponential backoff)
✅ Jitter implementation (prevents thundering herd)
✅ Manual refresh always available

### Critical Gaps:
❌ No user input → no feedback loop
❌ No data validation → accepts bad data
❌ No comments/notes → no collaboration
❌ No audit trail → can't track changes
❌ No write-back → changes can't be saved
❌ No error tracking → silent failures
❌ No user preferences → can't customize

### Overall Grade: C-

The BREZ Momentum Dashboard is a **read-only display** with excellent data freshness mechanics but zero feedback/input mechanisms. It's like a beautiful dashboard nailed to the wall - you can see it but can't interact with it meaningfully.

**Next Step:** Enable write-back to Google Sheets so dashboard becomes a true operational tool, not just a visualization.

---

## Files Referenced

- `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-os/src/app/momentum/page.tsx` - Main dashboard
- `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-os/src/lib/hooks/useGrowthData.ts` - Data fetching with backoff
- `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-os/src/app/api/metrics/sheet/route.ts` - Data API
- `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-os/src/app/api/metrics/sheet/edit/route.ts` - Write endpoint (unused)
- `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-os/src/components/growth/` - UI components

---

**Research Completed By LUNA (RECEIVE Phase)**
**Published to collective via NATS**
**Part of 8OWLS Collective Intelligence Framework**
