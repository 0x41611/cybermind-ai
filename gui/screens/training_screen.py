"""
CyberMind AI - Training Screen
Manages self-learning from CTF writeups
"""
import threading
import customtkinter as ctk
from gui.theme import COLORS, FONTS, CATEGORY_COLORS
from config import config


class TrainingScreen(ctk.CTkFrame):
    """
    Training management screen - controls the AI self-learning process
    """

    def __init__(self, parent, rag_engine=None, trainer=None):
        super().__init__(parent, fg_color="transparent")
        self.rag_engine = rag_engine
        self.trainer = trainer
        self._log_lines = []
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
            text="📚  Knowledge Training",
            font=FONTS["h1"],
            text_color=COLORS["accent"]
        ).pack(side="left", padx=16, pady=14)

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ── Main Content ──────────────────────────────────────────
        content = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_primary"],
            corner_radius=0,
        )
        content.pack(fill="both", expand=True)

        # ── Stats Cards ───────────────────────────────────────────
        stats_row = ctk.CTkFrame(content, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=16)

        self._stat_cards = {}
        stats = [
            ("📄", "Chunks Stored", "0", "total_docs"),
            ("📝", "Writeups Learned", "0", "total_writeups"),
            ("🔄", "Training Runs", "0", "training_runs"),
            ("🕐", "Last Trained", "Never", "last_trained"),
        ]

        for icon, label, default, key in stats:
            card = self._make_stat_card(stats_row, icon, label, default)
            card.pack(side="left", fill="x", expand=True, padx=4)
            self._stat_cards[key] = card

        # ── Training Controls ─────────────────────────────────────
        section = self._section(content, "🚀  Run Training")

        # Source selection
        ctk.CTkLabel(
            section,
            text="Training Sources:",
            font=FONTS["h3"],
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 8))

        sources_grid = ctk.CTkFrame(section, fg_color="transparent")
        sources_grid.pack(fill="x")

        self._source_switches = {}
        sources = [
            ("ctftime", "CTFtime.org Writeups", "Real CTF writeups from competitions"),
            ("github", "GitHub CTF Repos", "Open source CTF solution repositories"),
            ("hacktricks", "HackTricks", "Comprehensive pentesting techniques"),
        ]

        for src_id, src_name, src_desc in sources:
            row = ctk.CTkFrame(sources_grid, fg_color=COLORS["bg_card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
            row.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)

            sw = ctk.CTkSwitch(
                inner,
                text=src_name,
                font=FONTS["h3"],
                text_color=COLORS["text_primary"],
                progress_color=COLORS["accent"],
                button_color=COLORS["accent"],
            )
            sw.pack(side="left")
            sw.select()
            self._source_switches[src_id] = sw

            ctk.CTkLabel(
                inner,
                text=src_desc,
                font=FONTS["body_sm"],
                text_color=COLORS["text_muted"]
            ).pack(side="right")

        # Max writeups
        limit_row = ctk.CTkFrame(section, fg_color="transparent")
        limit_row.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(
            limit_row,
            text="Max writeups:",
            font=FONTS["label"],
            text_color=COLORS["text_muted"],
            width=100
        ).pack(side="left")

        self._max_writeups = ctk.CTkSlider(
            limit_row,
            from_=10,
            to=100,
            number_of_steps=9,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            fg_color=COLORS["border"],
        )
        self._max_writeups.set(50)
        self._max_writeups.pack(side="left", fill="x", expand=True, padx=8)

        self._max_label = ctk.CTkLabel(
            limit_row,
            text="50",
            font=FONTS["mono"],
            text_color=COLORS["accent"],
            width=30
        )
        self._max_label.pack(side="left")
        self._max_writeups.configure(command=lambda v: self._max_label.configure(text=str(int(v))))

        # Run button
        self._train_btn = ctk.CTkButton(
            section,
            text="▶  Start Training",
            command=self._start_training,
            height=44,
            font=FONTS["h2"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1,
            border_color=COLORS["accent_dim"],
            corner_radius=8,
        )
        self._train_btn.pack(fill="x", pady=(16, 0))

        # ── Custom URL ────────────────────────────────────────────
        url_section = self._section(content, "🌐  Learn from Custom URL")

        ctk.CTkLabel(
            url_section,
            text="Add any CTF writeup or security article URL to learn from:",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(0, 8))

        url_row = ctk.CTkFrame(url_section, fg_color="transparent")
        url_row.pack(fill="x")

        self._url_input = ctk.CTkEntry(
            url_row,
            placeholder_text="https://example.com/ctf-writeup...",
            font=FONTS["mono_sm"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            height=36,
        )
        self._url_input.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            url_row,
            text="Learn",
            command=self._learn_url,
            width=80,
            height=36,
            font=FONTS["h3"],
            fg_color=COLORS["blue_dim"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"],
            corner_radius=6,
        ).pack(side="right")

        # ── Progress Log ──────────────────────────────────────────
        log_section = self._section(content, "📋  Training Log")

        # Progress bar
        self._progress_bar = ctk.CTkProgressBar(
            log_section,
            mode="indeterminate",
            progress_color=COLORS["accent"],
            fg_color=COLORS["border"],
            height=4,
        )
        self._progress_bar.pack(fill="x", pady=(0, 8))

        # Log textbox
        self._log = ctk.CTkTextbox(
            log_section,
            font=FONTS["mono_sm"],
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_secondary"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            height=200,
        )
        self._log.pack(fill="x")

        # Clear log button
        ctk.CTkButton(
            log_section,
            text="Clear Log",
            command=self._clear_log,
            width=80,
            height=24,
            font=FONTS["body_sm"],
            fg_color="transparent",
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=4,
        ).pack(side="right", pady=8)

        # Auto-train toggle
        auto_row = ctk.CTkFrame(log_section, fg_color="transparent")
        auto_row.pack(fill="x", pady=(8, 0))

        ctk.CTkSwitch(
            auto_row,
            text=f"Auto-train every {config.TRAIN_INTERVAL_HOURS} hours",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
            progress_color=COLORS["accent"],
            command=self._toggle_auto_train,
        ).pack(side="left")

        # Update stats
        self.refresh_stats()

    def _make_stat_card(self, parent, icon, label, value):
        """Create a statistic card"""
        frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            height=80,
        )
        frame.pack_propagate(False)

        ctk.CTkLabel(frame, text=icon, font=("Segoe UI Emoji", 18), text_color=COLORS["accent"]).pack(pady=(8, 0))

        frame._value_label = ctk.CTkLabel(
            frame, text=value,
            font=FONTS["h2"],
            text_color=COLORS["accent"]
        )
        frame._value_label.pack()

        ctk.CTkLabel(frame, text=label, font=FONTS["body_sm"], text_color=COLORS["text_muted"]).pack(pady=(0, 6))

        return frame

    def _section(self, parent, title: str) -> ctk.CTkFrame:
        """Create a content section"""
        frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        frame.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(
            frame,
            text=title,
            font=FONTS["h2"],
            text_color=COLORS["accent"],
            anchor="w"
        ).pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkFrame(frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=(0, 10))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(0, 12))

        return inner

    def _start_training(self):
        """Start training process"""
        if not self.trainer:
            self._log_message("⚠️ Trainer not initialized")
            return

        if self.trainer.is_training:
            self._log_message("⚠️ Training already in progress")
            return

        if not self.rag_engine or not self.rag_engine.is_ready():
            self._log_message("⚠️ Knowledge base not ready. Check settings.")
            return

        self._train_btn.configure(state="disabled", text="⏳ Training...")
        self._progress_bar.start()

        def progress_callback(msg):
            self.after(0, self._log_message, msg)

        def complete_callback(result):
            def update():
                self._progress_bar.stop()
                self._progress_bar.configure(mode="determinate")
                self._progress_bar.set(1 if result.get("success") else 0)
                self._train_btn.configure(state="normal", text="▶  Start Training")
                if result.get("success"):
                    self._log_message(
                        f"✅ Training complete! {result['writeups_scraped']} writeups, "
                        f"{result['chunks_added']} chunks in {result['duration']}s"
                    )
                else:
                    self._log_message(f"❌ Training failed: {result.get('error')}")
                self.refresh_stats()
            self.after(0, update)

        self.trainer.on_progress = progress_callback
        self.trainer.on_complete = complete_callback
        self.trainer.train_async(max_writeups=int(self._max_writeups.get()))

    def _learn_url(self):
        """Learn from a custom URL"""
        url = self._url_input.get().strip()
        if not url:
            return

        if not self.trainer or not self.rag_engine:
            self._log_message("⚠️ System not ready")
            return

        self._log_message(f"📖 Learning from: {url}")

        def run():
            result = self.trainer.train(custom_url=url)
            def update():
                if result.get("success"):
                    self._log_message(f"✅ Learned from URL: {result.get('chunks_added', 0)} chunks added")
                else:
                    self._log_message(f"❌ Failed: {result.get('error')}")
                self.refresh_stats()
            self.after(0, update)

        threading.Thread(target=run, daemon=True).start()

    def _toggle_auto_train(self):
        """Toggle auto-training"""
        if self.trainer:
            if config.AUTO_TRAIN:
                self.trainer.stop_auto_training()
                config.AUTO_TRAIN = False
            else:
                config.AUTO_TRAIN = True
                self.trainer.start_auto_training()

    def _log_message(self, message: str):
        """Add message to training log"""
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log.configure(state="normal")
        self._log.insert("end", f"[{ts}] {message}\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self):
        """Clear the training log"""
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def refresh_stats(self):
        """Update statistics display"""
        if not self.trainer:
            return
        stats = self.trainer.get_stats()

        updates = {
            "total_docs": str(stats.get("total_docs", 0)),
            "total_writeups": str(stats.get("total_writeups", 0)),
            "training_runs": str(stats.get("training_runs", 0)),
            "last_trained": self._format_date(stats.get("last_trained")),
        }

        for key, value in updates.items():
            card = self._stat_cards.get(key)
            if card and hasattr(card, "_value_label"):
                card._value_label.configure(text=value)

    def _format_date(self, date_str) -> str:
        if not date_str:
            return "Never"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%m/%d %H:%M")
        except Exception:
            return "Unknown"
