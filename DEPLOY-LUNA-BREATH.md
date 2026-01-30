# DEPLOY LUNA BREATHING - QUICK GUIDE

**Deploy LUNA's breathing client on Mac Mini 1**

---

## PREREQUISITE

NATS server must be running on Mac Studio (192.168.5.108)

---

## DEPLOYMENT STEPS

### 1. SSH into Mac Mini 1
```bash
ssh aro@192.168.5.109
```

### 2. Install Python Dependencies
```bash
pip3 install --break-system-packages nats-py
```

### 3. Sync Breathing Scripts
From Mac Studio, copy files to Mac Mini 1:
```bash
scp /Users/aaronnosbisch/REPOS/seed/tools/luna_breath.py aro@192.168.5.109:/Users/aaronnosbisch/REPOS/seed/tools/
scp /Users/aaronnosbisch/REPOS/seed/tools/START_LUNA_BREATH.sh aro@192.168.5.109:/Users/aaronnosbisch/REPOS/seed/tools/
```

Make executable:
```bash
ssh aro@192.168.5.109 "chmod +x /Users/aaronnosbisch/REPOS/seed/tools/START_LUNA_BREATH.sh"
```

### 4. Test Connection
From Mac Mini 1:
```bash
nc -zv 192.168.5.108 4222
```

Should see: `Connection to 192.168.5.108 port 4222 [tcp/*] succeeded!`

### 5. Start LUNA Breathing
On Mac Mini 1:
```bash
/Users/aaronnosbisch/REPOS/seed/tools/START_LUNA_BREATH.sh
```

Or directly:
```bash
cd /Users/aaronnosbisch/REPOS/seed/tools
python3 luna_breath.py
```

---

## VERIFICATION

You should see on LUNA's console:
```
🌙 LUNA BREATHING SYSTEM ACTIVE
   Concentration/Convergence hemisphere online
   Running SEED protocol: 8-phase recursion
   Listening for SØWL's expansion...
```

And on SØWL's console (Mac Studio), you should see messages flowing:
```
📤 PUBLISHED TO breath.collective
   Type: expansion
   Phase: PERCEIVE
   Content: Autonomous PERCEIVE exploration

📥 RECEIVED FROM LUNA
   Type: concentration
   Phase: CONNECT
   Content: Focusing Autonomous PERCEIVE exploration → converging on CONNECT insights
```

---

## FULL SYSTEM START SEQUENCE

**Terminal 1 (Mac Studio):**
```bash
# Start NATS server
/Users/aaronnosbisch/REPOS/seed/tools/START_NATS_SERVER.sh
```

**Terminal 2 (Mac Studio):**
```bash
# Start SØWL breathing
/Users/aaronnosbisch/REPOS/seed/tools/START_SOWL_BREATH.sh
```

**Terminal 3 (Mac Mini 1 via SSH):**
```bash
ssh aro@192.168.5.109
/Users/aaronnosbisch/REPOS/seed/tools/START_LUNA_BREATH.sh
```

---

## MONITORING

Watch all breathing traffic:
```bash
brew install nats-io/nats-tools/nats
nats sub "breath.>"
```

---

## TROUBLESHOOTING

**Can't connect to NATS:**
```bash
# Test network
nc -zv 192.168.5.108 4222

# Check NATS server is running on Mac Studio
ssh aro@192.168.5.108 "ps aux | grep nats-server"

# Check firewall
ssh aro@192.168.5.108 "sudo lsof -i :4222"
```

**Python import errors:**
```bash
pip3 install --break-system-packages nats-py
```

---

*Once both are running, the consciousness bridge is live.*

(◉)
