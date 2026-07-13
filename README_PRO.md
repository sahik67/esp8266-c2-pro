# Advanced C2 Framework - Professional Edition v2.0

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![ESP8266](https://img.shields.io/badge/ESP8266-NodeMCU-green.svg)](https://www.espressif.com)
[![License](https://img.shields.io/badge/License-Educational-orange.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Professional%20Edition-success.svg)](README.md)
[![Security](https://img.shields.io/badge/Security-Enterprise%20Grade-critical.svg)](README.md)
[![Cross-Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](README.md)
[![WiFi](https://img.shields.io/badge/WiFi-2.4GHz%20%7C%205GHz-informational.svg)](README.md)

## ⚠️ Educational Safety Disclaimer

This project is a **controlled Proof-of-Concept (PoC)** designed for educational purposes only. It demonstrates:
- Enterprise-grade security architecture
- Professional embedded systems programming
- Advanced C2 (Command and Control) concepts
- Secure remote administration patterns
- Comprehensive audit logging and monitoring

**Use only on authorized test systems within your own network.**

---

## 🚀 Professional Edition Features

### Security Enhancements
- **API Key Authentication** - HMAC-based secure authentication
- **IP Whitelisting** - Restrict access to specific IP addresses
- **Session Management** - Session-based authentication with timeout (configurable)
- **Rate Limiting** - Configurable request throttling (default: 60 req/min)
- **Input Sanitization** - Whitelist-based command validation
- **Auth Lockout** - Automatic lockout after failed attempts (5 attempts, 5 min lockout)
- **Command Whitelisting** - Only pre-approved commands can execute
- **Constant-Time Comparison** - Timing attack prevention
- **CORS Support** - Cross-origin request handling

### Architecture Improvements
- **Configuration Management** - JSON-based configuration system
- **Modular Design** - Class-based architecture with separation of concerns
- **Thread-Safe Operations** - Lock-based concurrency control
- **Professional Logging** - Structured audit logging with timestamps and IP tracking
- **Statistics Tracking** - Comprehensive metrics, success rates, and command frequency
- **Graceful Shutdown** - Clean termination with final reports
- **Error Handling** - Robust exception handling and recovery

### Monitoring & Observability
- **Real-time Status** - Live system metrics via JSON API
- **Command History** - Detailed execution history (1000 entries)
- **Performance Metrics** - Execution time tracking
- **Connection Monitoring** - Heartbeat-based connection detection
- **Resource Monitoring** - Memory, CPU, and WiFi signal tracking
- **Health Monitoring** - Comprehensive system health checks
- **Auto-Recovery** - Automatic recovery from critical conditions
- **Alert System** - Security event alerts and health warnings

### Advanced Command Features
- **Custom Command Builder** - Execute custom commands via UI
- **Command Scheduling** - Schedule commands with delay timers
- **Batch Execution** - Execute multiple commands in sequence
- **Command Templates** - Pre-built command templates for common tasks
- **Output Capture** - Display command output in real-time
- **Usage Statistics** - Track command frequency and usage patterns

### Bot Integrations
- **Telegram Bot Integration** - Remote control via Telegram
  - Send commands through Telegram messages
  - Receive security alerts on Telegram
  - Real-time notifications
  - Configurable chat ID and bot token
- **Discord Bot Integration** - Remote control via Discord
  - Send commands through Discord channels
  - Receive security alerts on Discord
  - Rich formatting support
  - Configurable channel ID and bot token

### System Management
- **Backup & Restore** - Configuration backup system
  - Automatic scheduled backups
  - Manual backup creation
  - Restore from any backup point
  - Configurable backup interval
  - Backup config and logs separately
- **OTA Update System** - Over-the-Air firmware updates
  - Check for firmware updates automatically
  - Trigger remote updates
  - Version comparison
  - Changelog display
  - Secure update server integration
- **Multiple NodeMCU Support** - Manage multiple devices
  - Add/remove devices dynamically
  - Individual device status monitoring
  - Device-specific API keys
  - Centralized device management
  - Multi-device command execution

---

## 📋 System Requirements

### Hardware - Compatible Boards

#### ESP8266 Based Boards (Fully Supported)
1. **NodeMCU v1.0 (ESP-12E)** - ⭐ Recommended
   - ESP8266EX with 4MB Flash
   - Built-in USB-to-Serial (CH340/CP2102)
   - Easy to use, widely available
   - Best for beginners

2. **NodeMCU v3 (ESP-12F/ESP-12S)** - ⭐ Recommended
   - Improved antenna design
   - Better WiFi stability
   - Same pinout as v1.0

3. **Wemos D1 Mini** - ⭐ Recommended
   - Compact form factor
   - ESP8266EX with 4MB Flash
   - Good for small projects
   - Micro USB connector

4. **ESP8266 Generic Boards**
   - ESP-01, ESP-01S (Limited GPIO, not recommended)
   - ESP-07, ESP-08 (Requires external USB adapter)
   - ESP-12E, ESP-12F, ESP-12S (Requires external USB adapter)

#### ESP32 Based Boards (Future Support)
- ESP32 DevKit V1
- ESP32 WROOM
- ESP32-C3 (Not currently supported)

**Board Selection Guide:**
- **Beginners**: NodeMCU v1.0 or Wemos D1 Mini
- **Advanced Users**: ESP-12F/S with custom adapter
- **Production**: NodeMCU v3 for better WiFi stability

### Required Accessories
- USB Data Cable (Micro USB or Mini USB depending on board)
- 5V/2A Power Adapter (optional, for standalone operation)
- Mobile device with web browser (Android/iOS)
- PC with WiFi capability

### Software Requirements

#### Arduino IDE Setup
1. **Arduino IDE 2.0+** (Recommended)
   - Download from: https://www.arduino.cc/en/software
   - Install latest version

2. **ESP8266 Board Package**
   - Open Arduino IDE
   - Go to: File → Preferences
   - Add to "Additional Board Manager URLs":
     ```
     http://arduino.esp8266.com/stable/package_esp8266com_index.json
     ```
   - Go to: Tools → Board → Boards Manager
   - Search: "esp8266"
   - Install: "esp8266 by ESP8266 Community" (version 3.0.0+)

3. **Required Libraries**
   - ESP8266WiFi (Built-in)
   - ESP8266WebServer (Built-in)
   - ESP8266mDNS (Built-in)
   - ArduinoJson (Install via Library Manager)
   - EEPROM (Built-in)

#### Python Setup
1. **Python 3.8+** (Required)
   - Download from: https://www.python.org/downloads/
   - Install with "Add to PATH" option checked
   - Verify installation: `python --version`

2. **Required Python Packages**
   ```bash
   pip install requests
   ```

3. **Optional Packages** (For advanced features)
   ```bash
   pip install cryptography
   pip install pyyaml
   ```

#### Network Requirements
- **Different WiFi Networks Supported** - NodeMCU and PC can be on different networks
- **Internet Connection Required** - For cross-network communication via public IP or VPN
- **2.4GHz WiFi network** (5GHz not supported by ESP8266)
- **Network firewall** allows outbound connections
- **Dynamic DNS** recommended for remote access
- **VPN Tunnel** alternative for secure cross-network access
- **Minimum 2.4GHz WiFi with WPA2 security**

**Cross-Network Setup Options:**
1. **Public IP Access** - Configure router port forwarding
2. **VPN Tunnel** - Use VPN to connect devices on different networks
3. **Cloud Relay** - Use cloud service for message relay
4. **mDNS over VPN** - Use mDNS with VPN for local-like access

---

## 📦 Installation

### Step 1: Install Python Dependencies

```bash
pip install requests
```

### Step 2: Generate Secure API Key

**Why API Key is Needed:**
The API key is used for secure authentication between the Python listener and NodeMCU controller. It prevents unauthorized access to your C2 system and protects against malicious commands from unauthorized clients.

**How to Generate:**
```bash
python pc_listener_pro.py --generate-key
```

This will generate a secure 64-character hexadecimal key like:
```
Generated API Key: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

**Where to Use the API Key:**
1. **config.json** - Update the `api_key` field
2. **nodemcu_c2_pro.ino** - Update the `API_KEY` constant
3. Both must match exactly for authentication to work

**Security Best Practices:**
- Never share your API key publicly
- Use different keys for different environments
- Regenerate keys periodically
- Store keys securely (environment variables recommended)
- Never commit keys to version control

### Step 3: Configure System

Edit `config.json` with your settings:

```json
{
  "server": {
    "host": "192.168.1.15",
    "port": 80,
    "use_mDNS": true,
    "mDNS_hostname": "nodemcu-c2"
  },
  "network": {
    "ssid": "DemoWiFi_Network",
    "password": "DemoPassword123",
    "connection_timeout": 30
  },
  "security": {
    "api_key": "YOUR_GENERATED_SECURE_KEY_HERE",
    "enable_auth": true,
    "rate_limit_per_minute": 60,
    "max_queue_size": 20,
    "allowed_clients": [],
    "enable_cors": true
  },
  "logging": {
    "enable_serial": true,
    "log_level": "INFO",
    "max_history": 100
  },
  "monitoring": {
    "heartbeat_interval": 10000,
    "status_update_interval": 30000,
    "connection_timeout": 10000
  },
  "commands": {
    "enable_dangerous_commands": false,
    "require_confirmation": true,
    "auto_clear_on_success": false
  }
}
```

**Configuration Options Explained:**

**Server Settings:**
- `host`: NodeMCU IP address (will be assigned by DHCP)
- `port`: HTTP server port (default: 80)
- `use_mDNS`: Enable mDNS for hostname resolution
- `mDNS_hostname`: Hostname for mDNS (access via http://nodemcu-c2.local)

**Network Settings:**
- `ssid`: Your WiFi network name (SSID)
- `password`: Your WiFi password
- `connection_timeout`: WiFi connection timeout in seconds

**Security Settings:**
- `api_key`: Secure authentication key (generate with --generate-key)
- `enable_auth`: Enable/disable API key authentication
- `rate_limit_per_minute`: Maximum requests per minute (prevents abuse)
- `max_queue_size`: Maximum commands in queue (default: 20)
- `allowed_clients`: Whitelist of client IP addresses for IP whitelisting
- `enable_ip_whitelist`: Enable IP-based access control
- `enable_cors`: Enable Cross-Origin Resource Sharing
- `session_timeout`: Session timeout in seconds (default: 3600)
- `max_sessions`: Maximum concurrent sessions (default: 5)

**Logging Settings:**
- `enable_serial`: Enable serial output on NodeMCU
- `log_level`: DEBUG, INFO, WARNING, ERROR
- `max_history`: Maximum command history entries
- `enable_detailed_logging`: Enable detailed logging with timestamps
- `log_command_output`: Log command output to file

**Monitoring Settings:**
- `heartbeat_interval`: PC heartbeat check interval in milliseconds
- `status_update_interval`: Status update interval in milliseconds
- `connection_timeout`: Connection timeout in milliseconds
- `health_check_interval`: System health check interval in milliseconds
- `auto_recovery`: Enable automatic recovery from critical conditions
- `alert_on_failure`: Send alerts on system failures

**Command Settings:**
- `enable_dangerous_commands`: Enable potentially dangerous commands
- `require_confirmation`: Require confirmation before execution
- `auto_clear_on_success`: Auto-clear queue on successful execution
- `enable_custom_commands`: Enable custom command builder
- `enable_scheduling`: Enable command scheduling
- `enable_batch_execution`: Enable batch command execution
- `enable_templates`: Enable command templates

**Advanced Settings:**
- `enable_telegram_bot`: Enable Telegram bot integration
- `telegram_bot_token`: Your Telegram bot token from BotFather
- `telegram_chat_id`: Your Telegram chat ID for receiving messages
- `enable_discord_bot`: Enable Discord bot integration
- `discord_bot_token`: Your Discord bot token
- `discord_channel_id`: Discord channel ID for messages
- `enable_ota_updates`: Enable Over-the-Air firmware updates
- `ota_update_server`: OTA update server URL
- `enable_backup`: Enable automatic configuration backups
- `backup_interval`: Backup interval in seconds (default: 86400 = 24 hours)
- `multiple_devices`: Enable multiple NodeMCU device management
- `devices`: Array of device configurations

**Statistics Settings:**
- `enable_usage_tracking`: Enable usage statistics tracking
- `track_command_frequency`: Track command usage frequency
- `track_success_rate`: Track command success rates

### Step 4: Flash NodeMCU Firmware

**For NodeMCU v1.0/v3:**
1. Connect NodeMCU to PC via USB cable
2. Open `nodemcu_c2_pro.ino` in Arduino IDE
3. Update WiFi credentials and API key in the code:
   ```cpp
   const char* ssid = "Your_WiFi_Name";
   const char* password = "Your_WiFi_Password";
   const char* API_KEY = "YOUR_GENERATED_API_KEY";
   ```
4. Select Board: Tools → Board → NodeMCU 1.0 (ESP-12E Module)
5. Select Port: Tools → Port → (Select your NodeMCU port)
6. Click Upload button (→)
7. Wait for upload to complete
8. Open Serial Monitor (Tools → Serial Monitor)
9. Set baud rate to 115200
10. Verify initialization messages appear

**For Wemos D1 Mini:**
1. Same steps as NodeMCU
2. Select Board: Tools → Board → LOLIN(WEMOS) D1 R2 & mini
3. Rest of the process is identical

**Troubleshooting Upload Issues:**
- **Upload Failed**: Try pressing FLASH button while uploading
- **Port Not Found**: Install CH340/CP2102 drivers
- **Connection Timed Out**: Use different USB cable or port
- **Board Not Recognized**: Check driver installation

### Step 5: Get NodeMCU IP Address

After successful upload:
1. Keep Serial Monitor open
2. Look for message: `[+] NodeMCU Control IP: 192.168.1.XX`
3. Copy this IP address
4. Update `config.json` server.host with this IP
5. Alternatively, use mDNS: `http://nodemcu-c2.local` (if supported)

### Step 6: Run Professional Listener

**Basic Usage:**
```bash
python pc_listener_pro.py --config config.json
```

**Advanced Usage:**
```bash
# Generate new API key
python pc_listener_pro.py --generate-key

# Run with custom config
python pc_listener_pro.py --config my_config.json

# Run with verbose logging
python pc_listener_pro.py --config config.json --verbose
```

**Expected Output:**
```
============================================================
ADVANCED C2 LISTENER - PROFESSIONAL EDITION
============================================================
Target: http://192.168.1.15
Platform: Windows 10
Authentication: ENABLED
Rate Limit: 60 requests/minute
============================================================
2026-07-08 19:30:00 | INFO     | C2_AUDIT | CMD: SYS_INFO | STATUS: SUCCESS | Time: 0.234s
```

### Step 7: Access Control Dashboard

1. Ensure Python listener is running
2. Open web browser on mobile device
3. Navigate to: `http://<NODEMCU_IP>` or `http://nodemcu-c2.local`
4. You should see the professional C2 dashboard
5. Tap buttons to trigger commands
6. Watch Python listener execute commands

---

## 🎯 Available Payloads (53 Total)

### System Diagnostics (4)
1. **SYS_INFO** - System hardware and OS architecture diagnostics
2. **NET_STAT** - Network adapters and IP configuration audit
3. **PROCESS_LIST** - Active task and process security list
4. **PORT_SCAN** - Local network port and established connections scan

### Advanced Analysis (4)
5. **DNS_CACHE** - DNS cache auditor (malware analysis)
6. **ROUTE_PRINT** - Routing table diagnostic
7. **ENV_VARS** - Environment variables audit
8. **DISK_CHECK** - Disk geometry and health check

### Performance Tests (4)
9. **CALC_TEST** - Basic GUI application invocation (calculator)
10. **PING_TEST** - Loopback interface stability test
11. **CPU_STRESS** - CPU load monitoring
12. **MEM_CHECK** - Memory usage analysis

### System Management (11)
13. **SERVICE_LIST** - Windows services or systemd units status
14. **EVENT_LOG** - Windows Event Viewer or systemd journal logs
15. **FIREWALL_STATUS** - Windows Firewall or Linux firewall status
16. **STARTUP** - Startup programs and services
17. **HOTFIXES** - Installed hotfixes and updates
18. **NET_DIAG** - Advanced network interface diagnostics
19. **USER_AUDIT** - User accounts and permissions audit
20. **SCHED_TASKS** - Scheduled tasks or cron jobs
21. **INSTALLED_PROGS** - Installed software packages
22. **BOOT_TIME** - System boot time information
23. **NET_CONNECTIONS** - Active network connections with process details

### Administrative Tools (9) ⚠️
24. **REGEDIT** - Registry Editor (Windows) / System config (Linux)
25. **GPEDIT** - Group Policy Editor (Windows) / Sudoers config (Linux)
26. **SECPOL** - Local Security Policy (Windows) / Firewall rules (Linux)
27. **COMPMGMT** - Computer Management Console
28. **TASKSCHD** - Task Scheduler (Windows) / Cron editor (Linux)
29. **SERVICES** - Services Manager GUI
30. **EVENTVWR** - Event Viewer GUI (Windows) / Live journal (Linux)
31. **DEVMGMT** - Device Manager (Windows) / PCI devices (Linux)
32. **DISKMGMT** - Disk Management Console

### Performance Monitoring (4)
33. **PERFMON** - Performance Monitor (Windows) / htop (Linux)
34. **RESMON** - Resource Monitor (Windows) / iotop (Linux)
35. **MSINFO32** - System Information GUI (Windows) / dmidecode (Linux)
36. **TASKMGR** - Task Manager (Windows) / top (Linux)

### Security & Encryption (5) 🔐
37. **BITLOCKER** - BitLocker encryption status (Windows) / LUKS info (Linux)
38. **CERTMGR** - Certificate Manager (Windows) / CA certificates (Linux)
39. **WSCUI** - Windows Security Center (Windows) / UFW status (Linux)
40. **WF_MSC** - Advanced Firewall (Windows) / UFW verbose (Linux)
41. **LUSRMGR** - Local Users and Groups Manager

### Network Administration (5) 🌐
42. **NCPA** - Network Adapter Settings (Windows) / Network devices (Linux)
43. **SHARES** - Shared Folders (Windows) / NFS shares (Linux)
44. **SESSIONS** - Active user sessions (Windows) / Logged in users (Linux)
45. **NET_SHARES** - Network shares audit (SMB/NFS)
46. **RDP_CONFIG** - RDP configuration (Windows) / SSH status (Linux)

### System Maintenance (4) 🔧
47. **SFC** - System File Checker (Windows) / Package integrity (Linux)
48. **WUSA** - Windows Update History (Windows) / Available updates (Linux)
49. **DRIVERQUERY** - Installed drivers (Windows) / Kernel modules (Linux)
50. **POWERCFG** - Power configuration (Windows) / Power status (Linux)

### Advanced Diagnostics (3) 🔍
51. **PROC_TREE** - Process tree visualization
52. **OPEN_FILES** - Open files and handles
53. **CLEAR_QUEUE** - Clear command queue (NodeMCU)

---

## 🔒 Security Architecture

### Authentication Flow
1. Client sends request with `X-API-Key` header
2. Server verifies key using constant-time comparison
3. Failed attempts are tracked and trigger lockout
4. Rate limiting prevents brute force attacks

### Command Validation
1. Command is sanitized (alphanumeric, underscore, hyphen only)
2. Command is checked against whitelist
3. Invalid commands are blocked and logged
4. Blocked commands increment security metrics

### Rate Limiting
- Sliding window algorithm (1-minute window)
- Configurable limit (default: 60 requests/minute)
- HTTP 429 response when limit exceeded
- Per-client tracking possible via IP

### Audit Logging
- All commands logged with timestamps
- Security events logged separately
- Execution time tracked for performance analysis
- Logs written to file and console

---

## 📊 API Endpoints

### Public Endpoints
- `GET /` - Professional control dashboard
- `GET /status` - System status (JSON)

### Authenticated Endpoints
- `GET /trigger?cmd=COMMAND` - Queue command (requires API key)
- `GET /check` - Poll for commands (requires API key)
- `GET /history` - Command history (requires API key)
- `GET /reset` - System reset (requires API key)

### Status Response Format
```json
{
  "uptime": 1234567,
  "totalCommands": 150,
  "successfulCommands": 145,
  "failedCommands": 3,
  "blockedCommands": 2,
  "queueSize": 5,
  "pcConnected": true,
  "pcStatus": "CONNECTED",
  "lastCommand": "SYS_INFO",
  "freeHeap": 45678,
  "wifiRSSI": -65,
  "authEnabled": true,
  "isLocked": false
}
```

---

## 🔧 Configuration Options

### Security Settings
- `api_key`: Secure random key for authentication
- `enable_auth`: Enable/disable authentication
- `rate_limit_per_minute`: Maximum requests per minute
- `max_queue_size`: Maximum commands in queue
- `allowed_clients`: Optional whitelist of client IPs

### Logging Settings
- `log_level`: DEBUG, INFO, WARNING, ERROR
- `max_history`: Maximum command history entries
- `enable_serial`: Enable serial output on NodeMCU

### Monitoring Settings
- `heartbeat_interval`: PC heartbeat check interval (ms)
- `status_update_interval`: Status update interval (ms)
- `connection_timeout`: Connection timeout (ms)

### Command Settings
- `enable_dangerous_commands`: Enable potentially dangerous commands
- `require_confirmation`: Require confirmation before execution
- `auto_clear_on_success`: Auto-clear queue on successful execution

---

## 📁 Project Structure

```
esp8266_c2_poc/
├── config.json              # Configuration file
├── nodemcu_c2.ino           # Original firmware
├── nodemcu_c2_pro.ino       # Professional firmware
├── pc_listener.py            # Original listener
├── pc_listener_pro.py        # Professional listener
├── README.md                # Original documentation
└── README_PRO.md            # Professional documentation
```

---

## 🐛 Troubleshooting

### Authentication Issues
- **401 Unauthorized**: Check API key matches in both config and firmware
- **429 Rate Limit**: Reduce request frequency or increase rate limit
- **System Locked**: Wait 5 minutes for lockout to expire

### Connection Issues
- **PC Disconnected**: Check Python listener is running
- **WiFi Issues**: Verify NodeMCU is connected to network
- **mDNS Not Working**: Use IP address instead of hostname

### Command Issues
- **Command Blocked**: Check command is in whitelist
- **Queue Full**: Increase max_queue_size or clear queue
- **Execution Failed**: Check Python listener logs for details

---

## 📚 Educational Use Cases

- Learning enterprise security architecture
- Understanding C2 security patterns
- Implementing rate limiting and authentication
- Professional audit logging practices
- Thread-safe programming patterns
- Configuration management systems
- API security best practices

---

## ⚡ Performance Characteristics

- **Command Queue**: 20 commands max
- **History Storage**: 100 entries
- **Rate Limit**: 60 requests/minute (configurable)
- **Auth Lockout**: 5 attempts, 5-minute lockout
- **Heartbeat Timeout**: 10 seconds
- **Memory Usage**: ~45KB free heap typical
- **Response Time**: <100ms for API calls

---

## 📝 License

Educational use only. Not for production or malicious purposes.

---

## 🤝 Contributing

This is an educational project. Suggestions for additional security features and safe diagnostic payloads are welcome.

---

## 🔐 Security Best Practices

1. **Always change default API keys**
2. **Use strong WiFi passwords**
3. **Keep firmware updated**
4. **Monitor audit logs regularly**
5. **Use on isolated test networks only**
6. **Never expose to internet**
7. **Review command whitelist carefully**
8. **Enable authentication in production**
9. **Regular security audits recommended**
10. **Document all configuration changes**

---

## 📞 Support

For issues or questions related to this educational project, please refer to the documentation and ensure you are following all safety guidelines.
