"""
Single command launcher for TriadCouncil 3D:
Starts the FastAPI Backend Server and displays connection information.
"""

import subprocess
import sys
import time

def main():
    print("=" * 78)
    print("           🏢 TRIADCOUNCIL 3D: VIRTUAL AI OFFICE LAUNCHER")
    print("=" * 78)
    print("\n[1/2] Starting Python FastAPI Backend Server on http://localhost:8000...")
    
    server_process = subprocess.Popen(
        [sys.executable, "run_server.py"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    
    time.sleep(1.5)
    print("\n[2/2] Backend running! To start the 3D Frontend:")
    print("      cd frontend && npm run dev")
    print("      Open http://localhost:5173 in your browser!\n")
    print("=" * 78)

    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\nStopping TriadCouncil 3D Server...")
        server_process.terminate()

if __name__ == "__main__":
    main()
