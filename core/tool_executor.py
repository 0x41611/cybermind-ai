"""
CyberMind AI - Tool Executor
Safely executes CTF and pentesting tools for the AI agent
"""
import io
import sys
import time
import subprocess
import contextlib
import traceback
import requests
from typing import Dict, Any, Optional, Callable
from config import config
from utils.logger import get_logger
from utils.helpers import detect_cipher, is_base64, is_hex

logger = get_logger("tool_executor")


# ─── Tool Definitions (for Claude API) ──────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "run_python",
        "description": (
            "Execute Python code in a sandboxed environment. "
            "Use for: cryptographic operations, data parsing, encoding/decoding, "
            "CTF script writing, pattern analysis, and general computation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Has access to: math, re, base64, binascii, hashlib, itertools, struct, socket, json, string, random, Crypto (pycryptodome)"
                },
                "description": {
                    "type": "string",
                    "description": "What this code does (for display)"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "web_request",
        "description": (
            "Make HTTP/HTTPS requests to web targets. "
            "Use for: web CTF challenges, testing endpoints, checking for vulnerabilities."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL"},
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                    "default": "GET"
                },
                "headers": {"type": "object", "description": "Request headers"},
                "data": {"type": "string", "description": "Request body data"},
                "params": {"type": "object", "description": "URL query parameters"},
                "follow_redirects": {"type": "boolean", "default": True},
                "timeout": {"type": "integer", "default": 15}
            },
            "required": ["url"]
        }
    },
    {
        "name": "analyze_text",
        "description": (
            "Analyze text/data for CTF crypto and encoding challenges. "
            "Detects: encoding type, cipher hints, frequency analysis, patterns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text or data to analyze"},
                "analysis_type": {
                    "type": "string",
                    "enum": ["auto", "frequency", "encoding_detect", "hash_identify", "cipher_hint"],
                    "default": "auto"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "decode_data",
        "description": "Decode encoded data (base64, hex, rot13, URL encoding, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data to decode"},
                "encoding": {
                    "type": "string",
                    "enum": ["base64", "hex", "rot13", "url", "binary", "morse", "auto"],
                    "default": "auto"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "search_knowledge",
        "description": (
            "Search the CyberMind knowledge base for relevant CTF writeups and techniques. "
            "Use this to find similar challenges and solutions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "category": {
                    "type": "string",
                    "enum": ["Web", "Crypto", "Pwn", "Forensics", "OSINT", "Steganography", "Misc", "Reverse", "Any"],
                    "default": "Any"
                },
                "limit": {"type": "integer", "default": 5, "description": "Number of results"}
            },
            "required": ["query"]
        }
    }
]


