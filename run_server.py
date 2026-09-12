"""Launcher script for the TriadCouncil 3D FastAPI Backend Server."""

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
        reload=True,
    )
