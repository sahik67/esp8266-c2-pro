# ESP8266 C2 Professional Framework

Advanced C2 (Command & Control) framework for ESP8266/NodeMCU with Python listener for remote system administration.

## Features

- **Web Dashboard**: Modern responsive UI for command execution
- **Security**: API key authentication, rate limiting, command sanitization
- **Robustness**: Watchdog timer, memory protection, auto-recovery
- **Monitoring**: Real-time status tracking, health checks
- **Cross-Platform**: Windows/Linux support with 50+ system commands

## Architecture

### Components

1. **ESP8266 Firmware** (`nodemcu_c2_pro.ino`)
   - Web server on port 80
   - Command queue management
   - Security features
   - Memory protection

2. **Python Listener** (`pc_listener_pro.py`)
   - Command execution engine
   - System monitoring
   - Auto-recovery mechanisms
   - Comprehensive logging

## Setup

### Prerequisites

- ESP8266/NodeMCU board
- Arduino IDE with ESP8266 board support
- Python 3.7+
- Required Python packages: `requests`

### Arduino IDE Setup

**Option 1: Use Custom Board Manager (Recommended)**

1. Add Custom ESP8266 Board Manager URL:
   ```
   https://raw.githubusercontent.com/sahik67/esp8266-c2-pro/main/package_esp8266_c2_index.json
   ```
   - File → Preferences → Additional Boards Manager URLs

2. Install ESP8266 boards:
   - Tools → Board → Boards Manager → "esp8266"

3. Select board:
   - Tools → Board → ESP8266 Boards → NodeMCU C2 Professional

**Option 2: Use Official Board Manager**

1. Add ESP8266 Board Manager URL:
   ```
   https://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
   - File → Preferences → Additional Boards Manager URLs

2. Install ESP8266 boards:
   - Tools → Board → Boards Manager → "esp8266"

3. Select board:
   - Tools → Board → ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)

### ESP8266 Configuration

1. Open `nodemcu_c2_pro.ino` in Arduino IDE
2. Update WiFi credentials (lines 22-23):
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. Upload to ESP8266
4. Note the IP address from Serial Monitor

### Python Configuration

1. Install dependencies:
   ```bash
   pip install requests
   ```

2. Update `config.json`:
   ```json
   {
     "server": {
       "host": "YOUR_ESP8266_IP",
       "port": 80
     },
     "security": {
       "api_key": "YOUR_GENERATED_API_KEY"
     }
   }
   ```

3. Run the listener:
   ```bash
   python pc_listener_pro.py
   ```

### Generate API Key

```bash
python pc_listener_pro.py --generate-key
```

## Usage

### Web Dashboard

Access via browser: `http://YOUR_ESP8266_IP`

### Available Commands

**System Diagnostics:**
- `SYS_INFO` - System Information
- `NET_STAT` - Network Configuration
- `PROCESS_LIST` - Process Audit
- `PORT_SCAN` - Port Scanner

**Advanced Analysis:**
- `DNS_CACHE` - DNS Cache Analysis
- `ROUTE_PRINT` - Routing Table
- `ENV_VARS` - Environment Variables
- `DISK_CHECK` - Disk Health Check

**Performance Tests:**
- `CPU_STRESS` - CPU Stress Test
- `MEM_CHECK` - Memory Analysis
- `PING_TEST` - Network Latency Test

**System Management:**
- `SERVICE_LIST` - Services Status
- `EVENT_LOG` - Event Logs
- `FIREWALL_STATUS` - Firewall Status
- `STARTUP` - Startup Programs

**Administrative Tools:**
- `REGEDIT` - Registry Editor
- `TASKMGR` - Task Manager
- `SERVICES` - Services Manager
- `DEVMGMT` - Device Manager

## Security Features

- **API Key Authentication**: Secure communication
- **Rate Limiting**: 60 requests/minute
- **Command Sanitization**: Input validation
- **Auth Lockout**: 5 failed attempts = 5 min lockout
- **IP Whitelist**: Optional client filtering

## Robustness Features

- **Watchdog Timer**: 30-second hang detection
- **Memory Protection**: Auto-cleanup on low memory
- **Connection Retry**: 3 attempts with exponential backoff
- **Bounds Checking**: Array overflow prevention
- **Graceful Degradation**: Continues operation on errors

## Configuration

### Server Settings
- Connection timeout: 10s
- Max retries: 3
- Retry delay: 2s

### Security Settings
- Max auth attempts: 5
- Lockout duration: 5 minutes
- Session timeout: 1 hour

### Monitoring Settings
- Heartbeat interval: 10s
- Status update: 30s
- Health check: 60s

## Troubleshooting

### ESP8266 Not Connecting
- Check WiFi credentials
- Verify network range (192.168.x.x)
- Check Serial Monitor for errors

### Python Connection Timeout
- Verify ESP8266 IP address
- Check firewall settings
- Ensure ESP8266 is powered on

### Commands Not Executing
- Check API key matches
- Verify command whitelist
- Check audit logs

## License

Educational Proof-of-Concept for Authorized Security Testing Only.

## Disclaimer

This framework is for educational purposes and authorized security testing only. Unauthorized use is illegal.

## Author

Your Name - ESP8266 C2 Professional Framework
