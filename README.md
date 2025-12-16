# LubeLogger Home Assistant Integration

A Home Assistant custom integration for [LubeLogger](https://github.com/hargata/lubelog), a web-based vehicle maintenance and fuel mileage tracker.

## Features

This integration provides sensors for:
- Vehicle total miles
- Average MPG
- Total fuel cost
- Next maintenance due date
- Last maintenance date
- Last fuel fill date
- Last fuel price

## Installation

### Manual Installation

1. Copy the `custom_components/lubelogger` folder to your Home Assistant `custom_components` directory:
   ```
   <config directory>/custom_components/lubelogger/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "LubeLogger" and follow the setup instructions

### HACS Installation (Coming Soon)

This integration can be added to HACS for easier installation and updates.

## Configuration

During setup, you'll need to provide:
- **URL**: The URL of your LubeLogger instance (e.g., `http://localhost:5000` or `https://lubelogger.example.com`)
- **Username**: Your LubeLogger username
- **Password**: Your LubeLogger password

## API Compatibility

This integration assumes LubeLogger exposes REST API endpoints. The following endpoints are expected:
- `GET /api/Vehicle/GetAllVehicles` - Get all vehicles
- `GET /api/MaintenanceRecord/GetAllMaintenanceRecords` - Get maintenance records
- `GET /api/GasRecord/GetAllGasRecords` - Get fuel records
- `GET /api/Vehicle/GetVehicleStatistics` - Get vehicle statistics

**Note**: These API endpoints may need to be adjusted based on the actual LubeLogger API structure. If you encounter issues, please check the LubeLogger API documentation or open an issue.

## Troubleshooting

### Integration won't connect

1. Verify your LubeLogger instance is accessible from your Home Assistant server
2. Check that the URL is correct (include `http://` or `https://`)
3. Verify your username and password are correct
4. Check Home Assistant logs for detailed error messages

### Sensors not showing data

1. Ensure you have vehicles configured in LubeLogger
2. Check that your vehicles have maintenance or fuel records
3. Review the Home Assistant logs for any API errors

## Development

### Requirements

- Python 3.9+
- Home Assistant Core
- aiohttp library

### Testing

To test the integration locally:

1. Set up a development environment for Home Assistant
2. Install the integration in development mode
3. Use the Home Assistant test framework to verify functionality

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This integration is provided as-is. LubeLogger itself is licensed under the MIT license.

## Support

For issues related to:
- **This integration**: Open an issue on this repository
- **LubeLogger**: Visit the [LubeLogger repository](https://github.com/hargata/lubelog)

