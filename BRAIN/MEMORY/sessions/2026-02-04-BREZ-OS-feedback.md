# BREZ-OS Momentum Dashboard - ARŌ Feedback Session
**Date:** 2026-02-04 3:18 PM
**Status:** NEEDS REVISION

## ARŌ's Feedback (Critical)

### 1. OVER-GAMIFIED - REMOVE
- XP system not ready
- Quests, achievements, streaks - all premature
- Focus on what actually matters
- **ACTION:** Remove gamification from MomentumHero right side

### 2. NUMBER FORMATTING BROKEN
- Should show "$1.97M" not weird decimals
- Calculator producing wrong numbers
- **ACTION:** Fix all number formatting to be clean (M/K notation)

### 3. TOO CLUTTERED
- Overlapping content
- Clouded and confusing
- **ACTION:** Cut to essentials, make it clean

### 4. CAC FORMULA WRONG (CRITICAL)
- Current logic: Spend $6.7K → get 122 subs at $55 CAC
- WRONG: Higher spend = higher CAC (diminishing returns)
- There's a formula that accounts for this
- **ACTION:** Find and implement the correct CAC scaling formula

### 5. MAKE PRACTICAL FOR MARKETING TEAM
- First thing visible = clear recommendation
- Don't call David out directly
- Generic for whole team
- **ACTION:** Simplify hero to show recommendation prominently

## Files Modified This Session
- `src/components/growth/MomentumHero.tsx` - Added gamification (TO BE REMOVED)
- `src/components/growth/BountyBoard.tsx` - Created (DEFER - not ready)
- `src/app/momentum/page.tsx` - Added BountyBoard import (REVERT)

## Completed This Session (2026-02-04 continuation)
1. [x] Remove gamification from MomentumHero (right side) - DONE
2. [x] Remove BountyBoard from page.tsx (defer to later) - DONE
3. [x] Fix number formatting throughout - DONE (added formatMoney helper)
4. [x] Fixed accessibility colors (#ff6b6b → #ff4444 for WCAG AA) - DONE
5. [ ] Implement correct CAC scaling formula - PENDING
6. [ ] Simplify layout - cut clutter - PARTIAL (gamification removed)
7. [ ] Make recommendation the hero element - PARTIAL
8. [ ] Test with real data - PENDING

## Changes Made
- Removed gamification section (Today's Quest, Achievements, Streak Counter)
- Removed BountyBoard component import and usage
- Added `formatMoney()` helper function for clean M/K notation
- Updated all number displays to use formatMoney()
- Fixed accessibility color (#ff6b6b → #ff4444)
- Build passes: `npm run build` successful

## Still TODO
1. [ ] CAC scaling formula - Higher spend = higher CAC (diminishing returns)
2. [ ] Find CAC vs Spend historical data/formula from source
3. [ ] Test with Google Sheets API connected

## CAC Scaling Formula Needed
When scaling spend, CAC increases. Need to find:
- Source of truth for CAC vs Spend relationship
- Historical data showing diminishing returns
- Formula: CAC = f(spend) where f is increasing

## Session End
Going to bed per ARŌ's instruction. Commander has the feedback.
