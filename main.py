"""
CyberMind AI - Entry Point
AI-powered CTF and Penetration Testing Assistant
"""
import sys
import os
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

# Suppress SSL warnings for CTF environments
import warnings
warnings.filterwarnings("ignore")

# Suppress sentence-transformers tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Suppress TF/torch warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


def main():
    try:
        from gui.app import CyberMindApp
        app = CyberMindApp()
        app.run()
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("\nPlease install requirements:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to start CyberMind: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
