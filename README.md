# LubeLogger Home Assistant Integration

Home Assistant integration for [LubeLogger](https://github.com/hargata/lubelog), a web-based vehicle maintenance and fuel mileage tracker.

## Features

Creates a device for each vehicle in your LubeLogger instance with sensors for:

- Latest odometer reading
- Next planned maintenance item
- Latest tax payment
- Latest service record
- Latest repair record
- Latest upgrade record
- Latest supply/parts record
- Latest fuel fill-up
- Next reminder

Sensors only appear if data exists for that vehicle.

## Installation

### HACS (Recommended)

1. Open HACS → Integrations
2. Click the menu (⋮) → Custom repositories
3. Add repository: `https://github.com/larry/lubelogger-ha` (Category: Integration)
4. Search for "LubeLogger" and install
5. Restart Home Assistant

### Manual

1. Copy `custom_components/lubelogger` to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services

## Configuration

When adding the integration, provide:

- **URL**: Your LubeLogger instance URL (e.g., `http://192.168.1.100:8447`)
- **Username**: Your LubeLogger username
- **Password**: Your LubeLogger password

