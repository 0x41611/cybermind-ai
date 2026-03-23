"""
CyberMind AI - Auto Pentest Screen
Autonomous IP scanning with live terminal + report generation
"""
import threading
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
from typing import Optional
from gui.theme import COLORS, FONTS, SIZES
from config import config


# Log level colors
LOG_COLORS = {
    "info":     COLORS["text_secondary"],
    "success":  COLORS["success"],
    "warning":  COLORS["warning"],
    "error":    COLORS["error"],
    "critical": COLORS["red"],
    "phase":    COLORS["accent"],
    "port":     COLORS["blue"],
    "finding":  COLORS["orange"],
    "muted":    COLORS["text_muted"],
}

PHASE_LIST = [
    ("auth",        "🔑 Auth"),
    ("recon",       "🔭 Recon"),
    ("enum",        "🔬 Enum"),
    ("vuln",        "⚡ Vuln"),
    ("ai_analysis", "🧠 AI"),
    ("report",      "📄 Report"),
]

SEVERITY_COLORS = {
    "critical": COLORS["red"],
    "high":     COLORS["orange"],
    "medium":   COLORS["yellow"],
    "low":      COLORS["blue"],
    "info":     COLORS["text_muted"],
}


class AutopwnScreen(ctk.CTkFrame):
    """
    Autonomous penetration testing screen.
    Give it an IP — it thinks, scans, and writes a report.
    """

    def __init__(self, parent, ai_agent=None):
        super().__init__(parent, fg_color="transparent")
        self.ai_agent = ai_agent
        self._agent = None
        self._scan_thread: Optional[threading.Thread] = None
        self._current_result = None
        self._finding_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────
        header = ctk.CTkFrame(
            self, fg_color=COLORS["bg_secondary"],
            corner_radius=0, height=52
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="🎯  Auto Pentest Agent",
            font=FONTS["h1"],
            text_color=COLORS["accent"]
        ).pack(side="left", padx=16, pady=14)

        # Disclaimer badge
        ctk.CTkLabel(
            header,
            text="⚠️ Authorized testing only",
            font=FONTS["body_sm"],
            text_color=COLORS["warning"],
            fg_color=COLORS["bg_card"],
            corner_radius=4,
            padx=8, pady=2,
        ).pack(side="right", padx=12)

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ── Target Input Bar ──────────────────────────────────────
        target_bar = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"],
            corner_radius=0, height=60,
            border_width=0
        )
        target_bar.pack(fill="x")
        target_bar.pack_propagate(False)

        inner = ctk.CTkFrame(target_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=10)

        # Target icon
        ctk.CTkLabel(
            inner, text="🎯",
            font=("Segoe UI Emoji", 18),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=(0, 8))

        # IP / Hostname input
        self._target_input = ctk.CTkEntry(
            inner,
            placeholder_text="Enter target IP or hostname (e.g. 192.168.1.1)",
            font=FONTS["mono"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            border_width=1,
            height=36,
            corner_radius=8,
        )
        self._target_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._target_input.bind("<Return>", lambda e: self._start_scan())

        # Options (compact)
        self._aggressive = ctk.CTkSwitch(
            inner,
            text="Deep Scan",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"],
            progress_color=COLORS["orange"],
            button_color=COLORS["orange"],
            width=80,
        )
        self._aggressive.pack(side="left", padx=8)

        self._verbose = ctk.CTkSwitch(
            inner,
            text="Verbose",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"],
            progress_color=COLORS["blue"],
            button_color=COLORS["blue"],
            width=80,
        )
        self._verbose.pack(side="left", padx=4)

        # Start / Stop button
        self._scan_btn = ctk.CTkButton(
            inner,
            text="▶  START SCAN",
            command=self._toggle_scan,
            width=140, height=36,
            font=FONTS["h2"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1,
            border_color=COLORS["accent_dim"],
            corner_radius=8,
        )
        self._scan_btn.pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ── Auth Row ──────────────────────────────────────────────
        auth_bar = ctk.CTkFrame(
            self, fg_color=COLORS["bg_secondary"],
            corner_radius=0, height=50,
        )
        auth_bar.pack(fill="x")
        auth_bar.pack_propagate(False)

        auth_inner = ctk.CTkFrame(auth_bar, fg_color="transparent")
        auth_inner.pack(fill="both", expand=True, padx=16, pady=8)

        # Toggle switch
        self._auth_enabled = ctk.CTkSwitch(
            auth_inner,
            text="🔑 Auth",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"],
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            width=70,
            command=self._toggle_auth_fields,
        )
        self._auth_enabled.pack(side="left", padx=(0, 10))

        # Login URL
        self._login_url_input = ctk.CTkEntry(
            auth_inner,
            placeholder_text="Login URL (leave blank to auto-detect)",
            font=FONTS["mono_sm"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            border_width=1,
            height=30,
            corner_radius=6,
            state="disabled",
        )
        self._login_url_input.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Username
        self._auth_user_input = ctk.CTkEntry(
            auth_inner,
            placeholder_text="Username",
            font=FONTS["mono_sm"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            border_width=1,
            height=30,
            width=120,
            corner_radius=6,
            state="disabled",
        )
        self._auth_user_input.pack(side="left", padx=(0, 6))

        # Password
        self._auth_pass_input = ctk.CTkEntry(
            auth_inner,
            placeholder_text="Password",
            font=FONTS["mono_sm"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            border_width=1,
            height=30,
            width=120,
            corner_radius=6,
            show="*",
            state="disabled",
        )
        self._auth_pass_input.pack(side="left", padx=(0, 8))

        # Try defaults checkbox
        self._try_defaults = ctk.CTkCheckBox(
            auth_inner,
            text="Try defaults",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_dim"],
            state="disabled",
        )
        self._try_defaults.pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ── Phase Indicator ───────────────────────────────────────
        phase_bar = ctk.CTkFrame(
            self, fg_color=COLORS["bg_secondary"],
            corner_radius=0, height=44
        )
        phase_bar.pack(fill="x")
        phase_bar.pack_propagate(False)

        phase_row = ctk.CTkFrame(phase_bar, fg_color="transparent")
        phase_row.pack(fill="both", expand=True, padx=16)

        self._phase_labels = {}
        for i, (phase_id, phase_name) in enumerate(PHASE_LIST):
            # Arrow separator
            if i > 0:
                ctk.CTkLabel(
                    phase_row, text="→",
                    font=FONTS["body_sm"],
                    text_color=COLORS["text_muted"]
                ).pack(side="left", padx=2)

            lbl = ctk.CTkLabel(
                phase_row,
                text=f"○ {phase_name}",
                font=FONTS["body_sm"],
                text_color=COLORS["text_muted"],
                fg_color=COLORS["bg_card"],
                corner_radius=4,
                padx=8, pady=2,
            )
            lbl.pack(side="left")
            self._phase_labels[phase_id] = lbl

        # Progress bar
        self._progress_bar = ctk.CTkProgressBar(
            self,
            mode="determinate",
            progress_color=COLORS["accent"],
            fg_color=COLORS["border"],
            height=3,
        )
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x")

        self._progress_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"],
            height=18,
        )
        self._progress_label.pack(anchor="w", padx=16)

        # ── Main Content (split view) ─────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)

        # ── Left: Live Terminal Log ───────────────────────────────
        left = ctk.CTkFrame(
            content,
            fg_color=COLORS["bg_primary"],
            corner_radius=0,
        )
        left.pack(side="left", fill="both", expand=True)

        # Terminal header
        term_header = ctk.CTkFrame(
            left, fg_color=COLORS["bg_card"],
            corner_radius=0, height=32
        )
        term_header.pack(fill="x")
        term_header.pack_propagate(False)

        ctk.CTkLabel(
            term_header,
            text="⬛  Live Terminal",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=10, pady=6)

        ctk.CTkButton(
            term_header,
            text="Clear",
            command=self._clear_log,
            width=45, height=20,
            font=FONTS["body_sm"],
            fg_color="transparent",
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"],
            corner_radius=4,
        ).pack(side="right", padx=6, pady=5)

        # Terminal text area
        self._terminal = ctk.CTkTextbox(
            left,
            font=("Courier New", 12),
            fg_color="#050a0f",
            text_color=COLORS["text_secondary"],
            corner_radius=0,
            border_width=0,
            wrap="word",
            scrollbar_button_color=COLORS["border"],
        )
        self._terminal.pack(fill="both", expand=True)
        self._terminal.configure(state="disabled")
        self._terminal.tag_config("info",     foreground=LOG_COLORS["info"])
        self._terminal.tag_config("success",  foreground=LOG_COLORS["success"])
        self._terminal.tag_config("warning",  foreground=LOG_COLORS["warning"])
        self._terminal.tag_config("error",    foreground=LOG_COLORS["error"])
        self._terminal.tag_config("critical", foreground=LOG_COLORS["critical"])
        self._terminal.tag_config("phase",    foreground=LOG_COLORS["phase"])
        self._terminal.tag_config("port",     foreground=LOG_COLORS["port"])
        self._terminal.tag_config("finding",  foreground=LOG_COLORS["finding"])
        self._terminal.tag_config("muted",    foreground=LOG_COLORS["muted"])

        # ── Right: Findings + Report ──────────────────────────────
        ctk.CTkFrame(content, width=1, fg_color=COLORS["border"]).pack(side="left", fill="y")

        right = ctk.CTkFrame(
            content,
            fg_color=COLORS["bg_secondary"],
            corner_radius=0,
            width=320,
        )
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # ── Finding Counters ──────────────────────────────────────
        counters_frame = ctk.CTkFrame(
            right, fg_color=COLORS["bg_card"],
            corner_radius=0, height=50
        )
        counters_frame.pack(fill="x")
        counters_frame.pack_propagate(False)

        ctk.CTkLabel(
            counters_frame,
            text="Findings",
            font=FONTS["label"],
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=10, pady=14)

        self._counter_labels = {}
        sev_display = [("critical","🔴"), ("high","🟠"), ("medium","🟡"), ("low","🔵"), ("info","⚪")]
        for sev, icon in sev_display:
            lbl = ctk.CTkLabel(
                counters_frame,
                text=f"{icon}0",
                font=FONTS["mono_sm"],
                text_color=SEVERITY_COLORS[sev],
            )
            lbl.pack(side="right", padx=4)
            self._counter_labels[sev] = lbl

        ctk.CTkFrame(right, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # Findings list
        findings_header = ctk.CTkFrame(
            right, fg_color="transparent", height=30
        )
        findings_header.pack(fill="x", padx=10, pady=(8, 4))
        findings_header.pack_propagate(False)

        ctk.CTkLabel(
            findings_header,
            text="🔍 Live Findings",
            font=FONTS["h3"],
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self._findings_scroll = ctk.CTkScrollableFrame(
            right,
            fg_color="transparent",
            corner_radius=0,
            height=280,
        )
        self._findings_scroll.pack(fill="x", padx=6)

        # ── Report Buttons ────────────────────────────────────────
        ctk.CTkFrame(right, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(
            right,
            text="📄 Report",
            font=FONTS["h3"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(fill="x", padx=12, pady=(8, 4))

        self._view_report_btn = ctk.CTkButton(
            right,
            text="📋 View Full Report",
            command=self._show_report,
            height=36,
            font=FONTS["body"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1, border_color=COLORS["accent_dim"],
            corner_radius=8,
            state="disabled"
        )
        self._view_report_btn.pack(fill="x", padx=10, pady=3)

        self._export_btn = ctk.CTkButton(
            right,
            text="💾 Export Markdown",
            command=self._export_report,
            height=36,
            font=FONTS["body"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_secondary"],
            border_width=1, border_color=COLORS["border"],
            corner_radius=8,
            state="disabled"
        )
        self._export_btn.pack(fill="x", padx=10, pady=3)

        # Terminal welcome message
        self._log_terminal("CyberMind Auto Pentest Agent", "phase")
        self._log_terminal("Enter a target IP and press START SCAN", "muted")
        self._log_terminal("⚠️  Use only on authorized targets!", "warning")
        self._log_terminal("─" * 40, "muted")

    # ─── Scan Control ─────────────────────────────────────────────────────────

    def _toggle_auth_fields(self):
        """Enable/disable auth input fields based on switch state"""
        state = "normal" if self._auth_enabled.get() else "disabled"
        for widget in (self._login_url_input, self._auth_user_input,
                       self._auth_pass_input, self._try_defaults):
            widget.configure(state=state)

    def _toggle_scan(self):
        if self._agent and self._agent.is_running:
            self._stop_scan()
        else:
            self._start_scan()

    def _start_scan(self):
        target = self._target_input.get().strip()
        if not target:
            self._log_terminal("❌ Please enter a target IP or hostname", "error")
            return

        # Reset UI
        self._reset_ui()
        self._scan_btn.configure(text="⏹  STOP", fg_color=COLORS["red_dim"],
                                 text_color=COLORS["red"], border_color=COLORS["red"])

        # Build auth options
        auth_opts = {"enabled": False}
        if self._auth_enabled.get():
            auth_opts = {
                "enabled":      True,
                "login_url":    self._login_url_input.get().strip(),
                "username":     self._auth_user_input.get().strip(),
                "password":     self._auth_pass_input.get(),
                "try_defaults": bool(self._try_defaults.get()),
            }

        # Build agent
        from core.autonomous_agent import AutonomousAgent
        self._agent = AutonomousAgent(
            ai_agent=self.ai_agent,
            on_log=lambda msg, lvl: self.after(0, self._log_terminal, msg, lvl),
            on_phase=lambda pid, pn: self.after(0, self._update_phase, pid),
            on_progress=lambda pct, msg: self.after(0, self._update_progress, pct, msg),
            on_finding=lambda f: self.after(0, self._add_finding_card, f),
            on_complete=lambda r: self.after(0, self._scan_complete, r),
        )

        self._scan_thread = threading.Thread(
            target=self._agent.run,
            args=(target, {
                "deep":    bool(self._aggressive.get()),
                "verbose": bool(self._verbose.get()),
                "auth":    auth_opts,
            }),
            daemon=True
        )
        self._scan_thread.start()

    def _stop_scan(self):
        if self._agent:
            self._agent.stop()
        self._scan_btn.configure(
            text="▶  START SCAN",
            fg_color=COLORS["accent_dark"],
            text_color=COLORS["accent"],
            border_color=COLORS["accent_dim"]
        )
        self._progress_label.configure(text="Scan stopped by user")

    def _scan_complete(self, result):
        """Called when scan finishes"""
        self._current_result = result
        self._scan_btn.configure(
            text="▶  START SCAN",
            fg_color=COLORS["accent_dark"],
            text_color=COLORS["accent"],
            border_color=COLORS["accent_dim"]
        )

        if result.report_text:
            self._view_report_btn.configure(state="normal")
            self._export_btn.configure(state="normal")
            self._log_terminal("\n📄 Report ready! Click 'View Full Report'", "success")

    # ─── UI Updates ────────────────────────────────────────────────────────────

    def _log_terminal(self, message: str, level: str = "info"):
        """Write to terminal"""
        self._terminal.configure(state="normal")
        self._terminal.insert("end", message + "\n", level)
        self._terminal.see("end")
        self._terminal.configure(state="disabled")

    def _update_phase(self, active_phase: str):
        """Highlight active phase"""
        phase_order = [p[0] for p in PHASE_LIST]
        active_idx = phase_order.index(active_phase) if active_phase in phase_order else -1

        for i, (phase_id, phase_name) in enumerate(PHASE_LIST):
            lbl = self._phase_labels.get(phase_id)
            if not lbl:
                continue
            if i < active_idx:
                # Done
                lbl.configure(
                    text=f"✅ {phase_name}",
                    text_color=COLORS["success"],
                    fg_color=COLORS["bg_primary"]
                )
            elif i == active_idx:
                # Active
                lbl.configure(
                    text=f"● {phase_name}",
                    text_color=COLORS["accent"],
                    fg_color=COLORS["accent_dark"]
                )
            else:
                # Pending
                lbl.configure(
                    text=f"○ {phase_name}",
                    text_color=COLORS["text_muted"],
                    fg_color=COLORS["bg_card"]
                )

    def _update_progress(self, percent: int, message: str):
        """Update progress bar"""
        self._progress_bar.set(percent / 100)
        self._progress_label.configure(text=message)

    def _add_finding_card(self, finding):
        """Add a finding to the live findings list"""
        from core.autonomous_agent import SEVERITY
        sev = finding.severity
        color = SEVERITY_COLORS.get(sev, COLORS["text_muted"])
        icon = SEVERITY.get(sev, {}).get("icon", "⚪")

        # Update counter
        self._finding_counts[sev] = self._finding_counts.get(sev, 0) + 1
        lbl = self._counter_labels.get(sev)
        if lbl:
            lbl.configure(text=f"{icon}{self._finding_counts[sev]}")

        # Skip info in live list to avoid clutter
        if sev == "info":
            return

        # Add card
        card = ctk.CTkFrame(
            self._findings_scroll,
            fg_color=COLORS["bg_card"],
            corner_radius=6,
            border_width=1,
            border_color=color,
        )
        card.pack(fill="x", pady=2)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=5)

        # Severity badge
        ctk.CTkLabel(
            row,
            text=f"{icon} {sev.upper()}",
            font=FONTS["badge"],
            text_color=color,
            width=70, anchor="w"
        ).pack(side="left")

        # Title
        ctk.CTkLabel(
            row,
            text=finding.title[:36] + ("..." if len(finding.title) > 36 else ""),
            font=FONTS["body_sm"],
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

    # ─── Report ────────────────────────────────────────────────────────────────

    def _show_report(self):
        """Show full report in popup"""
        if not self._current_result or not self._current_result.report_text:
            return

        popup = ctk.CTkToplevel(self)
        popup.title("CyberMind Pentest Report")
        popup.geometry("900x700")
        popup.configure(fg_color=COLORS["bg_primary"])

        # Header
        hdr = ctk.CTkFrame(popup, fg_color=COLORS["bg_secondary"], corner_radius=0, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text=f"📄 Pentest Report — {self._current_result.target}",
            font=FONTS["h2"], text_color=COLORS["accent"]
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(
            hdr, text="💾 Export", command=self._export_report,
            width=80, height=30,
            font=FONTS["body_sm"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1, border_color=COLORS["accent_dim"],
            corner_radius=6,
        ).pack(side="right", padx=12)

        # Report text
        report_text = ctk.CTkTextbox(
            popup,
            font=FONTS["mono_sm"],
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            border_width=0,
            corner_radius=0,
            wrap="word",
        )
        report_text.pack(fill="both", expand=True, padx=12, pady=12)
        report_text.insert("end", self._current_result.report_text)
        report_text.configure(state="disabled")

        popup.lift()
        popup.focus()

    def _export_report(self):
        """Export report to file"""
        if not self._current_result or not self._current_result.report_text:
            return

        target = self._current_result.target.replace(".", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"cybermind_report_{target}_{ts}.md"

        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All", "*.*")],
            initialfile=default_name,
            title="Save Pentest Report"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._current_result.report_text)
            self._log_terminal(f"✅ Report saved: {path}", "success")

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _reset_ui(self):
        """Reset UI for new scan"""
        # Clear terminal
        self._terminal.configure(state="normal")
        self._terminal.delete("1.0", "end")
        self._terminal.configure(state="disabled")

        # Clear findings
        for w in self._findings_scroll.winfo_children():
            w.destroy()

        # Reset counters
        sev_icons = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🔵","info":"⚪"}
        for sev in self._finding_counts:
            self._finding_counts[sev] = 0
            lbl = self._counter_labels.get(sev)
            if lbl:
                lbl.configure(text=f"{sev_icons[sev]}0")

        # Reset phase indicators
        for phase_id, phase_name in PHASE_LIST:
            lbl = self._phase_labels.get(phase_id)
            if lbl:
                lbl.configure(text=f"○ {phase_name}",
                               text_color=COLORS["text_muted"],
                               fg_color=COLORS["bg_card"])

        # Reset progress
        self._progress_bar.set(0)
        self._progress_label.configure(text="Starting...")

        # Disable report buttons
        self._view_report_btn.configure(state="disabled")
        self._export_btn.configure(state="disabled")
        self._current_result = None

    def _clear_log(self):
        self._terminal.configure(state="normal")
        self._terminal.delete("1.0", "end")
        self._terminal.configure(state="disabled")
