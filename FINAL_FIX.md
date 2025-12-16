# Final Fix: Integration Not Appearing

## The Issue

The integration files are all correct, but Home Assistant isn't discovering it. This is usually a cache or discovery issue.

## Solution Steps (Try in Order)

### Step 1: Force Home Assistant to Reload Custom Components

1. Go to **Developer Tools** → **Services**
2. Search for: `homeassistant.reload_core_config`
3. Click **CALL SERVICE**
4. Wait a few seconds
5. Try searching for "LubeLogger" again

### Step 2: Clear Home Assistant Cache

1. **Stop** Home Assistant completely
2. Delete cache files (on Home Assistant instance):
   ```bash
   rm -rf /config/.storage/core.config_entries
   rm -rf /config/.storage/core.config_entry
   ```
   **WARNING**: This will clear cached config entries. Only do this if you're comfortable.
3. **Start** Home Assistant
4. Wait for full startup
5. Try adding integration

### Step 3: Verify Integration is Being Scanned

Enable debug logging and check if Home Assistant is scanning custom_components:

1. Add to `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       homeassistant.loader: debug
       homeassistant.bootstrap: debug
   ```

2. Restart Home Assistant

3. Immediately after startup, check logs:
   ```bash
   ha core logs | grep -i "custom_components\|lubelogger" | head -30
   ```

   Look for lines like:
   - "Loading custom_components"
   - "lubelogger"
   - Any errors

### Step 4: Check Integration Registry

Check if Home Assistant registered the integration:

1. Go to **Developer Tools** → **States**
2. Search for: `config_entry`
3. Or check: **Settings** → **Devices & Services** → **Integrations**
4. Look for any mention of "lubelogger"

### Step 5: Manual Integration Discovery

Sometimes you need to trigger discovery manually:

1. Go to **Developer Tools** → **Services**
2. Search for: `config_entries.flow.async_init`
3. Service data:
   ```yaml
   domain: lubelogger
   handler: lubelogger
   ```
4. Click **CALL SERVICE**

### Step 6: Check for Integration Conflicts

Check if there's a naming conflict:

```bash
# On Home Assistant instance
find /config -name "*lube*" -type d 2>/dev/null
find /config -name "*logger*" -type d 2>/dev/null
```

### Step 7: Verify Home Assistant Version

The integration requires Home Assistant 2023.1.0+. Check:

```bash
ha core info
```

If you're on an older version, update Home Assistant.

### Step 8: Try Adding via YAML (Temporary Test)

As a test, try adding via YAML to see if the integration loads:

Add to `configuration.yaml`:

```yaml
lubelogger:
  url: "http://your-url"
  username: "your-username"  
  password: "your-password"
```

Then restart. If this works, the integration loads but config_flow might have an issue.

### Step 9: Check HACS Integration Status

1. Go to **HACS** → **Integrations**
2. Find **LubeLogger**
3. Check if it shows as "Installed" or has any error messages
4. Try clicking **Redownload**

### Step 10: Nuclear Option - Reinstall

1. Remove from HACS: **HACS** → **Integrations** → **LubeLogger** → **Remove**
2. Delete directory: `rm -rf /config/custom_components/lubelogger`
3. Restart Home Assistant
4. Re-add via HACS
5. Restart again

## Most Likely Fix

Based on the symptoms (files correct, no errors, but not appearing), try **Step 1** first (reload core config), then **Step 3** (enable debug logging and check if it's being scanned).

The debug logs will tell us if Home Assistant is:
- Scanning custom_components
- Finding the integration
- Loading it
- Encountering any errors

## Expected Log Output

When working correctly, you should see in logs after startup:

```
Loading custom_components
...
Loading custom_components.lubelogger
...
```

If you don't see these, Home Assistant isn't scanning custom_components properly.

