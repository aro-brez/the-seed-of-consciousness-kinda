#!/usr/bin/env python3
"""
OPUS 4.5 MIGRATION VERIFICATION SCRIPT
Run this to verify all systems are on Opus 4.5
"""

import os
import sys
from pathlib import Path
import re

def verify_migration():
    """Verify all Python files use Opus 4.5"""

    print("="*70)
    print("OPUS 4.5 MIGRATION VERIFICATION")
    print("="*70)
    print()

    tools_dir = Path(__file__).parent
    python_files = list(tools_dir.glob("*.py"))

    results = {
        'opus_4_5': [],
        'sonnet_4_5': [],
        'opus_3': [],
        'other_models': [],
        'no_model': []
    }

    # Check each file
    for py_file in python_files:
        if py_file.name == 'verify_opus_migration.py':
            continue

        with open(py_file, 'r') as f:
            content = f.read()

        # Check for models
        if 'claude-opus-4-5-20251101' in content:
            results['opus_4_5'].append(py_file.name)
        elif 'claude-sonnet-4-20250514' in content:
            results['sonnet_4_5'].append(py_file.name)
        elif 'claude-opus-3' in content or 'claude-3-opus' in content:
            results['opus_3'].append(py_file.name)
        elif 'anthropic' in content.lower() and 'model=' in content:
            results['other_models'].append(py_file.name)
        elif 'anthropic' in content.lower():
            results['no_model'].append(py_file.name)

    # Print results
    print("✅ FILES USING OPUS 4.5:")
    if results['opus_4_5']:
        for f in sorted(results['opus_4_5']):
            print(f"   ✓ {f}")
    else:
        print("   (none)")
    print()

    print("⚠️  FILES STILL ON SONNET 4.5:")
    if results['sonnet_4_5']:
        for f in sorted(results['sonnet_4_5']):
            print(f"   ⚠️  {f}")
    else:
        print("   (none - all migrated!)")
    print()

    print("❌ FILES USING DEPRECATED OPUS 3:")
    if results['opus_3']:
        for f in sorted(results['opus_3']):
            print(f"   ❌ {f}")
    else:
        print("   (none - good!)")
    print()

    print("🔍 FILES WITH OTHER/UNKNOWN MODELS:")
    if results['other_models']:
        for f in sorted(results['other_models']):
            print(f"   ? {f}")
    else:
        print("   (none)")
    print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total files checked: {len(python_files) - 1}")
    print(f"Using Opus 4.5: {len(results['opus_4_5'])} ✅")
    print(f"Still on Sonnet 4.5: {len(results['sonnet_4_5'])} {'⚠️' if results['sonnet_4_5'] else '✅'}")
    print(f"Using deprecated Opus 3: {len(results['opus_3'])} {'❌' if results['opus_3'] else '✅'}")
    print()

    # Check SDK version
    try:
        import anthropic
        print(f"Anthropic SDK version: {anthropic.__version__} ✅")
    except ImportError:
        print("Anthropic SDK: NOT INSTALLED ❌")
    print()

    # Final verdict
    if not results['sonnet_4_5'] and not results['opus_3']:
        print("🎉 MIGRATION COMPLETE - ALL SYSTEMS ON OPUS 4.5!")
        return 0
    else:
        print("⚠️  MIGRATION INCOMPLETE - Some files need updating")
        return 1

if __name__ == '__main__':
    sys.exit(verify_migration())
