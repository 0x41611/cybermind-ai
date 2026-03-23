"""
CyberMind AI - Writeup Processor
Processes and enriches writeup data before storing
"""
import re
from typing import Dict, List, Optional
from utils.helpers import chunk_text, extract_code_blocks
from utils.logger import get_logger

logger = get_logger("processor")


class WriteupProcessor:
    """Processes raw writeup content for better RAG retrieval"""

    def process(self, writeup: Dict) -> Dict:
        """Process and enrich a writeup"""
        content = writeup.get("content", "")

        # Clean content
        content = self._clean_text(content)

        # Extract code blocks
        code_blocks = extract_code_blocks(content)
        if code_blocks:
            writeup["code_examples"] = [
                {"language": lang, "code": code[:500]}
                for lang, code in code_blocks[:5]
            ]

        # Extract flags (for validation)
        flags = self._extract_flags(content)
        if flags:
            writeup["flags"] = flags

        # Extract tools mentioned
        tools = self._extract_tools(content)
        if tools:
            writeup["tools_used"] = tools

        # Add search-friendly summary
        writeup["summary"] = self._create_summary(content)
        writeup["content"] = content

        return writeup

    def process_batch(self, writeups: List[Dict]) -> List[Dict]:
        """Process multiple writeups"""
        return [self.process(w) for w in writeups]

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        # Remove HTML entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&quot;", '"').replace("&#39;", "'")
        # Remove URLs (keep domain only for context)
        text = re.sub(r'https?://\S+', '[URL]', text)
        return text.strip()

    def _extract_flags(self, text: str) -> List[str]:
        """Extract CTF flags from text"""
        patterns = [
            r'[A-Z]{2,6}\{[^}]+\}',
            r'flag\{[^}]+\}',
            r'CTF\{[^}]+\}',
        ]
        flags = []
        for p in patterns:
            flags.extend(re.findall(p, text, re.IGNORECASE))
        return list(set(flags))

    def _extract_tools(self, text: str) -> List[str]:
        """Extract security tools mentioned"""
        tools_list = [
            "nmap", "gobuster", "dirb", "dirsearch", "sqlmap", "burpsuite",
            "metasploit", "wireshark", "tcpdump", "hashcat", "john",
            "binwalk", "strings", "file", "xxd", "hexdump", "stegsolve",
            "steghide", "exiftool", "volatility", "autopsy", "ghidra",
            "ida", "gdb", "pwndbg", "peda", "radare2", "objdump",
            "python", "pwntools", "z3", "angr", "openssl", "nc", "netcat",
        ]
        text_lower = text.lower()
        found = [t for t in tools_list if t in text_lower]
        return found

    def _create_summary(self, content: str, max_len: int = 300) -> str:
        """Create a brief summary of the writeup"""
        # Take first non-empty paragraph
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]
        if paragraphs:
            summary = paragraphs[0][:max_len]
            if len(paragraphs[0]) > max_len:
                summary += "..."
            return summary
        return content[:max_len]
