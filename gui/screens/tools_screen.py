"""
CyberMind AI - Tools Screen
Interactive CTF and pentesting tools panel
"""
import threading
from tkinter import filedialog
import customtkinter as ctk
from gui.theme import COLORS, FONTS, CATEGORY_COLORS
from config import config


class ToolCard(ctk.CTkFrame):
    """A single tool card"""

    def __init__(self, parent, title: str, description: str,
                 category: str, icon: str, on_run):
        super().__init__(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.on_run = on_run
        self._build(title, description, category, icon)

    def _build(self, title, description, category, icon):
        self.configure(cursor="hand2")

        # Category color bar
        cat_color = CATEGORY_COLORS.get(category, COLORS["text_muted"])
        bar = ctk.CTkFrame(self, height=3, fg_color=cat_color, corner_radius=0)
        bar.pack(fill="x")

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)

        # Icon + Title
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text=icon,
            font=("Segoe UI Emoji", 20),
            width=30,
            text_color=cat_color
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=title,
            font=FONTS["h3"],
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left", padx=6)

        # Category badge
        ctk.CTkLabel(
            header,
            text=category,
            font=FONTS["badge"],
            text_color=cat_color,
            fg_color=COLORS["bg_input"],
            corner_radius=4,
            padx=6, pady=2,
        ).pack(side="right")

        # Description
        ctk.CTkLabel(
            content,
            text=description,
            font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"],
            anchor="w",
            wraplength=200,
            justify="left",
        ).pack(fill="x", pady=(4, 8))

        # Run button
        ctk.CTkButton(
            content,
            text="▶ Run",
            command=self.on_run,
            height=28,
            font=FONTS["body_sm"],
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["bg_hover"],
            text_color=cat_color,
            border_width=1,
            border_color=cat_color,
            corner_radius=6,
        ).pack(fill="x")


