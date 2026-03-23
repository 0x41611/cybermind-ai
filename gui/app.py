"""
CyberMind AI - Main Application
Initializes all components and manages the GUI
"""
import threading
import customtkinter as ctk
from config import config
from utils.logger import get_logger

logger = get_logger("app")


class CyberMindApp:
    """
    Main CyberMind application.
    Initializes AI components, RAG engine, and GUI.
    """

    def __init__(self):
        self._setup_ctk()
        self._init_components()
        self._build_window()

    def _setup_ctk(self):
        """Configure CustomTkinter"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def _init_components(self):
        """Initialize AI components (lazy, in background)"""
        from core.ai_agent import AIAgent
        from core.rag_engine import RAGEngine
        from core.tool_executor import ToolExecutor
        from core.conversation import ConversationManager
        from learning.trainer import Trainer

        self.rag_engine = RAGEngine()
        self.conversation = ConversationManager()
        self.tool_executor = ToolExecutor(rag_engine=self.rag_engine)
        self.ai_agent = AIAgent(rag_engine=self.rag_engine, tool_executor=self.tool_executor)
        self.trainer = Trainer(rag_engine=self.rag_engine)

    def _build_window(self):
        """Build the main window"""
        from gui.theme import COLORS, FONTS
        from gui.components.sidebar import Sidebar
        from gui.screens.chat_screen import ChatScreen
        from gui.screens.tools_screen import ToolsScreen
        from gui.screens.training_screen import TrainingScreen
        from gui.screens.settings_screen import SettingsScreen
        from gui.screens.stats_screen import StatsScreen
        from gui.screens.autopwn_screen import AutopwnScreen

        # ── Root Window ───────────────────────────────────────────
        self.root = ctk.CTk()
        self.root.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.minsize(1100, 700)
        self.root.configure(fg_color=COLORS["bg_primary"])

        # Set window icon (optional)
        try:
            self.root.iconbitmap("")
        except Exception:
            pass

        # ── Title Bar Row ─────────────────────────────────────────
        titlebar = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0,
            height=36
        )
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        # App name in title bar
        ctk.CTkLabel(
            titlebar,
            text="⚡ CyberMind AI",
            font=FONTS["h3"],
            text_color=COLORS["accent"]
        ).pack(side="left", padx=12, pady=8)

        # Status
        self._titlebar_status = ctk.CTkLabel(
            titlebar,
            text="● Initializing...",
            font=FONTS["body_sm"],
            text_color=COLORS["warning"]
        )
        self._titlebar_status.pack(side="right", padx=12)

        # ── Main Layout ───────────────────────────────────────────
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent", corner_radius=0)
        main_frame.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(main_frame, on_navigate=self._navigate)
        self.sidebar.pack(side="left", fill="y")

        # Vertical separator
        ctk.CTkFrame(
            main_frame, width=1,
            fg_color=COLORS["border"],
            corner_radius=0
        ).pack(side="left", fill="y")

        # Content area
        self._content = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS["bg_primary"],
            corner_radius=0
        )
        self._content.pack(side="right", fill="both", expand=True)

        # ── Build Screens ─────────────────────────────────────────
        self._screens = {
            "chat": ChatScreen(
                self._content,
                ai_agent=self.ai_agent,
                rag_engine=self.rag_engine,
                tool_executor=self.tool_executor,
                conversation_manager=self.conversation,
            ),
            "autopwn": AutopwnScreen(
                self._content,
                ai_agent=self.ai_agent,
            ),
            "tools": ToolsScreen(
                self._content,
                tool_executor=self.tool_executor,
            ),
            "training": TrainingScreen(
                self._content,
                rag_engine=self.rag_engine,
                trainer=self.trainer,
            ),
            "stats": StatsScreen(
                self._content,
                rag_engine=self.rag_engine,
                trainer=self.trainer,
                conversation_manager=self.conversation,
            ),
            "settings": SettingsScreen(
                self._content,
                ai_agent=self.ai_agent,
                on_config_changed=self._on_config_changed,
            ),
        }

        # Show chat screen by default
        self._current_screen = None
        self._navigate("chat")

        # ── Start Background Initialization ───────────────────────
        threading.Thread(target=self._init_ai, daemon=True).start()

    def _navigate(self, page_id: str):
        """Navigate to a screen"""
        if self._current_screen:
            self._screens.get(self._current_screen, ctk.CTkFrame(self._content)).pack_forget()

        screen = self._screens.get(page_id)
        if screen:
            screen.pack(fill="both", expand=True)
            self._current_screen = page_id

    def _init_ai(self):
        """Initialize AI components in background"""
        def update_status(msg: str, color: str):
            self.root.after(0, lambda: self._titlebar_status.configure(
                text=msg, text_color=color
            ))
            self.root.after(0, lambda: self.sidebar.set_status(
                color == "#22c55e",
                msg.replace("● ", "")
            ))

        from gui.theme import COLORS

        update_status("● Loading AI...", COLORS["warning"])

        # Initialize AI agent
        ai_ok = self.ai_agent.initialize()

        if not ai_ok:
            update_status("● API Key needed", COLORS["error"])
        else:
            update_status("● AI Ready", COLORS["success"])

        # Initialize RAG (slower - loads embedding model)
        update_status("● Loading knowledge base...", COLORS["warning"])

        def rag_progress(msg):
            self.root.after(0, lambda m=msg: self._titlebar_status.configure(text=f"● {m}"))

        rag_ok = self.rag_engine.initialize(on_progress=rag_progress)

        if rag_ok:
            stats = self.rag_engine.get_stats()
            doc_count = stats.get("total_docs", 0)

            # Auto-seed bundled HTB writeups on first run
            if doc_count == 0:
                update_status("● Seeding knowledge base...", COLORS["warning"])
                self._seed_bundled_writeups()
                stats = self.rag_engine.get_stats()
                doc_count = stats.get("total_docs", 0)

            update_status(f"● Ready ({doc_count} docs)", COLORS["success"])

            # Start auto-training if enabled
            if config.AUTO_TRAIN:
                self.trainer.start_auto_training()
        else:
            update_status(
                "● AI Ready (no RAG)" if ai_ok else "● Setup needed",
                COLORS["warning"] if ai_ok else COLORS["error"]
            )

        logger.info("Initialization complete")

    def _seed_bundled_writeups(self):
        """Seed the knowledge base from bundled local data — no internet needed."""
        import time
        try:
            from data.htb_seed_data import HTB_WRITEUPS
            t0 = time.time()
            added = self.rag_engine.add_writeups_batch(HTB_WRITEUPS)
            duration = time.time() - t0
            # Record in trainer stats so the dashboard shows correct numbers
            self.trainer.stats.record_training(
                writeups_count=len(HTB_WRITEUPS),
                chunks_count=added,
                duration=duration
            )
            logger.info(f"Seeded {added} chunks from {len(HTB_WRITEUPS)} bundled HTB writeups")
        except Exception as e:
            logger.warning(f"Could not seed bundled writeups: {e}")

    def _on_config_changed(self, change_type: str):
        """Handle configuration changes"""
        if change_type == "api_key":
            # Re-initialize AI agent with new key
            self.ai_agent.initialize()

    def run(self):
        """Start the application"""
        logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
        self.root.mainloop()
