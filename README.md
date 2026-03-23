# CyberMind AI

An AI-powered CTF and penetration testing assistant that runs **100% locally** — no cloud, no API keys, no internet required after setup.

---

## Features

- **Autonomous Pentest Agent** — give it a target IP, it scans, enumerates, finds vulnerabilities, and writes a full report
- **AI Chat** — ask anything about CTF challenges, exploits, and techniques
- **RAG Knowledge Base** — pre-loaded with HTB writeups; learns more over time
- **CTF Tools** — web, crypto, forensics, steganography, PWN, OSINT tools in one place
- **Auth Support** — login to protected web challenges before scanning
- **Verbose Mode** — see every request, payload, and response in real-time
- **100% Offline** — powered by Ollama (local LLM)

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
- macOS / Linux (Windows via WSL)

Optional system tools for better scanning results:
`nmap` `gobuster` `nikto` `sqlmap` `ffuf` `hydra`

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/cybermind-ai.git
cd cybermind-ai

# Run the installer (sets up venv, installs deps, seeds knowledge base)
chmod +x install.sh
./install.sh
```

Then pull an Ollama model:
```bash
ollama pull gemma3:1b       # fast, lightweight
# or
ollama pull llama3.1:8b     # smarter, needs more RAM
```

---

## Running

```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python3 main.py
```

---

## Configuration

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

Key settings:

| Variable | Default | Description |
|---|---|---|
| `AI_MODEL` | `gemma3:1b` | Ollama model to use |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `AUTO_TRAIN` | `true` | Auto-learn from new writeups |

---

## Project Structure

```
cybermind-ai/
├── main.py              # Entry point
├── config.py            # Configuration loader
├── install.sh           # One-command installer
├── run.sh               # Launch script
├── requirements.txt     # Python dependencies
│
├── core/                # AI engine
│   ├── ai_agent.py          # Ollama LLM interface
│   ├── rag_engine.py         # ChromaDB knowledge base
│   ├── autonomous_agent.py   # Auto pentest agent
│   ├── tool_executor.py      # Tool runner
│   └── conversation.py       # Chat history
│
├── tools/               # CTF & pentest tools
│   ├── web_tools.py          # SQLi, XSS, SSRF, JWT, SSTI...
│   ├── crypto_tools.py       # Encodings, ciphers, RSA, XOR...
│   ├── forensics_tools.py    # File analysis, steganography...
│   ├── network_tools.py      # Port scan, DNS, banners...
│   ├── pwn_tools.py          # Binary exploitation, ROP, pwntools...
│   └── osint_tools.py        # WHOIS, crt.sh, Google dorks...
│
├── gui/                 # CustomTkinter interface
│   ├── app.py               # Main window
│   └── screens/             # Chat, Tools, Pentest, Stats, Settings
│
├── learning/            # Self-learning system
│   ├── trainer.py            # Training orchestrator
│   └── writeup_scraper.py    # Writeup fetcher
│
├── data/
│   ├── htb_seed_data.py      # Pre-bundled HTB writeups (29 machines)
│   └── htb_writeups_seed.json
│
└── utils/               # Helpers
```

---

## Auto Pentest Agent

1. Go to **Auto Pentest** tab
2. Enter target IP
3. Optionally enable **Auth** if the target requires login
4. Enable **Verbose** to see all requests live
5. Press **START SCAN**

Phases: `Auth → Recon → Enumeration → Vuln Scan → AI Analysis → Report`

Vulnerability checks: SQLi, XSS, LFI, Command Injection, IDOR, Open Redirect, SSRF, default credentials, and more.

---

## Disclaimer

> This tool is for **authorized security testing only** — CTF competitions, lab environments, and systems you have explicit permission to test. Unauthorized use is illegal.

---

## License

MIT
