"""
CyberMind AI - System Tools Detector & Runner
Detects and runs Kali/system pentesting tools if available
"""
import shutil
import subprocess
import platform
from typing import Dict, List, Optional, Callable
from utils.logger import get_logger

logger = get_logger("system_tools")


# ─── Known Pentesting Tools ────────────────────────────────────────────────

KNOWN_TOOLS = {
    # Scanning
    "nmap":       {"desc": "Network/port scanner",       "category": "scanning"},
    "masscan":    {"desc": "Fast port scanner",           "category": "scanning"},
    # Web
    "gobuster":   {"desc": "Directory/DNS brute-force",  "category": "web"},
    "dirb":       {"desc": "Web directory scanner",       "category": "web"},
    "ffuf":       {"desc": "Fast web fuzzer",             "category": "web"},
    "nikto":      {"desc": "Web vulnerability scanner",  "category": "web"},
    "sqlmap":     {"desc": "SQL injection tool",          "category": "web"},
    "wpscan":     {"desc": "WordPress scanner",           "category": "web"},
    "whatweb":    {"desc": "Web technology identifier",  "category": "web"},
    # Password
    "hydra":      {"desc": "Network login brute-force",  "category": "password"},
    "medusa":     {"desc": "Brute-force tool",            "category": "password"},
    "hashcat":    {"desc": "Password hash cracker",       "category": "password"},
    "john":       {"desc": "John the Ripper",             "category": "password"},
    # Forensics
    "binwalk":    {"desc": "Firmware/binary analysis",   "category": "forensics"},
    "exiftool":   {"desc": "Metadata reader",             "category": "forensics"},
    "foremost":   {"desc": "File carving tool",           "category": "forensics"},
    "volatility": {"desc": "Memory forensics",            "category": "forensics"},
    "steghide":   {"desc": "Steganography tool",          "category": "forensics"},
    "stegsolve":  {"desc": "Stego solver",                "category": "forensics"},
    # Network
    "wireshark":  {"desc": "Network packet analyzer",    "category": "network"},
    "tcpdump":    {"desc": "Packet capture",              "category": "network"},
    "netcat":     {"desc": "Network swiss-army knife",   "category": "network"},
    "nc":         {"desc": "Netcat",                      "category": "network"},
    "socat":      {"desc": "Data relay tool",             "category": "network"},
    # Exploitation
    "msfconsole": {"desc": "Metasploit Framework",       "category": "exploit"},
    "searchsploit":{"desc":"Exploit-DB search",           "category": "exploit"},
    # Reverse
    "gdb":        {"desc": "GNU debugger",                "category": "reverse"},
    "ghidra":     {"desc": "Reverse engineering tool",   "category": "reverse"},
    "radare2":    {"desc": "Reverse engineering",         "category": "reverse"},
    "r2":         {"desc": "Radare2",                     "category": "reverse"},
    "strings":    {"desc": "Extract strings",             "category": "reverse"},
    "objdump":    {"desc": "Object file disassembler",   "category": "reverse"},
    "ltrace":     {"desc": "Library call tracer",         "category": "reverse"},
    "strace":     {"desc": "System call tracer",          "category": "reverse"},
    # Crypto / General
    "openssl":    {"desc": "SSL/crypto tool",             "category": "crypto"},
    "gpg":        {"desc": "GNU Privacy Guard",           "category": "crypto"},
    "xxd":        {"desc": "Hex dump",                    "category": "forensics"},
    "hexdump":    {"desc": "Hex dump",                    "category": "forensics"},
    "file":       {"desc": "File type identifier",        "category": "forensics"},
    "curl":       {"desc": "HTTP client",                 "category": "web"},
    "wget":       {"desc": "HTTP downloader",             "category": "web"},
}


