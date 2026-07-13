#!/usr/bin/env python3
"""
Advanced C2 Listener - Professional Remote Administration Framework
Educational Proof-of-Concept for Authorized Security Testing
Version: 2.0 Professional
"""

import time
import requests
import subprocess
import os
import json
import logging
import hashlib
import hmac
import secrets
import shutil
from datetime import datetime, timedelta
from threading import Thread, Lock
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import platform
import signal
import sys
import argparse
import base64

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

class Config:
    """Centralized configuration management"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from JSON file with robust error handling"""
        default_config = {
            "server": {
                "host": "192.168.1.15",
                "port": 80,
                "use_mDNS": True,
                "mDNS_hostname": "nodemcu-c2",
                "connection_timeout": 10,
                "max_retries": 3,
                "retry_delay": 2
            },
            "security": {
                "api_key": "CHANGE_THIS_TO_SECURE_RANDOM_KEY",
                "enable_auth": True,
                "rate_limit_per_minute": 60,
                "max_queue_size": 20,
                "allowed_clients": ["192.168.1.100", "192.168.1.101"],
                "enable_cors": True,
                "enable_ip_whitelist": True,
                "session_timeout": 3600,
                "max_sessions": 5
            },
            "logging": {
                "enable_serial": True,
                "log_level": "INFO",
                "max_history": 100,
                "enable_detailed_logging": True,
                "log_command_output": True
            },
            "monitoring": {
                "heartbeat_interval": 10000,
                "status_update_interval": 30000,
                "connection_timeout": 10000,
                "health_check_interval": 60000,
                "auto_recovery": True,
                "alert_on_failure": True
            },
            "commands": {
                "enable_dangerous_commands": False,
                "require_confirmation": True,
                "auto_clear_on_success": False,
                "enable_custom_commands": True,
                "enable_scheduling": True,
                "enable_batch_execution": True,
                "enable_templates": True
            },
            "advanced": {
                "enable_telegram_bot": False,
                "telegram_bot_token": "",
                "enable_discord_bot": False,
                "discord_bot_token": "",
                "enable_ota_updates": True,
                "enable_backup": True,
                "backup_interval": 86400,
                "multiple_devices": False,
                "devices": []
            },
            "statistics": {
                "enable_usage_tracking": True,
                "track_command_frequency": True,
                "track_success_rate": True
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        default_config.update(loaded)
                    else:
                        print(f"Warning: Config file must contain a JSON object")
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in config file: {e}")
            except IOError as e:
                print(f"Warning: Could not read config file: {e}")
            except Exception as e:
                print(f"Warning: Unexpected error loading config: {e}")
        
        return default_config
    
    def get(self, *keys, default=None):
        """Get nested configuration value"""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

# ============================================================================
# SECURITY & AUTHENTICATION
# ============================================================================

class SecurityManager:
    """Handles authentication, encryption, and security operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.get("security", "api_key")
        self.enable_auth = config.get("security", "enable_auth")
        self.rate_limit = config.get("security", "rate_limit_per_minute")
        self.request_timestamps = []
        self.session_token = secrets.token_hex(32)
        self.enable_ip_whitelist = config.get("security", "enable_ip_whitelist", default=False)
        self.allowed_clients = config.get("security", "allowed_clients", default=[])
        self.session_timeout = config.get("security", "session_timeout", default=3600)
        self.max_sessions = config.get("security", "max_sessions", default=5)
        self.sessions = {}
        self.sessions_lock = Lock()
        
    def verify_api_key(self, provided_key: str) -> bool:
        """Verify API key using constant-time comparison"""
        if not self.enable_auth:
            return True
        return hmac.compare_digest(self.api_key, provided_key)
    
    def check_ip_whitelist(self, client_ip: str) -> bool:
        """Check if client IP is in whitelist"""
        if not self.enable_ip_whitelist:
            return True
        if not self.allowed_clients:
            return True
        return client_ip in self.allowed_clients
    
    def create_session(self, client_ip: str) -> str:
        """Create new session for client"""
        with self.sessions_lock:
            # Clean expired sessions
            now = datetime.now()
            expired = [sid for sid, data in self.sessions.items() 
                      if now - data['created'] > timedelta(seconds=self.session_timeout)]
            for sid in expired:
                del self.sessions[sid]
            
            # Check max sessions
            if len(self.sessions) >= self.max_sessions:
                return None
            
            # Create new session
            session_id = secrets.token_hex(16)
            self.sessions[session_id] = {
                'ip': client_ip,
                'created': now,
                'last_activity': now
            }
            return session_id
    
    def verify_session(self, session_id: str, client_ip: str) -> bool:
        """Verify session validity"""
        with self.sessions_lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            now = datetime.now()
            
            # Check timeout
            if now - session['last_activity'] > timedelta(seconds=self.session_timeout):
                del self.sessions[session_id]
                return False
            
            # Check IP match
            if session['ip'] != client_ip:
                return False
            
            # Update activity
            session['last_activity'] = now
            return True
    
    def check_rate_limit(self) -> bool:
        """Check if request is within rate limit"""
        now = datetime.now()
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < timedelta(minutes=1)
        ]
        
        if len(self.request_timestamps) >= self.rate_limit:
            return False
        
        self.request_timestamps.append(now)
        return True
    
    def generate_signature(self, data: str) -> str:
        """Generate HMAC signature for data"""
        return hmac.new(
            self.api_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def sanitize_command(self, command: str) -> str:
        """Sanitize command input to prevent injection"""
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
        return ''.join(c for c in command if c in allowed_chars)

# ============================================================================
# AUDIT & LOGGING
# ============================================================================

class AuditLogger:
    """Professional audit logging system with enhanced features"""
    
    def __init__(self, config: Config):
        self.config = config
        self.log_file = "c2_audit.log"
        self.detailed_logging = config.get("logging", "enable_detailed_logging", default=True)
        self.log_output = config.get("logging", "log_command_output", default=True)
        self.logger = self._setup_logger()
        self.audit_lock = Lock()
        self.command_log = []
        
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logging with error handling"""
        logger = logging.getLogger("C2_AUDIT")
        logger.setLevel(getattr(logging, self.config.get("logging", "log_level", default="INFO")))
        
        # Prevent duplicate handlers
        if logger.handlers:
            logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with error handling
        try:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except IOError as e:
            print(f"Warning: Could not create log file: {e}")
        
        # Console handler with error handling
        try:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        except Exception as e:
            print(f"Warning: Could not setup console logging: {e}")
        
        return logger
    
    def log_command(self, command: str, status: str, details: str = "", output: str = ""):
        """Log command execution with enhanced details"""
        with self.audit_lock:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "command": command,
                "status": status,
                "details": details,
                "output": output if self.log_output else None
            }
            
            if self.detailed_logging:
                self.command_log.append(log_entry)
                if len(self.command_log) > 1000:
                    self.command_log.pop(0)
            
            log_msg = f"CMD: {command} | STATUS: {status} | {details}"
            if output and self.log_output:
                log_msg += f" | OUTPUT: {output[:200]}"
            self.logger.info(log_msg)
    
    def log_security_event(self, event_type: str, details: str, client_ip: str = ""):
        """Log security-related events with IP tracking"""
        with self.audit_lock:
            timestamp = datetime.now().isoformat()
            log_msg = f"SECURITY: {event_type} | {details}"
            if client_ip:
                log_msg += f" | IP: {client_ip}"
            log_msg += f" | TIMESTAMP: {timestamp}"
            self.logger.warning(log_msg)
    
    def log_error(self, error: str, context: str = "", stack_trace: str = ""):
        """Log errors with optional stack trace"""
        with self.audit_lock:
            timestamp = datetime.now().isoformat()
            log_msg = f"ERROR: {error} | {context} | TIMESTAMP: {timestamp}"
            if stack_trace and self.detailed_logging:
                log_msg += f" | STACK: {stack_trace[:500]}"
            self.logger.error(log_msg)
    
    def get_command_log(self, count: int = 100) -> List[Dict]:
        """Get recent command log entries"""
        with self.audit_lock:
            return self.command_log[-count:]

# ============================================================================
# STATISTICS & MONITORING
# ============================================================================

@dataclass
class SystemStats:
    """Enhanced system statistics tracking"""
    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    blocked_commands: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_command: Optional[str] = None
    last_command_time: Optional[datetime] = None
    uptime: float = 0.0
    command_frequency: Dict[str, int] = field(default_factory=dict)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_errors: int = 0
    connection_failures: int = 0
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_commands == 0:
            return 0.0
        return (self.successful_commands / self.total_commands) * 100
    
    def update_command_frequency(self, command: str):
        """Track command frequency"""
        self.command_frequency[command] = self.command_frequency.get(command, 0) + 1
    
    def get_top_commands(self, count: int = 5) -> List[Tuple[str, int]]:
        """Get most used commands"""
        return sorted(self.command_frequency.items(), key=lambda x: x[1], reverse=True)[:count]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_commands": self.total_commands,
            "successful_commands": self.successful_commands,
            "failed_commands": self.failed_commands,
            "blocked_commands": self.blocked_commands,
            "success_rate": self.get_success_rate(),
            "start_time": self.start_time.isoformat(),
            "last_command": self.last_command,
            "last_command_time": self.last_command_time.isoformat() if self.last_command_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "network_errors": self.network_errors,
            "connection_failures": self.connection_failures,
            "top_commands": self.get_top_commands()
        }

