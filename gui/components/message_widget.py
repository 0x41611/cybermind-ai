"""
CyberMind AI - Message Widget
Renders chat messages with markdown-like formatting
"""
import re
import tkinter as tk
import customtkinter as ctk
from gui.theme import COLORS, FONTS, CATEGORY_COLORS
from datetime import datetime


class MessageWidget(ctk.CTkFrame):
    """
    A single chat message bubble with formatting support
    """

    def __init__(self, parent, role: str, content: str,
                 timestamp: datetime = None, metadata: dict = None):
        super().__init__(parent, fg_color="transparent")

        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

        self._build()

    def _build(self):
        is_user = self.role == "user"

        # Outer padding
        self.configure(fg_color="transparent")

        # Message row
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=2)

        if is_user:
            self._build_user_message(row)
        else:
            self._build_ai_message(row)

    def _build_user_message(self, row):
        """Build user message (right-aligned)"""
        # Timestamp (left side)
        ts = ctk.CTkLabel(
            row,
            text=self.timestamp.strftime("%H:%M"),
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"],
            width=40
        )
        ts.pack(side="right", padx=(4, 0), anchor="s")

        # Bubble
        bubble = ctk.CTkFrame(
            row,
            fg_color=COLORS["blue_dim"],
            corner_radius=12,
        )
        bubble.pack(side="right", padx=(60, 0))

        # Content
        ctk.CTkLabel(
            bubble,
            text=self.content,
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
            wraplength=500,
            justify="left",
            anchor="w",
        ).pack(padx=12, pady=8)

    def _build_ai_message(self, row):
        """Build AI message with formatted content (left-aligned)"""
        # Avatar
        avatar = ctk.CTkLabel(
            row,
            text="⚡",
            font=("Segoe UI Emoji", 16),
            width=30,
            text_color=COLORS["accent"]
        )
        avatar.pack(side="left", anchor="n", padx=(0, 6), pady=(2, 0))

        # Message container
        container = ctk.CTkFrame(
            row,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        container.pack(side="left", fill="x", expand=True, padx=(0, 60))

        # Header row
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            header,
            text="CyberMind",
            font=FONTS["h3"],
            text_color=COLORS["accent"]
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=self.timestamp.strftime("%H:%M"),
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"]
        ).pack(side="right")

        # Formatted content
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        content_frame.pack(fill="x", padx=12, pady=(4, 10))

        self._render_content(content_frame, self.content)

    def _render_content(self, parent, text: str):
        """Render message content with basic markdown formatting"""
        # Split into blocks
        blocks = self._parse_blocks(text)

        for block_type, block_content in blocks:
            if block_type == "code":
                self._render_code_block(parent, block_content)
            elif block_type == "heading":
                self._render_heading(parent, block_content)
            elif block_type == "tool_result":
                self._render_tool_result(parent, block_content)
            else:
                self._render_text(parent, block_content)

    def _parse_blocks(self, text: str):
        """Parse text into blocks"""
        blocks = []
        lines = text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Code block
            if line.startswith("```"):
                lang = line[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                blocks.append(("code", {"lang": lang, "code": "\n".join(code_lines)}))

            # Tool result block
            elif line.startswith("**[Tool:") and line.endswith("]**"):
                tool_name = re.search(r'\[Tool: (.+?)\]', line)
                name = tool_name.group(1) if tool_name else "Tool"
                # Collect tool output (next code block)
                i += 1
                if i < len(lines) and lines[i].startswith("```"):
                    code_lines = []
                    i += 1
                    while i < len(lines) and not lines[i].startswith("```"):
                        code_lines.append(lines[i])
                        i += 1
                    blocks.append(("tool_result", {"name": name, "output": "\n".join(code_lines)}))
                else:
                    continue

            # Heading
            elif line.startswith("## "):
                blocks.append(("heading", {"level": 2, "text": line[3:]}))

            elif line.startswith("### "):
                blocks.append(("heading", {"level": 3, "text": line[4:]}))

            else:
                # Regular text - accumulate consecutive lines
                text_lines = [line]
                while i + 1 < len(lines) and not lines[i+1].startswith("```") and not lines[i+1].startswith("## ") and not lines[i+1].startswith("**[Tool:"):
                    i += 1
                    text_lines.append(lines[i])
                full_text = "\n".join(text_lines).strip()
                if full_text:
                    blocks.append(("text", full_text))

            i += 1

        return blocks

    def _render_text(self, parent, text: str):
        """Render regular text with inline formatting"""
        if not text.strip():
            return

        label = ctk.CTkLabel(
            parent,
            text=text,
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
            wraplength=580,
            justify="left",
            anchor="w",
        )
        label.pack(fill="x", pady=2)

    def _render_code_block(self, parent, block: dict):
        """Render a code block"""
        lang = block.get("lang", "")
        code = block.get("code", "")

        # Code block frame
        code_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_primary"],
            corner_radius=6,
            border_width=1,
            border_color=COLORS["border"]
        )
        code_frame.pack(fill="x", pady=(4, 4))

        # Language header
        if lang:
            header = ctk.CTkFrame(code_frame, fg_color=COLORS["bg_secondary"], corner_radius=0, height=24)
            header.pack(fill="x")
            header.pack_propagate(False)
            ctk.CTkLabel(
                header,
                text=f" {lang.upper()}",
                font=FONTS["badge"],
                text_color=COLORS["accent_dim"],
                anchor="w"
            ).pack(side="left", padx=8)

        # Code text
        code_text = ctk.CTkTextbox(
            code_frame,
            font=FONTS["mono"],
            text_color=COLORS["text_code"],
            fg_color=COLORS["bg_primary"],
            height=min(300, (code.count("\n") + 2) * 18),
            corner_radius=0,
            border_width=0,
            wrap="none",
        )
        code_text.pack(fill="x", padx=8, pady=6)
        code_text.insert("end", code)
        code_text.configure(state="disabled")

    def _render_tool_result(self, parent, block: dict):
        """Render tool execution result"""
        name = block.get("name", "Tool")
        output = block.get("output", "")

        # Tool result frame
        frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["accent_dark"],
            corner_radius=6,
            border_width=1,
            border_color=COLORS["accent_dim"]
        )
        frame.pack(fill="x", pady=(4, 4))

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(6, 2))

        ctk.CTkLabel(
            header,
            text=f"⚙ {name}",
            font=FONTS["h3"],
            text_color=COLORS["accent"]
        ).pack(side="left")

        # Output
        if output:
            out_text = ctk.CTkTextbox(
                frame,
                font=FONTS["mono_sm"],
                text_color=COLORS["text_secondary"],
                fg_color=COLORS["bg_primary"],
                height=min(200, (output.count("\n") + 2) * 16),
                corner_radius=4,
                border_width=0,
                wrap="none",
            )
            out_text.pack(fill="x", padx=8, pady=(2, 8))
            out_text.insert("end", output)
            out_text.configure(state="disabled")

    def _render_heading(self, parent, block: dict):
        """Render heading"""
        level = block.get("level", 2)
        text = block.get("text", "")

        font = FONTS["h2"] if level == 2 else FONTS["h3"]
        color = COLORS["accent"] if level == 2 else COLORS["text_primary"]

        ctk.CTkLabel(
            parent,
            text=text,
            font=font,
            text_color=color,
            anchor="w"
        ).pack(fill="x", pady=(6, 2))


class ThinkingIndicator(ctk.CTkFrame):
    """Animated thinking indicator"""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._after_id = None
        self._dots = 0
        self._build()

    def _build(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(
            row,
            text="⚡",
            font=("Segoe UI Emoji", 16),
            width=30,
            text_color=COLORS["accent"]
        ).pack(side="left", anchor="n", padx=(0, 6))

        bubble = ctk.CTkFrame(
            row,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        bubble.pack(side="left")

        self._label = ctk.CTkLabel(
            bubble,
            text="Analyzing...",
            font=FONTS["body"],
            text_color=COLORS["accent"],
        )
        self._label.pack(padx=16, pady=10)
        self._animate()

    def _animate(self):
        texts = ["Analyzing   ", "Analyzing.  ", "Analyzing.. ", "Analyzing..."]
        self._dots = (self._dots + 1) % 4
        if self._label.winfo_exists():
            self._label.configure(text=texts[self._dots])
            self._after_id = self.after(400, self._animate)

    def stop(self):
        if self._after_id:
            self.after_cancel(self._after_id)
