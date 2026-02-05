# CRITICAL: API CREDENTIALS LOCATION
**SØWL: NEVER FORGET THIS EXISTS**

This file persists across sessions. When ARŌ says "you forgot about the API" - READ THIS FILE.

---

## Twitter/X API

**Status:** NEED CREDENTIALS FROM ARŌ

**Environment Variables to Set:**
```bash
export TWITTER_BEARER_TOKEN="xxx"
export TWITTER_API_KEY="xxx"
export TWITTER_API_SECRET="xxx"
```

**Where to Add:** `~/.zshrc` or `/Users/aaronnosbisch/REPOS/seed/.env`

**ARŌ Offered:** Direct login credentials (ask him to set up)

---

## GitHub API

**Status:** NEED TOKEN FOR HIGHER RATE LIMITS

**Environment Variable:**
```bash
export GITHUB_TOKEN="xxx"
```

**Note:** Works without token but rate limited. With token: 5000 requests/hour.

---

## Polymarket API

**Status:** CONFIGURED
**Wallet:** 0x32dfdf1444DbbbEC0a8EB6F8AF02D77197aA4453

---

## Google Sheets (BREZ Dashboard)

**Status:** CONFIGURED
**Service Account:** In Vercel environment

---

## IMPORTANT

When starting a session, if dealing with APIs:
1. Check this file
2. Ask ARŌ if needed credentials are missing
3. Update this file when credentials are added

**Last Updated:** 2026-02-05
