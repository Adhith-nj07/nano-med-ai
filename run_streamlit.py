"""
NanoMedAI Streamlit Launcher
"""
import sys
import os
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port", "8501"]
    print("=" * 65)
    print("  NanoMedAI Streamlit Suite starting at: http://localhost:8501")
    print("=" * 65)
    subprocess.run(cmd, cwd=PROJECT_ROOT)
