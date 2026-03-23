"""
CyberMind AI - UI Theme
Dark cybersecurity-themed color palette and typography
"""

# ─── Color Palette ─────────────────────────────────────────────────────────

COLORS = {
    # Backgrounds
    "bg_primary":    "#080d1a",
    "bg_secondary":  "#0d1526",
    "bg_card":       "#111f35",
    "bg_input":      "#0a1628",
    "bg_hover":      "#162040",
    "bg_active":     "#1a2850",
    "bg_sidebar":    "#070c18",

    # Borders
    "border":        "#1a3050",
    "border_light":  "#243d60",
    "border_accent": "#00cc7a",

    # Accent Colors (Cyber Green)
    "accent":        "#00ff9f",
    "accent_dim":    "#00cc7a",
    "accent_dark":   "#004d2e",
    "accent_glow":   "#00ff9f",

    # Secondary Accents
    "blue":          "#3b82f6",
    "blue_dim":      "#1d4ed8",
    "purple":        "#8b5cf6",
    "purple_dim":    "#6d28d9",
    "orange":        "#f97316",
    "red":           "#ef4444",
    "red_dim":       "#b91c1c",
    "yellow":        "#eab308",

    # Text
    "text_primary":  "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted":    "#4b6080",
    "text_accent":   "#00ff9f",
    "text_code":     "#a8ff78",

    # Status
    "success":       "#22c55e",
    "warning":       "#f59e0b",
    "error":         "#ef4444",
    "info":          "#3b82f6",
}

# ─── Fonts ─────────────────────────────────────────────────────────────────

FONTS = {
    "title":    ("Consolas", 22, "bold"),
    "h1":       ("Consolas", 18, "bold"),
    "h2":       ("Consolas", 14, "bold"),
    "h3":       ("Consolas", 12, "bold"),
    "body":     ("Consolas", 12),
    "body_sm":  ("Consolas", 11),
    "label":    ("Consolas", 11),
    "mono":     ("Courier New", 12),
    "mono_sm":  ("Courier New", 11),
    "nav":      ("Consolas", 12, "bold"),
    "badge":    ("Consolas", 10, "bold"),
}

# ─── Sizes ─────────────────────────────────────────────────────────────────

SIZES = {
    "sidebar_width":    160,
    "border_radius":    8,
    "padding":          12,
    "padding_sm":       6,
    "padding_lg":       20,
    "button_height":    36,
    "input_height":     40,
    "icon_size":        20,
}

# ─── Category Colors ───────────────────────────────────────────────────────

CATEGORY_COLORS = {
    "Web":           "#3b82f6",
    "Crypto":        "#8b5cf6",
    "Pwn":           "#ef4444",
    "Forensics":     "#22c55e",
    "OSINT":         "#f97316",
    "Steganography": "#ec4899",
    "Misc":          "#94a3b8",
    "Reverse":       "#eab308",
    "Any":           "#94a3b8",
}

# ─── CTK Theme Config ──────────────────────────────────────────────────────

CTK_THEME = {
    "CTkFrame": {
        "corner_radius": 8,
        "border_width": 1,
        "fg_color": COLORS["bg_card"],
        "border_color": COLORS["border"],
    },
    "CTkButton": {
        "corner_radius": 6,
        "border_width": 0,
        "fg_color": COLORS["accent_dark"],
        "hover_color": COLORS["bg_hover"],
        "text_color": COLORS["accent"],
        "font": FONTS["body"],
    },
}
