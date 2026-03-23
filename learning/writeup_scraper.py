"""
CyberMind AI - Writeup Scraper
Scrapes CTF writeups from multiple sources for self-learning
"""
import re
import time
import json
import requests
from typing import List, Dict, Optional, Callable
from bs4 import BeautifulSoup
from config import config
from utils.logger import get_logger
from utils.helpers import sanitize_filename, hash_text

logger = get_logger("scraper")

# Suppress SSL warnings for CTF environments
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WriteupScraper:
    """
    Scrapes CTF writeups from:
    - CTFtime.org writeups
    - GitHub CTF repositories
    - HackTricks (pentesting bible)
    - public CTF writeup blogs
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (CyberMind-AI CTF-Learning-Bot)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(self, on_progress: Optional[Callable] = None):
        self.on_progress = on_progress
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def scrape_all(self, max_total: int = 50) -> List[Dict]:
        """Scrape writeups from all sources"""
        all_writeups = []
        per_source = max_total // 3

        sources = [
            ("CTFtime Writeups", self._scrape_ctftime, per_source),
            ("GitHub CTF Repos", self._scrape_github, per_source),
            ("HackTricks Techniques", self._scrape_hacktricks, per_source),
        ]

        for source_name, scraper_fn, limit in sources:
            try:
                self._progress(f"Scraping {source_name}...")
                writeups = scraper_fn(limit)
                all_writeups.extend(writeups)
                self._progress(f"✅ Got {len(writeups)} writeups from {source_name}")
                time.sleep(1)  # Be respectful
            except Exception as e:
                logger.warning(f"Failed to scrape {source_name}: {e}")
                self._progress(f"⚠️ Skipped {source_name}: {e}")

        return all_writeups

    def _scrape_ctftime(self, limit: int = 20) -> List[Dict]:
        """Scrape CTFtime writeups list"""
        writeups = []
        try:
            # CTFtime writeups API
            url = "https://ctftime.org/api/v1/results/"
            # Their writeups are listed on the main page
            resp = self.session.get(
                "https://ctftime.org/writeups",
                timeout=15,
                verify=False
            )
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            writeup_links = []

            # Find writeup links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/writeup/" in href:
                    full_url = f"https://ctftime.org{href}" if href.startswith("/") else href
                    if full_url not in writeup_links:
                        writeup_links.append(full_url)
                if len(writeup_links) >= limit:
                    break

            # Fetch each writeup
            for url in writeup_links[:limit]:
                try:
                    writeup = self._fetch_ctftime_writeup(url)
                    if writeup:
                        writeups.append(writeup)
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"Failed to fetch writeup {url}: {e}")

        except Exception as e:
            logger.warning(f"CTFtime scraping error: {e}")

        return writeups

    def _fetch_ctftime_writeup(self, url: str) -> Optional[Dict]:
        """Fetch a single CTFtime writeup"""
        try:
            resp = self.session.get(url, timeout=10, verify=False)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "lxml")

            title = soup.find("h2")
            title_text = title.get_text(strip=True) if title else "CTF Writeup"

            # Get task description
            content_div = soup.find("div", class_="writeup-content") or \
                          soup.find("article") or \
                          soup.find("div", class_="content")

            if not content_div:
                return None

            content = content_div.get_text(separator="\n", strip=True)
            if len(content) < 100:
                return None

            # Detect category from title or content
            category = self._detect_category(title_text + " " + content[:500])

            return {
                "title": title_text,
                "content": content[:5000],
                "category": category,
                "source": url,
                "tags": self._extract_tags(content),
            }
        except Exception:
            return None

    def _scrape_github(self, limit: int = 20) -> List[Dict]:
        """Scrape GitHub CTF writeup repositories"""
        writeups = []

        # Search GitHub for CTF writeup repos
        search_queries = [
            "CTF+writeup+web+security",
            "CTF+writeup+cryptography",
            "CTF+writeup+pwn+exploitation",
            "CTF+writeup+forensics",
        ]

        for query in search_queries:
            if len(writeups) >= limit:
                break
            try:
                url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=5"
                resp = self.session.get(url, timeout=10)
                if resp.status_code != 200:
                    continue

                repos = resp.json().get("items", [])
                for repo in repos[:3]:
                    if len(writeups) >= limit:
                        break
                    # Get README
                    readme_url = f"https://raw.githubusercontent.com/{repo['full_name']}/main/README.md"
                    try:
                        readme_resp = self.session.get(readme_url, timeout=10)
                        if readme_resp.status_code == 200 and len(readme_resp.text) > 200:
                            content = readme_resp.text
                            category = self._detect_category(repo["description"] or "" + content[:500])
                            writeups.append({
                                "title": repo["name"],
                                "content": content[:5000],
                                "category": category,
                                "source": repo["html_url"],
                                "tags": ["github", "writeup"],
                            })
                    except Exception:
                        pass
                    time.sleep(0.3)

            except Exception as e:
                logger.debug(f"GitHub search error: {e}")

        return writeups

    def _scrape_hacktricks(self, limit: int = 20) -> List[Dict]:
        """Scrape HackTricks for pentesting techniques"""
        writeups = []

        # Key HackTricks pages (pentesting bible)
        pages = [
            ("https://book.hacktricks.xyz/pentesting-web/sql-injection", "SQL Injection", "Web"),
            ("https://book.hacktricks.xyz/pentesting-web/xss-cross-site-scripting", "XSS", "Web"),
            ("https://book.hacktricks.xyz/pentesting-web/file-inclusion", "LFI/RFI", "Web"),
            ("https://book.hacktricks.xyz/cryptography/hash-cracking", "Hash Cracking", "Crypto"),
            ("https://book.hacktricks.xyz/reversing/basic-python-keylogger", "Python Reversing", "Reverse"),
            ("https://book.hacktricks.xyz/forensics/basic-forensic-methodology", "Forensics Basics", "Forensics"),
            ("https://book.hacktricks.xyz/pentesting-web/ssrf-server-side-request-forgery", "SSRF", "Web"),
            ("https://book.hacktricks.xyz/pentesting-web/command-injection", "Command Injection", "Web"),
            ("https://book.hacktricks.xyz/pentesting-web/deserialization", "Deserialization", "Web"),
            ("https://book.hacktricks.xyz/crypto-and-stego/stego-tricks", "Steganography", "Steganography"),
        ]

        for url, title, category in pages[:limit]:
            try:
                resp = self.session.get(url, timeout=15, verify=False)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                # Remove nav/sidebar
                for nav in soup.find_all(["nav", "aside", "header", "footer"]):
                    nav.decompose()

                main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
                if not main_content:
                    continue

                content = main_content.get_text(separator="\n", strip=True)
                if len(content) > 200:
                    writeups.append({
                        "title": f"HackTricks: {title}",
                        "content": content[:6000],
                        "category": category,
                        "source": url,
                        "tags": ["hacktricks", "technique", title.lower().replace(" ", "-")],
                    })

                time.sleep(0.5)

            except Exception as e:
                logger.debug(f"Failed to fetch HackTricks page {url}: {e}")

        return writeups

    def scrape_custom_url(self, url: str) -> Optional[Dict]:
        """Scrape a custom URL for writeup content"""
        try:
            resp = self.session.get(url, timeout=15, verify=False)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml")

            # Remove navigation elements
            for tag in soup.find_all(["nav", "aside", "header", "footer", "script", "style"]):
                tag.decompose()

            # Try to find main content
            main = (soup.find("main") or
                    soup.find("article") or
                    soup.find("div", class_=re.compile(r"(content|post|writeup|article)", re.I)) or
                    soup.find("body"))

            if not main:
                return None

            title_tag = soup.find(["h1", "h2", "title"])
            title = title_tag.get_text(strip=True) if title_tag else url

            content = main.get_text(separator="\n", strip=True)
            category = self._detect_category(title + " " + content[:500])

            return {
                "title": title,
                "content": content[:8000],
                "category": category,
                "source": url,
                "tags": self._extract_tags(content),
            }

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None

    def _detect_category(self, text: str) -> str:
        """Detect CTF category from text"""
        text_lower = text.lower()
        category_keywords = {
            "Web": ["sqli", "sql injection", "xss", "csrf", "ssrf", "lfi", "rfi", "xxe", "web", "http", "php", "javascript", "cookie", "session", "injection"],
            "Crypto": ["crypto", "cipher", "rsa", "aes", "md5", "sha", "hash", "encrypt", "decrypt", "cryptography", "base64", "rot"],
            "Pwn": ["pwn", "buffer overflow", "rop", "shellcode", "exploit", "heap", "stack", "binary", "libc", "got", "plt"],
            "Forensics": ["forensic", "pcap", "wireshark", "memory", "disk", "carv", "volatility", "artifact", "timeline"],
            "OSINT": ["osint", "open source", "reconnaissance", "social media", "linkedin", "twitter", "geolocation"],
            "Steganography": ["stego", "steganography", "hidden", "lsb", "image", "audio", "wav", "png", "jpg"],
            "Reverse": ["reverse", "decompile", "assembly", "disassemble", "ida", "ghidra", "obfuscat", "malware"],
            "Misc": ["misc", "random", "trivia", "programming"],
        }

        scores = {cat: 0 for cat in category_keywords}
        for cat, keywords in category_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[cat] += 1

        if max(scores.values()) == 0:
            return "Misc"
        return max(scores, key=scores.get)

    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from writeup content"""
        text_lower = text.lower()
        tags = []
        tag_keywords = [
            "sql injection", "xss", "csrf", "ssrf", "lfi", "rfi", "xxe",
            "rsa", "aes", "base64", "rot13", "vigenere", "caesar",
            "buffer overflow", "rop chain", "shellcode", "heap overflow",
            "forensics", "steganography", "osint", "reverse engineering",
            "python", "php", "javascript", "c", "linux", "windows",
            "web", "crypto", "pwn", "rev", "misc"
        ]
        for tag in tag_keywords:
            if tag in text_lower:
                tags.append(tag)
        return list(set(tags))[:10]

    def _progress(self, message: str):
        if self.on_progress:
            self.on_progress(message)
        logger.info(message)