class CommandHistory:
    """Thread-safe command history management"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.history: List[Dict] = []
        self.lock = Lock()
    
    def add(self, command: str, status: str, execution_time: float = 0.0):
        """Add command to history"""
        with self.lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "status": status,
                "execution_time": execution_time
            }
            self.history.append(entry)
            
            if len(self.history) > self.max_size:
                self.history.pop(0)
    
    def get_recent(self, count: int = 10) -> List[Dict]:
        """Get recent commands"""
        with self.lock:
            return self.history[-count:]
    
    def clear(self):
        """Clear history"""
        with self.lock:
            self.history.clear()

# ============================================================================
# COMMAND EXECUTION ENGINE
# ============================================================================

class CommandExecutor:
    """Advanced command execution with safety checks"""
    
    def __init__(self, config: Config, security: SecurityManager, audit: AuditLogger):
        self.config = config
        self.security = security
        self.audit = audit
        self.os_type = os.name
        self.platform_system = platform.system()
        self.enable_dangerous = config.get("commands", "enable_dangerous_commands", default=False)
        
        # Command whitelist
        self.whitelisted_commands = self._build_whitelist()
    
    def _build_whitelist(self) -> set:
        """Build command whitelist"""
        base_commands = {
            "SYS_INFO", "NET_STAT", "PROCESS_LIST", "PORT_SCAN", "CALC_TEST",
            "DNS_CACHE", "ROUTE_PRINT", "ENV_VARS", "DISK_CHECK", "PING_TEST",
            "CPU_STRESS", "MEM_CHECK", "SERVICE_LIST", "EVENT_LOG", "FIREWALL_STATUS",
            "NET_DIAG", "USER_AUDIT", "SCHED_TASKS", "INSTALLED_PROGS", "BOOT_TIME",
            "NET_CONNECTIONS", "STARTUP", "HOTFIXES", "REGEDIT", "GPEDIT", "SECPOL",
            "COMPMGMT", "TASKSCHD", "SERVICES", "EVENTVWR", "PERFMON", "RESMON",
            "DEVMGMT", "DISKMGMT", "SHARES", "SESSIONS", "NCPA", "WF_MSC",
            "LUSRMGR", "POWERCFG", "MSINFO32", "DRIVERQUERY", "SFC", "WUSA",
            "BITLOCKER", "CERTMGR", "WSCUI", "RDP_CONFIG", "PROC_TREE", "OPEN_FILES",
            "NET_SHARES", "TASKMGR", "CLEAR_QUEUE"
        }
        
        if self.enable_dangerous:
            dangerous_commands = {
                # Add dangerous commands if enabled
            }
            base_commands.update(dangerous_commands)
        
        return base_commands
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate command against whitelist and security rules"""
        sanitized = self.security.sanitize_command(command)
        
        if sanitized != command:
            return False, "Command contains invalid characters"
        
        if command not in self.whitelisted_commands:
            return False, "Command not in whitelist"
        
        return True, "Valid"
    
    def execute_command(self, command: str, window_title: str = "Command Output") -> bool:
        """Execute system command safely with enhanced error handling"""
        if not command or not isinstance(command, str):
            self.audit.log_error("Invalid command", f"Command: {command}")
            return False
        
        try:
            if self.os_type == 'nt':
                # Sanitize window title to prevent injection
                safe_title = ''.join(c for c in window_title if c.isalnum() or c in ' _-')
                subprocess.Popen(
                    ["cmd.exe", "/c", f"start cmd.exe /k title {safe_title} && {command}"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    shell=False
                )
            else:
                # Try multiple terminal emulators with fallback
                terminals = [
                    ["gnome-terminal", "--title", window_title, "--", "bash", "-c", 
                     f"{command}; read -p 'Press Enter to close...'"]
                ]
                
                for term_cmd in terminals:
                    try:
                        subprocess.Popen(term_cmd, shell=False)
                        return True
                    except FileNotFoundError:
                        continue
                
                # Fallback to basic shell
                subprocess.Popen(["bash", "-c", command], shell=False)
            return True
        except subprocess.SubprocessError as e:
            self.audit.log_error(str(e), f"Subprocess error: {command}")
            return False
        except Exception as e:
            self.audit.log_error(str(e), f"Command: {command}")
            return False
    
    def execute_gui(self, command: List[str]) -> bool:
        """Execute GUI application with validation"""
        if not command or not isinstance(command, list):
            self.audit.log_error("Invalid command", f"GUI: {command}")
            return False
        
        if not command[0]:
            self.audit.log_error("Empty command", "GUI execution")
            return False
        
        try:
            subprocess.Popen(command, shell=False)
            return True
        except FileNotFoundError:
            self.audit.log_error("Application not found", f"GUI: {command[0]}")
            return False
        except subprocess.SubprocessError as e:
            self.audit.log_error(str(e), f"GUI: {command}")
            return False
        except Exception as e:
            self.audit.log_error(str(e), f"GUI: {command}")
            return False

# ============================================================================
# PAYLOAD EXECUTION ENGINE
# ============================================================================

class PayloadExecutor:
    """Advanced payload execution with comprehensive command mapping"""
    
    def __init__(self, executor: CommandExecutor, audit: AuditLogger, stats: SystemStats, history: CommandHistory):
        self.executor = executor
        self.audit = audit
        self.stats = stats
        self.history = history
        self.command_map = self._build_command_map()
    
    def _build_command_map(self) -> Dict:
        """Build comprehensive command mapping"""
        return {
            # System Diagnostics
            "SYS_INFO": {"nt": ("systeminfo", "System Information"), "posix": ("uname -a", "System Information")},
            "NET_STAT": {"nt": ("ipconfig /all", "Network Configuration"), "posix": ("ifconfig", "Network Configuration")},
            "PROCESS_LIST": {"nt": ("tasklist /v", "Process List"), "posix": ("ps aux", "Process List")},
            "PORT_SCAN": {"nt": ("netstat -ano", "Port Scanner"), "posix": ("netstat -tulpn", "Port Scanner")},
            # Advanced Analysis
            "DNS_CACHE": {"nt": ("ipconfig /displaydns", "DNS Cache"), "posix": ("cat /etc/resolv.conf", "DNS Configuration")},
            "ROUTE_PRINT": {"nt": ("route print", "Routing Table"), "posix": ("route -n", "Routing Table")},
            "ENV_VARS": {"nt": ("set", "Environment Variables"), "posix": ("printenv", "Environment Variables")},
            "DISK_CHECK": {"nt": ("wmic logicaldisk get caption,description,freespace,size,volumename", "Disk Information"), "posix": ("df -h", "Disk Information")},
            # Performance Tests
            "CALC_TEST": {"nt": ("GUI", ["calc.exe"]), "posix": ("GUI", ["gnome-calculator"])},
            "PING_TEST": {"nt": ("ping -n 4 127.0.0.1", "Network Latency Test"), "posix": ("ping -c 4 127.0.0.1", "Network Latency Test")},
            "CPU_STRESS": {"nt": ("wmic cpu get loadpercentage /value", "CPU Load"), "posix": ("top -bn1 | head -20", "CPU Load")},
            "MEM_CHECK": {"nt": ("wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value", "Memory Information"), "posix": ("free -h", "Memory Information")},
            # System Management
            "SERVICE_LIST": {"nt": ("sc query state= all", "Services Status"), "posix": ("systemctl list-units --type=service", "Services Status")},
            "EVENT_LOG": {"nt": ("wevtutil qe System /c:10 /rd:true /f:text", "Event Logs"), "posix": ("journalctl -n 20 --no-pager", "System Logs")},
            "FIREWALL_STATUS": {"nt": ("netsh advfirewall show allprofiles", "Firewall Status"), "posix": ("sudo ufw status", "Firewall Status")},
            "STARTUP": {"nt": ("wmic startup get command,caption", "Startup Programs"), "posix": ("systemctl list-unit-files --type=service", "Startup Services")},
            "HOTFIXES": {"nt": ("wmic qfe get hotfixid,installedon", "Hotfixes"), "posix": ("dpkg --get-selections | grep -v deinstall", "Installed Packages")},
            "NET_DIAG": {"nt": ("netsh interface ipv4 show interfaces", "Network Interfaces"), "posix": ("ip link show", "Network Interfaces")},
            "USER_AUDIT": {"nt": ("net user", "User Accounts"), "posix": ("whoami && id", "User Information")},
            "SCHED_TASKS": {"nt": ("schtasks /query /fo LIST", "Scheduled Tasks"), "posix": ("crontab -l", "Cron Jobs")},
            "INSTALLED_PROGS": {"nt": ("wmic product get name,version,vendor", "Installed Programs"), "posix": ("dpkg -l", "Installed Packages")},
            "BOOT_TIME": {"nt": ("wmic os get lastbootuptime", "Boot Time"), "posix": ("uptime -s", "Boot Time")},
            "NET_CONNECTIONS": {"nt": ("netstat -b", "Network Connections with Processes"), "posix": ("ss -tulpn", "Network Connections")},
            # Administrative Tools
            "REGEDIT": {"nt": ("GUI", ["regedit.exe"]), "posix": ("nano /etc/passwd", "System Configuration")},
            "GPEDIT": {"nt": ("GUI", ["gpedit.msc"]), "posix": ("sudo visudo", "Sudoers Configuration")},
            "SECPOL": {"nt": ("GUI", ["secpol.msc"]), "posix": ("sudo iptables -L -v", "Firewall Rules")},
            "COMPMGMT": {"nt": ("GUI", ["compmgmt.msc"]), "posix": ("sudo systemctl status", "System Status")},
            "TASKSCHD": {"nt": ("GUI", ["taskschd.msc"]), "posix": ("crontab -e", "Cron Editor")},
            "SERVICES": {"nt": ("GUI", ["services.msc"]), "posix": ("sudo systemctl list-units --type=service --state=running", "Running Services")},
            "EVENTVWR": {"nt": ("GUI", ["eventvwr.msc"]), "posix": ("sudo journalctl -f", "Live Journal Logs")},
            "PERFMON": {"nt": ("GUI", ["perfmon.exe"]), "posix": ("htop", "System Monitor")},
            "TASKMGR": {"nt": ("GUI", ["taskmgr.exe"]), "posix": ("top", "Task Manager")},
            "RESMON": {"nt": ("GUI", ["resmon.exe"]), "posix": ("iotop", "I/O Monitor")},
            "DEVMGMT": {"nt": ("GUI", ["devmgmt.msc"]), "posix": ("lspci -v", "PCI Devices")},
            "DISKMGMT": {"nt": ("GUI", ["diskmgmt.msc"]), "posix": ("sudo fdisk -l", "Disk Partitions")},
            "SHARES": {"nt": ("net share", "Shared Folders"), "posix": ("sudo exportfs -v", "NFS Shares")},
            "SESSIONS": {"nt": ("query session", "Active Sessions"), "posix": ("who", "Logged In Users")},
            "NCPA": {"nt": ("GUI", ["ncpa.cpl"]), "posix": ("nmcli device show", "Network Devices")},
            "WF_MSC": {"nt": ("GUI", ["wf.msc"]), "posix": ("sudo ufw show verbose", "Firewall Details")},
            "LUSRMGR": {"nt": ("GUI", ["lusrmgr.msc"]), "posix": ("sudo cat /etc/group", "User Groups")},
            "POWERCFG": {"nt": ("powercfg /list", "Power Plans"), "posix": ("upower -i /org/freedesktop/UPower", "Power Status")},
            "MSINFO32": {"nt": ("GUI", ["msinfo32.exe"]), "posix": ("sudo dmidecode", "Hardware Info")},
            "DRIVERQUERY": {"nt": ("driverquery", "Installed Drivers"), "posix": ("lsmod", "Kernel Modules")},
            "SFC": {"nt": ("sfc /scannow", "System File Checker"), "posix": ("sudo debsums -c", "Package Integrity")},
            "WUSA": {"nt": ("wmic qfe list", "Update History"), "posix": ("apt list --upgradable", "Available Updates")},
            "BITLOCKER": {"nt": ("manage-bde -status", "BitLocker Status"), "posix": ("sudo cryptsetup luksDump", "LUKS Info")},
            "CERTMGR": {"nt": ("GUI", ["certmgr.msc"]), "posix": ("sudo update-ca-certificates --fresh", "Certificates")},
            "WSCUI": {"nt": ("GUI", ["windowsdefender://"]), "posix": ("sudo ufw status verbose", "Security Status")},
            "RDP_CONFIG": {"nt": ("reg query \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\"", "RDP Settings"), "posix": ("systemctl status sshd", "SSH Status")},
            "NET_SHARES": {"nt": ("powershell \"Get-SmbShare | Select-Object Name,Path,Description\"", "SMB Shares"), "posix": ("showmount -e localhost", "NFS Exports")},
            "PROC_TREE": {"nt": ("wmic process get name,parentprocessid,processid", "Process Tree"), "posix": ("pstree -p", "Process Tree")},
            "OPEN_FILES": {"nt": ("openfiles /query /v", "Open Files"), "posix": ("sudo lsof", "Open Files")}
        }
    
    def execute(self, command_type: str) -> bool:
        """Execute payload with validation and logging"""
        start_time = time.time()
        
        # Validate command
        is_valid, reason = self.executor.validate_command(command_type)
        if not is_valid:
            self.audit.log_security_event("COMMAND_BLOCKED", f"{command_type} - {reason}")
            self.stats.blocked_commands += 1
            return False
        
        # Get command mapping
        if command_type not in self.command_map:
            self.audit.log_error("Unknown command", command_type)
            return False
        
        cmd_map = self.command_map[command_type]
        os_type = "nt" if self.executor.os_type == 'nt' else "posix"
        
        if os_type not in cmd_map:
            self.audit.log_error("Platform not supported", f"{command_type} on {os_type}")
            return False
        
        cmd_data = cmd_map[os_type]
        success = False
        
        try:
            if cmd_data[0] == "GUI":
                success = self.executor.execute_gui(cmd_data[1])
            else:
                success = self.executor.execute_command(cmd_data[0], cmd_data[1])
        except Exception as e:
            self.audit.log_error(str(e), f"Command: {command_type}")
        
        execution_time = time.time() - start_time
        
        # Update statistics
        self.stats.total_commands += 1
        if success:
            self.stats.successful_commands += 1
        else:
            self.stats.failed_commands += 1
        self.stats.last_command = command_type
        self.stats.last_command_time = datetime.now()
        
        # Add to history
        self.history.add(command_type, "SUCCESS" if success else "FAILED", execution_time)
        
        # Log execution
        self.audit.log_command(command_type, "SUCCESS" if success else "FAILED", f"Time: {execution_time:.3f}s")
        
        return success

# ============================================================================
# C2 CLIENT - MAIN CONTROLLER
# ============================================================================

class HealthMonitor:
    """System health monitoring and auto-recovery"""
    
    def __init__(self, config: Config, audit: AuditLogger, stats: SystemStats):
        self.config = config
        self.audit = audit
        self.stats = stats
        self.health_check_interval = config.get("monitoring", "health_check_interval", default=60000)
        self.auto_recovery = config.get("monitoring", "auto_recovery", default=True)
        self.alert_on_failure = config.get("monitoring", "alert_on_failure", default=True)
        self.health_status = "HEALTHY"
        self.last_health_check = datetime.now()
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
    def check_system_health(self) -> bool:
        """Perform comprehensive health check with graceful degradation"""
        self.last_health_check = datetime.now()
        
        try:
            import psutil
            
            # Check memory usage with timeout protection
            try:
                memory = psutil.virtual_memory()
                self.stats.memory_usage = memory.percent
            except Exception as mem_error:
                self.audit.log_error(str(mem_error), "Memory check failed")
                self.stats.memory_usage = 0.0
            
            # Check CPU usage with timeout protection
            try:
                cpu = psutil.cpu_percent(interval=0.5)
                self.stats.cpu_usage = cpu
            except Exception as cpu_error:
                self.audit.log_error(str(cpu_error), "CPU check failed")
                self.stats.cpu_usage = 0.0
            
            # Check if system is healthy
            if self.stats.memory_usage > 90 or self.stats.cpu_usage > 90:
                self.health_status = "CRITICAL"
                if self.alert_on_failure:
                    self.audit.log_security_event("HEALTH_CRITICAL", 
                        f"Memory: {self.stats.memory_usage}%, CPU: {self.stats.cpu_usage}%")
                return False
            elif self.stats.memory_usage > 75 or self.stats.cpu_usage > 75:
                self.health_status = "WARNING"
                if self.alert_on_failure:
                    self.audit.log_security_event("HEALTH_WARNING", 
                        f"Memory: {self.stats.memory_usage}%, CPU: {self.stats.cpu_usage}%")
                return True
            else:
                self.health_status = "HEALTHY"
                return True
                
        except ImportError:
            # psutil not available, basic check
            self.health_status = "HEALTHY"
            self.stats.memory_usage = 0.0
            self.stats.cpu_usage = 0.0
            return True
        except Exception as e:
            self.audit.log_error(str(e), "Health check failed")
            self.health_status = "ERROR"
            self.stats.memory_usage = 0.0
            self.stats.cpu_usage = 0.0
            return True  # Don't fail on health check errors
    
    def attempt_recovery(self) -> bool:
        """Attempt automatic recovery"""
        if not self.auto_recovery:
            return False
        
        if self.recovery_attempts >= self.max_recovery_attempts:
            self.audit.log_error("Max recovery attempts reached", "Auto-recovery disabled")
            return False
        
        self.recovery_attempts += 1
        self.audit.log_security_event("RECOVERY_ATTEMPT", f"Attempt {self.recovery_attempts}/{self.max_recovery_attempts}")
        
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear old logs
            if len(self.audit.command_log) > 500:
                self.audit.command_log = self.audit.command_log[-500:]
            
            # Reset recovery counter on success
            self.recovery_attempts = 0
            self.health_status = "HEALTHY"
            return True
            
        except Exception as e:
            self.audit.log_error(str(e), "Recovery failed")
            return False
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        return {
            "status": self.health_status,
            "last_check": self.last_health_check.isoformat(),
            "memory_usage": self.stats.memory_usage,
            "cpu_usage": self.stats.cpu_usage,
            "recovery_attempts": self.recovery_attempts,
            "auto_recovery_enabled": self.auto_recovery
        }

class BackupManager:
    """Configuration backup and restore system"""
    
    def __init__(self, config: Config, audit: AuditLogger):
        self.config = config
        self.audit = audit
        self.backup_interval = config.get("advanced", "backup_interval", default=86400)
        self.enable_backup = config.get("advanced", "enable_backup", default=True)
        self.backup_dir = "backups"
        self.last_backup = None
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self) -> bool:
        """Create configuration backup"""
        if not self.enable_backup:
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"config_backup_{timestamp}.json")
            
            # Backup config file
            if os.path.exists(self.config.config_file):
                shutil.copy2(self.config.config_file, backup_file)
            
            # Backup logs
            log_backup = os.path.join(self.backup_dir, f"logs_backup_{timestamp}.zip")
            if os.path.exists("c2_audit.log"):
                shutil.make_archive(log_backup.replace('.zip', ''), 'zip', '.', 'c2_audit.log')
            
            self.last_backup = datetime.now()
            self.audit.log_security_event("BACKUP_CREATED", f"Backup: {backup_file}")
            return True
            
        except Exception as e:
            self.audit.log_error(str(e), "Backup creation failed")
            return False
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore configuration from backup"""
        try:
            if not os.path.exists(backup_file):
                self.audit.log_error("Backup file not found", backup_file)
                return False
            
            shutil.copy2(backup_file, self.config.config_file)
            self.audit.log_security_event("BACKUP_RESTORED", f"Restored: {backup_file}")
            return True
            
        except Exception as e:
            self.audit.log_error(str(e), "Backup restore failed")
            return False
    
    def list_backups(self) -> List[str]:
        """List available backups"""
        if not os.path.exists(self.backup_dir):
            return []
        
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('.json'):
                backups.append(os.path.join(self.backup_dir, file))
        
        return sorted(backups, reverse=True)

class TelegramBot:
    """Telegram bot integration for remote control"""
    
    def __init__(self, config: Config, audit: AuditLogger):
        self.config = config
        self.audit = audit
        self.enabled = config.get("advanced", "enable_telegram_bot", default=False)
        self.bot_token = config.get("advanced", "telegram_bot_token", default="")
        self.chat_id = config.get("advanced", "telegram_chat_id", default="")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message: str) -> bool:
        """Send message via Telegram bot"""
        if not self.enabled or not self.bot_token:
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {"chat_id": self.chat_id, "text": message}
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.audit.log_error(str(e), "Telegram message failed")
            return False
    
    def send_alert(self, event_type: str, details: str) -> bool:
        """Send security alert via Telegram"""
        message = f"🚨 C2 Alert\n\nType: {event_type}\nDetails: {details}\nTime: {datetime.now().isoformat()}"
        return self.send_message(message)

class DiscordBot:
    """Discord bot integration for remote control"""
    
    def __init__(self, config: Config, audit: AuditLogger):
        self.config = config
        self.audit = audit
        self.enabled = config.get("advanced", "enable_discord_bot", default=False)
        self.bot_token = config.get("advanced", "discord_bot_token", default="")
        self.channel_id = config.get("advanced", "discord_channel_id", default="")
        self.base_url = "https://discord.com/api/v10"
    
    def send_message(self, message: str) -> bool:
        """Send message via Discord bot"""
        if not self.enabled or not self.bot_token:
            return False
        
        try:
            url = f"{self.base_url}/channels/{self.channel_id}/messages"
            headers = {"Authorization": f"Bot {self.bot_token}"}
            data = {"content": message}
            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.audit.log_error(str(e), "Discord message failed")
            return False
    
    def send_alert(self, event_type: str, details: str) -> bool:
        """Send security alert via Discord"""
        message = f"🚨 **C2 Alert**\n\n**Type:** {event_type}\n**Details:** {details}\n**Time:** {datetime.now().isoformat()}"
        return self.send_message(message)

class OTAUpdateManager:
    """Over-the-Air firmware update system"""
    
    def __init__(self, config: Config, audit: AuditLogger):
        self.config = config
        self.audit = audit
        self.enabled = config.get("advanced", "enable_ota_updates", default=False)
        self.update_server = config.get("advanced", "ota_update_server", default="")
        self.current_version = "2.0.0"
        
    def check_for_updates(self) -> Dict:
        """Check for available firmware updates"""
        if not self.enabled or not self.update_server:
            return {"available": False, "reason": "OTA disabled"}
        
        try:
            response = requests.get(f"{self.update_server}/version.json", timeout=10)
            if response.status_code == 200:
                version_info = response.json()
                latest_version = version_info.get("version", self.current_version)
                
                if latest_version != self.current_version:
                    return {
                        "available": True,
                        "current": self.current_version,
                        "latest": latest_version,
                        "download_url": version_info.get("download_url"),
                        "changelog": version_info.get("changelog", "")
                    }
                else:
                    return {"available": False, "reason": "Already up to date"}
        except Exception as e:
            self.audit.log_error(str(e), "Update check failed")
            return {"available": False, "reason": "Check failed"}
        
        return {"available": False, "reason": "Unknown"}
    
    def trigger_update(self, update_url: str) -> bool:
        """Trigger OTA update on NodeMCU"""
        if not self.enabled:
            return False
        
        try:
            # Send update command to NodeMCU
            headers = {"X-API-Key": self.config.get("security", "api_key")}
            data = {"update_url": update_url}
            response = requests.post(
                f"{self.config.get('server', 'host')}/ota",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.audit.log_security_event("OTA_UPDATE_TRIGGERED", f"URL: {update_url}")
                return True
            else:
                self.audit.log_error("Update rejected", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.audit.log_error(str(e), "OTA update failed")
            return False

class MultiDeviceManager:
    """Multiple NodeMCU device management"""
    
    def __init__(self, config: Config, audit: AuditLogger):
        self.config = config
        self.audit = audit
        self.enabled = config.get("advanced", "multiple_devices", default=False)
        self.devices = config.get("advanced", "devices", default=[])
        self.device_status = {}
        
    def add_device(self, device_id: str, host: str, api_key: str) -> bool:
        """Add new device to management"""
        if not self.enabled:
            return False
        
        device = {
            "id": device_id,
            "host": host,
            "api_key": api_key,
            "last_seen": None,
            "status": "OFFLINE"
        }
        
        self.devices.append(device)
        self.device_status[device_id] = device
        self.audit.log_security_event("DEVICE_ADDED", f"Device: {device_id}")
        return True
    
    def check_device_status(self, device_id: str) -> Dict:
        """Check status of specific device"""
        if device_id not in self.device_status:
            return {"status": "UNKNOWN"}
        
        device = self.device_status[device_id]
        try:
            headers = {"X-API-Key": device["api_key"]}
            response = requests.get(f"http://{device['host']}/status", headers=headers, timeout=5)
            
            if response.status_code == 200:
                device["status"] = "ONLINE"
                device["last_seen"] = datetime.now().isoformat()
                return response.json()
            else:
                device["status"] = "ERROR"
                return {"status": "ERROR"}
                
        except Exception as e:
            device["status"] = "OFFLINE"
            self.audit.log_error(str(e), f"Device check failed: {device_id}")
            return {"status": "OFFLINE"}
    
    def get_all_device_status(self) -> Dict:
        """Get status of all devices"""
        status = {}
        for device_id in self.device_status:
            status[device_id] = self.check_device_status(device_id)
        return status

class C2Client:
    """Main C2 client controller"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = Config(config_file)
        self.security = SecurityManager(self.config)
        self.audit = AuditLogger(self.config)
        self.stats = SystemStats()
        self.history = CommandHistory(self.config.get("logging", "max_history", default=100))
        self.executor = CommandExecutor(self.config, self.security, self.audit)
        self.payload_executor = PayloadExecutor(self.executor, self.audit, self.stats, self.history)
        self.health_monitor = HealthMonitor(self.config, self.audit, self.stats)
        self.backup_manager = BackupManager(self.config, self.audit)
        self.telegram_bot = TelegramBot(self.config, self.audit)
        self.discord_bot = DiscordBot(self.config, self.audit)
        self.multi_device = MultiDeviceManager(self.config, self.audit)
        self.ota_manager = OTAUpdateManager(self.config, self.audit)
        
        self.base_url = f"http://{self.config.get('server', 'host')}"
        self.running = False
        
    def get_node_status(self) -> Optional[Dict]:
        """Get NodeMCU status with retry logic and robust error handling"""
        max_retries = self.config.get("server", "max_retries", default=3)
        retry_delay = self.config.get("server", "retry_delay", default=2)
        timeout = self.config.get("server", "connection_timeout", default=10)
        
        for attempt in range(max_retries):
            try:
                headers = {}
                if self.security.enable_auth:
                    headers["X-API-Key"] = self.security.api_key
                
                response = requests.get(f"{self.base_url}/status", headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        self.audit.log_error("Invalid JSON response", "Status check")
                        return None
                elif response.status_code == 429:
                    self.audit.log_security_event("RATE_LIMITED", "Status endpoint")
                    time.sleep(retry_delay)
                    continue
                else:
                    self.audit.log_error(f"HTTP {response.status_code}", "Status check")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                self.audit.log_error("Request timeout", f"Status check (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
            except requests.exceptions.ConnectionError:
                self.audit.log_error("Connection failed", f"Status check (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
            except Exception as e:
                self.audit.log_error(str(e), f"Status check (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
        
        return None
    
    def check_for_commands(self) -> Optional[str]:
        """Check for pending commands from NodeMCU with retry logic"""
        max_retries = self.config.get("server", "max_retries", default=3)
        retry_delay = self.config.get("server", "retry_delay", default=2)
        timeout = self.config.get("server", "connection_timeout", default=10)
        
        for attempt in range(max_retries):
            try:
                if not self.security.check_rate_limit():
                    self.audit.log_security_event("RATE_LIMIT_EXCEEDED", "Too many requests")
                    time.sleep(1)
                    continue
                
                headers = {}
                if self.security.enable_auth:
                    headers["X-API-Key"] = self.security.api_key
                
                response = requests.get(f"{self.base_url}/check", headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    server_response = response.text.strip() if response.text else ""
                    if server_response not in ["WAITING", "NONE", ""]:
                        return server_response
                    return None
                elif response.status_code == 429:
                    self.audit.log_security_event("RATE_LIMITED", "Check endpoint")
                    time.sleep(retry_delay)
                    continue
                else:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
            except Exception as e:
                self.audit.log_error(str(e), f"Command check (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
        
        return None
    
    def status_monitor(self):
        """Background status monitoring thread with health checks and error recovery"""
        status_interval = self.config.get("monitoring", "status_update_interval", default=30000) / 1000
        health_interval = self.health_monitor.health_check_interval / 1000
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                # Status check with error handling
                status = self.get_node_status()
                if status:
                    consecutive_errors = 0
                    try:
                        self.audit.logger.info(
                            f"NodeMCU Status - Uptime: {status.get('uptime', 0)/1000:.0f}s, "
                            f"Queue: {status.get('queueSize', 0)}, "
                            f"PC Connected: {status.get('pcConnected', False)}, "
                            f"Free Heap: {status.get('freeHeap', 0)} bytes"
                        )
                    except Exception as log_error:
                        pass  # Don't crash on logging errors
                else:
                    consecutive_errors += 1
                
                # Health check with error handling
                try:
                    is_healthy = self.health_monitor.check_system_health()
                    if not is_healthy:
                        self.health_monitor.attempt_recovery()
                        health_status = self.health_monitor.get_health_status()
                        try:
                            self.audit.logger.info(f"Health Status: {health_status}")
                        except Exception:
                            pass
                except Exception as health_error:
                    self.audit.log_error(str(health_error), "Health monitoring error")
                
                # Exponential backoff on consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    sleep_time = min(status_interval * 2, 60)
                else:
                    sleep_time = min(status_interval, health_interval)
                
                time.sleep(sleep_time)
                
            except Exception as e:
                consecutive_errors += 1
                try:
                    self.audit.log_error(str(e), "Status monitor error")
                except Exception:
                    pass
                time.sleep(min(status_interval * 2, 60))
    
    def run(self):
        """Main execution loop with comprehensive error handling"""
        self.running = True
        
        try:
            self.audit.logger.info("=" * 60)
            self.audit.logger.info("ADVANCED C2 LISTENER - PROFESSIONAL EDITION")
            self.audit.logger.info("=" * 60)
            self.audit.logger.info(f"Target: {self.base_url}")
            self.audit.logger.info(f"Platform: {platform.system()} {platform.release()}")
            self.audit.logger.info(f"Authentication: {'ENABLED' if self.security.enable_auth else 'DISABLED'}")
            self.audit.logger.info(f"Rate Limit: {self.security.rate_limit} requests/minute")
            self.audit.logger.info("=" * 60)
        except Exception as log_error:
            print(f"Logging initialization error: {log_error}")
        
        # Start status monitor thread with error handling
        monitor_thread = None
        try:
            monitor_thread = Thread(target=self.status_monitor, daemon=True)
            monitor_thread.start()
        except Exception as thread_error:
            try:
                self.audit.log_error(str(thread_error), "Monitor thread failed to start")
            except Exception:
                print(f"Monitor thread failed: {thread_error}")
        
        consecutive_failures = 0
        max_failures = 10
        
        try:
            while self.running:
                try:
                    command = self.check_for_commands()
                    
                    if command:
                        try:
                            self.audit.logger.info(f"[+] Command received: {command}")
                        except Exception:
                            print(f"[+] Command received: {command}")
                        
                        try:
                            success = self.payload_executor.execute(command)
                            consecutive_failures = 0
                        except Exception as exec_error:
                            try:
                                self.audit.log_error(str(exec_error), f"Command execution failed: {command}")
                            except Exception:
                                print(f"Command execution error: {exec_error}")
                            consecutive_failures += 1
                    else:
                        consecutive_failures = 0 if consecutive_failures == 0 else consecutive_failures - 1
                    
                    # Check for too many consecutive failures
                    if consecutive_failures >= max_failures:
                        try:
                            self.audit.logger.warning(f"[!] Too many consecutive failures ({consecutive_failures}), pausing...")
                        except Exception:
                            print(f"[!] Too many consecutive failures, pausing...")
                        time.sleep(10)
                        consecutive_failures = max_failures // 2
                    
                    time.sleep(1)
                    
                except Exception as loop_error:
                    consecutive_failures += 1
                    try:
                        self.audit.log_error(str(loop_error), "Main loop error")
                    except Exception:
                        print(f"Main loop error: {loop_error}")
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            try:
                self.audit.logger.info("[!] Shutdown signal received")
            except Exception:
                print("[!] Shutdown signal received")
        except Exception as e:
            try:
                self.audit.logger.error(f"[!] Fatal error: {e}")
            except Exception:
                print(f"[!] Fatal error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        self.audit.logger.info("=" * 60)
        self.audit.logger.info("FINAL STATISTICS")
        self.audit.logger.info("=" * 60)
        self.audit.logger.info(json.dumps(self.stats.to_dict(), indent=2))
        self.audit.logger.info("=" * 60)
        self.audit.logger.info("RECENT COMMAND HISTORY")
        self.audit.logger.info("=" * 60)
        for entry in self.history.get_recent(10):
            self.audit.logger.info(json.dumps(entry, indent=2))
        self.audit.logger.info("=" * 60)
        self.audit.logger.info("C2 Listener Shutdown Complete")

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Advanced C2 Listener")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("--generate-key", action="store_true", help="Generate new API key")
    
    args = parser.parse_args()
    
    if args.generate_key:
        print(f"Generated API Key: {secrets.token_hex(32)}")
        return
    
    client = C2Client(args.config)
    client.run()

if __name__ == "__main__":
    main()
