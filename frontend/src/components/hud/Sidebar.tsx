import React from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import { Users, Code, Search, ShieldCheck, Briefcase } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const agents = useOfficeStore((state) => state.agents);
  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);
  const setSelectedAgent = useOfficeStore((state) => state.setSelectedAgent);

  const getDepartmentIcon = (dept: string) => {
    switch (dept) {
      case 'Management':
        return <Briefcase className="w-4 h-4 text-amber-400" />;
      case 'Research':
        return <Search className="w-4 h-4 text-blue-400" />;
      case 'Engineering':
        return <Code className="w-4 h-4 text-emerald-400" />;
      case 'Quality Assurance':
        return <ShieldCheck className="w-4 h-4 text-purple-400" />;
      default:
        return <Users className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <aside className="w-72 bg-surface/90 backdrop-blur border-r border-border flex flex-col h-full z-10 select-none">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse" />
          <h1 className="font-bold text-sm tracking-wide text-white">TRIADCOUNCIL 3D</h1>
        </div>
        <span className="text-[10px] font-mono bg-surfaceHover px-2 py-0.5 rounded text-gray-400 border border-border">
          4 AGENTS
        </span>
      </div>

      {/* Roster */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        <div className="text-[11px] font-semibold tracking-wider text-gray-400 uppercase px-1">
          Active Engineering Roster
        </div>

        <div className="space-y-2">
          {Object.values(agents).map((agent) => {
            const isSelected = selectedAgentId === agent.id;
            return (
              <button
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id)}
                className={`w-full text-left p-3 rounded-lg border transition-all flex items-start gap-3 ${
                  isSelected
                    ? 'bg-surfaceHover border-blue-500/50 shadow-md ring-1 ring-blue-500/20'
                    : 'bg-surface/50 border-border hover:bg-surfaceHover/70 hover:border-gray-600'
                }`}
              >
                <div className="text-xl p-1.5 rounded-md bg-background border border-border flex items-center justify-center">
                  {agent.avatarIcon}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-white truncate">
                      {agent.name}
                    </span>
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: agent.color }}
                    />
                  </div>

                  <div className="flex items-center gap-1 mt-0.5 text-xs text-gray-400">
                    {getDepartmentIcon(agent.department)}
                    <span className="truncate">{agent.role}</span>
                  </div>

                  <div className="mt-2 text-[11px] font-mono text-gray-300 bg-background/60 px-2 py-1 rounded border border-border/50 truncate">
                    {agent.statusBadge || 'Idle'}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* System Status Footer */}
      <div className="p-3 border-t border-border bg-background/40 text-xs text-gray-400 font-mono">
        <div className="flex justify-between items-center">
          <span>Engine</span>
          <span className="text-emerald-400">LangGraph 0.2+</span>
        </div>
        <div className="flex justify-between items-center mt-1">
          <span>Simulation</span>
          <span className="text-blue-400">R3F / Three.js</span>
        </div>
      </div>
    </aside>
  );
};
