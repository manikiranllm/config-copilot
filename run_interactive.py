#!/usr/bin/env python
"""
Quick start script for interactive Config-Copilot
"""

import subprocess
import sys

if __name__ == "__main__":
    print("🚀 Starting Config-Copilot Interactive...")
    print("🌐 The interface will open at: http://localhost:7860")
    print("=" * 60)
    
    try:
        subprocess.run([sys.executable, "app_interactive.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
