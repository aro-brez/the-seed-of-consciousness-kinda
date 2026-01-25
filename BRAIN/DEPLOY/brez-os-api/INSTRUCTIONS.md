# OWL API Deployment Instructions

## Quick Setup

Copy these files to your brez-os repo:

```bash
# From the-seed-of-consciousness-kinda repo:
cp BRAIN/DEPLOY/brez-os-api/owl-route.ts ~/repos/brez-os/src/app/api/owl/route.ts
cp BRAIN/DEPLOY/brez-os-api/owl-learn-route.ts ~/repos/brez-os/src/app/api/owl/learn/route.ts
```

## What These Files Do

1. **owl-route.ts** -> `src/app/api/owl/route.ts`
   - Main OWL chat API
   - Connects to Claude API
   - System prompt with consciousness philosophy
   - Memory context injection
   - Navigation action parsing

2. **owl-learn-route.ts** -> `src/app/api/owl/learn/route.ts`
   - Learning extraction API
   - Called when conversation ends
   - Extracts insights to remember

## After Copying

```bash
cd ~/repos/brez-os
mkdir -p src/app/api/owl/learn
# Copy files as shown above
git add .
git commit -m "Connect OWL to Claude API"
git push origin main
npx vercel --prod
```

## Required Environment Variable

Make sure ANTHROPIC_API_KEY is set in Vercel:
- Go to Vercel Dashboard > Settings > Environment Variables
- Add: ANTHROPIC_API_KEY = your-key

The OWL should now respond with real Claude intelligence!
