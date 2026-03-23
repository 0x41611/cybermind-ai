"""
CyberMind AI - Configuration Manager
100% Local AI - No API keys needed
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Central configuration for CyberMind"""

    # Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    CHROMA_DB_PATH = str(DATA_DIR / "chroma_db")
    WRITEUPS_DIR = DATA_DIR / "writeups"
    SESSIONS_DIR = DATA_DIR / "sessions"

    # ── Ollama (Local AI) Settings ─────────────────────────────────
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    AI_MODEL: str = os.getenv("AI_MODEL", "llama3.1:8b")
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "4096"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))

    # Recommended models for CTF (ordered by quality/speed)
    RECOMMENDED_MODELS = [
        "llama3.1:8b",        # Best overall for CTF - 4.7GB
        "qwen2.5-coder:7b",   # Best for code tasks - 4.7GB
        "mistral:7b",         # Fast & smart - 4.1GB
        "deepseek-r1:8b",     # Strong reasoning - 4.9GB
        "llama3.2:3b",        # Lightweight - 2.0GB
    ]

    # ── RAG Settings ───────────────────────────────────────────────
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    MAX_CONTEXT_DOCS: int = int(os.getenv("MAX_CONTEXT_DOCS", "5"))
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # ── Learning Settings ──────────────────────────────────────────
    AUTO_TRAIN: bool = os.getenv("AUTO_TRAIN", "true").lower() == "true"
    TRAIN_INTERVAL_HOURS: int = int(os.getenv("TRAIN_INTERVAL_HOURS", "24"))
    MAX_WRITEUPS_PER_SCRAPE: int = int(os.getenv("MAX_WRITEUPS_PER_SCRAPE", "50"))

    # ── Tool Settings ──────────────────────────────────────────────
    TOOL_TIMEOUT: int = int(os.getenv("TOOL_TIMEOUT", "30"))
    ALLOW_NETWORK_TOOLS: bool = os.getenv("ALLOW_NETWORK_TOOLS", "true").lower() == "true"
    ALLOW_CODE_EXECUTION: bool = os.getenv("ALLOW_CODE_EXECUTION", "true").lower() == "true"

    # ── GUI Settings ───────────────────────────────────────────────
    WINDOW_WIDTH: int = int(os.getenv("WINDOW_WIDTH", "1400"))
    WINDOW_HEIGHT: int = int(os.getenv("WINDOW_HEIGHT", "900"))
    APP_NAME: str = "CyberMind AI"
    APP_VERSION: str = "1.0.0"

    # ── CTF Categories ─────────────────────────────────────────────
    CTF_CATEGORIES = [
        "Web", "Crypto", "Pwn", "Forensics",
        "OSINT", "Steganography", "Misc", "Reverse"
    ]

    # ── Writeup Sources ────────────────────────────────────────────
    WRITEUP_SOURCES = [
        "https://ctftime.org/writeups",
        "https://github.com/search?q=ctf+writeup&type=repositories",
    ]

    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        for d in [cls.DATA_DIR, cls.WRITEUPS_DIR, cls.SESSIONS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Ollama is reachable"""
        try:
            import requests
            resp = requests.get(f"{cls.OLLAMA_HOST}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_available_models(cls) -> list:
        """Get list of installed Ollama models"""
        try:
            import requests
            resp = requests.get(f"{cls.OLLAMA_HOST}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return [m["name"] for m in models]
        except Exception:
            pass
        return []

    @classmethod
    def save_model(cls, model_name: str):
        """Save selected model to .env"""
        env_path = cls.BASE_DIR / ".env"
        lines = []
        key_found = False

        if env_path.exists():
            with open(env_path) as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith("AI_MODEL="):
                    lines[i] = f"AI_MODEL={model_name}\n"
                    key_found = True
                    break

        if not key_found:
            lines.append(f"AI_MODEL={model_name}\n")

        with open(env_path, "w") as f:
            f.writelines(lines)

        cls.AI_MODEL = model_name


# Global config instance
config = Config()
config.ensure_dirs()
