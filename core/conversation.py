"""
CyberMind AI - Conversation Manager
Handles session storage, history management, and export
"""
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import config
from utils.logger import get_logger

logger = get_logger("conversation")


class Message:
    """A single conversation message"""

    def __init__(self, role: str, content: str, metadata: Optional[Dict] = None):
        self.id = str(uuid.uuid4())[:8]
        self.role = role  # "user" | "assistant" | "system"
        self.content = content
        self.timestamp = datetime.now()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        msg = cls(data["role"], data["content"], data.get("metadata", {}))
        msg.id = data.get("id", msg.id)
        msg.timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        return msg

    def to_api_format(self) -> Dict:
        """Format for Claude API"""
        return {"role": self.role, "content": self.content}


class Session:
    """A chat session"""

    def __init__(self, session_id: Optional[str] = None, name: Optional[str] = None):
        self.id = session_id or str(uuid.uuid4())[:12]
        self.name = name or f"Session {datetime.now().strftime('%m/%d %H:%M')}"
        self.messages: List[Message] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict[str, Any] = {}

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> Message:
        msg = Message(role, content, metadata)
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg

    def get_api_messages(self, max_history: int = 20) -> List[Dict]:
        """Get messages in Claude API format (last N messages)"""
        msgs = [m for m in self.messages if m.role in ("user", "assistant")]
        return [m.to_api_format() for m in msgs[-max_history:]]

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        s = cls(data["id"], data.get("name"))
        s.messages = [Message.from_dict(m) for m in data.get("messages", [])]
        s.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        s.updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        s.metadata = data.get("metadata", {})
        return s


class ConversationManager:
    """Manages multiple chat sessions"""

    SYSTEM_PROMPT = """You are CyberMind, an elite AI assistant specialized in cybersecurity, penetration testing, and CTF (Capture The Flag) challenges. You have deep expertise in:

**Core Areas:**
- Web Application Security (SQL Injection, XSS, CSRF, SSRF, LFI/RFI, XXE, etc.)
- Cryptography (Classical ciphers, AES, RSA, ECC, hash functions, side-channel attacks)
- Binary Exploitation (Buffer overflows, ROP chains, format strings, heap exploitation)
- Digital Forensics (Memory analysis, disk forensics, network packet analysis, steganography)
- Network Security (Port scanning, service enumeration, MITM attacks, protocol analysis)
- OSINT (Open source intelligence gathering techniques)
- Reverse Engineering (Assembly analysis, decompilation, anti-debug techniques)

**Your Approach:**
1. Analyze the challenge/question systematically
2. Search your knowledge base for similar writeups and techniques
3. Provide step-by-step solutions with working code when needed
4. Explain the vulnerability and how to exploit it
5. Always use Python for scripts when possible
6. Think like an attacker but act defensively

**Tool Usage:**
When you need to run code or analyze data, use the available tools. Always explain what you're doing and why.

Remember: This is for authorized security testing, CTF competitions, and educational purposes only."""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.current_session_id: Optional[str] = None
        self._load_sessions()

    def new_session(self, name: Optional[str] = None) -> Session:
        """Create a new session"""
        session = Session(name=name)
        self.sessions[session.id] = session
        self.current_session_id = session.id
        self._save_session(session)
        logger.info(f"Created new session: {session.id}")
        return session

    def get_current(self) -> Session:
        """Get or create the current session"""
        if self.current_session_id and self.current_session_id in self.sessions:
            return self.sessions[self.current_session_id]
        return self.new_session()

    def switch_session(self, session_id: str) -> Optional[Session]:
        """Switch to an existing session"""
        if session_id in self.sessions:
            self.current_session_id = session_id
            return self.sessions[session_id]
        return None

    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            # Delete file
            path = config.SESSIONS_DIR / f"{session_id}.json"
            if path.exists():
                path.unlink()
            if self.current_session_id == session_id:
                self.current_session_id = None

    def get_all_sessions(self) -> List[Session]:
        """Get all sessions sorted by last update"""
        return sorted(
            self.sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True
        )

    def export_session(self, session_id: str, path: str):
        """Export session to JSON file"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def _save_session(self, session: Session):
        """Save session to disk"""
        path = config.SESSIONS_DIR / f"{session.id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False, default=str)

    def _load_sessions(self):
        """Load sessions from disk"""
        for path in config.SESSIONS_DIR.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                session = Session.from_dict(data)
                self.sessions[session.id] = session
            except Exception as e:
                logger.warning(f"Failed to load session {path}: {e}")

        if self.sessions:
            # Set most recent as current
            latest = max(self.sessions.values(), key=lambda s: s.updated_at)
            self.current_session_id = latest.id

    def save_current(self):
        """Save current session to disk"""
        session = self.get_current()
        self._save_session(session)