class ToolsScreen(ctk.CTkFrame):
    """
    Tools panel - interactive CTF and pentesting tools
    """

    TOOLS = [
        {
            "id": "sqli_test",
            "title": "SQL Injection Tester",
            "description": "Test URL parameters for SQL injection vulnerabilities",
            "category": "Web",
            "icon": "💉",
            "fields": [
                ("URL", "https://example.com/page", "entry"),
                ("Parameter", "id", "entry"),
            ]
        },
        {
            "id": "xss_payloads",
            "title": "XSS Payload Generator",
            "description": "Generate XSS payloads for different injection contexts",
            "category": "Web",
            "icon": "🕷️",
            "fields": [
                ("Context", "html|attribute|javascript|filter_bypass", "menu"),
            ]
        },
        {
            "id": "header_scan",
            "title": "HTTP Header Analyzer",
            "description": "Analyze security headers and misconfigurations",
            "category": "Web",
            "icon": "📡",
            "fields": [
                ("URL", "https://example.com", "entry"),
            ]
        },
        {
            "id": "auto_decode",
            "title": "Auto Decoder",
            "description": "Automatically detect and decode encoded data",
            "category": "Crypto",
            "icon": "🔓",
            "fields": [
                ("Encoded Data", "SGVsbG8gV29ybGQ=", "text"),
            ]
        },
        {
            "id": "caesar_brute",
            "title": "Caesar Cipher Brute",
            "description": "Brute force all 25 Caesar cipher shifts",
            "category": "Crypto",
            "icon": "🔑",
            "fields": [
                ("Ciphertext", "Khoor Zruog", "text"),
            ]
        },
        {
            "id": "hash_id",
            "title": "Hash Identifier",
            "description": "Identify hash type and crack common hashes",
            "category": "Crypto",
            "icon": "🧮",
            "fields": [
                ("Hash", "5d41402abc4b2a76b9719d911017c592", "entry"),
            ]
        },
        {
            "id": "file_analyze",
            "title": "File Analyzer",
            "description": "Analyze files for type, entropy, hidden data",
            "category": "Forensics",
            "icon": "🔬",
            "fields": [
                ("File Path", "*", "file"),
            ]
        },
        {
            "id": "lsb_extract",
            "title": "LSB Steganography",
            "description": "Extract hidden data from image LSB",
            "category": "Steganography",
            "icon": "🖼️",
            "fields": [
                ("Image Path", "*.png *.jpg *.jpeg *.bmp *.gif", "file"),
                ("Channel", "all|r|g|b", "menu"),
            ]
        },
        {
            "id": "port_scan",
            "title": "Port Scanner",
            "description": "Quick TCP port scan and service detection",
            "category": "Web",
            "icon": "🔭",
            "fields": [
                ("Host", "192.168.1.1", "entry"),
            ]
        },
        {
            "id": "dir_enum",
            "title": "Directory Enumerator",
            "description": "Discover hidden web directories and files",
            "category": "Web",
            "icon": "📂",
            "fields": [
                ("Base URL", "http://example.com", "entry"),
            ]
        },
        {
            "id": "strings_search",
            "title": "Strings Extractor",
            "description": "Extract and search strings from binary files",
            "category": "Forensics",
            "icon": "🔤",
            "fields": [
                ("File Path", "*", "file"),
                ("Pattern (optional)", "flag|CTF", "entry"),
            ]
        },
        {
            "id": "hex_dump",
            "title": "Hex Dump",
            "description": "View file contents as hex dump",
            "category": "Forensics",
            "icon": "💾",
            "fields": [
                ("File Path", "*", "file"),
                ("Offset", "0", "entry"),
                ("Length", "256", "entry"),
            ]
        },
    ]

    def __init__(self, parent, tool_executor=None):
        super().__init__(parent, fg_color="transparent")
        self.tool_executor = tool_executor
        self._active_tool = None
        self._field_widgets = {}
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
            text="🔧  CTF Tools",
            font=FONTS["h1"],
            text_color=COLORS["accent"]
        ).pack(side="left", padx=16, pady=14)

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ── Main Content (split view) ─────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)

        # Left: Tools grid
        left = ctk.CTkScrollableFrame(
            content,
            width=480,
            fg_color=COLORS["bg_primary"],
            corner_radius=0,
        )
        left.pack(side="left", fill="both", expand=True)

        # Build tool cards in a 2-column grid
        self._build_tool_cards(left)

        # Divider
        ctk.CTkFrame(content, width=1, fg_color=COLORS["border"]).pack(side="left", fill="y")

        # Right: Tool runner
        self._runner_frame = ctk.CTkFrame(
            content,
            width=400,
            fg_color=COLORS["bg_secondary"],
            corner_radius=0,
        )
        self._runner_frame.pack(side="right", fill="both")
        self._runner_frame.pack_propagate(False)

        self._show_runner_placeholder()

    def _build_tool_cards(self, parent):
        """Build tool cards in grid layout"""
        # Category filter
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filter_frame.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            filter_frame,
            text="Filter:",
            font=FONTS["label"],
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=(0, 6))

        self._filter_var = ctk.StringVar(value="All")
        for cat in ["All", "Web", "Crypto", "Forensics", "Steganography"]:
            color = CATEGORY_COLORS.get(cat, COLORS["text_muted"])
            btn = ctk.CTkButton(
                filter_frame,
                text=cat,
                command=lambda c=cat: self._filter_tools(c),
                width=60,
                height=24,
                font=FONTS["badge"],
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["bg_hover"],
                text_color=color,
                border_width=1,
                border_color=color,
                corner_radius=12,
            )
            btn.pack(side="left", padx=2)

        # Grid container
        self._grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._grid_frame.pack(fill="both", expand=True, padx=8)

        self._render_tool_grid(self.TOOLS)

    def _render_tool_grid(self, tools):
        """Render tools in 2-column grid"""
        for widget in self._grid_frame.winfo_children():
            widget.destroy()

        col = 0
        row_frame = None

        for tool in tools:
            if col % 2 == 0:
                row_frame = ctk.CTkFrame(self._grid_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=4)

            card = ToolCard(
                row_frame,
                title=tool["title"],
                description=tool["description"],
                category=tool["category"],
                icon=tool["icon"],
                on_run=lambda t=tool: self._show_tool_runner(t)
            )
            card.pack(side="left", fill="x", expand=True, padx=4)
            col += 1

    def _filter_tools(self, category: str):
        """Filter tools by category"""
        if category == "All":
            filtered = self.TOOLS
        else:
            filtered = [t for t in self.TOOLS if t["category"] == category]
        self._render_tool_grid(filtered)

    def _show_runner_placeholder(self):
        """Show placeholder in runner panel"""
        for w in self._runner_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._runner_frame,
            text="🔧",
            font=("Segoe UI Emoji", 48),
            text_color=COLORS["text_muted"]
        ).pack(expand=True)

        ctk.CTkLabel(
            self._runner_frame,
            text="Select a tool to run",
            font=FONTS["h2"],
            text_color=COLORS["text_muted"]
        ).pack()

        ctk.CTkLabel(
            self._runner_frame,
            text="Click any tool card on the left",
            font=FONTS["body"],
            text_color=COLORS["text_muted"]
        ).pack(pady=4)

    def _show_tool_runner(self, tool: dict):
        """Show tool runner panel for selected tool"""
        for w in self._runner_frame.winfo_children():
            w.destroy()

        self._field_widgets = {}
        self._active_tool = tool

        # Header
        header = ctk.CTkFrame(
            self._runner_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=0,
            height=50
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        cat_color = CATEGORY_COLORS.get(tool["category"], COLORS["accent"])
        ctk.CTkLabel(
            header,
            text=f"{tool['icon']}  {tool['title']}",
            font=FONTS["h2"],
            text_color=cat_color
        ).pack(side="left", padx=12, pady=14)

        # Fields
        fields_frame = ctk.CTkFrame(
            self._runner_frame,
            fg_color=COLORS["bg_primary"],
            corner_radius=0
        )
        fields_frame.pack(fill="x")

        for field_label, placeholder, field_type in tool.get("fields", []):
            field_row = ctk.CTkFrame(fields_frame, fg_color="transparent")
            field_row.pack(fill="x", padx=12, pady=4)

            ctk.CTkLabel(
                field_row,
                text=field_label,
                font=FONTS["label"],
                text_color=COLORS["text_muted"],
                width=100,
                anchor="w"
            ).pack(side="left")

            if field_type == "file":
                # File picker: button + label showing chosen path
                picker_frame = ctk.CTkFrame(
                    field_row,
                    fg_color=COLORS["bg_input"],
                    corner_radius=6,
                    border_width=1,
                    border_color=COLORS["border"],
                    height=32,
                )
                picker_frame.pack(side="left", fill="x", expand=True)
                picker_frame.pack_propagate(False)

                path_var = ctk.StringVar(value="")
                path_label = ctk.CTkLabel(
                    picker_frame,
                    textvariable=path_var,
                    font=FONTS["mono_sm"],
                    text_color=COLORS["text_muted"],
                    anchor="w",
                )
                path_label.pack(side="left", fill="x", expand=True, padx=8)

                # Build filetypes for dialog
                filetypes = [("All Files", "*.*")]
                if placeholder != "*":
                    exts = placeholder.strip()
                    filetypes = [(f"Allowed ({exts})", exts), ("All Files", "*.*")]

                def _pick_file(_pv=path_var, _pl=path_label, _ft=filetypes):
                    chosen = filedialog.askopenfilename(filetypes=_ft)
                    if chosen:
                        _pv.set(chosen)
                        _pl.configure(
                            text_color=COLORS["text_primary"],
                            text=chosen.split("/")[-1]   # show filename only
                        )
                        _pv.set(chosen)  # keep full path in var

                upload_btn = ctk.CTkButton(
                    picker_frame,
                    text="📂 Upload",
                    command=_pick_file,
                    width=80,
                    height=28,
                    font=FONTS["body_sm"],
                    fg_color=COLORS["accent_dark"],
                    hover_color=COLORS["bg_hover"],
                    text_color=COLORS["accent"],
                    border_width=1,
                    border_color=COLORS["accent_dim"],
                    corner_radius=5,
                )
                upload_btn.pack(side="right", padx=4, pady=2)

                # Widget proxy: get() returns the full path from path_var
                class _FileWidget:
                    def get(self): return path_var.get()

                widget = _FileWidget()

            elif field_type == "entry":
                widget = ctk.CTkEntry(
                    field_row,
                    placeholder_text=placeholder,
                    font=FONTS["mono_sm"],
                    fg_color=COLORS["bg_input"],
                    text_color=COLORS["text_primary"],
                    border_color=COLORS["border"],
                    height=32,
                )
                widget.pack(side="left", fill="x", expand=True)

            elif field_type == "text":
                widget = ctk.CTkTextbox(
                    field_row,
                    font=FONTS["mono_sm"],
                    fg_color=COLORS["bg_input"],
                    text_color=COLORS["text_primary"],
                    border_color=COLORS["border"],
                    height=60,
                )
                widget.pack(side="left", fill="x", expand=True)
                widget.insert("1.0", placeholder)

            elif field_type == "menu":
                options = placeholder.split("|")
                widget = ctk.CTkOptionMenu(
                    field_row,
                    values=options,
                    font=FONTS["body_sm"],
                    fg_color=COLORS["bg_input"],
                    button_color=COLORS["bg_hover"],
                    text_color=COLORS["text_primary"],
                    height=32,
                )
                widget.set(options[0])
                widget.pack(side="left", fill="x", expand=True)

            else:
                widget = None

            if widget:
                self._field_widgets[field_label] = widget

        # Run button
        ctk.CTkButton(
            self._runner_frame,
            text=f"▶  Run {tool['title']}",
            command=self._run_tool,
            height=40,
            font=FONTS["h3"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1,
            border_color=COLORS["accent_dim"],
            corner_radius=8,
        ).pack(fill="x", padx=12, pady=8)

        # Output
        ctk.CTkLabel(
            self._runner_frame,
            text="Output:",
            font=FONTS["label"],
            text_color=COLORS["text_muted"],
            anchor="w"
        ).pack(fill="x", padx=12)

        self._output = ctk.CTkTextbox(
            self._runner_frame,
            font=FONTS["mono_sm"],
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_code"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
        )
        self._output.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def _run_tool(self):
        """Execute the selected tool"""
        if not self._active_tool:
            return

        tool = self._active_tool
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("end", f"⏳ Running {tool['title']}...\n\n")

        # Get field values
        field_values = {}
        for label, widget in self._field_widgets.items():
            if hasattr(widget, "get"):
                try:
                    val = widget.get()
                    if callable(val):
                        val = val()
                except TypeError:
                    val = widget.get("1.0", "end").strip()
                field_values[label] = val if not isinstance(val, str) or val else ""
            if isinstance(widget, ctk.CTkTextbox):
                field_values[label] = widget.get("1.0", "end").strip()

        def run():
            try:
                result = self._execute_tool(tool["id"], field_values)
                self.after(0, self._show_output, result)
            except Exception as e:
                self.after(0, self._show_output, f"❌ Error: {str(e)}")

        threading.Thread(target=run, daemon=True).start()

    def _execute_tool(self, tool_id: str, fields: dict) -> str:
        """Execute a specific tool"""
        from tools.web_tools import WebTools
        from tools.crypto_tools import CryptoTools
        from tools.forensics_tools import ForensicsTools
        from tools.network_tools import NetworkTools
        import json

        if tool_id == "sqli_test":
            web = WebTools()
            result = web.test_sqli_basic(fields.get("URL", ""), fields.get("Parameter", "id"))
            return json.dumps(result, indent=2)

        elif tool_id == "xss_payloads":
            web = WebTools()
            context = fields.get("Context", "html")
            payloads = web.generate_xss_payloads(context)
            return f"XSS Payloads for context: {context}\n\n" + "\n".join(f"  {i+1}. {p}" for i, p in enumerate(payloads))

        elif tool_id == "header_scan":
            web = WebTools()
            result = web.analyze_headers(fields.get("URL", ""))
            return json.dumps(result, indent=2)

        elif tool_id == "auto_decode":
            crypto = CryptoTools()
            result = crypto.auto_decode(fields.get("Encoded Data", ""))
            if result:
                return "\n".join(f"[{method}]: {decoded}" for method, decoded in result.items())
            return "No successful decodings found."

        elif tool_id == "caesar_brute":
            crypto = CryptoTools()
            results = crypto.caesar_brute(fields.get("Ciphertext", ""))
            lines = ["Top Caesar decryptions (by English score):\n"]
            for r in results:
                lines.append(f"Shift {r['shift']:2d} (score: {r['score']:.3f}): {r['text']}")
            return "\n".join(lines)

        elif tool_id == "hash_id":
            crypto = CryptoTools()
            hash_val = fields.get("Hash", "")
            types = crypto.identify_hash(hash_val)
            result = f"Hash: {hash_val}\nPossible types: {', '.join(types)}\n"
            cracked = crypto.brute_force_hash(hash_val)
            if cracked:
                result += f"\n✅ CRACKED: {cracked}"
            return result

        elif tool_id == "file_analyze":
            forensics = ForensicsTools()
            result = forensics.analyze_file(fields.get("File Path", ""))
            return json.dumps(result, indent=2, default=str)

        elif tool_id == "lsb_extract":
            forensics = ForensicsTools()
            result = forensics.lsb_extract(
                fields.get("Image Path", ""),
                fields.get("Channel", "all")
            )
            return json.dumps(result, indent=2)

        elif tool_id == "port_scan":
            net = NetworkTools()
            result = net.check_common_services(fields.get("Host", ""))
            return json.dumps(result, indent=2)

        elif tool_id == "dir_enum":
            web = WebTools()
            result = web.enumerate_directories(fields.get("Base URL", ""))
            if result.get("found"):
                lines = [f"Found {len(result['found'])} paths:\n"]
                for item in result["found"]:
                    lines.append(f"  [{item['status']}] /{item['path']} ({item['size']} bytes)")
                return "\n".join(lines)
            return "No interesting paths found."

        elif tool_id == "strings_search":
            forensics = ForensicsTools()
            pattern = fields.get("Pattern (optional)", "").strip() or None
            result = forensics.strings_search(fields.get("File Path", ""), pattern)
            return json.dumps(result, indent=2)

        elif tool_id == "hex_dump":
            forensics = ForensicsTools()
            return forensics.hex_dump(
                fields.get("File Path", ""),
                int(fields.get("Offset", "0") or "0"),
                int(fields.get("Length", "256") or "256")
            )

        return "Tool not implemented"

    def _show_output(self, text: str):
        """Display tool output"""
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("end", text)
        self._output.configure(state="disabled")
