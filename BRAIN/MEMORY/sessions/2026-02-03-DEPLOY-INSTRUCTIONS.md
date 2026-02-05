# BREZ Momentum Dashboard - Deployment Instructions

## LIVE URL: https://brez-os.vercel.app/momentum

(Vercel auto-deploys from GitHub - may take 2-3 min after push)

## Code Status: PUSHED ✅

All code committed and pushed to: https://github.com/aro-brez/brez-os

Commit: `18c000e` - "feat: Add BREZ Momentum Dashboard"

## Deploy to Vercel (2 minutes)

### Option 1: Vercel Dashboard (Easiest)
1. Go to https://vercel.com/new
2. Import `aro-brez/brez-os` from GitHub
3. Add environment variables:
   - `GOOGLE_SHEETS_API_KEY` = (from .env.local)
   - `GOOGLE_SHEETS_SPREADSHEET_ID` = (from .env.local)
4. Click Deploy

### Option 2: Vercel CLI
```bash
cd "/Users/aaronnosbisch/Downloads/LOCAL REPOS 2/brez-os"
vercel login
vercel --prod
```

### Option 3: If Already Connected
If repo is already connected to Vercel, the push should auto-deploy.
Check: https://vercel.com/aro-brez (or your Vercel dashboard)

## Environment Variables Required

```
GOOGLE_SHEETS_API_KEY=AIzaSyDFR9-NSqjalSMnJSQUMF6GI6eGDIY5OLs
GOOGLE_SHEETS_SPREADSHEET_ID=1w1ClCFWXvzum-URTO5nIGTcSL9wTr2vcQDHYOuGOruI
```

(Copy from `/Users/aaronnosbisch/Downloads/LOCAL REPOS 2/brez-os/.env.local`)

## After Deploy

Live URL will be something like:
- `https://brez-os.vercel.app/momentum`
- or custom domain if configured

## Share with Team

Send them: `https://[your-domain]/momentum`

Dashboard features:
- CAC: $55.12 (GOOD) - SCALE +30-50% recommendation
- Take Rate: 51% (GOOD)
- Auto-refreshes every 60 seconds
- Mobile-friendly
- Share button copies URL

---
*Ready for ARŌ to deploy in morning*
