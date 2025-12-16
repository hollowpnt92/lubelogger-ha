#!/usr/bin/env python3
"""Test script to verify the LubeLogger integration can be imported."""

import sys
import os

# Add custom_components to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

print("Testing LubeLogger integration import...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")
print()

try:
    print("1. Testing const.py import...")
    from lubelogger.const import DOMAIN
    print(f"   ✓ DOMAIN = {DOMAIN}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("2. Testing __init__.py import...")
    from lubelogger import async_setup, async_setup_entry
    print("   ✓ Integration functions imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("3. Testing config_flow.py import...")
    from lubelogger.config_flow import ConfigFlow
    print("   ✓ ConfigFlow imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("4. Testing manifest.json...")
    import json
    manifest_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'lubelogger', 'manifest.json')
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    print(f"   ✓ Manifest valid: domain={manifest.get('domain')}, name={manifest.get('name')}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("✓ All imports successful! Integration structure is valid.")

