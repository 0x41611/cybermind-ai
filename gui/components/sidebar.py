"""
CyberMind AI - Sidebar Navigation Component
"""
import customtkinter as ctk
from gui.theme import COLORS, FONTS, SIZES
from typing import Callable, Dict


class NavButton(ctk.CTkFrame):
    """Individual navigation button"""

    def __init__(self, parent, icon: str, label: str, command: Callable,
                 is_active: bool = False):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=8,
            cursor="hand2"
        )
        self.command = command
        self._is_active = is_active
        self._icon = icon
        self._label = label

        self._build()
        self._bind_events()
        self.set_active(is_active)

    def _build(self):
        self.configure(height=46)
        self.pack_propagate(False)

        # Container
        self._container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=8)
        self._container.pack(fill="both", expand=True, padx=4, pady=2)

        # Accent bar (left side indicator)
        self._accent_bar = ctk.CTkFrame(
            self._container,
            width=3, height=30,
            fg_color=COLORS["accent"],
            corner_radius=2
        )
        self._accent_bar.place(x=0, y=8)

        # Icon
        self._icon_label = ctk.CTkLabel(
            self._container,
            text=self._icon,
            font=("Segoe UI Emoji", 16),
            width=28,
            text_color=COLORS["text_secondary"]
        )
        self._icon_label.pack(side="left", padx=(10, 4))

        # Text
        self._text_label = ctk.CTkLabel(
            self._container,
            text=self._label,
            font=FONTS["nav"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self._text_label.pack(side="left", fill="x", expand=True)

    def _bind_events(self):
        for widget in [self, self._container, self._icon_label, self._text_label]:
            widget.bind("<Button-1>", lambda e: self.command())
            widget.bind("<Enter>", lambda e: self._on_hover(True))
            widget.bind("<Leave>", lambda e: self._on_hover(False))

    def _on_hover(self, is_hover: bool):
        if not self._is_active:
            color = COLORS["bg_hover"] if is_hover else "transparent"
            self._container.configure(fg_color=color)

    def set_active(self, active: bool):
        self._is_active = active
        if active:
            self._container.configure(fg_color=COLORS["bg_active"])
            self._icon_label.configure(text_color=COLORS["accent"])
            self._text_label.configure(text_color=COLORS["accent"])
            self._accent_bar.place(x=0, y=8)
        else:
            self._container.configure(fg_color="transparent")
            self._icon_label.configure(text_color=COLORS["text_secondary"])
            self._text_label.configure(text_color=COLORS["text_secondary"])
            self._accent_bar.place_forget()


class Sidebar(ctk.CTkFrame):
    """
    Left sidebar navigation panel
    """

    NAV_ITEMS = [
        ("💬", "Chat",     "chat"),
        ("🎯", "AutoPwn",  "autopwn"),
        ("🔧", "Tools",    "tools"),
        ("📚", "Training", "training"),
        ("📊", "Stats",    "stats"),
        ("⚙️",  "Settings", "settings"),
    ]

    def __init__(self, parent, on_navigate: Callable[[str], None]):
        super().__init__(
            parent,
            width=SIZES["sidebar_width"],
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0,
        )
        self.on_navigate = on_navigate
        self._active_page = "chat"
        self._nav_buttons: Dict[str, NavButton] = {}

        self.pack_propagate(False)
        self._build()

    def _build(self):
        # ── Logo Section ──────────────────────────────────────────
        logo_frame = ctk.CTkFrame(
            self, fg_color="transparent", height=70
        )
        logo_frame.pack(fill="x", pady=(10, 0))
        logo_frame.pack_propagate(False)

        # Logo icon
        ctk.CTkLabel(
            logo_frame,
            text="⚡",
            font=("Segoe UI Emoji", 28),
            text_color=COLORS["accent"]
        ).pack(pady=(12, 0))

        # Divider
        ctk.CTkFrame(
            self, height=1, fg_color=COLORS["border"]
        ).pack(fill="x", padx=10, pady=(8, 12))

        # ── Navigation Items ──────────────────────────────────────
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True)

        for icon, label, page_id in self.NAV_ITEMS:
            btn = NavButton(
                nav_frame,
                icon=icon,
                label=label,
                command=lambda p=page_id: self._navigate(p),
                is_active=(page_id == self._active_page)
            )
            btn.pack(fill="x", padx=8, pady=1)
            self._nav_buttons[page_id] = btn

        # ── Bottom Section ────────────────────────────────────────
        ctk.CTkFrame(
            self, height=1, fg_color=COLORS["border"]
        ).pack(fill="x", padx=10, side="bottom", pady=(0, 8))

        # Version label
        ctk.CTkLabel(
            self,
            text="v1.0.0",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"],
        ).pack(side="bottom", pady=(0, 12))

        # Status indicator
        self._status_frame = ctk.CTkFrame(
            self, fg_color="transparent", height=30
        )
        self._status_frame.pack(side="bottom", fill="x", padx=8)

        self._status_dot = ctk.CTkLabel(
            self._status_frame,
            text="●",
            font=("Consolas", 10),
            text_color=COLORS["error"],
            width=16
        )
        self._status_dot.pack(side="left", padx=(6, 2))

        self._status_label = ctk.CTkLabel(
            self._status_frame,
            text="Not Ready",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"],
        )
        self._status_label.pack(side="left")

    def _navigate(self, page_id: str):
        """Handle navigation"""
        if page_id == self._active_page:
            return

        # Update button states
        if self._active_page in self._nav_buttons:
            self._nav_buttons[self._active_page].set_active(False)

        self._active_page = page_id
        if page_id in self._nav_buttons:
            self._nav_buttons[page_id].set_active(True)

        self.on_navigate(page_id)

    def set_status(self, ready: bool, message: str = ""):
        """Update AI status indicator"""
        if ready:
            self._status_dot.configure(text_color=COLORS["success"])
            self._status_label.configure(text=message or "AI Ready", text_color=COLORS["text_secondary"])
        else:
            self._status_dot.configure(text_color=COLORS["error"])
            self._status_label.configure(text=message or "Not Ready", text_color=COLORS["text_muted"])

    def navigate_to(self, page_id: str):
        """Programmatically navigate to a page"""
        self._navigate(page_id)
