import React from 'react';
import { useOfficeSocket } from './hooks/useOfficeSocket';
import { TopBar } from './components/hud/TopBar';
import { Sidebar } from './components/hud/Sidebar';
import { AgentDossier } from './components/hud/AgentDossier';
import { TerminalDock } from './components/hud/TerminalDock';
import { WhiteboardGateModal } from './components/hud/WhiteboardGateModal';
import { DeliveryReportModal } from './components/hud/DeliveryReportModal';
import { OfficeCanvas } from './components/office/OfficeCanvas';

export const App: React.FC = () => {
  // Activate persistent WebSocket connection
  useOfficeSocket();

  return (
    <div className="w-screen h-screen flex flex-col bg-background overflow-hidden">
      {/* Top Objective Bar */}
      <TopBar />

      {/* Main Simulation Viewport with Floating Overlaid HUD Panels */}
      <div className="flex-1 relative overflow-hidden">
        {/* Full-bleed Center 3D Virtual Office Canvas */}
        <main className="w-full h-full absolute inset-0">
          <OfficeCanvas />
        </main>

        {/* Left Floating Team Sidebar / Navigation Rail */}
        <div className="absolute left-0 top-0 bottom-0 z-30 pointer-events-none flex">
          <div className="pointer-events-auto h-full">
            <Sidebar />
          </div>
        </div>

        {/* Right Floating Slide-out Agent Dossier */}
        <div className="absolute right-0 top-0 bottom-0 z-30 pointer-events-none flex">
          <div className="pointer-events-auto h-full">
            <AgentDossier />
          </div>
        </div>
      </div>

      {/* Bottom Terminal Dock */}
      <TerminalDock />

      {/* Interactive Human Steering Gate (Whiteboard Modal) */}
      <WhiteboardGateModal />

      {/* Final Delivery & Verified Artifacts Modal */}
      <DeliveryReportModal />
    </div>
  );
};
