# VOO HACS

Home Assistant integration for VOO Gateway (Technicolor CGA4233VOO C0A4233VOO) modem/router manufactured for VOO (Belgian ISP).

This custom integration provides local LAN access to your modem's status and network information via its REST API.

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
   - URL: `https://github.com/MrPlanetRider/VOO-HACS`
   - Category: `Integration`
username/VOO-HACS`
   - Category: `Integration`

2. Search for "VOO Gateway" in HACS and install it

3. Restart Home Assistant

### Quick Setup

Once installed:
1. Go to **Settings → Devices & Services → Create Integration**
2. Select **VOO Gateway**
3. Enter your router credentials from the device label
4. Click **Create**

1. Clone or download this repository
2. Copy the `custom_components/voo_gateway` folder to your Home Assistant `custom_components` folder
3. Restart Home Assistant

## CRouter Credentials

Your router credentials are printed on the device label on the back of the modem:

- **IP Address**: `192.168.0.1` (factory default)
- **Username**: Usually "user" (some models use "voo")
- **Password**: Custom password from your device label

**Note**: Do not use the ISP admin interface credentials; use the credentials from your device sticker. in the integration options

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

## Supported Devices (Model C0A4233VOO): ✅ Confirmed working
- **Technicolor CGA4233-EU variants**: Should work
- **Other Technicolor CGA models**: May work with similar firmware/API

If you have a different modem model and it works, please let us know!
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
git clone https://github.com/MrPlanetRider/VOO-HACS.git
cd VOO-HACS
```

### Testing

Place the integration in your Home Assistant `custom_components` folder and test via the UI.
VOO-HACS/
├── custom_components/voo_gateway/
│   ├── __init__.py              # Integration setup & entry points
│   ├── config_flow.py           # Configuration UI
│   ├── const.py                 # Constants & API endpoints
│   ├── coordinator.py           # Data coordinator
│   ├── voo_api.py              # API client (PBKDF2 auth)
│   ├── sensor.py               # Sensor entities
│   ├── binary_sensor.py        # Binary sensor entities
│   ├── manifest.json           # Integration metadata
│   └── strings.json            # UI strings & translations
├── hacs.json                    # HACS manifest
├── README.md                    # Documentation
├── LICENSE                      # Apache 2.0 License
└── .gitignore                   # Git ignore rules
```

### How the API Client Works

1. **2-Step PBKDF2 Authentication**:
   - First request: Get salt values from gateway
   - Hash password using PBKDF2-SHA256(password, salt1, 1000 iterations)
   - Hash result again with salt2
   - Submit hashed password for authentication

2. **Session Management**:
   - All requests use session cookies
   - CSRF token stored in request headers

3. **Data Endpoints**:
   - `/api/v1/system/*` - System & modem info
   - `/api/v1/dhcp/v4/1/*` - Network configuration
   - `/api/v1/host/*` - Connected devices
   - `/api/v1/wifi/*` - WiFi status
   - `/api/v1/modem/*` - DOCSIS modem info sensor.py               # Sensor entities
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

- Check the [Issues](https://github.com/MrPlanetRider/VOO-HACS/issues) page
- Visit the [Home Assistant Community](https://community.home-assistant.io)
