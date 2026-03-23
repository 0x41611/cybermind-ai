"""
CyberMind AI - Chat Screen
Main AI conversation interface
"""
import threading
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
from typing import Optional, Callable
from gui.theme import COLORS, FONTS, SIZES, CATEGORY_COLORS
from gui.components.message_widget import MessageWidget, ThinkingIndicator
from config import config


class ChatScreen(ctk.CTkFrame):
    """
    Main chat interface for interacting with CyberMind AI
    """

    def __init__(self, parent, ai_agent=None, rag_engine=None,
                 tool_executor=None, conversation_manager=None):
        super().__init__(parent, fg_color="transparent")
        self.ai_agent = ai_agent
        self.rag_engine = rag_engine
        self.tool_executor = tool_executor
        self.conversation = conversation_manager
        self._is_generating = False
        self._thinking_widget: Optional[ThinkingIndicator] = None
        self._selected_category = "Any"

        self._build()
        self._load_current_session()

    def _build(self):
        # ── Header ────────────────────────────────────────────────
        header = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            corner_radius=0,
            height=52,
            border_width=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        # Title
        ctk.CTkLabel(
            header,
            text="💬  CyberMind Chat",
            font=FONTS["h1"],
            text_color=COLORS["accent"]
        ).pack(side="left", padx=16, pady=14)

        # Header right controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right", padx=12)

        # Category selector
        ctk.CTkLabel(
            controls,
            text="Category:",
            font=FONTS["label"],
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=(0, 4))

        self._category_menu = ctk.CTkOptionMenu(
            controls,
            values=["Any"] + config.CTF_CATEGORIES,
            command=self._on_category_change,
            font=FONTS["body_sm"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["bg_hover"],
            button_hover_color=COLORS["bg_active"],
            text_color=COLORS["text_primary"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_text_color=COLORS["text_primary"],
            dropdown_hover_color=COLORS["bg_hover"],
            width=110,
            height=28,
        )
        self._category_menu.set("Any")
        self._category_menu.pack(side="left", padx=4)

        # New session button
        ctk.CTkButton(
            controls,
            text="+ New",
            command=self._new_session,
            width=60,
            height=28,
            font=FONTS["body_sm"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1,
            border_color=COLORS["accent_dim"],
            corner_radius=6,
        ).pack(side="left", padx=4)

        # Clear button
        ctk.CTkButton(
            controls,
            text="Clear",
            command=self._clear_chat,
            width=55,
            height=28,
            font=FONTS["body_sm"],
            fg_color="transparent",
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=6,
        ).pack(side="left", padx=2)

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ── Chat Messages Area ────────────────────────────────────
        self._messages_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_primary"],
            corner_radius=0,
            scrollbar_fg_color=COLORS["bg_secondary"],
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["bg_hover"],
        )
        self._messages_frame.pack(fill="both", expand=True)

        # Welcome message
        self._show_welcome()

        # ── Input Area ────────────────────────────────────────────
        input_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            corner_radius=0,
            height=90,
        )
        input_frame.pack(fill="x", side="bottom")
        input_frame.pack_propagate(False)

        # Inner padding
        inner = ctk.CTkFrame(input_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=8)

        # Text input
        self._input = ctk.CTkTextbox(
            inner,
            font=FONTS["body"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
            height=56,
            wrap="word",
            scrollbar_button_color=COLORS["border"],
        )
        self._input.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._input.bind("<Return>", self._on_enter)
        self._input.bind("<Shift-Return>", lambda e: None)  # Allow shift+enter

        # Set placeholder
        self._set_placeholder()

        # Send button
        self._send_btn = ctk.CTkButton(
            inner,
            text="Send  ↵",
            command=self._send_message,
            width=90,
            height=56,
            font=FONTS["h3"],
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"],
            border_width=1,
            border_color=COLORS["accent_dim"],
            corner_radius=10,
        )
        self._send_btn.pack(side="right")

    def _show_welcome(self):
        """Show welcome message"""
        welcome = ctk.CTkFrame(
            self._messages_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        welcome.pack(fill="x", padx=16, pady=20)

        ctk.CTkLabel(
            welcome,
            text="⚡ CyberMind AI",
            font=FONTS["h1"],
            text_color=COLORS["accent"]
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            welcome,
            text="Your AI-powered CTF & Penetration Testing Assistant",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"]
        ).pack(pady=(0, 12))

        # Quick prompts
        prompts_frame = ctk.CTkFrame(welcome, fg_color="transparent")
        prompts_frame.pack(fill="x", padx=16, pady=(0, 16))

        quick_prompts = [
            ("🕷️  Web CTF",        "I have a web CTF challenge. Help me find SQL injection vulnerabilities."),
            ("🔐  Crypto",          "Solve this crypto challenge: I have ciphertext that looks like base64..."),
            ("💾  Binary/Pwn",       "I have a binary exploitation challenge. How do I find buffer overflows?"),
            ("🔍  Forensics",        "I have a suspicious PNG file. Help me analyze it for hidden data."),
        ]

        for label, prompt in quick_prompts:
            btn = ctk.CTkButton(
                prompts_frame,
                text=label,
                command=lambda p=prompt: self._quick_prompt(p),
                font=FONTS["body_sm"],
                fg_color=COLORS["bg_input"],
                hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_secondary"],
                border_width=1,
                border_color=COLORS["border"],
                corner_radius=8,
                height=32,
            )
            btn.pack(side="left", padx=4)

    def _load_current_session(self):
        """Load messages from current session"""
        if not self.conversation:
            return
        session = self.conversation.get_current()
        for msg in session.messages:
            if msg.role in ("user", "assistant"):
                self._add_message_widget(msg.role, msg.content, msg.timestamp)

    def _add_message_widget(self, role: str, content: str, timestamp: datetime = None):
        """Add a message widget to the chat"""
        widget = MessageWidget(
            self._messages_frame,
            role=role,
            content=content,
            timestamp=timestamp or datetime.now(),
        )
        widget.pack(fill="x", pady=2)
        self._scroll_to_bottom()
        return widget

    def _send_message(self):
        """Send the user's message"""
        if self._is_generating:
            return

        text = self._input.get("1.0", "end").strip()
        if not text or text == self._placeholder_text:
            return

        # Clear input
        self._input.delete("1.0", "end")
        self._is_generating = True
        self._send_btn.configure(state="disabled", text="...")

        # Add user message
        self._add_message_widget("user", text)

        # Save to conversation
        if self.conversation:
            self.conversation.get_current().add_message("user", text)

        # Show thinking indicator
        self._thinking_widget = ThinkingIndicator(self._messages_frame)
        self._thinking_widget.pack(fill="x", pady=2)
        self._scroll_to_bottom()

        # Generate response in background
        thread = threading.Thread(
            target=self._generate_response,
            args=(text,),
            daemon=True
        )
        thread.start()

    def _generate_response(self, user_text: str):
        """Generate AI response (runs in background thread)"""
        if not self.ai_agent or not self.ai_agent.is_ready():
            self.after(0, self._finish_response,
                       "⚠️ AI agent not configured. Please add your API key in Settings.")
            return

        # Get conversation history
        messages = []
        if self.conversation:
            messages = self.conversation.get_current().get_api_messages(max_history=20)

        response_parts = []

        def on_text(chunk: str):
            response_parts.append(chunk)
            # Update last message widget if exists (streaming)

        def on_done(full_response: str):
            self.after(0, self._finish_response, full_response)

        try:
            from core.conversation import ConversationManager
            system = ConversationManager.SYSTEM_PROMPT

            # Add category hint to system if selected
            if self._selected_category != "Any":
                system += f"\n\nThe user is working on a **{self._selected_category}** challenge."

            self.ai_agent.chat(
                messages=messages,
                system_prompt=system,
                on_text=on_text,
                on_done=on_done,
                use_rag=True,
                use_tools=True,
            )
        except Exception as e:
            self.after(0, self._finish_response, f"❌ Error: {str(e)}")

    def _finish_response(self, response: str):
        """Called when AI response is complete"""
        # Remove thinking indicator
        if self._thinking_widget:
            self._thinking_widget.stop()
            self._thinking_widget.destroy()
            self._thinking_widget = None

        # Add AI response
        self._add_message_widget("assistant", response)

        # Save to conversation
        if self.conversation:
            self.conversation.get_current().add_message("assistant", response)
            self.conversation.save_current()

        self._is_generating = False
        self._send_btn.configure(state="normal", text="Send  ↵")
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """Scroll chat to bottom"""
        self.after(50, lambda: self._messages_frame._parent_canvas.yview_moveto(1.0))

    def _new_session(self):
        """Start a new chat session"""
        if self.conversation:
            self.conversation.new_session()
        # Clear messages
        for widget in self._messages_frame.winfo_children():
            widget.destroy()
        self._show_welcome()

    def _clear_chat(self):
        """Clear all messages in current session"""
        if self.conversation:
            session = self.conversation.get_current()
            session.messages.clear()
        for widget in self._messages_frame.winfo_children():
            widget.destroy()
        self._show_welcome()

    def _quick_prompt(self, prompt: str):
        """Insert a quick prompt into input"""
        self._input.delete("1.0", "end")
        self._input.insert("1.0", prompt)
        self._input.configure(text_color=COLORS["text_primary"])

    def _on_enter(self, event):
        """Handle Enter key"""
        if event.state & 0x1:  # Shift held
            return None
        self._send_message()
        return "break"

    def _on_category_change(self, value: str):
        self._selected_category = value

    def _set_placeholder(self):
        self._placeholder_text = "Ask CyberMind anything... (Enter to send, Shift+Enter for new line)"
        self._input.insert("1.0", self._placeholder_text)
        self._input.configure(text_color=COLORS["text_muted"])

        def on_focus_in(e):
            content = self._input.get("1.0", "end").strip()
            if content == self._placeholder_text:
                self._input.delete("1.0", "end")
                self._input.configure(text_color=COLORS["text_primary"])

        def on_focus_out(e):
            content = self._input.get("1.0", "end").strip()
            if not content:
                self._input.insert("1.0", self._placeholder_text)
                self._input.configure(text_color=COLORS["text_muted"])

        self._input.bind("<FocusIn>", on_focus_in)
        self._input.bind("<FocusOut>", on_focus_out)