class SystemTools:
    """
    Detects available system pentesting tools and provides
    a unified interface to run them.
    """

    def __init__(self):
        self._available: Dict[str, str] = {}  # name → path
        self._detected = False

    def detect(self) -> Dict[str, str]:
        """Scan PATH for available tools"""
        self._available = {}
        for tool in KNOWN_TOOLS:
            path = shutil.which(tool)
            if path:
                self._available[tool] = path
        self._detected = True
        logger.info(f"Detected {len(self._available)} system tools")
        return self._available

    def is_available(self, tool: str) -> bool:
        if not self._detected:
            self.detect()
        return tool in self._available

    def get_available(self) -> Dict[str, str]:
        if not self._detected:
            self.detect()
        return self._available.copy()

    def get_by_category(self) -> Dict[str, List[str]]:
        """Group available tools by category"""
        cats = {}
        for name in self._available:
            cat = KNOWN_TOOLS[name]["category"]
            cats.setdefault(cat, []).append(name)
        return cats

    def run(self, command: List[str], timeout: int = 60,
            on_output: Optional[Callable[[str], None]] = None,
            on_heartbeat: Optional[Callable[[int], None]] = None) -> Dict:
        """
        Run a system command and return output.
        Streams output line by line via on_output callback.
        on_heartbeat(elapsed_seconds) fires every 15s when no new output.
        """
        import threading, time

        output_lines = []
        process = None

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            last_output_time = [time.time()]
            start_time = time.time()
            done = threading.Event()

            # Heartbeat thread — fires when silent for >15s
            def heartbeat():
                while not done.wait(timeout=15):
                    silent_for = int(time.time() - last_output_time[0])
                    elapsed   = int(time.time() - start_time)
                    if silent_for >= 15 and on_heartbeat:
                        on_heartbeat(elapsed)

            if on_heartbeat:
                hb = threading.Thread(target=heartbeat, daemon=True)
                hb.start()

            for line in iter(process.stdout.readline, ""):
                line = line.rstrip()
                if line:
                    output_lines.append(line)
                    last_output_time[0] = time.time()
                    if on_output:
                        on_output(line)

            done.set()
            process.wait(timeout=timeout)
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "output": "\n".join(output_lines),
            }

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            return {"success": False, "error": f"Timeout after {timeout}s",
                    "output": "\n".join(output_lines)}
        except FileNotFoundError:
            return {"success": False, "error": f"Tool not found: {command[0]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Nmap Wrappers ────────────────────────────────────────────

    def nmap_quick(self, target: str,
                   on_output: Optional[Callable] = None) -> Dict:
        """Quick nmap scan - top 1000 ports + service detection"""
        return self.run(
            ["nmap", "-sV", "--open", "-T4", "-n", target],
            timeout=120, on_output=on_output
        )

    def nmap_full(self, target: str,
                  on_output: Optional[Callable] = None,
                  on_heartbeat: Optional[Callable] = None) -> Dict:
        """Full nmap scan - all 65535 ports with service detection"""
        return self.run(
            ["nmap", "-sV", "-p-", "-T4", "--open", "-n",
             "--stats-every", "15s", target],
            timeout=1800,   # 30 min ceiling — full scan can take time
            on_output=on_output,
            on_heartbeat=on_heartbeat,
        )

    def nmap_vuln(self, target: str, ports: str = "80,443,22",
                  on_output: Optional[Callable] = None) -> Dict:
        """Nmap with vuln scripts"""
        return self.run(
            ["nmap", "--script=vuln", f"-p{ports}", "-T4", target],
            timeout=180, on_output=on_output
        )

    def parse_nmap_output(self, output: str) -> List[Dict]:
        """Parse nmap output into structured port list"""
        import re
        ports = []
        for line in output.splitlines():
            # Match: "80/tcp   open  http    Apache httpd 2.4.41"
            m = re.match(r'(\d+)/(tcp|udp)\s+(\w+)\s+(\S+)\s*(.*)', line)
            if m and m.group(3) == "open":
                ports.append({
                    "port": int(m.group(1)),
                    "protocol": m.group(2),
                    "state": m.group(3),
                    "service": m.group(4),
                    "version": m.group(5).strip(),
                })
        return ports

    # ─── Web Tool Wrappers ────────────────────────────────────────

    def gobuster_dir(self, url: str,
                     wordlist: str = "/usr/share/wordlists/dirb/common.txt",
                     on_output: Optional[Callable] = None) -> Dict:
        """Run gobuster directory scan"""
        if not self.is_available("gobuster"):
            return {"error": "gobuster not installed"}
        return self.run(
            ["gobuster", "dir", "-u", url, "-w", wordlist,
             "-q", "--no-error", "-t", "20"],
            timeout=120, on_output=on_output
        )

    def nikto_scan(self, url: str,
                   on_output: Optional[Callable] = None) -> Dict:
        """Run nikto web vulnerability scan"""
        if not self.is_available("nikto"):
            return {"error": "nikto not installed"}
        return self.run(
            ["nikto", "-h", url, "-nointeractive"],
            timeout=120, on_output=on_output
        )

    def sqlmap_scan(self, url: str, data: str = None,
                    on_output: Optional[Callable] = None) -> Dict:
        """Run sqlmap scan"""
        if not self.is_available("sqlmap"):
            return {"error": "sqlmap not installed"}
        cmd = ["sqlmap", "-u", url, "--batch", "--level=2", "--risk=1",
               "--output-dir=/tmp/sqlmap_output"]
        if data:
            cmd += ["--data", data]
        return self.run(cmd, timeout=180, on_output=on_output)

    # ─── Forensics Wrappers ────────────────────────────────────────

    def binwalk_analyze(self, filepath: str,
                        on_output: Optional[Callable] = None) -> Dict:
        """Run binwalk file analysis"""
        if not self.is_available("binwalk"):
            return {"error": "binwalk not installed"}
        return self.run(["binwalk", filepath], timeout=30, on_output=on_output)

    def exiftool_read(self, filepath: str,
                      on_output: Optional[Callable] = None) -> Dict:
        """Read file metadata with exiftool"""
        if not self.is_available("exiftool"):
            return {"error": "exiftool not installed"}
        return self.run(["exiftool", filepath], timeout=10, on_output=on_output)

    def strings_extract(self, filepath: str, min_len: int = 8,
                        on_output: Optional[Callable] = None) -> Dict:
        """Extract strings from binary"""
        if not self.is_available("strings"):
            return {"error": "strings not installed"}
        return self.run(
            ["strings", f"-n{min_len}", filepath],
            timeout=15, on_output=on_output
        )

    # ─── System Info ─────────────────────────────────────────────

    @staticmethod
    def get_os_info() -> Dict:
        """Get OS information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "is_kali": _is_kali(),
            "is_linux": platform.system() == "Linux",
        }


def _is_kali() -> bool:
    """Check if running on Kali Linux"""
    try:
        with open("/etc/os-release") as f:
            content = f.read().lower()
            return "kali" in content
    except Exception:
        return False


# Global instance
system_tools = SystemTools()
