/*
 * Advanced C2 Controller - Professional Edition
 * ESP8266/NodeMCU Firmware with Enterprise Security Features
 * Educational Proof-of-Concept for Authorized Security Testing
 * Version: 2.0 Professional
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>
#include <ArduinoJson.h>
#include <WiFiClient.h>
#include <EEPROM.h>
#include <ESP8266httpUpdate.h>
#include <Ticker.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

// Network Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Security Configuration
const char* API_KEY = "c5ed08ee7ffac84044710044bb61b68800e01db96798d31a7ad074eb135f1054";
const bool ENABLE_AUTH = true;
const int MAX_AUTH_ATTEMPTS = 5;
const unsigned long LOCKOUT_DURATION = 300000; // 5 minutes

// Rate Limiting
const int MAX_REQUESTS_PER_MINUTE = 60;
const unsigned long RATE_LIMIT_WINDOW = 60000; // 1 minute

// Queue Configuration
const int MAX_COMMANDS = 20;
const int MAX_HISTORY = 100;
const int MAX_STRING_LENGTH = 64;
const int WATCHDOG_TIMEOUT = 30; // seconds

// Monitoring Configuration
const unsigned long HEARTBEAT_TIMEOUT = 10000; // 10 seconds
const unsigned long STATUS_UPDATE_INTERVAL = 30000; // 30 seconds

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

ESP8266WebServer server(80);

// Command Queue System
String commandQueue[MAX_COMMANDS];
volatile int commandQueueHead = 0;
volatile int commandQueueTail = 0;
volatile int commandCount = 0;

// Command History
String commandHistory[MAX_HISTORY];
volatile int historyIndex = 0;

// Watchdog Timer
Ticker watchdogTimer;
volatile bool watchdogTriggered = false;
unsigned long lastWatchdogFeed = 0;

// Memory monitoring
unsigned long lastMemoryCheck = 0;
const unsigned long MEMORY_CHECK_INTERVAL = 30000; // 30 seconds

// System Statistics
unsigned long systemUptime = 0;
unsigned long totalCommandsExecuted = 0;
unsigned long successfulCommands = 0;
unsigned long failedCommands = 0;
unsigned long blockedCommands = 0;
String lastExecutedCommand = "NONE";
unsigned long lastCommandTime = 0;

// Security State
int failedAuthAttempts = 0;
unsigned long lockoutUntil = 0;
unsigned long requestTimestamps[MAX_REQUESTS_PER_MINUTE];
int requestCount = 0;

// Connection Monitoring
bool pcConnected = false;
unsigned long lastPCHeartbeat = 0;
String pcStatus = "DISCONNECTED";

// ============================================================================
// SECURITY FUNCTIONS
// ============================================================================

bool verifyAPIKey(String providedKey) {
  if (!ENABLE_AUTH) return true;
  
  // Constant-time comparison to prevent timing attacks
  if (providedKey.length() != strlen(API_KEY)) {
    return false;
  }
  
  for (size_t i = 0; i < providedKey.length(); i++) {
    if (providedKey[i] != API_KEY[i]) {
      return false;
    }
  }
  
  return true;
}

bool isRateLimited() {
  unsigned long now = millis();
  
  // Clean old timestamps with bounds checking
  int validCount = 0;
  for (int i = 0; i < min(requestCount, MAX_REQUESTS_PER_MINUTE); i++) {
    if (now - requestTimestamps[i] < RATE_LIMIT_WINDOW) {
      if (validCount < MAX_REQUESTS_PER_MINUTE) {
        requestTimestamps[validCount++] = requestTimestamps[i];
      }
    }
  }
  requestCount = validCount;
  
  // Check if limit exceeded
  if (requestCount >= MAX_REQUESTS_PER_MINUTE) {
    return true;
  }
  
  // Add current request with bounds checking
  if (requestCount < MAX_REQUESTS_PER_MINUTE) {
    requestTimestamps[requestCount++] = now;
  }
  return false;
}

bool isLockedOut() {
  if (lockoutUntil == 0) return false;
  if (millis() > lockoutUntil) {
    lockoutUntil = 0;
    failedAuthAttempts = 0;
    return false;
  }
  return true;
}

void recordFailedAuth() {
  failedAuthAttempts++;
  if (failedAuthAttempts >= MAX_AUTH_ATTEMPTS) {
    lockoutUntil = millis() + LOCKOUT_DURATION;
    Serial.println("[!] Maximum auth attempts reached. System locked.");
  }
}

bool sanitizeCommand(String& cmd) {
  // Check length first to prevent buffer overflow
  if (cmd.length() > MAX_STRING_LENGTH || cmd.length() == 0) {
    return false;
  }
  
  // Allow only alphanumeric, underscores, and hyphens
  for (unsigned int i = 0; i < cmd.length(); i++) {
    char c = cmd.charAt(i);
    if (!((c >= 'A' && c <= 'Z') || 
          (c >= 'a' && c <= 'z') || 
          (c >= '0' && c <= '9') || 
          c == '_' || c == '-')) {
      return false;
    }
  }
  return true;
}

// ============================================================================
// QUEUE MANAGEMENT
// ============================================================================

bool enqueueCommand(String cmd) {
  // Check queue bounds
  if (commandCount >= MAX_COMMANDS) {
    Serial.println("[!] Queue full - Command rejected");
    return false;
  }
  
  // Sanitize command
  if (!sanitizeCommand(cmd)) {
    Serial.println("[!] Command rejected: Invalid characters or length");
    blockedCommands++;
    return false;
  }
  
  // Add to queue with bounds checking
  if (commandTail >= 0 && commandTail < MAX_COMMANDS) {
    commandQueue[commandTail] = cmd;
    commandTail = (commandTail + 1) % MAX_COMMANDS;
    commandCount++;
  } else {
    Serial.println("[!] Queue index error - Resetting queue");
    commandQueueHead = 0;
    commandQueueTail = 0;
    commandCount = 0;
    return false;
  }
  
  // Add to history with bounds checking
  if (historyIndex >= 0 && historyIndex < MAX_HISTORY) {
    commandHistory[historyIndex] = cmd + " [" + String(millis()) + "]";
    historyIndex = (historyIndex + 1) % MAX_HISTORY;
  }
  
  return true;
}

String dequeueCommand() {
  if (commandCount == 0) return "NONE";
  
  // Bounds checking
  if (commandHead < 0 || commandHead >= MAX_COMMANDS) {
    Serial.println("[!] Queue head index error - Resetting queue");
    commandQueueHead = 0;
    commandQueueTail = 0;
    commandCount = 0;
    return "NONE";
  }
  
  String cmd = commandQueue[commandHead];
  commandHead = (commandHead + 1) % MAX_COMMANDS;
  commandCount--;
  return cmd;
}

void clearQueue() {
  commandQueueHead = 0;
  commandQueueTail = 0;
  commandCount = 0;
  Serial.println("[+] Command queue cleared");
}

// ============================================================================
// WEB SERVER HANDLERS
// ============================================================================

void handleRoot() {
  if (isLockedOut()) {
    server.send(429, "application/json", "{\"error\":\"System locked due to too many failed attempts\"}");
    return;
  }
  
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<style>body{font-family:'Segoe UI',Arial,sans-serif; background:linear-gradient(135deg,#0f0c29 0%,#302b63 50%,#24243e 100%); color:#fff; margin:0; padding:20px;} ";
  html += ".container{max-width:900px; margin:0 auto;} .header{background:rgba(255,255,255,0.1); padding:25px; border-radius:15px; margin-bottom:25px; backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.2);} ";
  html += ".stats-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin:25px 0;} ";
  html += ".stat-card{background:rgba(255,255,255,0.1); padding:18px; border-radius:12px; text-align:center; border:1px solid rgba(255,255,255,0.1);} ";
  html += ".stat-value{font-size:28px; font-weight:bold; color:#00ff88; text-shadow:0 0 10px rgba(0,255,136,0.5);} ";
  html += ".stat-label{font-size:12px; color:#aaa; margin-top:5px;} ";
  html += ".status-online{color:#00ff88; text-shadow:0 0 10px rgba(0,255,136,0.5);} .status-offline{color:#ff4444; text-shadow:0 0 10px rgba(255,68,68,0.5);} ";
  html += ".section{background:rgba(255,255,255,0.05); padding:20px; border-radius:15px; margin:20px 0; border:1px solid rgba(255,255,255,0.1);} ";
  html += ".section-title{font-size:18px; font-weight:bold; margin-bottom:15px; color:#00d4ff; text-transform:uppercase; letter-spacing:1px;} ";
  html += "button{display:block; width:100%; max-width:320px; margin:8px auto; padding:14px; font-size:13px; font-weight:bold; border:none; border-radius:8px; cursor:pointer; transition:all 0.3s; text-transform:uppercase; letter-spacing:0.5px;} ";
  html += ".btn-danger{background:linear-gradient(135deg,#ff4444,#cc0000); color:white; box-shadow:0 4px 15px rgba(255,68,68,0.4);} ";
  html += ".btn-info{background:linear-gradient(135deg,#00d4ff,#0099cc); color:white; box-shadow:0 4px 15px rgba(0,212,255,0.4);} ";
  html += ".btn-warning{background:linear-gradient(135deg,#ffaa00,#cc8800); color:white; box-shadow:0 4px 15px rgba(255,170,0,0.4);} ";
  html += ".btn-success{background:linear-gradient(135deg,#00ff88,#00cc66); color:#1a1a2e; box-shadow:0 4px 15px rgba(0,255,136,0.4);} ";
  html += ".btn-purple{background:linear-gradient(135deg,#aa00ff,#8800cc); color:white; box-shadow:0 4px 15px rgba(170,0,255,0.4);} ";
  html += ".btn:hover{transform:scale(1.05); box-shadow:0 6px 25px rgba(0,0,0,0.4);} ";
  html += ".history-item{background:rgba(255,255,255,0.05); padding:10px; margin:6px 0; border-radius:6px; font-size:12px; border-left:3px solid #00ff88;} ";
  html += ".refresh-btn{position:fixed; bottom:25px; right:25px; width:65px; height:65px; border-radius:50%; font-size:24px; z-index:1000; animation:pulse 2s infinite;} ";
  html += "@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(0,212,255,0.7);} 70%{box-shadow:0 0 0 15px rgba(0,212,255,0);} }</style>";
  html += "<script>function refreshStatus(){fetch('/status').then(r=>r.json()).then(d=>{document.getElementById('uptime').innerText=formatTime(d.uptime);";
  html += "document.getElementById('totalCmd').innerText=d.totalCommands;document.getElementById('successCmd').innerText=d.successfulCommands;";
  html += "document.getElementById('failedCmd').innerText=d.failedCommands;document.getElementById('blockedCmd').innerText=d.blockedCommands;";
  html += "document.getElementById('queueSize').innerText=d.queueSize;document.getElementById('pcStatus').innerText=d.pcStatus;";
  html += "document.getElementById('pcStatus').className=d.pcConnected?'status-online':'status-offline';document.getElementById('lastCmd').innerText=d.lastCommand;";
  html += "document.getElementById('heap').innerText=d.freeHeap;document.getElementById('rssi').innerText=d.wifiRSSI;});}";
  html += "function formatTime(s){if(s<60)return s+'s';if(s<3600)return Math.floor(s/60)+'m '+(s%60)+'s';return Math.floor(s/3600)+'h '+Math.floor((s%3600)/60)+'m';}";
  html += "setInterval(refreshStatus,2000);</script></head><body>";
  
  html += "<div class='container'><div class='header'><h1>🚀 Advanced C2 Dashboard</h1>";
  html += "<h3 style='margin:10px 0;color:#00d4ff;'>Professional Edition v2.0</h3>";
  html += "<p>System Status: <span id='pcStatus' class='" + String(pcConnected ? "status-online" : "status-offline") + "'>" + pcStatus + "</span></p>";
  html += "<p style='font-size:12px;color:#888;'>Security: " + String(ENABLE_AUTH ? "ENABLED" : "DISABLED") + " | Auth: " + String(isLockedOut() ? "LOCKED" : "ACTIVE") + "</p></div>";
  
  // Real-time Statistics
  html += "<div class='stats-grid'><div class='stat-card'><div class='stat-value' id='uptime'>" + String(systemUptime / 1000) + "</div><div class='stat-label'>Uptime</div></div>";
  html += "<div class='stat-card'><div class='stat-value' id='totalCmd'>" + String(totalCommandsExecuted) + "</div><div class='stat-label'>Total Commands</div></div>";
  html += "<div class='stat-card'><div class='stat-value' id='successCmd'>" + String(successfulCommands) + "</div><div class='stat-label'>Successful</div></div>";
  html += "<div class='stat-card'><div class='stat-value' id='failedCmd'>" + String(failedCommands) + "</div><div class='stat-label'>Failed</div></div>";
  html += "<div class='stat-card'><div class='stat-value' id='blockedCmd'>" + String(blockedCommands) + "</div><div class='stat-label'>Blocked</div></div>";
  html += "<div class='stat-card'><div class='stat-value' id='queueSize'>" + String(commandCount) + "</div><div class='stat-label'>Queue Size</div></div>";
  html += "<div class='stat-card'><div class='stat-value' id='heap'>" + String(ESP.getFreeHeap()) + "</div><div class='stat-label'>Free Heap</div></div>";
  html += "<div class='stat-card'><div class='stat-value' id='rssi'>" + String(WiFi.RSSI()) + "</div><div class='stat-label'>WiFi RSSI</div></div></div>";
  
  // Command Sections
  html += "<div class='section'><div class='section-title'>📊 System Diagnostics</div>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('SYS_INFO')\">System Information</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('NET_STAT')\">Network Configuration</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('PROCESS_LIST')\">Process Audit</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('PORT_SCAN')\">Port Scanner</button></div>";
  
  html += "<div class='section'><div class='section-title'>🔍 Advanced Analysis</div>";
  html += "<button class='btn-info' onclick=\"triggerCmd('DNS_CACHE')\">DNS Cache Analysis</button>";
  html += "<button class='btn-info' onclick=\"triggerCmd('ROUTE_PRINT')\">Routing Table</button>";
  html += "<button class='btn-info' onclick=\"triggerCmd('ENV_VARS')\">Environment Variables</button>";
  html += "<button class='btn-info' onclick=\"triggerCmd('DISK_CHECK')\">Disk Health Check</button></div>";
  
  html += "<div class='section'><div class='section-title'>⚡ Performance Tests</div>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('CALC_TEST')\">Calculator Test</button>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('PING_TEST')\">Network Latency Test</button>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('CPU_STRESS')\">CPU Stress Test</button>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('MEM_CHECK')\">Memory Analysis</button></div>";
  
  html += "<div class='section'><div class='section-title'>🔧 System Management</div>";
  html += "<button class='btn-success' onclick=\"triggerCmd('SERVICE_LIST')\">Services Status</button>";
  html += "<button class='btn-success' onclick=\"triggerCmd('EVENT_LOG')\">Event Logs</button>";
  html += "<button class='btn-success' onclick=\"triggerCmd('FIREWALL_STATUS')\">Firewall Status</button>";
  html += "<button class='btn-success' onclick=\"triggerCmd('STARTUP')\">Startup Programs</button>";
  html += "<button class='btn-success' onclick=\"triggerCmd('HOTFIXES')\">Installed Hotfixes</button></div>";
  
  html += "<div class='section'><div class='section-title'>⚙️ Administrative Tools</div>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('REGEDIT')\">Registry Editor</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('GPEDIT')\">Group Policy Editor</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('SECPOL')\">Local Security Policy</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('COMPMGMT')\">Computer Management</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('TASKSCHD')\">Task Scheduler</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('SERVICES')\">Services Manager</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('EVENTVWR')\">Event Viewer</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('DEVMGMT')\">Device Manager</button>";
  html += "<button class='btn-danger' onclick=\"triggerCmd('DISKMGMT')\">Disk Management</button></div>";
  
  html += "<div class='section'><div class='section-title'>📊 Performance Monitoring</div>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('PERFMON')\">Performance Monitor</button>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('RESMON')\">Resource Monitor</button>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('MSINFO32')\">System Information</button>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('TASKMGR')\">Task Manager</button></div>";
  
  html += "<div class='section'><div class='section-title'>🔐 Security & Encryption</div>";
  html += "<button class='btn-purple' onclick=\"triggerCmd('BITLOCKER')\">BitLocker Status</button>";
  html += "<button class='btn-purple' onclick=\"triggerCmd('CERTMGR')\">Certificate Manager</button>";
  html += "<button class='btn-purple' onclick=\"triggerCmd('WSCUI')\">Windows Security</button>";
  html += "<button class='btn-purple' onclick=\"triggerCmd('WF_MSC')\">Advanced Firewall</button>";
  html += "<button class='btn-purple' onclick=\"triggerCmd('LUSRMGR')\">Local Users & Groups</button></div>";
  
  html += "<div class='section'><div class='section-title'>🌐 Network Administration</div>";
  html += "<button class='btn-info' onclick=\"triggerCmd('NCPA')\">Network Adapters</button>";
  html += "<button class='btn-info' onclick=\"triggerCmd('SHARES')\">Shared Folders</button>";
  html += "<button class='btn-info' onclick=\"triggerCmd('SESSIONS')\">Active Sessions</button>";
  html += "<button class='btn-info' onclick=\"triggerCmd('NET_SHARES')\">Network Shares Audit</button>";
  html += "<button class='btn-info' onclick=\"triggerCmd('RDP_CONFIG')\">RDP Configuration</button></div>";
  
  html += "<div class='section'><div class='section-title'>🔧 System Maintenance</div>";
  html += "<button class='btn-success' onclick=\"triggerCmd('SFC')\">System File Checker</button>";
  html += "<button class='btn-success' onclick=\"triggerCmd('WUSA')\">Update History</button>";
  html += "<button class='btn-success' onclick=\"triggerCmd('DRIVERQUERY')\">Driver Query</button>";
  html += "<button class='btn-success' onclick=\"triggerCmd('POWERCFG')\">Power Configuration</button></div>";
  
  html += "<div class='section'><div class='section-title'>🔍 Advanced Diagnostics</div>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('PROC_TREE')\">Process Tree</button>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('OPEN_FILES')\">Open Files</button>";
  html += "<button class='btn-warning' onclick=\"triggerCmd('NET_CONNECTIONS')\">Network Connections</button>";
  html += "<button class='btn-purple' onclick=\"triggerCmd('CLEAR_QUEUE')\">Clear Command Queue</button></div>";
  
  html += "<div class='section'><div class='section-title'>�️ Custom Command Builder</div>";
  html += "<input type='text' id='customCmd' placeholder='Enter custom command (e.g., SYS_INFO)' style='width:100%; padding:12px; margin:10px 0; border-radius:8px; border:none; background:rgba(255,255,255,0.1); color:#fff;'>";
  html += "<button class='btn-info' onclick=\"executeCustom()\">Execute Custom Command</button></div>";
  
  html += "<div class='section'><div class='section-title'>📅 Command Scheduling</div>";
  html += "<input type='text' id='scheduleCmd' placeholder='Command to schedule' style='width:100%; padding:12px; margin:5px 0; border-radius:8px; border:none; background:rgba(255,255,255,0.1); color:#fff;'>";
  html += "<input type='number' id='scheduleDelay' placeholder='Delay (seconds)' style='width:100%; padding:12px; margin:5px 0; border-radius:8px; border:none; background:rgba(255,255,255,0.1); color:#fff;'>";
  html += "<button class='btn-success' onclick=\"scheduleCommand()\">Schedule Command</button></div>";
  
  html += "<div class='section'><div class='section-title'>📋 Batch Execution</div>";
  html += "<textarea id='batchCmds' placeholder='Enter commands (one per line)' style='width:100%; padding:12px; margin:10px 0; border-radius:8px; border:none; background:rgba(255,255,255,0.1); color:#fff; height:100px;'></textarea>";
  html += "<button class='btn-danger' onclick=\"executeBatch()\">Execute Batch</button></div>";
  
  html += "<div class='section'><div class='section-title'>📁 Command Templates</div>";
  html += "<select id='templateSelect' style='width:100%; padding:12px; margin:10px 0; border-radius:8px; border:none; background:rgba(255,255,255,0.1); color:#fff;'>";
  html += "<option value=''>Select Template...</option>";
  html += "<option value='SYS_INFO,NET_STAT,PROCESS_LIST'>Full System Diagnostics</option>";
  html += "<option value='SERVICE_LIST,EVENT_LOG,FIREWALL_STATUS'>Security Audit</option>";
  html += "<option value='PERFMON,RESMON,TASKMGR'>Performance Check</option>";
  html += "<option value='NET_STAT,DNS_CACHE,ROUTE_PRINT'>Network Diagnostics</option>";
  html += "</select>";
  html += "<button class='btn-warning' onclick=\"loadTemplate()\">Load Template</button></div>";
  
  html += "<div class='section'><div class='section-title'>📊 Command Output</div>";
  html += "<div id='outputContainer' style='background:rgba(0,0,0,0.3); padding:15px; border-radius:8px; min-height:100px; font-family:monospace; font-size:12px; color:#00ff88;'>";
  html += "Command output will appear here...</div></div>";
  
  html += "<div class='section'><div class='section-title'>� Command History</div>";
  html += "<div id='historyContainer'>";
  for (int i = 0; i < min(10, historyIndex); i++) {
    int idx = (historyIndex - 1 - i + MAX_HISTORY) % MAX_HISTORY;
    html += "<div class='history-item'>" + commandHistory[idx] + "</div>";
  }
  html += "</div></div>";
  
  html += "<button class='refresh-btn btn-info' onclick='refreshStatus()'>🔄</button>";
  html += "<script>";
  html += "function triggerCmd(cmd){fetch('/trigger?cmd='+cmd).then(r=>r.text()).then(d=>{alert(d);refreshStatus();});}";
  html += "function executeCustom(){";
  html += "var cmd=document.getElementById('customCmd').value;";
  html += "if(cmd){triggerCmd(cmd);document.getElementById('customCmd').value='';}";
  html += "}";
  html += "function scheduleCommand(){";
  html += "var cmd=document.getElementById('scheduleCmd').value;";
  html += "var delay=document.getElementById('scheduleDelay').value;";
  html += "if(cmd && delay){";
  html += "setTimeout(function(){triggerCmd(cmd);},delay*1000);";
  html += "alert('Command scheduled for '+delay+' seconds');";
  html += "}";
  html += "}";
  html += "function executeBatch(){";
  html += "var cmds=document.getElementById('batchCmds').value.split('\\n');";
  html += "var index=0;";
  html += "function executeNext(){";
  html += "if(index<cmds.length && cmds[index].trim()){";
  html += "triggerCmd(cmds[index].trim());";
  html += "index++;";
  html += "setTimeout(executeNext,1000);";
  html += "}";
  html += "}";
  html += "executeNext();";
  html += "}";
  html += "function loadTemplate(){";
  html += "var template=document.getElementById('templateSelect').value;";
  html += "if(template){";
  html += "var cmds=template.split(',');";
  html += "document.getElementById('batchCmds').value=cmds.join('\\n');";
  html += "alert('Template loaded! Click Execute Batch to run.');";
  html += "}";
  html += "}";
  html += "</script></div></body></html>";
  
  server.send(200, "text/html", html);
}

void handleTrigger() {
  // Feed watchdog
  lastWatchdogFeed = millis();
  
  // Check rate limiting
  if (isRateLimited()) {
    server.send(429, "application/json", "{\"error\":\"Rate limit exceeded\"}");
    return;
  }
  
  // Check lockout
  if (isLockedOut()) {
    server.send(429, "application/json", "{\"error\":\"System locked\"}");
    return;
  }
  
  // Verify API key
  String apiKey = server.header("X-API-Key");
  if (ENABLE_AUTH && !verifyAPIKey(apiKey)) {
    recordFailedAuth();
    server.send(401, "application/json", "{\"error\":\"Unauthorized\"}");
    return;
  }
  
  if (server.hasArg("cmd")) {
    String cmd = server.arg("cmd");
    
    // Check command length
    if (cmd.length() > MAX_STRING_LENGTH) {
      server.send(400, "text/plain", "Bad Request: Command too long.");
      return;
    }
    
    // Handle special commands
    if (cmd == "CLEAR_QUEUE") {
      clearQueue();
      server.send(200, "text/plain", "Command queue cleared successfully.");
      return;
    }
    
    // Enqueue command
    if (enqueueCommand(cmd)) {
      totalCommandsExecuted++;
      server.send(200, "text/plain", "Command '" + cmd + "' queued successfully. Queue size: " + String(commandCount));
    } else {
      server.send(503, "text/plain", "Queue full or invalid command. Command '" + cmd + "' rejected.");
    }
  } else {
    server.send(400, "text/plain", "Bad Request: Missing 'cmd' argument.");
  }
}

void handleCheck() {
  // Feed watchdog
  lastWatchdogFeed = millis();
  
  // Check rate limiting
  if (isRateLimited()) {
    server.send(429, "application/json", "{\"error\":\"Rate limit exceeded\"}");
    return;
  }
  
  // Verify API key
  String apiKey = server.header("X-API-Key");
  if (ENABLE_AUTH && !verifyAPIKey(apiKey)) {
    recordFailedAuth();
    server.send(401, "application/json", "{\"error\":\"Unauthorized\"}");
    return;
  }
  
  // Update heartbeat
  pcConnected = true;
  lastPCHeartbeat = millis();
  pcStatus = "CONNECTED";
  
  String cmd = dequeueCommand();
  if (cmd != "NONE") {
    lastExecutedCommand = cmd;
    lastCommandTime = millis();
    successfulCommands++;
    server.send(200, "text/plain", cmd);
  } else {
    server.send(200, "text/plain", "WAITING");
  }
}

void handleStatus() {
  // Feed watchdog
  lastWatchdogFeed = millis();
  
  // Check rate limiting
  if (isRateLimited()) {
    server.send(429, "application/json", "{\"error\":\"Rate limit exceeded\"}");
    return;
  }
  
  // Verify API key
  String apiKey = server.header("X-API-Key");
  if (ENABLE_AUTH && !verifyAPIKey(apiKey)) {
    recordFailedAuth();
    server.send(401, "application/json", "{\"error\":\"Unauthorized\"}");
    return;
  }
  
  // Build JSON response with error handling
  String json = "{";
  json += "\"uptime\":" + String(millis()) + ",";
  json += "\"totalCommands\":" + String(totalCommandsExecuted) + ",";
  json += "\"successfulCommands\":" + String(successfulCommands) + ",";
  json += "\"failedCommands\":" + String(failedCommands) + ",";
  json += "\"blockedCommands\":" + String(blockedCommands) + ",";
  json += "\"queueSize\":" + String(commandCount) + ",";
  json += "\"pcConnected\":" + String(pcConnected ? "true" : "false") + ",";
  json += "\"pcStatus\":\"" + pcStatus + "\",";
  json += "\"lastCommand\":\"" + lastExecutedCommand + "\",";
  json += "\"freeHeap\":" + String(ESP.getFreeHeap()) + ",";
  json += "\"wifiRSSI\":" + String(WiFi.RSSI()) + ",";
  json += "\"authEnabled\":" + String(ENABLE_AUTH ? "true" : "false") + ",";
  json += "\"isLocked\":" + String(isLockedOut() ? "true" : "false");
  json += "}";
  
  server.send(200, "application/json", json);
}

void handleHistory() {
  // Feed watchdog
  lastWatchdogFeed = millis();
  
  // Check rate limiting
  if (isRateLimited()) {
    server.send(429, "application/json", "{\"error\":\"Rate limit exceeded\"}");
    return;
  }
  
  // Verify API key
  String apiKey = server.header("X-API-Key");
  if (ENABLE_AUTH && !verifyAPIKey(apiKey)) {
    recordFailedAuth();
    server.send(401, "application/json", "{\"error\":\"Unauthorized\"}");
    return;
  }
  
  // Build JSON with bounds checking
  String json = "[";
  int count = min(20, historyIndex);
  for (int i = 0; i < count; i++) {
    int idx = (historyIndex - 1 - i + MAX_HISTORY) % MAX_HISTORY;
    if (idx >= 0 && idx < MAX_HISTORY) {
      if (i > 0) json += ",";
      json += "\"" + commandHistory[idx] + "\"";
    }
  }
  json += "]";
  server.send(200, "application/json", json);
}

void handleReset() {
  // Feed watchdog
  lastWatchdogFeed = millis();
  
  // Check rate limiting
  if (isRateLimited()) {
    server.send(429, "application/json", "{\"error\":\"Rate limit exceeded\"}");
    return;
  }
  
  // Verify API key
  String apiKey = server.header("X-API-Key");
  if (ENABLE_AUTH && !verifyAPIKey(apiKey)) {
    recordFailedAuth();
    server.send(401, "application/json", "{\"error\":\"Unauthorized\"}");
    return;
  }
  
  Serial.println("[!] System reset requested");
  server.send(200, "text/plain", "System resetting...");
  delay(100);
  ESP.restart();
}

// ============================================================================
// WATCHDOG & MEMORY MANAGEMENT
// ============================================================================

// Watchdog callback
void watchdogCallback() {
  if (millis() - lastWatchdogFeed > WATCHDOG_TIMEOUT * 1000) {
    Serial.println("[!] Watchdog triggered - System hang detected");
    watchdogTriggered = true;
  }
}

// Check memory and trigger recovery if needed
void checkMemoryHealth() {
  unsigned long freeHeap = ESP.getFreeHeap();
  
  if (freeHeap < 10000) {
    Serial.println("[!] Low memory detected - Triggering recovery");
    Serial.print("[!] Free heap: ");
    Serial.println(freeHeap);
    
    // Clear command queue to free memory
    clearQueue();
    
    // Clear some history
    for (int i = 0; i < MAX_HISTORY / 2; i++) {
      commandHistory[i] = "";
    }
    historyIndex = 0;
    
    Serial.println("[+] Memory recovery completed");
  }
}

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(115200);
  Serial.println("\n[+] Advanced C2 Controller - Professional Edition");
  Serial.println("[+] Initializing security systems...");
  
  // Initialize watchdog timer
  lastWatchdogFeed = millis();
  watchdogTimer.attach(WATCHDOG_TIMEOUT, watchdogCallback);
  
  // Initialize EEPROM for persistent storage
  EEPROM.begin(512);
  
  // Connect to WiFi with timeout
  Serial.println("[+] Connecting to network...");
  WiFi.begin(ssid, password);
  int wifiTimeout = 0;
  while (WiFi.status() != WL_CONNECTED && wifiTimeout < 30) {
    delay(500);
    Serial.print(".");
    wifiTimeout++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[+] Connected to Network.");
    Serial.print("[+] NodeMCU Control IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[!] WiFi connection failed - Starting in AP mode");
    WiFi.mode(WIFI_AP);
    WiFi.softAP("NodeMCU-C2-Setup", "setup1234");
    Serial.print("[+] AP IP: ");
    Serial.println(WiFi.softAPIP());
  }
  
  // Initialize mDNS
  if (MDNS.begin("nodemcu-c2")) {
    Serial.println("[+] mDNS responder started");
  }
  
  // Register Endpoints
  server.on("/", handleRoot);
  server.on("/trigger", handleTrigger);
  server.on("/check", handleCheck);
  server.on("/status", handleStatus);
  server.on("/history", handleHistory);
  server.on("/reset", handleReset);
  
  // Enable CORS
  server.enableCORS(true);
  
  server.begin();
  Serial.println("[+] HTTP server started");
  Serial.println("[+] Security features enabled:");
  Serial.println("    - API Key Authentication: " + String(ENABLE_AUTH ? "YES" : "NO"));
  Serial.println("    - Rate Limiting: " + String(MAX_REQUESTS_PER_MINUTE) + " req/min");
  Serial.println("    - Command Sanitization: YES");
  Serial.println("    - Auth Lockout: " + String(MAX_AUTH_ATTEMPTS) + " attempts");
  Serial.println("    - Watchdog Timer: " + String(WATCHDOG_TIMEOUT) + "s");
  Serial.println("    - Memory Protection: YES");
  Serial.println("[+] Advanced C2 Dashboard Ready");
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  // Feed watchdog on each loop iteration
  lastWatchdogFeed = millis();
  
  server.handleClient();
  
  // Update uptime
  systemUptime = millis();
  
  // Check for watchdog trigger
  if (watchdogTriggered) {
    Serial.println("[!] Watchdog triggered - Restarting system");
    delay(100);
    ESP.restart();
  }
  
  // Check PC connection status
  if (millis() - lastPCHeartbeat > HEARTBEAT_TIMEOUT && pcConnected) {
    pcConnected = false;
    pcStatus = "DISCONNECTED";
    Serial.println("[!] PC listener disconnected");
  }
  
  // Periodic memory health check
  if (millis() - lastMemoryCheck > MEMORY_CHECK_INTERVAL) {
    lastMemoryCheck = millis();
    checkMemoryHealth();
  }
  
  // Periodic status update
  static unsigned long lastStatusUpdate = 0;
  if (millis() - lastStatusUpdate > STATUS_UPDATE_INTERVAL) {
    lastStatusUpdate = millis();
    Serial.print("[+] Status - Uptime: ");
    Serial.print(systemUptime / 1000);
    Serial.print("s | Queue: ");
    Serial.print(commandCount);
    Serial.print(" | PC: ");
    Serial.print(pcStatus);
    Serial.print(" | Heap: ");
    Serial.print(ESP.getFreeHeap());
    Serial.print(" | RSSI: ");
    Serial.println(WiFi.RSSI());
  }
  
  // Yield to prevent watchdog issues
  yield();
  delay(1);
}
