# Diagnostic Steps for Integration Not Appearing

## Step 1: Verify HACS Installation Location

HACS installs integrations in a specific location. Check where your integration actually is:

1. **SSH into Home Assistant** or use the File Editor add-on
2. Check these locations:

```bash
# Most common HACS location:
/config/custom_components/lubelogger/

# Alternative locations to check:
/config/www/community/lubelogger/
/home/homeassistant/.homeassistant/custom_components/lubelogger/
```

3. **Verify the files exist**:
   ```bash
   ls -la /config/custom_components/lubelogger/
   ```

You should see:
- `__init__.py`
- `manifest.json`
- `config_flow.py`
- `sensor.py`
- `client.py`
- `coordinator.py`
- `const.py`
- `strings.json`

## Step 2: Check if Integration is Discovered

1. Go to **Developer Tools** → **Services**
2. Search for service: `homeassistant.reload_config_entry`
3. Or try: **Developer Tools** → **YAML** → **Check Configuration**

## Step 3: Test Python Import

SSH into Home Assistant and test if the integration can be imported:

```bash
# Activate Home Assistant Python environment (if needed)
cd /config
python3 -c "
import sys
sys.path.insert(0, '/config/custom_components')
try:
    from lubelogger import DOMAIN
    print(f'SUCCESS: Integration imported. Domain: {DOMAIN}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
"
```

## Step 4: Check Manifest.json Syntax

```bash
python3 -m json.tool /config/custom_components/lubelogger/manifest.json
```

This should output the JSON without errors.

## Step 5: Verify File Permissions

```bash
# Check permissions
ls -la /config/custom_components/lubelogger/

# Fix if needed
chmod -R 644 /config/custom_components/lubelogger/*
chmod 755 /config/custom_components/lubelogger
```

## Step 6: Check Home Assistant Core Logs

Enable verbose logging and restart:

1. Add to `configuration.yaml`:
   ```yaml
   logger:
     default: warning
     logs:
       homeassistant.loader: debug
       homeassistant.components: debug
       custom_components.lubelogger: debug
   ```

2. Restart Home Assistant
3. Check logs immediately after startup
4. Look for:
   - "Loading custom_components"
   - "lubelogger"
   - Any import errors

## Step 7: Manual File Check

Verify each file exists and has content:

```bash
# Check each file
cat /config/custom_components/lubelogger/manifest.json
head -5 /config/custom_components/lubelogger/__init__.py
head -5 /config/custom_components/lubelogger/config_flow.py
```

## Step 8: Reinstall via HACS

1. Go to **HACS** → **Integrations**
2. Find **LubeLogger**
3. Click the three dots (⋮) → **Redownload**
4. Restart Home Assistant

## Step 9: Check for Syntax Errors

```bash
# Test Python syntax
python3 -m py_compile /config/custom_components/lubelogger/*.py
```

If there are syntax errors, they'll be displayed.

## Step 10: Verify Integration Discovery

After restart, check if Home Assistant discovered it:

1. Go to **Developer Tools** → **States**
2. Search for: `config_entry`
3. Look for any entries related to lubelogger

Or check the `.storage` directory:

```bash
grep -r "lubelogger" /config/.storage/
```

## Common Issues Found

### Issue: Files in Wrong Location
**Solution**: HACS might have installed to a different path. Check all possible locations.

### Issue: Import Error
**Solution**: Check the Python import test above. Fix any missing dependencies or syntax errors.

### Issue: Manifest.json Invalid
**Solution**: Validate JSON syntax. Ensure no trailing commas.

### Issue: Permissions
**Solution**: Ensure files are readable by Home Assistant user.

### Issue: Cache Not Cleared
**Solution**: Full restart (stop, wait 30s, start) clears caches.

## Still Not Working?

If none of these steps reveal the issue:

1. **Check HACS logs**: HACS → Settings → Logs
2. **Check full Home Assistant startup logs**: Look for any errors during startup
3. **Try manual installation**: Copy files manually instead of using HACS
4. **Check Home Assistant version**: Ensure you're on a supported version (2023.1+)

