#!/usr/bin/env bash
# CyberMind AI Launcher
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "Starting Ollama..."
    ollama serve &>/dev/null &
    sleep 3
fi

# Launch CyberMind
python3 main.py
