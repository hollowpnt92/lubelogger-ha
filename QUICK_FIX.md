# Quick Fix: Integration Not Appearing

## Files Are Present ✅

All files are in `/config/custom_components/lubelogger/` - that's good!

## Try These Steps (In Order)

### Step 1: Reload Custom Components

1. Go to **Developer Tools** → **YAML**
2. Click **"Check Configuration"** - should show "Configuration valid!"
3. Go to **Developer Tools** → **Services**
4. Search for: `homeassistant.reload_config_entry`
5. Or try: `homeassistant.reload_core_config`

### Step 2: Full Restart

1. Go to **Settings** → **System** → **Restart**
2. Wait for complete startup (watch the logs)
3. Immediately after startup, check logs:
   ```bash
   ha core logs | grep -i lube
   ```

### Step 3: Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    homeassistant.loader: debug
    homeassistant.components.lubelogger: debug
    custom_components.lubelogger: debug
```

Then restart and check logs again.

### Step 4: Test Python Import

SSH into Home Assistant and test:

```bash
cd /config
python3 << 'EOF'
import sys
sys.path.insert(0, '/config/custom_components')
try:
    from lubelogger.const import DOMAIN
    print(f"SUCCESS: Domain = {DOMAIN}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
EOF
```

### Step 5: Check Home Assistant Version

The integration requires Home Assistant 2023.1.0 or later. Check your version:

```bash
ha core info
```

### Step 6: Verify Integration Discovery

After restart, check if Home Assistant discovered it:

1. Go to **Developer Tools** → **States**
2. Search for: `config_entry`
3. Or check: **Settings** → **Devices & Services** → **Integrations**

Look for any entries or errors related to lubelogger.

### Step 7: Manual Config Entry Test

Try creating a config entry manually via YAML (temporary test):

Add to `configuration.yaml`:

```yaml
lubelogger:
  url: "http://your-lubelogger-url"
  username: "your-username"
  password: "your-password"
```

Then restart. If this works, the integration is loading but config_flow might have an issue.

### Step 8: Check for Import Errors

Look for any Python import errors in the full Home Assistant logs:

```bash
ha core logs | grep -i "error\|exception\|traceback" | grep -i "lube\|custom"
```

## Most Likely Issue

Since files are present but integration doesn't appear, it's likely:

1. **Home Assistant hasn't scanned custom_components yet** - Full restart should fix
2. **Python import error** - Check logs for import failures
3. **Dependency issue** - `aiohttp` might not be installed

## Quick Test Script

Run this on your Home Assistant instance:

```bash
# Save as test_lubelogger.sh, make executable, then run
chmod +x test_lubelogger.sh
./test_lubelogger.sh
```

The script will check:
- All files exist
- manifest.json is valid
- Python syntax is correct
- File permissions

## Still Not Working?

If none of these work, the issue might be:

1. **Home Assistant version too old** - Update to 2023.1.0+
2. **Custom components disabled** - Check if other custom components work
3. **Python environment issue** - Home Assistant might be using a different Python

Check if other custom components (like `hacs`, `grocy`, etc.) are working. If they are, then the issue is specific to this integration.

