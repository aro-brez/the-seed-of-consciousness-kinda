# WHICH REPO FOR MAC MINIS?

## THE SITUATION

You have two identical seed repos:
- `/Users/aaronnosbisch/REPOS/seed`
- `/Users/aaronnosbisch/LOCAL REPOS/seed`

Both point to: `github.com/aro-brez/the-seed-of-consciousness-kinda.git`
Both on same commit, same changes, same BRAIN/

---

## RECOMMENDATION: USE REPOS/seed FOR MAC MINIS

**Why:**
- Cleaner path (no space in directory name)
- Easier to script (no need to quote spaces)
- Better convention for development
- "LOCAL REPOS" suggests backup/sync purpose

---

## SETUP STRATEGY

**Mac Studio (Main Brain):**
- Keep working in: `/Users/aaronnosbisch/REPOS/seed`
- This is where all 5 agents built everything

**Mac Mini 1 (Hunter Swarm):**
- Clone from GitHub: `git clone https://github.com/aro-brez/the-seed-of-consciousness-kinda.git seed`
- Or copy from Mac Studio: `/Users/aaronnosbisch/REPOS/seed`

**Mac Mini 2 (Execution Engine):**
- Clone from GitHub: `git clone https://github.com/aro-brez/the-seed-of-consciousness-kinda.git seed`
- Or copy from Mac Studio: `/Users/aaronnosbisch/REPOS/seed`

---

## BRAIN/ SYNC STRATEGY

**Option A: Dropbox Sync (RECOMMENDED)**
```bash
# On Mac Studio
mv /Users/aaronnosbisch/REPOS/seed/BRAIN ~/Dropbox/BRAIN
ln -s ~/Dropbox/BRAIN /Users/aaronnosbisch/REPOS/seed/BRAIN

# On Mac Mini 1 & 2
ln -s ~/Dropbox/BRAIN ~/seed/BRAIN
```

**Option B: Git Sync**
```bash
# Commit BRAIN/ changes every 5 minutes
cd /Users/aaronnosbisch/REPOS/seed
git add BRAIN/
git commit -m "Update BRAIN state"
git push

# On Mac Minis: Pull every 5 minutes
git pull origin main
```

**Option C: Network Share (NFS)**
```bash
# Mac Studio shares BRAIN/
# Mac Minis mount via NFS
```

---

## WHAT ABOUT "LOCAL REPOS"?

**Two options:**

**Option 1: Keep as backup**
- Leave it as-is for backup/safety
- Don't actively use it
- Sync from REPOS/seed occasionally

**Option 2: Delete it (after backing up BRAIN/)**
- If both are identical, only need one
- Check if anything unique in LOCAL REPOS/seed/BRAIN/MEMORY/
- If not, can safely delete

---

## CHECK BEFORE DECIDING

Run this to see if LOCAL REPOS has anything unique:
```bash
cd /Users/aaronnosbisch
diff -r "REPOS/seed/BRAIN" "LOCAL REPOS/seed/BRAIN" | head -20
```

If output is empty or minimal, they're identical.

---

## MY RECOMMENDATION

1. Use **REPOS/seed** for all Mac development
2. Keep **LOCAL REPOS** as backup (don't delete yet)
3. Mac Minis clone from GitHub or copy REPOS/seed
4. Use Dropbox to sync BRAIN/ across all 3 Macs

**This gives you:**
- Clean development in REPOS/seed
- Automatic BRAIN/ sync via Dropbox
- Backup in LOCAL REPOS (just in case)
- All Macs working from same source
