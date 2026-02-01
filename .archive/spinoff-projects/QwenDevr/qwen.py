#!/usr/bin/env python3
"""
QwenDevr Launcher Script

Quick launcher for QwenDevr CLI with simplified name.
Usage: python qwen.py [args]
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch QwenDevr CLI with all arguments passed through."""
    # Get the directory of this script
    qwen_dir = Path(__file__).parent
    cli_script = qwen_dir / "qwen_devr_cli.py"
    
    # Pass all arguments to the main CLI
    cmd = [sys.executable, str(cli_script)] + sys.argv[1:]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Happy coding with QwenDevr!")
        sys.exit(0)

if __name__ == "__main__":
    main()