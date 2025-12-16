# Fix Empty Directory Issue

## Problem
The `/config/custom_components/lubelogger/` directory exists but appears to be empty or missing files.

## Solution Steps

### Step 1: Verify What's Actually in the Directory

Run this command on your Home Assistant instance:

```bash
ls -la /config/custom_components/lubelogger/
```

You should see these files:
- `__init__.py`
- `manifest.json`
- `config_flow.py`
- `sensor.py`
- `client.py`
- `coordinator.py`
- `const.py`
- `strings.json`

### Step 2: If Directory is Empty or Missing Files

HACS may have failed to download the files properly. Try one of these solutions:

#### Option A: Re-download via HACS

1. Go to **HACS** → **Integrations**
2. Find **LubeLogger**
3. Click the three dots (⋮) → **Remove**
4. Restart Home Assistant
5. Go back to **HACS** → **Integrations** → **Custom repositories**
6. Add the repository again
7. Download **LubeLogger** again
8. Restart Home Assistant

#### Option B: Manual Copy (Recommended for Testing)

1. **Download the integration files** from your repository
2. **Copy all files** to the directory:

```bash
# On your Home Assistant instance, create the directory if needed
mkdir -p /config/custom_components/lubelogger

# Copy all files (you'll need to do this from your local machine or via SCP)
# The files should be:
# - __init__.py
# - manifest.json
# - config_flow.py
# - sensor.py
# - client.py
# - coordinator.py
# - const.py
# - strings.json
```

#### Option C: Use File Editor Add-on

1. Install **File Editor** add-on if you haven't
2. Navigate to `/config/custom_components/lubelogger/`
3. Create each file manually or upload them
4. Ensure all 8 files are present

### Step 3: Verify File Permissions

After copying files, set correct permissions:

```bash
chmod -R 644 /config/custom_components/lubelogger/*
chmod 755 /config/custom_components/lubelogger
chown -R root:root /config/custom_components/lubelogger
```

### Step 4: Verify Files Are Valid

Check that manifest.json is valid:

```bash
python3 -m json.tool /config/custom_components/lubelogger/manifest.json
```

### Step 5: Restart Home Assistant

After ensuring all files are in place:

1. **Full restart** (not just reload)
2. Wait for complete startup
3. Check logs: `ha core logs | grep -i lube`
4. Try adding the integration again

### Step 6: Check HACS Installation Location

Sometimes HACS installs to a different location. Check:

```bash
# Check HACS community directory
ls -la /config/www/community/

# Search for lubelogger anywhere
find /config -name "lubelogger" -type d 2>/dev/null
```

If files are in `/config/www/community/lubelogger/`, copy them:

```bash
cp -r /config/www/community/lubelogger/* /config/custom_components/lubelogger/
```

## Quick Fix Script

If you have SSH access, you can verify and fix in one go:

```bash
#!/bin/bash
INTEGRATION_DIR="/config/custom_components/lubelogger"

echo "Checking integration directory..."
if [ ! -d "$INTEGRATION_DIR" ]; then
    echo "Creating directory..."
    mkdir -p "$INTEGRATION_DIR"
fi

echo "Files in directory:"
ls -la "$INTEGRATION_DIR"

echo ""
echo "Required files:"
REQUIRED_FILES=("__init__.py" "manifest.json" "config_flow.py" "sensor.py" "client.py" "coordinator.py" "const.py" "strings.json")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$INTEGRATION_DIR/$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file MISSING"
    fi
done
```

Save this as `check_integration.sh`, make it executable (`chmod +x check_integration.sh`), and run it.

