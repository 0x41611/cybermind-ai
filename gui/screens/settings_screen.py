"""
CyberMind AI - Settings Screen
Local AI configuration via Ollama
"""
import threading
import customtkinter as ctk
from gui.theme import COLORS, FONTS
from config import config
from typing import Callable, Optional


class SettingsScreen(ctk.CTkFrame):
    """
    Application settings - Ollama model management
    """

    def __init__(self, parent, ai_agent=None, on_config_changed: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.ai_agent = ai_agent
        self.on_config_changed = on_config_changed
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
            text="⚙️  Settings",
            font=FONTS["h1"],
            text_color=COLORS["accent"]
        ).pack(side="left", padx=16, pady=14)

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ── Scrollable Content ────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["bg_primary"], corner_radius=0
        )
        scroll.pack(fill="both", expand=True)

        # ── Ollama Status ─────────────────────────────────────────
        status_section = self._section(scroll, "🤖  Ollama Status")

        self._status_card = ctk.CTkFrame(
            status_section,
            fg_color=COLORS["bg_input"],
            corner_radius=8,
        )
        self._status_card.pack(fill="x")

        status_inner = ctk.CTkFrame(self._status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=12, pady=10)

        self._status_dot = ctk.CTkLabel(
            status_inner, text="●", font=("Consolas", 16),
            text_color=COLORS["warning"], width=20
        )
        self._status_dot.pack(side="left")

        self._status_text = ctk.CTkLabel(
            status_inner,
            text="Checking Ollama...",
            font=FONTS["h3"],
            text_color=COLORS["text_primary"]
        )
        self._status_text.pack(side="left", padx=6)

        ctk.CTkButton(
            status_inner,
            text="↻ Refresh",
            command=self._check_ollama_status,
            width=70, height=28,
            font=FONTS["body_sm"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_secondary"],
            border_width=1, border_color=COLORS["border"],
            corner_radius=6,
        ).pack(side="right")

        # Install instructions (hidden if running)
        self._install_frame = ctk.CTkFrame(
            status_section,
            fg_color=COLORS["accent_dark"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["accent_dim"]
        )
        self._install_frame.pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(
            self._install_frame,
            text="📥  How to install Ollama:",
            font=FONTS["h3"],
            text_color=COLORS["accent"],
            anchor="w"
        ).pack(fill="x", padx=12, pady=(10, 4))

        install_steps = [
            "1. Go to  ollama.com  and download for your OS",
            "2. Install and run Ollama",
            "3. Open terminal and run:  ollama pull llama3.1",
            "4. Restart CyberMind",
        ]
        for step in install_steps:
            ctk.CTkLabel(
                self._install_frame,
                text=step,
                font=FONTS["mono_sm"],
                text_color=COLORS["text_secondary"],
                anchor="w"
            ).pack(fill="x", padx=16, pady=1)

        ctk.CTkFrame(self._install_frame, height=8, fg_color="transparent").pack()

        # ── Model Selection ───────────────────────────────────────
        model_section = self._section(scroll, "🧠  Active Model")

        model_row = ctk.CTkFrame(model_section, fg_color="transparent")
        model_row.pack(fill="x")

        ctk.CTkLabel(
            model_row,
            text="Current model:",
            font=FONTS["label"],
            text_color=COLORS["text_muted"],
            width=110, anchor="w"
        ).pack(side="left")

        self._model_menu = ctk.CTkOptionMenu(
            model_row,
            values=[config.AI_MODEL],
            font=FONTS["body"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["bg_hover"],
            button_hover_color=COLORS["bg_active"],
            text_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_text_color=COLORS["text_primary"],
            width=220, height=34,
            command=self._on_model_change,
        )
        self._model_menu.set(config.AI_MODEL)
        self._model_menu.pack(side="left", padx=8)

        ctk.CTkButton(
            model_row,
            text="Apply",
            command=self._apply_model,
            width=65, height=34,
            font=FONTS["h3"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1, border_color=COLORS["accent_dim"],
            corner_radius=6,
        ).pack(side="left")

        # ── Download Models ───────────────────────────────────────
        download_section = self._section(scroll, "📥  Download Models")

        ctk.CTkLabel(
            download_section,
            text="Recommended models for CTF & Pentesting:",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        model_cards = [
            ("llama3.1:8b",       "Best overall",    "4.7 GB", "⭐⭐⭐⭐⭐"),
            ("qwen2.5-coder:7b",  "Best for code",   "4.7 GB", "⭐⭐⭐⭐⭐"),
            ("mistral:7b",        "Fast & smart",    "4.1 GB", "⭐⭐⭐⭐"),
            ("deepseek-r1:8b",    "Best reasoning",  "4.9 GB", "⭐⭐⭐⭐"),
            ("llama3.2:3b",       "Lightweight",     "2.0 GB", "⭐⭐⭐"),
        ]

        for model_id, desc, size, rating in model_cards:
            self._model_card(download_section, model_id, desc, size, rating)

        # ── Download Progress ─────────────────────────────────────
        self._dl_frame = ctk.CTkFrame(
            download_section, fg_color=COLORS["bg_card"],
            corner_radius=8, border_width=1, border_color=COLORS["border"]
        )
        self._dl_frame.pack(fill="x", pady=(8, 0))

        self._dl_label = ctk.CTkLabel(
            self._dl_frame,
            text="Select a model above to download",
            font=FONTS["body"],
            text_color=COLORS["text_muted"]
        )
        self._dl_label.pack(padx=12, pady=8)

        self._dl_progress = ctk.CTkProgressBar(
            self._dl_frame,
            mode="indeterminate",
            progress_color=COLORS["accent"],
            fg_color=COLORS["border"],
            height=4,
        )

        # ── Tool Settings ─────────────────────────────────────────
        tools_section = self._section(scroll, "🔧  Tool Permissions")

        self._allow_code = ctk.CTkSwitch(
            tools_section,
            text="Allow Python Code Execution",
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
        )
        if config.ALLOW_CODE_EXECUTION:
            self._allow_code.select()
        self._allow_code.pack(anchor="w", pady=4)

        self._allow_network = ctk.CTkSwitch(
            tools_section,
            text="Allow Network / Web Tools",
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
        )
        if config.ALLOW_NETWORK_TOOLS:
            self._allow_network.select()
        self._allow_network.pack(anchor="w", pady=4)

        # ── RAG Settings ──────────────────────────────────────────
        rag_section = self._section(scroll, "🔍  Knowledge Base (RAG)")

        ctx_row = ctk.CTkFrame(rag_section, fg_color="transparent")
        ctx_row.pack(fill="x")

        ctk.CTkLabel(
            ctx_row, text="Context docs:",
            font=FONTS["label"], text_color=COLORS["text_muted"], width=110
        ).pack(side="left")

        self._ctx_slider = ctk.CTkSlider(
            ctx_row, from_=1, to=10, number_of_steps=9,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
        )
        self._ctx_slider.set(config.MAX_CONTEXT_DOCS)
        self._ctx_slider.pack(side="left", fill="x", expand=True, padx=8)

        self._ctx_label = ctk.CTkLabel(
            ctx_row, text=str(config.MAX_CONTEXT_DOCS),
            font=FONTS["mono"], text_color=COLORS["accent"], width=25
        )
        self._ctx_label.pack(side="left")
        self._ctx_slider.configure(
            command=lambda v: self._ctx_label.configure(text=str(int(v)))
        )

        # ── Save ──────────────────────────────────────────────────
        ctk.CTkButton(
            scroll,
            text="💾  Save Settings",
            command=self._save_all,
            height=44,
            font=FONTS["h2"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1, border_color=COLORS["accent_dim"],
            corner_radius=8,
        ).pack(fill="x", padx=16, pady=16)

        # Check status on load
        self.after(500, self._check_ollama_status)

    def _model_card(self, parent, model_id, desc, size, rating):
        """Single model download card"""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_input"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(fill="x", pady=3)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=6)

        # Model name
        ctk.CTkLabel(
            row, text=model_id,
            font=FONTS["mono"], text_color=COLORS["text_primary"],
            width=160, anchor="w"
        ).pack(side="left")

        # Description
        ctk.CTkLabel(
            row, text=desc,
            font=FONTS["body_sm"], text_color=COLORS["text_muted"],
            width=120, anchor="w"
        ).pack(side="left")

        # Rating
        ctk.CTkLabel(
            row, text=rating,
            font=FONTS["body_sm"], text_color=COLORS["yellow"],
            width=80
        ).pack(side="left")

        # Size
        ctk.CTkLabel(
            row, text=size,
            font=FONTS["mono_sm"], text_color=COLORS["text_muted"],
            width=60
        ).pack(side="left")

        # Download button
        ctk.CTkButton(
            row,
            text="⬇ Pull",
            command=lambda m=model_id: self._download_model(m),
            width=65, height=26,
            font=FONTS["body_sm"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["blue"],
            border_width=1, border_color=COLORS["blue_dim"],
            corner_radius=4,
        ).pack(side="right")

    def _section(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"],
            corner_radius=10, border_width=1, border_color=COLORS["border"]
        )
        frame.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(
            frame, text=title,
            font=FONTS["h2"], text_color=COLORS["accent"], anchor="w"
        ).pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkFrame(frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=(0, 8))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(0, 12))
        return inner

    def _check_ollama_status(self):
        """Check if Ollama is running"""
        def check():
            is_running = config.is_configured()
            models = config.get_available_models() if is_running else []

            def update():
                if is_running:
                    self._status_dot.configure(text_color=COLORS["success"])
                    model_count = len(models)
                    self._status_text.configure(
                        text=f"✅ Ollama running  •  {model_count} model{'s' if model_count != 1 else ''} installed",
                        text_color=COLORS["success"]
                    )
                    self._install_frame.pack_forget()

                    # Update model dropdown with installed models
                    if models:
                        self._model_menu.configure(values=models)
                        if config.AI_MODEL in models:
                            self._model_menu.set(config.AI_MODEL)
                        else:
                            self._model_menu.set(models[0])
                else:
                    self._status_dot.configure(text_color=COLORS["error"])
                    self._status_text.configure(
                        text="❌ Ollama not running",
                        text_color=COLORS["error"]
                    )
                    self._install_frame.pack(fill="x", pady=(8, 0))

            self.after(0, update)

        threading.Thread(target=check, daemon=True).start()

    def _download_model(self, model_name: str):
        """Pull a model via Ollama"""
        if not self.ai_agent:
            return

        self._dl_label.configure(
            text=f"⏳ Starting download: {model_name}",
            text_color=COLORS["accent"]
        )
        self._dl_progress.pack(fill="x", padx=12, pady=(0, 8))
        self._dl_progress.start()

        def progress(msg):
            self.after(0, lambda m=msg: self._dl_label.configure(
                text=m, text_color=COLORS["text_secondary"]
            ))

        def run():
            success = self.ai_agent.pull_model(model_name, on_progress=progress)

            def done():
                self._dl_progress.stop()
                self._dl_progress.pack_forget()
                if success:
                    self._dl_label.configure(
                        text=f"✅ {model_name} downloaded! Refreshing...",
                        text_color=COLORS["success"]
                    )
                    self._check_ollama_status()
                else:
                    self._dl_label.configure(
                        text=f"❌ Failed to download {model_name}",
                        text_color=COLORS["error"]
                    )

            self.after(0, done)

        threading.Thread(target=run, daemon=True).start()

    def _on_model_change(self, value: str):
        pass

    def _apply_model(self):
        """Apply selected model"""
        model = self._model_menu.get()
        config.save_model(model)
        config.AI_MODEL = model

        if self.ai_agent:
            self.ai_agent.initialize()

        if self.on_config_changed:
            self.on_config_changed("model")

    def _save_all(self):
        """Save all settings"""
        config.ALLOW_CODE_EXECUTION = bool(self._allow_code.get())
        config.ALLOW_NETWORK_TOOLS = bool(self._allow_network.get())
        config.MAX_CONTEXT_DOCS = int(self._ctx_slider.get())

        if self.on_config_changed:
            self.on_config_changed("settings")
