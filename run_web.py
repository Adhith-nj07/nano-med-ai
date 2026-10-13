"""
NanoMedAI Full-Stack Web Application Launcher
Starts the FastAPI application and opens the interactive dashboard in your browser.
"""

import sys
import os
import time
import threading
import webbrowser
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def find_port(preferred=8000):
    import socket
    for p in [preferred, 8008, 8050, 8080]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            continue
    return 8008

HOST = "127.0.0.1"
PORT = find_port(8000)
URL = f"http://{HOST}:{PORT}"

def open_browser():
    time.sleep(1.2)
    print(f"\n[+] Opening NanoMedAI Web Dashboard: {URL}")
    webbrowser.open(URL)

if __name__ == "__main__":
    print("=" * 65)
    print("  NanoMedAI — Full-Stack ML & Biophysical Simulation Web Platform")
    print(f"  Server URL: {URL}")
    print("  Models: Stability (Zeta mV), Cytotoxicity, Korsmeyer-Peppas ODE")
    print("=" * 65)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("src.web.server:app", host=HOST, port=PORT, reload=False, log_level="info")
