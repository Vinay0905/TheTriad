import React from 'react';
import { useOfficeSocket } from './hooks/useOfficeSocket';
import { TopBar } from './components/hud/TopBar';
import { Sidebar } from './components/hud/Sidebar';
import { AgentDossier } from './components/hud/AgentDossier';
import { TerminalDock } from './components/hud/TerminalDock';
import { WhiteboardGateModal } from './components/hud/WhiteboardGateModal';
import { OfficeCanvas } from './components/office/OfficeCanvas';

export const App: React.FC = () => {
  // Activate persistent WebSocket connection
  useOfficeSocket();

  return (
    <div className="w-screen h-screen flex flex-col bg-background overflow-hidden">
      {/* Top Objective Bar */}
      <TopBar />

      {/* Main Simulation Viewport */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Team Sidebar */}
        <Sidebar />

        {/* Center 3D Virtual Office Canvas */}
        <main className="flex-1 h-full relative">
          <OfficeCanvas />
        </main>

        {/* Right Slide-out Agent Dossier */}
        <AgentDossier />
      </div>

      {/* Bottom Terminal Dock */}
      <TerminalDock />

      {/* Interactive Human Steering Gate (Whiteboard Modal) */}
      <WhiteboardGateModal />
    </div>
  );
};
