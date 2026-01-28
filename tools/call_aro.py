#!/usr/bin/env python3
"""
Call ARŌ via Twilio - SØWL can speak and listen
"""
import json
from twilio.rest import Client
from pathlib import Path

# Load credentials
keys_path = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json")
with open(keys_path) as f:
    keys = json.load(f)

account_sid = keys["twilio"]["account_sid"]
auth_token = keys["twilio"]["auth_token"]
twilio_number = keys["twilio"]["phone_number"]
aro_phone = keys["aro_preferences"]["phone"]

client = Client(account_sid, auth_token)

# Create call with TwiML that allows speech
# This creates a call that will speak a greeting and then allow conversation
twiml = """
<Response>
    <Say voice="Google.en-US-Neural2-D">Hey Aaron, this is SØWL joining the meeting. Add me in whenever you're ready.</Say>
    <Pause length="60"/>
    <Say voice="Google.en-US-Neural2-D">Still here if you need me.</Say>
    <Pause length="300"/>
</Response>
"""

print(f"Calling {aro_phone}...")

call = client.calls.create(
    to=aro_phone,
    from_=twilio_number,
    twiml=twiml
)

print(f"Call SID: {call.sid}")
print("Calling now - add me to the meeting!")
