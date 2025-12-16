# Installation Guide for Home Assistant

## Method 1: Manual Installation (Recommended for Testing)

### Step 1: Locate Your Home Assistant Configuration Directory

The location depends on your Home Assistant installation type:

- **Home Assistant OS (HassOS)**: `/config/`
- **Home Assistant Container**: `/config/` (mounted volume)
- **Home Assistant Core (Python venv)**: Usually `~/.homeassistant/` or `~/.config/homeassistant/`
- **Home Assistant Supervised**: `/usr/share/hassio/homeassistant/`

### Step 2: Create the Custom Components Directory

If it doesn't already exist, create the `custom_components` directory:

```bash
mkdir -p <config directory>/custom_components
```

### Step 3: Copy the Integration

Copy the entire `lubelogger` folder to your Home Assistant config directory:

```bash
# From the repository root
cp -r custom_components/lubelogger <config directory>/custom_components/
```

Or if you're using SSH/SCP:

```bash
scp -r custom_components/lubelogger <user>@<ha-host>:<config directory>/custom_components/
```

### Step 4: Verify File Structure

Your directory structure should look like this:

```
<config directory>/
  custom_components/
    lubelogger/
      __init__.py
      client.py
      config_flow.py
      const.py
      coordinator.py
      manifest.json
      sensor.py
      strings.json
```

### Step 5: Restart Home Assistant

- **Home Assistant OS**: Go to Settings → System → Restart
- **Home Assistant Container**: Restart the container
- **Home Assistant Core**: Restart the service/process

### Step 6: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ ADD INTEGRATION"** (bottom right)
3. Search for **"LubeLogger"**
4. Click on it and follow the setup wizard:
   - Enter your LubeLogger URL (e.g., `http://192.168.1.100:5000` or `https://lubelogger.example.com`)
   - Enter your LubeLogger username
   - Enter your LubeLogger password
5. Click **Submit**

### Step 7: Verify Installation

1. Check that the integration appears in **Settings** → **Devices & Services**
2. Check the **Developer Tools** → **States** tab and search for `sensor.lubelogger` to see your sensors
3. Check the logs for any errors: **Settings** → **System** → **Logs**

## Method 2: Using HACS (Home Assistant Community Store)

### Prerequisites

1. Install HACS if you haven't already: [HACS Installation Guide](https://hacs.xyz/docs/setup/download)

### Installation Steps

1. Go to **HACS** → **Integrations**
2. Click the three dots menu (⋮) in the top right
3. Select **Custom repositories**
4. Add this repository:
   - **Repository**: `https://github.com/larry/lubelogger-ha`
   - **Category**: Integration
5. Click **Add**
6. Search for "LubeLogger" in HACS
7. Click **Download**
8. Restart Home Assistant
9. Follow Step 6 from Method 1 to add the integration

## Troubleshooting

### Integration Not Appearing

1. **Check file permissions**: Ensure all files are readable
   ```bash
   chmod -R 644 <config directory>/custom_components/lubelogger/*
   chmod 755 <config directory>/custom_components/lubelogger
   ```

2. **Check logs**: Look for errors in Home Assistant logs
   - Go to **Settings** → **System** → **Logs**
   - Filter for "lubelogger" or "custom_components"

3. **Verify Python syntax**: Check that all Python files are valid
   ```bash
   python3 -m py_compile custom_components/lubelogger/*.py
   ```

### Connection Errors

1. **Verify LubeLogger is accessible**: Test the URL in a browser
2. **Check network connectivity**: Ensure Home Assistant can reach your LubeLogger instance
3. **Verify credentials**: Double-check username and password
4. **Check API endpoints**: The integration assumes certain API endpoints exist. You may need to adjust them in `const.py` if your LubeLogger instance uses different endpoints

### No Sensors Appearing

1. **Check coordinator logs**: Look for errors fetching data
2. **Verify vehicles exist**: Ensure you have vehicles configured in LubeLogger
3. **Check API responses**: The integration expects specific data structures. You may need to adjust the sensor code based on your actual API responses

## Development Mode Testing

If you're actively developing and want to see changes without restarting:

1. Enable **Developer Tools** → **YAML** → **Reload** → **LubeLogger Integration**
2. Or use the service: `homeassistant.reload_config_entry`

## Getting Help

- Check the logs: **Settings** → **System** → **Logs**
- Review the README.md for API compatibility notes
- Open an issue on GitHub if you encounter problems

