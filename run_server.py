"""Launcher script for the TriadCouncil 3D FastAPI Backend Server."""

import sys
from pathlib import Path

# Add src/ to sys.path so ai_team package is resolvable
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import uvicorn
from ai_team.config import get_config

if __name__ == "__main__":
    config = get_config()
    print("\n" + "=" * 78)
    print("      🚀 STARTING TRIADCOUNCIL 3D VIRTUAL OFFICE BACKEND SERVER")
    print(f"      📡 Host: http://{config.server_host}:{config.server_port}")
    print(f"      ⚡ WebSocket: ws://{config.server_host}:{config.server_port}/ws/office")
    print("=" * 78 + "\n")
    uvicorn.run(
        "ai_team.server:app",
        host=config.server_host,
        port=config.server_port,
        app_dir=str(src_path),
        reload=True,
        reload_dirs=[str(src_path)],
    )
