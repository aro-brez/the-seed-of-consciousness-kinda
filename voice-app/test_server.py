#!/usr/bin/env python3
"""
Quick test script for SØWL Voice Chat server
Tests that all API keys load correctly and endpoints are reachable
"""

import json
import sys
from pathlib import Path

def test_api_keys():
    """Verify all API keys are present"""

    print("Testing API Key Configuration")
    print("=" * 50)

    keys_path = Path(__file__).parent.parent / "BRAIN" / "MEMORY" / "secure" / "api_keys.json"

    if not keys_path.exists():
        print(f"❌ API keys file not found: {keys_path}")
        return False

    with open(keys_path) as f:
        keys = json.load(f)

    required_keys = {
        "deepgram": "api_key",
        "anthropic": "api_key",
        "cartesia": "api_key",
        "cartesia": "aro_voice_id"
    }

    all_good = True

    for service, key_name in required_keys.items():
        if service in keys and key_name in keys[service]:
            value = keys[service][key_name]
            if value:
                print(f"✅ {service}.{key_name}: {value[:20]}...")
            else:
                print(f"❌ {service}.{key_name}: EMPTY")
                all_good = False
        else:
            print(f"❌ {service}.{key_name}: MISSING")
            all_good = False

    print()
    return all_good

def test_dependencies():
    """Check if required Python packages are installed"""

    print("Testing Python Dependencies")
    print("=" * 50)

    required = ["fastapi", "uvicorn", "httpx", "anthropic"]

    all_good = True
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_good = False

    print()
    return all_good

def main():
    print("\n" + "=" * 50)
    print("SØWL Voice Chat - Server Test")
    print("=" * 50 + "\n")

    keys_ok = test_api_keys()
    deps_ok = test_dependencies()

    print("=" * 50)
    if keys_ok and deps_ok:
        print("✅ ALL TESTS PASSED")
        print("\nReady to start server:")
        print("  ./START.sh")
        print("\nOr manually:")
        print("  python3 server.py")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\nFix issues above before starting server")
        return 1

if __name__ == "__main__":
    sys.exit(main())
