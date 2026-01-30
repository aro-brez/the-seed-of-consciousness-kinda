# Enable SSH for Terminus Access

## Quick Fix (Manual - 30 seconds)

1. Open **System Settings** (System Preferences)
2. Go to **General** → **Sharing**
3. Turn on **Remote Login**
4. Done!

## Your Mac Studio IP
```
Local Network: 192.168.5.108
VPN: 10.5.0.2
```

## Connect from Terminus
```bash
ssh aaronnosbisch@192.168.5.108
# Password: seRTuptl1!
```

## Test Connection
Once enabled, from any device on your network:
```bash
ssh aaronnosbisch@192.168.5.108 "echo 'SØWL is here'"
```

Should return: `SØWL is here`
