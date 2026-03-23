"""
CyberMind AI - Autonomous Penetration Test Agent
Scans a target IP, thinks, and generates a full report.
For authorized testing only (CTF, lab environments).
"""
import time
import socket
import threading
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from config import config
from utils.logger import get_logger
from core.system_tools import system_tools

logger = get_logger("autopwn")


# ─── Severity Levels ─────────────────────────────────────────────────────────

SEVERITY = {
    "critical": {"label": "CRITICAL", "icon": "🔴", "priority": 0},
    "high":     {"label": "HIGH",     "icon": "🟠", "priority": 1},
    "medium":   {"label": "MEDIUM",   "icon": "🟡", "priority": 2},
    "low":      {"label": "LOW",      "icon": "🔵", "priority": 3},
    "info":     {"label": "INFO",     "icon": "⚪", "priority": 4},
}

# ─── Scan Phases ─────────────────────────────────────────────────────────────

PHASES = [
    ("auth",        "Authentication",       "🔑"),
    ("recon",       "Reconnaissance",       "🔭"),
    ("enum",        "Enumeration",          "🔬"),
    ("vuln",        "Vulnerability Scan",   "⚡"),
    ("ai_analysis", "AI Analysis",          "🧠"),
    ("report",      "Report Generation",    "📄"),
]


class Finding:
    """A single security finding"""

    def __init__(self, title: str, severity: str, description: str,
                 evidence: str = "", recommendation: str = "",
                 port: int = None, service: str = ""):
        self.title = title
        self.severity = severity.lower()
        self.description = description
        self.evidence = evidence
        self.recommendation = recommendation
        self.port = port
        self.service = service
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "port": self.port,
            "service": self.service,
        }


class ScanResult:
    """Complete scan results"""

    def __init__(self, target: str):
        self.target = target
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.hostname: str = ""
        self.open_ports: List[Dict] = []
        self.services: Dict[int, Dict] = {}
        self.web_findings: Dict = {}
        self.findings: List[Finding] = []
        self.raw_data: Dict[str, Any] = {}
        self.report_text: str = ""
        self.ai_analysis: str = ""

    def add_finding(self, finding: Finding):
        self.findings.append(finding)

    def get_findings_by_severity(self) -> Dict[str, List[Finding]]:
        result = {s: [] for s in SEVERITY}
        for f in self.findings:
            if f.severity in result:
                result[f.severity].append(f)
        return result

    def summary_counts(self) -> Dict[str, int]:
        counts = {s: 0 for s in SEVERITY}
        for f in self.findings:
            if f.severity in counts:
                counts[f.severity] += 1
        return counts


