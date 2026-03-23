#!/bin/bash
# CyberMind AI Setup Script

echo ""
echo "  ⚡ CyberMind AI - Setup"
echo "  ========================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt

echo ""
echo "🔧 Setting up config..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
    echo "  ⚠️  Please add your Anthropic API key to .env"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "  To run CyberMind:"
echo "  1. Add your API key: edit .env → ANTHROPIC_API_KEY=sk-ant-..."
echo "  2. Run: python main.py"
echo ""