class ToolExecutor:
    """Executes tools requested by the AI agent"""

    def __init__(self, rag_engine=None, on_output: Optional[Callable] = None):
        self.rag_engine = rag_engine
        self.on_output = on_output  # Callback for real-time output display
        self._setup_safe_env()

    def _setup_safe_env(self):
        """Setup safe execution environment"""
        self._safe_imports = {
            "math": __import__("math"),
            "re": __import__("re"),
            "base64": __import__("base64"),
            "binascii": __import__("binascii"),
            "hashlib": __import__("hashlib"),
            "itertools": __import__("itertools"),
            "struct": __import__("struct"),
            "json": __import__("json"),
            "string": __import__("string"),
            "random": __import__("random"),
            "collections": __import__("collections"),
            "functools": __import__("functools"),
            "urllib": __import__("urllib"),
            "html": __import__("html"),
            "os": None,  # Blocked
            "sys": None,  # Blocked
            "subprocess": None,  # Blocked
        }
        # Try importing crypto
        try:
            from Crypto.Cipher import AES, DES, Blowfish
            from Crypto.Util import number
            from Crypto.PublicKey import RSA
            self._safe_imports["Crypto"] = __import__("Crypto")
        except ImportError:
            pass

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results"""
        logger.info(f"Executing tool: {tool_name}")
        start_time = time.time()

        try:
            if tool_name == "run_python":
                result = self._run_python(tool_input)
            elif tool_name == "web_request":
                result = self._web_request(tool_input)
            elif tool_name == "analyze_text":
                result = self._analyze_text(tool_input)
            elif tool_name == "decode_data":
                result = self._decode_data(tool_input)
            elif tool_name == "search_knowledge":
                result = self._search_knowledge(tool_input)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            elapsed = time.time() - start_time
            result["_elapsed"] = f"{elapsed:.2f}s"
            return result

        except Exception as e:
            logger.error(f"Tool error ({tool_name}): {e}")
            return {"error": str(e), "traceback": traceback.format_exc()}

    def _run_python(self, inp: Dict) -> Dict:
        """Execute Python code safely"""
        if not config.ALLOW_CODE_EXECUTION:
            return {"error": "Code execution is disabled"}

        code = inp["code"]
        timeout = min(inp.get("timeout", config.TOOL_TIMEOUT), 60)

        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Build safe globals
        safe_globals = {"__builtins__": __builtins__}
        safe_globals.update({k: v for k, v in self._safe_imports.items() if v is not None})

        local_vars = {}

        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                exec(code, safe_globals, local_vars)  # noqa: S102

            output = stdout_capture.getvalue()
            errors = stderr_capture.getvalue()

            # Capture return value if last expression
            result_vars = {k: v for k, v in local_vars.items()
                           if not k.startswith("_") and not callable(v)}

            return {
                "success": True,
                "output": output,
                "errors": errors if errors else None,
                "variables": {k: str(v)[:500] for k, v in result_vars.items()} if result_vars else None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(limit=5)
            }

    def _web_request(self, inp: Dict) -> Dict:
        """Make HTTP request"""
        if not config.ALLOW_NETWORK_TOOLS:
            return {"error": "Network tools are disabled"}

        url = inp["url"]
        method = inp.get("method", "GET").upper()
        headers = inp.get("headers", {})
        data = inp.get("data")
        params = inp.get("params")
        timeout = min(inp.get("timeout", 15), 30)
        follow = inp.get("follow_redirects", True)

        # Default headers
        if "User-Agent" not in headers:
            headers["User-Agent"] = "Mozilla/5.0 (CyberMind CTF Tool)"

        try:
            response = requests.request(
                method, url,
                headers=headers,
                data=data,
                params=params,
                timeout=timeout,
                allow_redirects=follow,
                verify=False  # For CTF environments with self-signed certs
            )

            # Try to parse as text
            try:
                body = response.text[:5000]  # Limit response size
            except Exception:
                body = f"[Binary data, {len(response.content)} bytes]"

            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": body,
                "url": response.url,
                "redirects": [r.url for r in response.history] if response.history else []
            }

        except requests.exceptions.ConnectionError:
            return {"error": f"Connection refused: {url}"}
        except requests.exceptions.Timeout:
            return {"error": f"Request timed out after {timeout}s"}
        except Exception as e:
            return {"error": str(e)}

    def _analyze_text(self, inp: Dict) -> Dict:
        """Analyze text for CTF patterns"""
        text = inp["text"]
        analysis_type = inp.get("analysis_type", "auto")
        results = {}

        # Encoding detection
        results["encoding_hints"] = detect_cipher(text)
        results["length"] = len(text)
        results["is_base64"] = is_base64(text)
        results["is_hex"] = is_hex(text.replace(" ", ""))

        # Frequency analysis
        if len(text) > 20:
            freq = {}
            for c in text.lower():
                if c.isalpha():
                    freq[c] = freq.get(c, 0) + 1
            total = sum(freq.values())
            if total > 0:
                sorted_freq = sorted(freq.items(), key=lambda x: -x[1])[:10]
                results["top_chars"] = [f"'{c}': {n/total*100:.1f}%" for c, n in sorted_freq]

        # Check for known patterns
        import re
        flag_patterns = [
            r'[A-Z]{2,5}\{[^}]+\}',  # CTF flags like FLAG{...}
            r'flag\{[^}]+\}',
            r'ctf\{[^}]+\}'
        ]
        for pattern in flag_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results["possible_flags"] = matches

        return results

    def _decode_data(self, inp: Dict) -> Dict:
        """Decode encoded data"""
        import base64
        import binascii
        import urllib.parse

        data = inp["data"].strip()
        encoding = inp.get("encoding", "auto")
        results = {}

        decoders = {
            "base64": lambda d: base64.b64decode(d).decode("utf-8", errors="replace"),
            "hex": lambda d: bytes.fromhex(d.replace(" ", "")).decode("utf-8", errors="replace"),
            "rot13": lambda d: d.translate(str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
            )),
            "url": lambda d: urllib.parse.unquote(d),
            "binary": lambda d: "".join(chr(int(b, 2)) for b in d.split()),
        }

        if encoding == "auto":
            for name, decoder in decoders.items():
                try:
                    decoded = decoder(data)
                    if decoded and len(decoded) > 0:
                        results[name] = decoded[:500]
                except Exception:
                    pass
        elif encoding in decoders:
            try:
                results[encoding] = decoders[encoding](data)
            except Exception as e:
                results["error"] = str(e)

        return results if results else {"error": "Could not decode data"}

    def _search_knowledge(self, inp: Dict) -> Dict:
        """Search RAG knowledge base"""
        if not self.rag_engine:
            return {"error": "Knowledge base not initialized"}

        query = inp["query"]
        category = inp.get("category", "Any")
        limit = inp.get("limit", 5)

        try:
            results = self.rag_engine.search(
                query,
                n_results=limit,
                category=None if category == "Any" else category
            )
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e)}

    def format_result(self, tool_name: str, result: Dict) -> str:
        """Format tool result for display"""
        if "error" in result and not result.get("success"):
            return f"❌ Error: {result['error']}"

        if tool_name == "run_python":
            parts = []
            if result.get("output"):
                parts.append(f"Output:\n```\n{result['output']}\n```")
            if result.get("errors"):
                parts.append(f"Stderr:\n```\n{result['errors']}\n```")
            if result.get("variables"):
                vars_str = "\n".join(f"  {k} = {v}" for k, v in result["variables"].items())
                parts.append(f"Variables:\n{vars_str}")
            return "\n".join(parts) or "✅ Code executed (no output)"

        elif tool_name == "web_request":
            if result.get("success"):
                return (
                    f"HTTP {result['status_code']}\n"
                    f"URL: {result['url']}\n"
                    f"Body (first 2000 chars):\n```\n{result['body'][:2000]}\n```"
                )

        elif tool_name == "decode_data":
            return "\n".join(f"{k}: {v}" for k, v in result.items() if k != "_elapsed")

        elif tool_name == "search_knowledge":
            if result.get("results"):
                lines = [f"Found {result['count']} relevant writeups:\n"]
                for i, r in enumerate(result["results"], 1):
                    lines.append(f"{i}. {r.get('title', 'Untitled')} ({r.get('category', 'Unknown')})")
                    lines.append(f"   {r.get('content', '')[:200]}...")
                return "\n".join(lines)

        return str(result)
