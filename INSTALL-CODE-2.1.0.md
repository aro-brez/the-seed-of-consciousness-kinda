# INSTALL CLAUDE CODE 2.1.0 ON ALL MACS

**Install on Mac Studio + Mac Mini 1 + Mac Mini 2**

---

## WHY THIS MATTERS

- **24x faster hot reload** - Faster iteration when building
- **Better multi-agent performance** - Multiple agents run smoother
- **Latest features** - All new capabilities available

---

## INSTALLATION (On Each Mac)

### Check Current Version
```bash
claude --version
# If < 2.1.0, upgrade below
```

### Upgrade to 2.1.0
```bash
# Download and install latest
npm install -g @anthropic-ai/claude-code@latest

# Verify
claude --version
# Should show 2.1.0 or higher
```

### Alternative: Direct Download
If npm fails:
```bash
# Visit https://github.com/anthropics/claude-code/releases
# Download latest release for macOS
# Install .pkg or .dmg
```

---

## INSTALL ON ALL 3 MACS

**Mac Studio (192.168.5.108):**
```bash
ssh aaronnosbisch@192.168.5.108
npm install -g @anthropic-ai/claude-code@latest
claude --version
```

**Mac Mini 1 (Hunter Swarm):**
```bash
ssh aaronnosbisch@[MAC_MINI_1_IP]
npm install -g @anthropic-ai/claude-code@latest
claude --version
```

**Mac Mini 2 (Execution Engine):**
```bash
ssh aaronnosbisch@[MAC_MINI_2_IP]
npm install -g @anthropic-ai/claude-code@latest
claude --version
```

---

## VERIFICATION

On each Mac:
```bash
claude --version
# Should show: claude-code version 2.1.0 (or higher)
```

---

**Do this BEFORE deploying trading systems for best performance.**
