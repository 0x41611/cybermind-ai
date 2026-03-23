"""
CyberMind AI - Helper Utilities
"""
import re
import os
import json
import hashlib
import base64
import binascii
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable size"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def truncate_text(text: str, max_len: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length"""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as filename"""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name[:200]


def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
    """Extract code blocks from markdown text. Returns list of (language, code)"""
    pattern = r'```(\w*)\n?(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return [(lang or "text", code.strip()) for lang, code in matches]


def detect_encoding(data: bytes) -> str:
    """Try to detect encoding of bytes data"""
    # Try UTF-8
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    # Try latin-1
    try:
        data.decode("latin-1")
        return "latin-1"
    except UnicodeDecodeError:
        pass
    return "binary"


def is_base64(text: str) -> bool:
    """Check if string looks like base64"""
    try:
        text = text.strip()
        if len(text) % 4 != 0:
            return False
        base64.b64decode(text)
        return bool(re.match(r'^[A-Za-z0-9+/=]+$', text))
    except Exception:
        return False


def is_hex(text: str) -> bool:
    """Check if string looks like hex"""
    text = text.strip().replace(" ", "").replace("0x", "")
    if len(text) % 2 != 0:
        return False
    try:
        binascii.unhexlify(text)
        return True
    except Exception:
        return False


def detect_cipher(ciphertext: str) -> List[str]:
    """Try to detect what cipher was used"""
    hints = []
    text = ciphertext.strip()

    if is_base64(text):
        hints.append("Base64 encoded")
    if is_hex(text.replace(" ", "")):
        hints.append("Hex encoded")
    if re.match(r'^[A-Z\s]+$', text) and len(text) > 10:
        hints.append("Possible Caesar/Vigenere cipher (uppercase only)")
    if re.match(r'^[01\s]+$', text):
        hints.append("Binary encoded")
    if "==" in text or text.endswith("="):
        hints.append("Likely base64 (padding detected)")
    if re.match(r'^[a-zA-Z0-9+/]{20,}={0,2}$', text):
        hints.append("Possibly base64")

    return hints or ["Unknown encoding"]


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime for display"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def load_json(path: str | Path) -> Optional[Dict]:
    """Safely load JSON file"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_json(path: str | Path, data: Any, indent: int = 2):
    """Safely save JSON file"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)


def hash_text(text: str) -> str:
    """Get MD5 hash of text (for deduplication)"""
    return hashlib.md5(text.encode()).hexdigest()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind(".", start, end)
            last_newline = text.rfind("\n", start, end)
            break_point = max(last_period, last_newline)
            if break_point > start + chunk_size // 2:
                end = break_point + 1

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]


def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 chars)"""
    return len(text) // 4
