import React from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import {
  Coffee,
  PenTool,
  Users,
  Monitor,
  Minimize2,
  ChevronLeft,
  ChevronRight,
  Crosshair,
  Footprints,
} from 'lucide-react';


export const Sidebar: React.FC = () => {
  const agents = useOfficeStore((state) => state.agents);
  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);
  const setSelectedAgent = useOfficeStore((state) => state.setSelectedAgent);
  const setAgentMovement = useOfficeStore((state) => state.setAgentMovement);
  const setAgentStatus = useOfficeStore((state) => state.setAgentStatus);

  const isLeftPanelOpen = useOfficeStore((state) => state.isLeftPanelOpen);
  const isLeftPanelMinimized = useOfficeStore((state) => state.isLeftPanelMinimized);
  const setLeftPanelMinimized = useOfficeStore((state) => state.setLeftPanelMinimized);
  const toggleLeftPanel = useOfficeStore((state) => state.toggleLeftPanel);

  const ambientCirculation = useOfficeStore((state) => state.ambientCirculation);
  const toggleAmbientCirculation = useOfficeStore((state) => state.toggleAmbientCirculation);
  const isRunning = useOfficeStore((state) => state.isRunning);


  if (!isLeftPanelOpen) return null;

  // Minimized micro-rail state (w-16)
  if (isLeftPanelMinimized) {
    return (
      <aside className="w-16 bg-surface-container-lowest/95 backdrop-blur-xl border-r border-surface-variant/40 flex flex-col items-center py-4 h-full z-20 select-none transition-all duration-300 shadow-2xl">
        <button
          onClick={() => setLeftPanelMinimized(false)}
          className="w-10 h-10 rounded-lg bg-surface-container hover:bg-surface-bright text-on-surface flex items-center justify-center mb-4 border border-surface-variant/40 transition-all hover:scale-105"
          title="Expand Engineering Roster"
        >
          <ChevronRight className="w-5 h-5 text-primary" />
        </button>

        <div className="flex flex-col gap-3 flex-1 items-center">
          {Object.values(agents).map((agent) => {
            const isSelected = selectedAgentId === agent.id;
            return (
              <button
                key={agent.id}
                onClick={() => {
                  setSelectedAgent(agent.id);
                  setLeftPanelMinimized(false);
                }}
                className={`w-10 h-10 rounded-xl border flex items-center justify-center font-headline font-extrabold text-sm relative transition-all ${
                  isSelected
                    ? 'ring-2 shadow-lg scale-110'
                    : 'bg-surface-container hover:bg-surface-bright opacity-85 hover:opacity-100'
                }`}
                style={{
                  borderColor: isSelected ? agent.color : 'rgba(255,255,255,0.15)',
                  color: agent.color,
                  backgroundColor: isSelected ? `${agent.color}25` : '#181c24',
                  boxShadow: isSelected ? `0 0 14px ${agent.color}40` : undefined,
                }}
                title={`Click to focus ${agent.name} (${agent.role})`}
              >
                {agent.name.charAt(0)}
                <span
                  className="w-2.5 h-2.5 rounded-full absolute -top-1 -right-1 border-2 border-surface-container-lowest"
                  style={{ backgroundColor: agent.color }}
                />
              </button>
            );
          })}
        </div>

        {/* Between-run office-life indicator */}
        <button
          onClick={toggleAmbientCirculation}
          className={`p-2 rounded-lg text-xs font-mono transition-colors ${
            ambientCirculation ? 'text-emerald-400 bg-emerald-500/20' : 'text-gray-500 bg-surface-container'
          }`}
          title={`Between-run office life: ${ambientCirculation ? 'ON' : 'OFF'}`}
        >
          <Footprints className="w-4 h-4" />
        </button>
      </aside>
    );
  }

  // Full Expanded Left Panel (w-72)
  const currentAgent = selectedAgentId ? agents[selectedAgentId] : null;

  const handleCommandWalk = (destination: string, activityName: string) => {
    if (!selectedAgentId || isRunning) return;
    setAgentStatus(selectedAgentId, 'Walk', activityName);
    setAgentMovement(selectedAgentId, destination);
  };

  return (
    <aside className="w-72 bg-surface-container-lowest/95 backdrop-blur-xl border-r border-surface-variant/30 flex flex-col h-full z-20 select-none transition-all duration-300">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-surface-variant/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]" />
          <span className="font-headline text-xs font-extrabold uppercase tracking-wider text-on-surface">
            Engineering Roster
          </span>
          <span className="font-mono text-[9px] text-emerald-400 bg-emerald-950/60 px-1.5 py-0.2 rounded border border-emerald-500/30">
            4 ACTIVE
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setLeftPanelMinimized(true)}
            className="p-1 rounded bg-surface-container hover:bg-surface-bright text-on-surface-variant hover:text-on-surface transition-colors"
            title="Minimize to Micro-Rail"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={toggleLeftPanel}
            className="p-1 rounded bg-surface-container hover:bg-surface-bright text-on-surface-variant hover:text-on-surface transition-colors"
            title="Hide Panel"
          >
            <Minimize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-4">
        {/* Agent Selection Cards */}
        <div className="flex flex-col gap-1.5">
          {Object.values(agents).map((agent) => {
            const isSelected = selectedAgentId === agent.id;
            return (
              <button
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id)}
                className={`w-full text-left p-2.5 rounded-lg border transition-all flex items-center justify-between group relative ${
                  isSelected
                    ? 'bg-surface-container-high ring-1 shadow-lg'
                    : 'bg-surface-container/60 hover:bg-surface-container-high/80 border-surface-variant/30'
                }`}
                style={{
                  borderColor: isSelected ? `${agent.color}80` : undefined,
                  boxShadow: isSelected ? `0 0 12px ${agent.color}25` : undefined,
                }}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div
                    className="w-7 h-7 rounded-md border flex items-center justify-center font-bold text-xs shrink-0"
                    style={{
                      borderColor: `${agent.color}60`,
                      backgroundColor: `${agent.color}20`,
                      color: agent.color,
                    }}
                  >
                    {agent.name.charAt(0)}
                  </div>

                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-headline text-xs font-semibold text-on-surface group-hover:text-primary transition-colors truncate">
                        {agent.name}
                      </span>
                      <span className="font-mono text-[9px] text-on-surface-variant">
                        {agent.nodeId}
                      </span>
                    </div>
                    <span className="font-mono text-[9px] text-on-surface-variant truncate">
                      {agent.role}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  <Crosshair
                    className={`w-3.5 h-3.5 transition-transform group-hover:scale-125 ${
                      isSelected ? 'text-primary' : 'text-gray-500'
                    }`}
                  />
                </div>
              </button>
            );
          })}
        </div>

        {/* Optional visual office direction, separate from real workflow events */}
        <div className="border-t border-surface-variant/30 pt-3 flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] text-on-surface-variant uppercase font-semibold">
              Office Direction for {currentAgent ? currentAgent.name : 'Active Agent'}:
            </span>
          </div>

          <div className="grid grid-cols-2 gap-1.5 font-mono text-[10px]">
            <button
              disabled={isRunning}
              onClick={() => handleCommandWalk('pantry', 'Grabbing an espresso in Pantry...')}
              className="p-2 rounded bg-surface-container hover:bg-surface-bright disabled:opacity-40 disabled:cursor-not-allowed text-secondary text-left flex items-center gap-1.5 border border-secondary/20 transition-all hover:scale-[1.02]"
            >
              <Coffee className="w-3.5 h-3.5" />
              <span>Pantry</span>
            </button>
            <button
              disabled={isRunning}
              onClick={() => handleCommandWalk('whiteboard', 'Reviewing Whiteboard blueprints...')}
              className="p-2 rounded bg-surface-container hover:bg-surface-bright disabled:opacity-40 disabled:cursor-not-allowed text-tertiary text-left flex items-center gap-1.5 border border-tertiary/20 transition-all hover:scale-[1.02]"
            >
              <PenTool className="w-3.5 h-3.5" />
              <span>Whiteboard</span>
            </button>
            <button
              disabled={isRunning}
              onClick={() => {
                if (currentAgent) {
                  const meetingSeats: Record<string, string> = {
                    manager: 'meeting_david',
                    researcher: 'meeting_elena',
                    developer: 'meeting_alex',
                    qa: 'meeting_maya',
                  };
                  const seat = meetingSeats[currentAgent.id] || 'meeting';
                  handleCommandWalk(seat, 'Heading to Round Meeting Table...');
                }
              }}
              className="p-2 rounded bg-surface-container hover:bg-surface-bright disabled:opacity-40 disabled:cursor-not-allowed text-emerald-400 text-left flex items-center gap-1.5 border border-emerald-400/20 transition-all hover:scale-[1.02]"
            >
              <Users className="w-3.5 h-3.5" />
              <span>Meeting</span>
            </button>
            <button
              disabled={isRunning}
              onClick={() => {
                if (currentAgent) {
                  handleCommandWalk(currentAgent.currentWaypoint.startsWith('desk_') ? currentAgent.currentWaypoint : `desk_${currentAgent.id === 'manager' ? 'david' : currentAgent.id === 'researcher' ? 'elena' : currentAgent.id === 'developer' ? 'alex' : 'maya'}`, 'Returning to workstation...');
                }
              }}
              className="p-2 rounded bg-surface-container hover:bg-surface-bright disabled:opacity-40 disabled:cursor-not-allowed text-primary text-left flex items-center gap-1.5 border border-primary/20 transition-all hover:scale-[1.02]"
            >
              <Monitor className="w-3.5 h-3.5" />
              <span>Back to Desk</span>
            </button>
          </div>
        </div>

        {/* Between-run office-life toggle */}
        <div className="border-t border-surface-variant/30 pt-3 flex items-center justify-between px-1">
          <div className="flex items-center gap-1.5 font-mono text-[10px] text-on-surface-variant">
            <Footprints className="w-3.5 h-3.5 text-primary" />
            <span>Between-run office life:</span>
          </div>
          <button
            onClick={toggleAmbientCirculation}
            className={`px-2.5 py-0.5 rounded-full text-[9.5px] font-mono font-bold uppercase transition-all ${
              ambientCirculation
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                : 'bg-surface-container text-gray-500 border border-surface-variant/40'
            }`}
          >
            {ambientCirculation ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>
    </aside>
  );
};
