"""
CyberMind AI - Stats Screen
Knowledge base and usage statistics
"""
import customtkinter as ctk
from gui.theme import COLORS, FONTS, CATEGORY_COLORS
from config import config


class StatsScreen(ctk.CTkFrame):
    """Statistics and knowledge base overview"""

    def __init__(self, parent, rag_engine=None, trainer=None, conversation_manager=None):
        super().__init__(parent, fg_color="transparent")
        self.rag_engine = rag_engine
        self.trainer = trainer
        self.conversation = conversation_manager
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
            text="📊  Statistics & Knowledge",
            font=FONTS["h1"],
            text_color=COLORS["accent"]
        ).pack(side="left", padx=16, pady=14)

        refresh_btn = ctk.CTkButton(
            header,
            text="↻ Refresh",
            command=self.refresh,
            width=80,
            height=28,
            font=FONTS["body_sm"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_secondary"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=6,
        )
        refresh_btn.pack(side="right", padx=12)

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ── Scrollable Content ────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_primary"],
            corner_radius=0,
        )
        scroll.pack(fill="both", expand=True)

        # ── Knowledge Base Stats ──────────────────────────────────
        kb_frame = self._section(scroll, "🧠  Knowledge Base")

        top_stats = ctk.CTkFrame(kb_frame, fg_color="transparent")
        top_stats.pack(fill="x")

        self._kb_labels = {}
        kb_stats_items = [
            ("total_chunks", "Total Chunks", "0"),
            ("total_writeups", "Writeups Learned", "0"),
            ("training_runs", "Training Runs", "0"),
            ("last_trained", "Last Trained", "Never"),
        ]

        for key, label, default in kb_stats_items:
            card = self._mini_card(top_stats, label, default)
            card.pack(side="left", fill="x", expand=True, padx=4)
            self._kb_labels[key] = card

        # ── Categories Breakdown ──────────────────────────────────
        cats_frame = self._section(scroll, "🗂️  Knowledge by Category")
        self._cats_content = ctk.CTkFrame(cats_frame, fg_color="transparent")
        self._cats_content.pack(fill="x")

        # ── Chat Sessions ─────────────────────────────────────────
        sessions_frame = self._section(scroll, "💬  Recent Sessions")
        self._sessions_content = ctk.CTkFrame(sessions_frame, fg_color="transparent")
        self._sessions_content.pack(fill="x")

        # ── System Info ───────────────────────────────────────────
        sys_frame = self._section(scroll, "⚙️  System Info")
        self._sys_content = ctk.CTkFrame(sys_frame, fg_color="transparent")
        self._sys_content.pack(fill="x")
        self._build_system_info()

        self.refresh()

    def _mini_card(self, parent, label: str, value: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            height=70,
        )
        frame.pack_propagate(False)

        frame._value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=FONTS["h2"],
            text_color=COLORS["accent"]
        )
        frame._value_label.pack(pady=(10, 0))

        ctk.CTkLabel(
            frame,
            text=label,
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"]
        ).pack(pady=(0, 8))

        return frame

    def _section(self, parent, title: str) -> ctk.CTkFrame:
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

        ctk.CTkFrame(frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=(0, 8))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(0, 12))
        return inner

    def _build_system_info(self):
        """Build system information panel"""
        import platform
        import sys

        info = [
            ("Model", config.AI_MODEL),
            ("Python", f"{sys.version.split()[0]}"),
            ("Platform", platform.system()),
            ("Embedding Model", config.EMBEDDING_MODEL),
            ("DB Path", str(config.CHROMA_DB_PATH)[:50] + "..."),
            ("API Configured", "✅ Yes" if config.is_configured() else "❌ No"),
        ]

        for i, (label, value) in enumerate(info):
            row = ctk.CTkFrame(self._sys_content, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=label + ":",
                font=FONTS["label"],
                text_color=COLORS["text_muted"],
                width=130,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=value,
                font=FONTS["mono_sm"],
                text_color=COLORS["text_primary"],
                anchor="w"
            ).pack(side="left")

    def refresh(self):
        """Refresh all statistics"""
        # Update KB stats
        if self.trainer:
            stats = self.trainer.get_stats()
            updates = {
                "total_chunks": str(stats.get("total_docs", 0)),
                "total_writeups": str(stats.get("total_writeups", 0)),
                "training_runs": str(stats.get("training_runs", 0)),
                "last_trained": self._format_date(stats.get("last_trained")),
            }
            for key, value in updates.items():
                card = self._kb_labels.get(key)
                if card and hasattr(card, "_value_label"):
                    card._value_label.configure(text=value)

            # Category breakdown
            for w in self._cats_content.winfo_children():
                w.destroy()

            categories = stats.get("categories", {})
            if categories:
                total = sum(categories.values())
                for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                    self._build_category_bar(self._cats_content, cat, count, total)
            else:
                ctk.CTkLabel(
                    self._cats_content,
                    text="No knowledge stored yet. Run training to populate the knowledge base.",
                    font=FONTS["body"],
                    text_color=COLORS["text_muted"]
                ).pack()

        # Sessions
        for w in self._sessions_content.winfo_children():
            w.destroy()

        if self.conversation:
            sessions = self.conversation.get_all_sessions()[:5]
            for session in sessions:
                self._build_session_row(self._sessions_content, session)

    def _build_category_bar(self, parent, category: str, count: int, total: int):
        """Build category progress bar"""
        pct = count / total if total > 0 else 0
        color = CATEGORY_COLORS.get(category, COLORS["text_muted"])

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

        # Label
        ctk.CTkLabel(
            row,
            text=category,
            font=FONTS["body"],
            text_color=color,
            width=100,
            anchor="w"
        ).pack(side="left")

        # Bar
        bar_bg = ctk.CTkFrame(row, fg_color=COLORS["border"], corner_radius=3, height=8)
        bar_bg.pack(side="left", fill="x", expand=True, padx=8, pady=8)

        bar_fill = ctk.CTkFrame(
            bar_bg,
            fg_color=color,
            corner_radius=3,
            height=8,
        )
        bar_fill.place(relx=0, rely=0, relwidth=pct, relheight=1)

        # Count
        ctk.CTkLabel(
            row,
            text=f"{count}",
            font=FONTS["mono_sm"],
            text_color=COLORS["text_muted"],
            width=50
        ).pack(side="right")

    def _build_session_row(self, parent, session):
        """Build a session row"""
        row = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_input"],
            corner_radius=6,
        )
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(
            row,
            text=session.name,
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left", padx=10, pady=6)

        msg_count = len([m for m in session.messages if m.role in ("user", "assistant")])
        ctk.CTkLabel(
            row,
            text=f"{msg_count} msgs",
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"]
        ).pack(side="right", padx=10)

        ctk.CTkLabel(
            row,
            text=session.updated_at.strftime("%m/%d %H:%M"),
            font=FONTS["body_sm"],
            text_color=COLORS["text_muted"]
        ).pack(side="right", padx=4)

    def _format_date(self, date_str) -> str:
        if not date_str:
            return "Never"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%m/%d %H:%M")
        except Exception:
            return "Unknown"
