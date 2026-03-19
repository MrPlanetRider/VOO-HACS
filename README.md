# VOO HACS

![GitHub Release (latest by date)](https://img.shields.io/github/v/release/your-github-username/VOO-HACS)
![GitHub](https://img.shields.io/github/license/your-github-username/VOO-HACS)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/your-github-username/VOO-HACS/test.yml)

Home Assistant integration for VOO Gateway (Technicolor CGA4233VOO) modem manufactured for VOO (Belgian ISP).

## Features

- **System Information**: Model, firmware version, hardware version, uptime
- **Network Information**: WAN & LAN IP, gateway IP, subnet mask, DNS servers
- **Connected Devices**: Monitor number of devices connected to the router
- **Modem Status**: Check if modem is online and operational
- **Automatic Updates**: Configurable polling interval (default: 5 minutes)
- **Clean Device Integration**: All sensors grouped under one device in Home Assistant

## Installation

### Via HACS (Recommended)

1. Add the following custom repository to HACS:
   - URL: `https://github.com/your-github-username/VOO-HACS`
   - Category: `Integration`

2. Search for "VOO Gateway" in HACS and install it

3. Restart Home Assistant

### Manual Installation

1. Clone or download this repository
2. Copy the `custom_components/voo_gateway` folder to your Home Assistant `custom_components` folder
3. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Create Integration**
2. Search for **VOO Gateway**
3. Enter your router IP address, username, and password
4. Click **Create**
5. (Optional) Configure the scan interval in the integration options

### Default Credentials

Your VOO router uses the credentials printed on the device label:

- **Username**: Usually "user" or "voo"
- **Password**: Check your router label
- **IP Address**: `192.168.0.1` (default)

## Available Sensors

### System Sensors
- **Model**: Router model name (e.g., CGA4233VOO)
- **Firmware Version**: Current firmware version
- **Hardware Version**: Hardware revision
- **Uptime**: Router uptime in seconds
- **Local Time**: Router's local time

### Network Sensors
- **WAN IP Address**: Your public IP address assigned by VOO
- **LAN IP Address**: Router's local IP address
- **LAN Subnet Mask**: Network subnet mask
- **Gateway IP**: Network gateway IP
- **DNS Servers**: Configured DNS servers (comma-separated)

### Device Sensors
- **Connected Devices**: Number of devices currently connected
- **Modem Status**: Whether modem is online (binary sensor)

## Supported Devices

- **Technicolor CGA4233VOO**: Confirmed working
- **Technicolor CGA4233-EU variants**: Should work (untested)
- **Other Technicolor CGA models**: May work depending on firmware

## How It Works

The integration communicates with your router's web interface using the REST API:

1. **Authentication**: Uses 2-step PBKDF2-SHA256 challenge-response with salt
2. **API Calls**: Queries endpoints like `/api/v1/system`, `/api/v1/dhcp`, `/api/v1/host`
3. **Data Parsing**: Extracts JSON responses and exposes data as Home Assistant sensors

This is purely **read-only** - no configuration changes are made to your router.

## Compatibility

- **Home Assistant**: 2024.1.0 or later
- **Python**: 3.11+
- **Network**: Local LAN access to router (no cloud dependency)

## Development

### Setup

```bash
git clone https://github.com/your-github-username/VOO-HACS.git
cd VOO-HACS
```

### Testing

Place the integration in your Home Assistant `custom_components` folder and test via the UI.

### Code Structure

```
custom_components/voo_gateway/
├── __init__.py              # Integration setup
├── config_flow.py           # Config UI
├── const.py                 # Constants
├── coordinator.py           # Data coordinator
├── voo_api.py              # API client
├── sensor.py               # Sensor entities
├── binary_sensor.py        # Binary sensor entities
├── manifest.json           # Integration metadata
└── strings.json            # UI strings
```

## Troubleshooting

### Authentication Failed

- Verify your username and password are correct
- Check that your router is accessible at the configured IP address
- Ensure you're on the same network as the router

### No Data / Sensors Not Updating

- Check the Home Assistant logs for errors: **Settings → System → Logs**
- Verify the router is online and responsive
- Try increasing the scan interval if you have network latency

### All Connections Reset

- Some routers have connection limits; if you see "too many connections", try increasing the scan interval to >300 seconds

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details.

## Disclaimer

This is an **unofficial** integration not affiliated with VOO or Technicolor. Use at your own risk. The author assumes no responsibility for any issues arising from the use of this integration.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

**Need Help?**

- Check the [Issues](https://github.com/your-github-username/VOO-HACS/issues) page
- Visit the [Home Assistant Community](https://community.home-assistant.io)
