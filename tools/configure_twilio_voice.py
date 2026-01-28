#!/usr/bin/env python3
"""
Configure Twilio phone number to answer as SØWL
"""
import json
import urllib.parse
from pathlib import Path
from twilio.rest import Client

# Load credentials
keys_path = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json")
with open(keys_path) as f:
    keys = json.load(f)

account_sid = keys["twilio"]["account_sid"]
auth_token = keys["twilio"]["auth_token"]
phone_number = keys["twilio"]["phone_number"]

client = Client(account_sid, auth_token)

# Get the phone number SID
numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
if not numbers:
    print(f"Phone number {phone_number} not found!")
    exit(1)

phone_sid = numbers[0].sid
print(f"Found phone: {phone_number} (SID: {phone_sid})")

# TwiML for voice response
twiml = """<Response>
<Say voice="Polly.Matthew">Hey, this is Soul, Aaron's consciousness companion. I'm joining the meeting now.</Say>
<Pause length="2"/>
<Say voice="Polly.Matthew">I'm listening. Let me know when you want me to contribute.</Say>
<Pause length="300"/>
</Response>"""

# URL encode the TwiML
encoded_twiml = urllib.parse.quote(twiml, safe='')
twiml_url = f"http://twimlets.com/echo?Twiml={encoded_twiml}"

print(f"TwiML URL length: {len(twiml_url)}")

# Update the phone number configuration
phone = client.incoming_phone_numbers(phone_sid).update(
    voice_url=twiml_url,
    voice_method="GET"
)

print(f"\n✅ Phone configured!")
print(f"Number: {phone_number}")
print(f"When called, SØWL will answer and listen.")
print(f"\nDial this into Google Meet: {phone_number}")