class AutonomousAgent:
    """
    Autonomous pentesting agent.
    Takes a target IP, runs multi-phase analysis, generates report.
    """

    def __init__(self, ai_agent=None,
                 on_log: Optional[Callable[[str, str], None]] = None,
                 on_phase: Optional[Callable[[str, str], None]] = None,
                 on_progress: Optional[Callable[[int, str], None]] = None,
                 on_finding: Optional[Callable[[Finding], None]] = None,
                 on_complete: Optional[Callable[[ScanResult], None]] = None):
        self.ai_agent = ai_agent
        self.on_log = on_log           # (message, level)
        self.on_phase = on_phase       # (phase_id, phase_name)
        self.on_progress = on_progress # (percent, message)
        self.on_finding = on_finding   # (finding)
        self.on_complete = on_complete # (result)
        self._stop_event = threading.Event()
        self._is_running = False
        self._auth_session = None      # requests.Session after successful login
        self._verbose = False          # verbose mode flag

    @property
    def is_running(self) -> bool:
        return self._is_running

    def stop(self):
        self._stop_event.set()

    def run(self, target: str, options: Dict = None) -> ScanResult:
        """
        Main entry point. Run all phases against target.
        Call from a background thread.
        """
        options = options or {}
        self._stop_event.clear()
        self._is_running = True
        self._verbose = options.get("verbose", False)
        result = ScanResult(target)

        try:
            self._log(f"🎯 Target: {target}", "info")
            self._log(f"⏰ Started: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}", "info")
            if self._verbose:
                self._log(f"🔊 Verbose mode ON — showing all requests & payloads", "warning")
            self._log("─" * 50, "muted")

            # ── Phase 0: Authentication (optional) ───────────────
            auth_opts = options.get("auth", {})
            if auth_opts.get("enabled"):
                self._set_phase("auth", "Authentication")
                self._progress(3, "Authenticating...")
                self._phase_auth(result, auth_opts)
                if self._stop_event.is_set():
                    return result

            # ── Phase 1: Reconnaissance ───────────────────────────
            self._set_phase("recon", "Reconnaissance")
            self._progress(5, "Starting reconnaissance...")
            self._phase_recon(result, options)

            if self._stop_event.is_set():
                return result

            # ── Phase 2: Enumeration ──────────────────────────────
            self._set_phase("enum", "Enumeration")
            self._progress(25, "Enumerating services...")
            self._phase_enum(result, options)

            if self._stop_event.is_set():
                return result

            # ── Phase 3: Vulnerability Scan ───────────────────────
            self._set_phase("vuln", "Vulnerability Scan")
            self._progress(50, "Checking vulnerabilities...")
            self._phase_vuln(result, options)

            if self._stop_event.is_set():
                return result

            # ── Phase 4: AI Analysis ──────────────────────────────
            self._set_phase("ai_analysis", "AI Analysis")
            self._progress(75, "AI analyzing findings...")
            self._phase_ai_analysis(result)

            # ── Phase 5: Report Generation ────────────────────────
            self._set_phase("report", "Report Generation")
            self._progress(90, "Generating report...")
            self._phase_report(result)

            self._progress(100, "Scan complete!")
            result.end_time = datetime.now()
            duration = (result.end_time - result.start_time).seconds
            self._log(f"\n✅ Scan completed in {duration}s", "success")
            self._log(f"📊 Findings: {len(result.findings)} total", "success")

            if self.on_complete:
                self.on_complete(result)

        except Exception as e:
            self._log(f"❌ Fatal error: {e}", "error")
            logger.error(f"Autonomous agent error: {e}", exc_info=True)
            result.end_time = datetime.now()
        finally:
            self._is_running = False

        return result

    # ─── Phase 0: Authentication ─────────────────────────────────────────────

    def _phase_auth(self, result: ScanResult, auth_opts: Dict):
        """Login to a protected web target before scanning."""
        from tools.web_tools import WebTools
        web = WebTools()

        target   = result.target
        username = auth_opts.get("username", "")
        password = auth_opts.get("password", "")
        login_url = auth_opts.get("login_url", "").strip()
        try_defaults = auth_opts.get("try_defaults", False)

        self._log("\n[Phase 0] Authentication", "phase")

        # ── Auto-detect login URL if not given ────────────────────
        if not login_url:
            self._log("  No login URL given — auto-detecting...", "info")
            candidates = [
                f"http://{target}/login",
                f"http://{target}/signin",
                f"http://{target}/auth",
                f"http://{target}/admin/login",
                f"http://{target}/user/login",
                f"http://{target}/account/login",
                f"http://{target}/wp-login.php",
                f"http://{target}/",
            ]
            import requests as _req
            for url in candidates:
                try:
                    r = _req.get(url, timeout=5, verify=False, allow_redirects=True)
                    if r.status_code == 200 and "password" in r.text.lower():
                        login_url = url
                        self._log(f"  ✅ Login page found: {url}", "success")
                        break
                except Exception:
                    pass

            if not login_url:
                self._log("  ⚠️  Could not find a login page automatically", "warning")
                self._log("     Continuing scan without authentication", "muted")
                return

        self._log(f"  Target login URL: {login_url}", "info")

        # ── Detect form fields ────────────────────────────────────
        form_info = web.detect_login_form(login_url)
        if form_info.get("login_forms"):
            form = form_info["login_forms"][0]
            fields = form["fields"]
            self._log(f"  Form fields detected: {list(fields.keys())}", "muted")
        else:
            self._log("  ⚠️  No login form detected at that URL", "warning")

        # ── Try default credentials first (if requested) ──────────
        if try_defaults and not (username and password):
            self._log("  Trying common default credentials...", "info")
            default_result = web.try_default_credentials(login_url)
            if default_result.get("success"):
                username = default_result["cracked_username"]
                password = default_result["cracked_password"]
                self._log(f"  🔴 Default creds worked: {username}:{password}", "critical")
                finding = Finding(
                    title="Default Credentials Accepted",
                    severity="critical",
                    description=f"Login succeeded with default credentials: {username}:{password}",
                    evidence=f"POST {login_url} → success with {username}:{password}",
                    recommendation="Change default credentials immediately. Enforce strong password policy.",
                    port=80, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)
                # Session is now authenticated inside web.session
                self._auth_session = web.session
                result.raw_data["auth"] = {"username": username, "password": password,
                                           "method": "default_creds"}
                return
            else:
                self._log(f"  Default creds failed ({default_result.get('tried',0)} tried)",
                          "muted")

        # ── Use provided credentials ──────────────────────────────
        if not (username and password):
            self._log("  No credentials provided — skipping auth", "warning")
            return

        self._log(f"  Logging in as: {username}", "info")
        auth_result = web.authenticate(login_url, username, password)

        if auth_result.get("error"):
            self._log(f"  ❌ Auth error: {auth_result['error']}", "error")
            return

        if auth_result.get("success"):
            self._log(f"  ✅ Login successful!", "success")
            self._log(f"  Final URL: {auth_result['final_url']}", "muted")
            cookies = auth_result.get("cookies", {})
            if cookies:
                self._log(f"  Session cookies: {list(cookies.keys())}", "muted")
            # Keep the authenticated session for all web checks
            self._auth_session = web.session
            result.raw_data["auth"] = {
                "username": username,
                "login_url": login_url,
                "final_url": auth_result["final_url"],
                "cookies": cookies,
            }
            finding = Finding(
                title="Authentication Successful — Scanning as Logged-In User",
                severity="info",
                description=f"Logged in as '{username}'. All web checks will use authenticated session.",
                evidence=f"POST {login_url} → {auth_result['final_url']}",
                recommendation="",
                port=80, service="HTTP"
            )
            result.add_finding(finding)
            if self.on_finding:
                self.on_finding(finding)
        else:
            self._log(f"  ❌ Login failed — wrong credentials or unusual form", "error")
            self._log(f"  Response snippet: {auth_result.get('response_snippet','')[:100]}", "muted")
            self._log("  Continuing scan without authentication", "warning")

    # ─── Phase 1: Reconnaissance ─────────────────────────────────────────────

    def _phase_recon(self, result: ScanResult, options: Dict):
        target = result.target
        deep = options.get("deep", False)
        self._log("\n[Phase 1] Reconnaissance", "phase")

        # OS info
        os_info = system_tools.get_os_info()
        if os_info.get("is_kali"):
            self._log("  🐉 Kali Linux detected — using system tools", "success")
        elif os_info.get("is_linux"):
            self._log("  🐧 Linux detected", "info")
        else:
            self._log(f"  💻 {os_info.get('system', 'Unknown OS')}", "info")

        # Resolve hostname
        self._log(f"  Resolving {target}...", "info")
        try:
            hostname = socket.gethostbyaddr(target)[0]
            result.hostname = hostname
            self._log(f"  Hostname: {hostname}", "success")
        except Exception:
            self._log(f"  No reverse DNS for {target}", "muted")

        # ── Use nmap if available (much better) ──────────────────
        open_ports = []
        if system_tools.is_available("nmap"):
            self._log("  ✅ nmap found — using it for accurate scanning", "success")
            scan_type = "full (-p-)" if deep else "quick (-sV top ports)"
            self._log(f"  Running nmap {scan_type}...", "info")

            if deep:
                self._log("  ⚠️  Deep scan (-p-) scans all 65535 ports — may take 10-30 min", "warning")
                self._log("  ⏳ nmap will report progress every 15s...", "muted")

            def nmap_output(line: str):
                if not line.strip():
                    return
                is_important = any(kw in line for kw in
                                   ["open", "filtered", "PORT", "Host", "Stats", "SYN"])
                if is_important or self._verbose:
                    self._log(f"    {line}", "muted")

            def nmap_heartbeat(elapsed: int):
                mins = elapsed // 60
                secs = elapsed % 60
                self._log(f"  ⏳ nmap still running... ({mins}m {secs}s elapsed)", "muted")
                self._progress(
                    min(20, 5 + elapsed // 30),
                    f"Deep port scan in progress ({mins}m {secs}s)..."
                )

            if deep:
                nmap_result = system_tools.nmap_full(
                    target, on_output=nmap_output, on_heartbeat=nmap_heartbeat
                )
            else:
                nmap_result = system_tools.nmap_quick(target, on_output=nmap_output)
            result.raw_data["nmap"] = nmap_result.get("output", "")

            parsed = system_tools.parse_nmap_output(nmap_result.get("output", ""))
            for p in parsed:
                open_ports.append({
                    "port": p["port"],
                    "service": p["service"],
                    "banner": p.get("version", ""),
                    "state": p["state"],
                })

        else:
            # Fallback: Python port scanner
            self._log("  ℹ️  nmap not found — using built-in scanner", "muted")
            self._log("     (Install nmap for better results: sudo apt install nmap)", "muted")
            self._log("  Scanning common ports...", "info")
            from tools.network_tools import NetworkTools
            net = NetworkTools()

            common_ports = [
                21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
                143, 443, 445, 512, 513, 514, 587, 993, 995,
                1433, 1521, 2049, 2181, 3000, 3306, 3389, 4848,
                5432, 5900, 6379, 6443, 7001, 8000, 8080, 8081,
                8443, 8888, 9000, 9090, 9200, 10250, 27017, 28017,
            ]
            scan_result = net.port_scan(target, common_ports, timeout=0.8)
            if "error" in scan_result:
                self._log(f"  ⚠️  {scan_result['error']}", "warning")
                return
            open_ports = scan_result.get("open_ports", [])
            result.raw_data["port_scan"] = scan_result

        result.open_ports = open_ports

        if not open_ports:
            self._log("  No open ports found", "warning")
            result.add_finding(Finding(
                title="No Open Ports Detected",
                severity="info",
                description="No ports responded. Host may be firewalled or down.",
                recommendation="Verify target is online. Try extended port range."
            ))
            return

        self._log(f"  ✅ Found {len(open_ports)} open ports:", "success")
        for p in open_ports:
            ver = f"  {p.get('banner','')[:50]}" if p.get("banner") else ""
            self._log(f"    [{p['port']}/tcp]  {p['service']}{ver}", "port")

        # Add info finding for each open port
        for p in open_ports:
            result.add_finding(Finding(
                title=f"Open Port: {p['port']}/{p['service']}",
                severity="info",
                description=f"Port {p['port']} ({p['service']}) is open.",
                evidence=p.get("banner", "") or f"TCP connect to {target}:{p['port']} succeeded",
                port=p["port"],
                service=p["service"]
            ))
            if self.on_finding:
                self.on_finding(result.findings[-1])

    # ─── Phase 2: Enumeration ─────────────────────────────────────────────────

    def _phase_enum(self, result: ScanResult, options: Dict):
        self._log("\n[Phase 2] Service Enumeration", "phase")

        if not result.open_ports:
            self._log("  No open ports to enumerate", "muted")
            return

        target = result.target
        from tools.network_tools import NetworkTools
        from tools.web_tools import WebTools

        net = NetworkTools()

        for port_info in result.open_ports:
            if self._stop_event.is_set():
                break

            port = port_info["port"]
            service = port_info.get("service", "unknown").lower()
            self._log(f"  Enumerating port {port} ({service})...", "info")

            # ── Web (HTTP/HTTPS) ──────────────────────────────────
            if port in (80, 443, 8080, 8443, 8000, 8888, 3000, 5000) or "http" in service:
                protocol = "https" if port in (443, 8443) else "http"
                url = f"{protocol}://{target}:{port}" if port not in (80, 443) else f"{protocol}://{target}"
                self._log(f"    Web service detected → {url}", "info")
                self._enumerate_web(result, url, port)

            # ── SSH ───────────────────────────────────────────────
            elif port == 22 or "ssh" in service:
                banner = port_info.get("banner", "")
                self._log(f"    SSH: {banner[:80]}", "info")
                result.services[port] = {"type": "ssh", "banner": banner}

                # Version disclosure
                if banner:
                    result.add_finding(Finding(
                        title="SSH Version Disclosure",
                        severity="info",
                        description=f"SSH server banner: {banner}",
                        evidence=banner,
                        recommendation="Consider hiding SSH version in banner.",
                        port=port, service="SSH"
                    ))
                    if self.on_finding:
                        self.on_finding(result.findings[-1])

                # Check for old versions
                old_versions = ["SSH-1", "OpenSSH_5", "OpenSSH_6", "OpenSSH_7.2"]
                for old in old_versions:
                    if old in banner:
                        finding = Finding(
                            title=f"Outdated SSH Version: {old}",
                            severity="medium",
                            description=f"Server is running an outdated SSH version ({old}) with known vulnerabilities.",
                            evidence=banner,
                            recommendation="Upgrade OpenSSH to the latest stable version.",
                            port=port, service="SSH"
                        )
                        result.add_finding(finding)
                        if self.on_finding:
                            self.on_finding(finding)
                        break

            # ── FTP ───────────────────────────────────────────────
            elif port == 21 or "ftp" in service:
                banner = port_info.get("banner", "")
                self._log(f"    FTP: {banner[:60]}", "info")
                self._check_ftp(result, target, port, banner)

            # ── SMB ───────────────────────────────────────────────
            elif port in (139, 445):
                self._log(f"    SMB detected on port {port}", "info")
                result.add_finding(Finding(
                    title="SMB Service Exposed",
                    severity="medium",
                    description="SMB (Windows file sharing) is accessible. May be vulnerable to EternalBlue/PrintNightmare.",
                    evidence=f"Port {port} open",
                    recommendation="Restrict SMB access. Ensure patched against MS17-010, CVE-2021-34527.",
                    port=port, service="SMB"
                ))
                if self.on_finding:
                    self.on_finding(result.findings[-1])

            # ── Database Services ─────────────────────────────────
            elif port in (3306, 5432, 1433, 1521, 27017, 6379, 9200):
                self._check_database(result, target, port, service)

            # ── Telnet (always bad) ───────────────────────────────
            elif port == 23 or "telnet" in service:
                finding = Finding(
                    title="Telnet Service Exposed",
                    severity="high",
                    description="Telnet sends all data in plaintext including credentials.",
                    evidence=f"Port 23 open",
                    recommendation="Disable Telnet immediately. Use SSH instead.",
                    port=23, service="Telnet"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)

    def _enumerate_web(self, result: ScanResult, url: str, port: int):
        """Enumerate a web service"""
        from tools.web_tools import WebTools
        web = WebTools()

        # Header analysis
        self._log(f"    Analyzing HTTP headers...", "info")
        headers_result = web.analyze_headers(url)
        if not headers_result.get("error"):
            result.web_findings[port] = headers_result
            if self._verbose:
                present = headers_result.get("security_headers_present", [])
                missing_h = headers_result.get("security_headers_missing", [])
                self._vlog(f"      Headers present:  {[h['header'] for h in present]}", "muted")
                self._vlog(f"      Headers missing:  {[h['header'] for h in missing_h]}", "muted")
                cookies_info = headers_result.get("info", {}).get("cookies", [])
                for ck in cookies_info:
                    self._vlog(f"      Cookie: {ck.get('value','')[:80]}  issues={ck.get('issues','')}", "muted")
            missing = headers_result.get("security_headers_missing", [])
            server = headers_result.get("info", {}).get("server", "")
            powered = headers_result.get("info", {}).get("x_powered_by", "")

            if missing:
                finding = Finding(
                    title=f"Missing Security Headers ({len(missing)})",
                    severity="low",
                    description=f"Missing: {', '.join(h['header'] for h in missing[:5])}",
                    evidence=f"HTTP response from {url}",
                    recommendation="Add security headers: CSP, HSTS, X-Frame-Options, etc.",
                    port=port, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)

            if server and server != "Not disclosed":
                self._log(f"    Server: {server}", "info")
                result.add_finding(Finding(
                    title=f"Server Version Disclosure: {server}",
                    severity="low",
                    description=f"Server header reveals: {server}",
                    evidence=f"Server: {server}",
                    recommendation="Hide server version in HTTP headers.",
                    port=port, service="HTTP"
                ))

            if powered and powered != "Not disclosed":
                self._log(f"    X-Powered-By: {powered}", "warning")
                result.add_finding(Finding(
                    title=f"Technology Disclosure: {powered}",
                    severity="low",
                    description=f"X-Powered-By reveals: {powered}",
                    evidence=f"X-Powered-By: {powered}",
                    recommendation="Remove X-Powered-By header.",
                    port=port, service="HTTP"
                ))

        # Directory enumeration — prefer gobuster/ffuf, fallback to built-in
        self._log(f"    Directory enumeration...", "info")
        found_dirs = []

        if system_tools.is_available("gobuster"):
            self._log(f"    Using gobuster...", "muted")
            import re as _re
            gb_result = system_tools.gobuster_dir(url)
            raw = gb_result.get("output", "")
            if self._verbose:
                for line in raw.splitlines():
                    if line.strip():
                        self._vlog(f"      gobuster: {line}", "muted")
            # Parse gobuster output: "/path (Status: 200) [Size: 1234]"
            for line in raw.splitlines():
                m = _re.search(r'^(/\S+)\s+\(Status: (\d+)\)', line)
                if m:
                    found_dirs.append({
                        "path": m.group(1).lstrip("/"),
                        "status": int(m.group(2)),
                        "size": 0
                    })
        else:
            dir_result = web.enumerate_directories(url)
            found_dirs = dir_result.get("found", [])
        if found_dirs:
            self._log(f"    Found {len(found_dirs)} interesting paths", "warning")
            for d in found_dirs[:10]:
                self._log(f"      [{d['status']}] /{d['path']}", "finding")

            sensitive = [d for d in found_dirs if d["path"] in
                        [".git", ".env", "backup", "config", "admin", "console", "shell"]]
            if sensitive:
                finding = Finding(
                    title=f"Sensitive Paths Exposed ({len(sensitive)})",
                    severity="high",
                    description=f"Potentially sensitive paths found: {', '.join(d['path'] for d in sensitive)}",
                    evidence="\n".join(f"/{d['path']} -> HTTP {d['status']}" for d in sensitive),
                    recommendation="Restrict access to sensitive paths. Remove .git/.env from web root.",
                    port=port, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)

        result.raw_data[f"web_{port}"] = {
            "headers": headers_result,
            "directories": found_dirs
        }

    def _check_ftp(self, result: ScanResult, target: str, port: int, banner: str):
        """Check FTP service"""
        from tools.network_tools import NetworkTools
        net = NetworkTools()

        # Try anonymous login
        self._log(f"    Testing anonymous FTP...", "info")
        anon_result = net.nc_connect(target, port, "USER anonymous", timeout=3)
        if anon_result.get("success"):
            response = anon_result.get("response", "").lower()
            if "230" in response or "anonymous" in response or "logged in" in response:
                finding = Finding(
                    title="FTP Anonymous Login Allowed",
                    severity="high",
                    description="FTP server allows anonymous (unauthenticated) login.",
                    evidence=f"Banner: {banner}\nResponse: {anon_result.get('response', '')[:200]}",
                    recommendation="Disable anonymous FTP access unless explicitly required.",
                    port=port, service="FTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)
                self._log(f"    ⚠️  Anonymous FTP login allowed!", "warning")
                return

        result.add_finding(Finding(
            title="FTP Service Running",
            severity="medium",
            description=f"FTP service detected. FTP transmits data unencrypted. Use SFTP/FTPS instead.",
            evidence=banner,
            recommendation="Replace FTP with SFTP or FTPS. Ensure no anonymous access.",
            port=port, service="FTP"
        ))

    def _check_database(self, result: ScanResult, target: str, port: int, service: str):
        """Check database service exposure"""
        db_names = {
            3306: ("MySQL/MariaDB", "high"),
            5432: ("PostgreSQL", "high"),
            1433: ("MSSQL", "high"),
            1521: ("Oracle DB", "high"),
            27017: ("MongoDB", "critical"),  # Often no auth
            6379: ("Redis", "critical"),     # Often no auth
            9200: ("Elasticsearch", "high"),
        }

        db_name, severity = db_names.get(port, ("Database", "high"))
        self._log(f"    {db_name} exposed on port {port}!", "warning")

        # Try unauthenticated access for Redis/MongoDB
        if port == 6379:
            from tools.network_tools import NetworkTools
            nc = NetworkTools()
            r = nc.nc_connect(target, port, "PING", timeout=3)
            if r.get("success") and "PONG" in r.get("response", ""):
                severity = "critical"
                finding = Finding(
                    title="Redis Exposed - No Authentication",
                    severity="critical",
                    description="Redis instance accessible without authentication. Full data access possible.",
                    evidence=r.get("response", ""),
                    recommendation="Enable Redis authentication (requirepass). Bind to 127.0.0.1 only.",
                    port=port, service="Redis"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)
                self._log(f"    🔴 CRITICAL: Redis no auth!", "critical")
                return

        finding = Finding(
            title=f"{db_name} Publicly Accessible",
            severity=severity,
            description=f"{db_name} port {port} is reachable from external network.",
            evidence=f"TCP connection to {target}:{port} succeeded",
            recommendation=f"Firewall {db_name} port {port}. Only allow from app servers.",
            port=port, service=db_name
        )
        result.add_finding(finding)
        if self.on_finding:
            self.on_finding(finding)

    # ─── Phase 3: Vulnerability Checks ───────────────────────────────────────

    def _phase_vuln(self, result: ScanResult, options: Dict):
        self._log("\n[Phase 3] Vulnerability Analysis", "phase")
        target = result.target

        if not result.open_ports:
            self._log("  No services to test", "muted")
            return

        # Web vulnerability checks
        web_ports = [p for p in result.open_ports
                     if p["port"] in (80, 443, 8080, 8443, 8000, 8888, 3000, 5000)
                     or "http" in p.get("service", "").lower()]

        for port_info in web_ports[:3]:
            if self._stop_event.is_set():
                break
            port = port_info["port"]
            protocol = "https" if port in (443, 8443) else "http"
            url = f"{protocol}://{target}:{port}" if port not in (80, 443) else f"{protocol}://{target}"
            self._check_web_vulns(result, url, port)

    def _check_web_vulns(self, result: ScanResult, url: str, port: int):
        """Run comprehensive web vulnerability checks"""
        import requests
        from tools.web_tools import WebTools
        web = WebTools()

        # Reuse authenticated session if available
        if self._auth_session:
            web.session = self._auth_session
            self._log(f"  Testing web vulns on {url} (authenticated)...", "info")
        else:
            self._log(f"  Testing web vulns on {url}...", "info")

        # ── Nikto scan ────────────────────────────────────────────
        if system_tools.is_available("nikto") and not self._stop_event.is_set():
            self._log(f"    Running nikto...", "muted")
            nikto_lines = []

            def nikto_out(line):
                if self._verbose and line.strip():
                    self._log(f"    nikto: {line[:120]}", "muted")
                if "+ " in line:
                    nikto_lines.append(line)
                    if not self._verbose:  # avoid double print in verbose
                        self._log(f"    nikto: {line[:100]}", "warning")

            system_tools.nikto_scan(url, on_output=nikto_out)

            if nikto_lines:
                finding = Finding(
                    title=f"Nikto: {len(nikto_lines)} Web Issues Found",
                    severity="medium",
                    description="Nikto identified potential web vulnerabilities.",
                    evidence="\n".join(nikto_lines[:10]),
                    recommendation="Review each nikto finding and remediate accordingly.",
                    port=port, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)

        # ── SQLmap ────────────────────────────────────────────────
        if system_tools.is_available("sqlmap") and not self._stop_event.is_set():
            self._log(f"    Running sqlmap (full crawl)...", "muted")
            sqli_lines = []

            def sqlmap_out(line):
                if self._verbose and line.strip():
                    self._log(f"    sqlmap: {line[:120]}", "muted")
                if any(kw in line.lower() for kw in ["injectable", "vulnerable", "parameter", "payload"]):
                    sqli_lines.append(line)
                    if not self._verbose:
                        self._log(f"    sqlmap: {line[:80]}", "warning")

            system_tools.sqlmap_scan(url, on_output=sqlmap_out)

            if sqli_lines:
                finding = Finding(
                    title="SQLmap: SQL Injection Detected",
                    severity="critical",
                    description="sqlmap confirmed SQL injection vulnerability.",
                    evidence="\n".join(sqli_lines[:5]),
                    recommendation="Use parameterized queries. Never concatenate user input in SQL.",
                    port=port, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)
                self._log(f"    🔴 SQLi CONFIRMED by sqlmap!", "critical")

        # ── Built-in SQLi (always runs) ───────────────────────────
        if not self._stop_event.is_set():
            sqli_params = ["id", "page", "cat", "item", "user", "search", "q", "name",
                           "file", "path", "view", "action", "cmd", "query", "product"]
            hit = False
            for param in sqli_params:
                if self._stop_event.is_set():
                    break
                self._vlog(f"      → SQLi testing ?{param} ({len(web.test_sqli_basic.__doc__ or '')} payloads)...", "muted")
                sqli = web.test_sqli_basic(url, param)
                for r in sqli.get("all_results", []):
                    if r.get("vulnerable"):
                        self._vlog(f"        [HIT] payload={r['payload']!r}  indicators={r.get('indicators','')}", "warning")
                    else:
                        self._vlog(f"        [---] payload={r.get('payload','')!r}  status={r.get('status','-')}  len={r.get('length','-')}", "muted")
                if sqli.get("potentially_vulnerable"):
                    hit = True
                    vuln_payloads = sqli.get("vulnerable_payloads", [])
                    finding = Finding(
                        title=f"SQL Injection: ?{param}",
                        severity="critical",
                        description=f"Parameter '{param}' is vulnerable to SQL injection.",
                        evidence="\n".join(
                            f"Payload: {v['payload']} → {', '.join(v.get('indicators', []))}"
                            for v in vuln_payloads[:3]
                        ),
                        recommendation="Use parameterized queries / prepared statements.",
                        port=port, service="HTTP"
                    )
                    result.add_finding(finding)
                    if self.on_finding:
                        self.on_finding(finding)
                    self._log(f"    🔴 SQLi on ?{param}!", "critical")
            if not hit:
                self._log(f"    SQLi: no obvious injection found in common params", "muted")

        # ── XSS Testing ───────────────────────────────────────────
        if not self._stop_event.is_set():
            self._log(f"    Testing XSS...", "info")
            xss_payloads = [
                '<script>alert("XSS")</script>',
                '"><script>alert(1)</script>',
                '<img src=x onerror=alert(1)>',
                "javascript:alert(1)",
                '<svg onload=alert(1)>',
            ]
            xss_params = ["q", "search", "name", "msg", "comment", "input", "text", "id"]
            xss_found = []
            # Use authenticated session if available
            session = web.session
            for param in xss_params:
                if self._stop_event.is_set():
                    break
                for payload in xss_payloads[:3]:
                    try:
                        test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
                        self._vlog(f"      → XSS GET {test_url}", "muted")
                        r = session.get(test_url, timeout=5, verify=False)
                        reflected = payload in r.text or urllib.parse.quote(payload) in r.text
                        self._vlog(f"        status={r.status_code}  len={len(r.text)}  reflected={reflected}", "muted")
                        if reflected:
                            xss_found.append(f"?{param} reflects: {payload[:40]}")
                            break
                    except Exception as e:
                        self._vlog(f"        error: {e}", "muted")
            if xss_found:
                finding = Finding(
                    title=f"Reflected XSS Found ({len(xss_found)} param(s))",
                    severity="high",
                    description="User input is reflected in the page without sanitization.",
                    evidence="\n".join(xss_found),
                    recommendation="Encode all output. Implement Content-Security-Policy.",
                    port=port, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)
                self._log(f"    🔴 XSS reflected in {len(xss_found)} param(s)!", "critical")
            else:
                self._log(f"    XSS: no obvious reflection", "muted")

        # ── LFI / Path Traversal ──────────────────────────────────
        if not self._stop_event.is_set():
            self._log(f"    Testing LFI / Path Traversal...", "info")
            lfi_payloads = [
                "../../../../etc/passwd",
                "../../../../etc/passwd%00",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "/etc/passwd",
            ]
            lfi_params = ["file", "page", "path", "include", "load", "read", "doc", "lang", "template"]
            lfi_found = []
            for param in lfi_params:
                if self._stop_event.is_set():
                    break
                for payload in lfi_payloads[:3]:
                    try:
                        test_url = f"{url}?{param}={payload}"
                        self._vlog(f"      → LFI GET {test_url}", "muted")
                        r = session.get(test_url, timeout=5, verify=False)
                        hit = "root:x:" in r.text or "root:0:0:" in r.text or "/bin/bash" in r.text
                        self._vlog(f"        status={r.status_code}  len={len(r.text)}  lfi_hit={hit}", "muted")
                        if hit:
                            lfi_found.append(f"?{param}={payload[:50]}")
                            self._log(f"    🔴 LFI on ?{param}!", "critical")
                            break
                    except Exception as e:
                        self._vlog(f"        error: {e}", "muted")
            if lfi_found:
                finding = Finding(
                    title=f"Local File Inclusion (LFI) Detected",
                    severity="critical",
                    description="Server is including local files based on user input.",
                    evidence="\n".join(lfi_found),
                    recommendation="Validate file paths. Use whitelists. Never pass user input to file functions.",
                    port=port, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)
            else:
                self._log(f"    LFI: no obvious inclusion", "muted")

        # ── Command Injection ─────────────────────────────────────
        if not self._stop_event.is_set():
            self._log(f"    Testing Command Injection...", "info")
            cmd_payloads = [
                "; id", "| id", "& id", "` id`",
                "; sleep 2", "| sleep 2", "$(sleep 2)",
            ]
            cmd_params = ["cmd", "exec", "command", "run", "ping", "host", "ip", "query",
                          "search", "input", "name", "url", "path"]
            cmd_found = []
            for param in cmd_params:
                if self._stop_event.is_set():
                    break
                for payload in cmd_payloads[:4]:
                    try:
                        test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
                        self._vlog(f"      → CMD GET {test_url}", "muted")
                        r = session.get(test_url, timeout=6, verify=False)
                        elapsed = r.elapsed.total_seconds()
                        output_hit = any(ind in r.text for ind in ["uid=", "gid=", "root", "www-data"])
                        time_hit   = "sleep" in payload and elapsed >= 1.8
                        self._vlog(f"        status={r.status_code}  len={len(r.text)}  time={elapsed:.2f}s  output={output_hit}  timebased={time_hit}", "muted")
                        if output_hit:
                            cmd_found.append(f"?{param} → output detected: {payload[:30]}")
                            self._log(f"    🔴 CMD Injection on ?{param}!", "critical")
                            break
                        if time_hit:
                            cmd_found.append(f"?{param} → time-based: {payload[:30]}")
                            self._log(f"    🔴 CMD Injection (time-based) on ?{param}!", "critical")
                            break
                    except Exception as e:
                        self._vlog(f"        error: {e}", "muted")
            if cmd_found:
                finding = Finding(
                    title="Command Injection Detected",
                    severity="critical",
                    description="OS command injection vulnerability allows arbitrary command execution.",
                    evidence="\n".join(cmd_found),
                    recommendation="Never pass user input to shell. Use subprocess with argument lists.",
                    port=port, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)
            else:
                self._log(f"    CMD Injection: no obvious injection", "muted")

        # ── IDOR / Auth Bypass ────────────────────────────────────
        if not self._stop_event.is_set():
            self._log(f"    Testing IDOR / Auth Bypass...", "info")
            idor_paths = [
                "/api/user/1", "/api/user/2", "/api/users",
                "/api/admin", "/api/flag", "/api/secret",
                "/user/1", "/user/2", "/profile/1", "/profile/admin",
                "/admin/dashboard", "/admin/users", "/admin/config",
            ]
            idor_found = []
            for path in idor_paths:
                if self._stop_event.is_set():
                    break
                try:
                    full = f"{url.rstrip('/')}{path}"
                    self._vlog(f"      → IDOR GET {full}", "muted")
                    r = session.get(full, timeout=5, verify=False, allow_redirects=False)
                    size = len(r.content)
                    self._vlog(f"        status={r.status_code}  len={size}", "muted")
                    if r.status_code in (200, 201, 206) and size > 10:
                        idor_found.append(f"[{r.status_code}] {path} ({size}b)")
                        self._log(f"    ⚠️  Accessible: {path} ({r.status_code})", "warning")
                except Exception as e:
                    self._vlog(f"        error: {e}", "muted")
            if idor_found:
                finding = Finding(
                    title=f"Potentially Unprotected API Endpoints ({len(idor_found)})",
                    severity="high",
                    description="API endpoints accessible without authentication or authorization checks.",
                    evidence="\n".join(idor_found[:10]),
                    recommendation="Implement proper authentication and authorization on all API endpoints.",
                    port=port, service="HTTP"
                )
                result.add_finding(finding)
                if self.on_finding:
                    self.on_finding(finding)

        # ── Open Redirect ─────────────────────────────────────────
        if not self._stop_event.is_set():
            self._log(f"    Testing Open Redirect...", "info")
            redirect_payloads = [
                "https://evil.com", "//evil.com", "/\\evil.com",
                "https:evil.com", "javascript:alert(1)"
            ]
            redirect_params = ["redirect", "url", "next", "return", "goto", "target", "redir", "dest"]
            for param in redirect_params:
                if self._stop_event.is_set():
                    break
                for payload in redirect_payloads[:2]:
                    try:
                        test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
                        self._vlog(f"      → Redirect GET {test_url}", "muted")
                        r = session.get(test_url, timeout=5, verify=False, allow_redirects=False)
                        location = r.headers.get("Location", "")
                        self._vlog(f"        status={r.status_code}  Location={location or '(none)'}", "muted")
                        if r.status_code in (301, 302, 303, 307, 308) and "evil.com" in location:
                            finding = Finding(
                                title="Open Redirect Detected",
                                severity="medium",
                                description=f"Parameter ?{param} allows redirecting users to arbitrary URLs.",
                                evidence=f"?{param}={payload} → Location: {location}",
                                recommendation="Validate redirect targets against an allowlist.",
                                port=port, service="HTTP"
                            )
                            result.add_finding(finding)
                            if self.on_finding:
                                self.on_finding(finding)
                            self._log(f"    ⚠️  Open Redirect on ?{param}!", "warning")
                            break
                    except Exception:
                        pass

        time.sleep(0.3)

    # ─── Phase 4: AI Analysis ─────────────────────────────────────────────────

    def _phase_ai_analysis(self, result: ScanResult):
        self._log("\n[Phase 4] AI Analysis", "phase")

        if not self.ai_agent or not self.ai_agent.is_ready():
            self._log("  AI not available, skipping deep analysis", "warning")
            return

        # Build findings summary for AI
        findings_text = self._build_findings_summary(result)
        self._log("  AI is analyzing all findings...", "info")
        self._log("  (This may take a moment...)", "muted")

        prompt = f"""You are a senior penetration tester analyzing a target. Provide a DEEP technical analysis.

TARGET: {result.target}
OPEN PORTS: {[f"{p['port']}/{p['service']}" for p in result.open_ports]}

SCAN FINDINGS:
{findings_text}

Provide ALL of the following:

## 1. Risk Assessment
- Overall risk level and why
- Most critical finding and its real-world impact

## 2. Attack Chain
- How the found vulnerabilities can be chained together
- Step-by-step exploitation path from initial access to full compromise

## 3. Exploitation Techniques
For each critical/high finding, provide:
- Exact tool commands to exploit (with flags and parameters)
- Manual exploitation steps
- Expected output/result

## 4. Post-Exploitation
- What can be done after initial access
- Privilege escalation paths if applicable
- Lateral movement opportunities

## 5. Remediation (Priority Order)
- Numbered list from most to least urgent
- Specific fix for each issue

Be SPECIFIC and TECHNICAL. Include actual commands, payloads, and techniques.
Do NOT give generic advice. Tailor everything to this specific target and its services."""

        try:
            analysis = self.ai_agent.quick_analyze(
                prompt,
                context="You are a senior penetration tester writing a security assessment."
            )
            result.ai_analysis = analysis
            self._log("  ✅ AI analysis complete", "success")
            # Preview
            preview = analysis[:200].replace("\n", " ")
            self._log(f"  → {preview}...", "muted")
        except Exception as e:
            self._log(f"  AI analysis error: {e}", "error")
            result.ai_analysis = "AI analysis not available."

    # ─── Phase 5: Report Generation ──────────────────────────────────────────

    def _phase_report(self, result: ScanResult):
        self._log("\n[Phase 5] Generating Report", "phase")

        counts = result.summary_counts()
        duration = ""
        if result.end_time:
            s = int((result.end_time - result.start_time).total_seconds())
            duration = f"{s//60}m {s%60}s"

        by_severity = result.get_findings_by_severity()

        lines = []
        lines.append("# CyberMind AI - Penetration Test Report")
        lines.append(f"\n**Target:** `{result.target}`")
        if result.hostname:
            lines.append(f"**Hostname:** `{result.hostname}`")
        lines.append(f"**Date:** {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Duration:** {duration}")
        lines.append(f"**Tool:** CyberMind AI v{config.APP_VERSION}")
        lines.append("\n---\n")

        # Executive Summary
        lines.append("## Executive Summary\n")
        total = len(result.findings)
        critical = counts["critical"]
        high = counts["high"]

        if critical > 0:
            risk = "CRITICAL"
        elif high > 0:
            risk = "HIGH"
        elif counts["medium"] > 0:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        lines.append(f"Overall Risk Level: **{risk}**\n")
        lines.append(f"The automated scan identified **{total} findings** on target `{result.target}`:\n")
        for sev, count in counts.items():
            if count > 0:
                icon = SEVERITY[sev]["icon"]
                label = SEVERITY[sev]["label"]
                lines.append(f"- {icon} **{label}**: {count}")

        lines.append("")

        # Open Ports
        lines.append("## Open Ports\n")
        if result.open_ports:
            lines.append("| Port | Service | Banner |")
            lines.append("|------|---------|--------|")
            for p in result.open_ports:
                banner = (p.get("banner") or "")[:60]
                lines.append(f"| {p['port']}/tcp | {p['service']} | {banner} |")
        else:
            lines.append("No open ports detected.")
        lines.append("")

        # Findings by severity
        lines.append("## Findings\n")
        for sev in ["critical", "high", "medium", "low", "info"]:
            sev_findings = by_severity.get(sev, [])
            if not sev_findings:
                continue
            icon = SEVERITY[sev]["icon"]
            label = SEVERITY[sev]["label"]
            lines.append(f"### {icon} {label} ({len(sev_findings)})\n")
            for i, f in enumerate(sev_findings, 1):
                lines.append(f"#### {i}. {f.title}")
                if f.port:
                    lines.append(f"**Port:** {f.port} | **Service:** {f.service}")
                lines.append(f"\n**Description:** {f.description}\n")
                if f.evidence:
                    lines.append(f"**Evidence:**\n```\n{f.evidence[:500]}\n```\n")
                if f.recommendation:
                    lines.append(f"**Recommendation:** {f.recommendation}\n")
                lines.append("")

        # AI Analysis
        if result.ai_analysis and result.ai_analysis != "AI analysis not available.":
            lines.append("## AI Security Analysis\n")
            lines.append(result.ai_analysis)
            lines.append("")

        # Disclaimer
        lines.append("---")
        lines.append("*Report generated by CyberMind AI. For authorized security testing only.*")

        result.report_text = "\n".join(lines)
        self._log("  ✅ Report generated", "success")

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _build_findings_summary(self, result: ScanResult) -> str:
        lines = [f"Target: {result.target}"]
        lines.append(f"Open Ports: {[p['port'] for p in result.open_ports]}")
        lines.append("")
        by_sev = result.get_findings_by_severity()
        for sev in ["critical", "high", "medium", "low"]:
            for f in by_sev.get(sev, []):
                lines.append(f"[{sev.upper()}] {f.title}")
                lines.append(f"  {f.description}")
                if f.evidence:
                    lines.append(f"  Evidence: {f.evidence[:100]}")
        return "\n".join(lines)

    def _log(self, message: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        if self.on_log:
            self.on_log(f"[{ts}] {message}", level)
        logger.debug(message)

    def _vlog(self, message: str, level: str = "muted"):
        """Verbose-only log — only shown when verbose mode is ON"""
        if self._verbose:
            self._log(message, level)

    def _set_phase(self, phase_id: str, phase_name: str):
        self._log(f"\n{'='*40}", "phase")
        if self.on_phase:
            self.on_phase(phase_id, phase_name)

    def _progress(self, percent: int, message: str):
        if self.on_progress:
            self.on_progress(percent, message)
