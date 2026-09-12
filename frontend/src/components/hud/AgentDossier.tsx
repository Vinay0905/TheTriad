import React, { useState } from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import {
  X,
  Send,
  Minimize2,
  Maximize2,
  Gavel,
  MessageSquare,
} from 'lucide-react';

export const AgentDossier: React.FC = () => {
  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);
  const isRightPanelOpen = useOfficeStore((state) => state.isRightPanelOpen);
  const isRightPanelMinimized = useOfficeStore((state) => state.isRightPanelMinimized);
  const setRightPanelMinimized = useOfficeStore((state) => state.setRightPanelMinimized);
  const toggleRightPanel = useOfficeStore((state) => state.toggleRightPanel);
  const openGate = useOfficeStore((state) => state.openGate);

  const agent = useOfficeStore((state) =>
    selectedAgentId ? state.agents[selectedAgentId] : null
  );

  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<{ sender: 'user' | 'agent'; text: string }[]>([
    {
      sender: 'agent',
      text: 'Ring buffer lock-free validation passed with 1.84M ops/sec on Tokio cluster.',
    },
  ]);

  if (!isRightPanelOpen || !agent) return null;

  // Minimized state: Sleek floating badge docked at bottom-right
  if (isRightPanelMinimized) {
    return (
      <div className="absolute right-4 bottom-14 z-30 bg-surface-container-lowest/95 border border-surface-variant/40 p-2.5 rounded-xl shadow-2xl flex items-center gap-3 backdrop-blur-xl animate-in fade-in">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center font-headline font-bold text-xs"
          style={{
            backgroundColor: `${agent.color}25`,
            borderColor: agent.color,
            color: agent.color,
          }}
        >
          {agent.name.charAt(0)}
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-headline text-xs font-bold text-on-surface">{agent.name}</span>
            <span className="font-mono text-[9px] text-primary">{agent.nodeId}</span>
          </div>
          <span className="text-[10px] font-mono text-on-surface-variant truncate max-w-[140px]">
            {agent.speed || '78.4 tok/s'} · {agent.cost || '$3.42'}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setRightPanelMinimized(false)}
            className="p-1 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors"
            title="Maximize Dossier"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            onClick={toggleRightPanel}
            className="p-1 text-on-surface-variant hover:text-red-400 rounded hover:bg-surface-container transition-colors"
            title="Close Panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userText = chatInput.trim();
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setChatInput('');

    setTimeout(() => {
      let reply = '';
      if (agent.id === 'manager') {
        reply = `Sprint burn target is < 150k tok/hr. Partitioning active subgraphs with RFC lock.`;
      } else if (agent.id === 'researcher') {
        reply = `Validated lock-free formal proof for crossbeam ring buffer against Linux kernel docs.`;
      } else if (agent.id === 'developer') {
        reply = `Cargo test --package triad-storage passes all unit tests without mutex lock contention.`;
      } else {
        reply = `Fuzz engine 100k gRPC payloads: 0 memory leaks, 0 data races detected.`;
      }
      setMessages((prev) => [...prev, { sender: 'agent', text: reply }]);
    }, 450);
  };

  return (
    <aside className="w-80 bg-surface-container-lowest/95 backdrop-blur-xl border-l border-surface-variant/30 flex flex-col justify-between shrink-0 z-20 transition-all duration-300 shadow-2xl">
      {/* Dossier Header */}
      <div className="p-3.5 border-b border-surface-variant/30 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center font-headline font-bold text-xs shadow-md shrink-0"
            style={{
              backgroundColor: agent.color,
              color: '#0a0e16',
            }}
          >
            {agent.name.charAt(0)}
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-headline text-xs font-bold text-on-surface">
                {agent.name}
              </span>
              <span
                className="px-1.5 py-0.2 rounded font-mono text-[9px] font-bold"
                style={{
                  backgroundColor: `${agent.color}25`,
                  color: agent.color,
                }}
              >
                {agent.nodeId}
              </span>
            </div>
            <span
              className="font-mono text-[9.5px] uppercase tracking-wide truncate max-w-[160px]"
              style={{ color: agent.color }}
            >
              {agent.role}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setRightPanelMinimized(true)}
            className="p-1 rounded bg-surface-container hover:bg-surface-bright text-on-surface-variant hover:text-on-surface transition-colors"
            title="Minimize to Floating Pill"
          >
            <Minimize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={toggleRightPanel}
            className="p-1 rounded bg-surface-container hover:bg-surface-bright text-on-surface-variant hover:text-on-surface transition-colors"
            title="Close Dossier"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Telemetry Vitals Grid (2x2 from Stitch) */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <div className="p-2 rounded bg-surface-container border border-surface-variant/30">
            <span className="text-[9px] text-on-surface-variant uppercase">Model Engine</span>
            <div className="font-bold text-on-surface mt-0.5 truncate">{agent.model}</div>
          </div>
          <div className="p-2 rounded bg-surface-container border border-surface-variant/30">
            <span className="text-[9px] text-on-surface-variant uppercase">Context Budget</span>
            <div className="font-bold text-secondary mt-0.5 truncate">
              {agent.contextBudget || '142,890 / 200k'}
            </div>
          </div>
          <div className="p-2 rounded bg-surface-container border border-surface-variant/30">
            <span className="text-[9px] text-on-surface-variant uppercase">Current Cost</span>
            <div className="font-bold text-on-surface mt-0.5 truncate">
              {agent.cost || '$3.42'}
            </div>
          </div>
          <div className="p-2 rounded bg-surface-container border border-surface-variant/30">
            <span className="text-[9px] text-on-surface-variant uppercase">Inference Speed</span>
            <div className="font-bold text-primary mt-0.5 truncate">
              {agent.speed || '78.4 tok/s'}
            </div>
          </div>
        </div>

        {/* Active Directive Card */}
        <div className="p-2.5 rounded-lg bg-surface-container/70 border border-surface-variant/40 flex flex-col gap-1">
          <span className="font-mono text-[10px] text-primary uppercase font-bold">
            Active Directive:
          </span>
          <p className="font-mono text-[10.5px] text-on-surface-variant leading-relaxed">
            "{agent.directive || 'Zero-copy concurrency rules. Prioritize lock-free ring buffer algorithms.'}"
          </p>
        </div>

        {/* Live Node Interrogation Console */}
        <div className="flex-1 flex flex-col gap-1.5 min-h-[140px]">
          <span className="font-mono text-[10px] text-on-surface-variant uppercase font-semibold flex items-center gap-1">
            <MessageSquare className="w-3 h-3 text-primary" /> Interrogate Node State:
          </span>
          <div className="flex-1 overflow-y-auto p-2.5 rounded bg-surface-container-lowest border border-surface-variant/40 flex flex-col gap-2 font-mono text-[10.5px] max-h-40">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`p-1.5 rounded ${
                  m.sender === 'user'
                    ? 'ml-auto bg-primary/20 text-primary border border-primary/30 max-w-[85%]'
                    : 'bg-surface-container text-on-surface border border-surface-variant/30'
                }`}
              >
                <span className="font-bold text-[9px] uppercase tracking-wider block mb-0.5" style={{ color: m.sender === 'agent' ? agent.color : '#4cd7f6' }}>
                  {m.sender === 'user' ? 'Lead Architect' : agent.name}:
                </span>
                {m.text}
              </div>
            ))}
          </div>

          <form onSubmit={handleSendMessage} className="flex gap-1.5 mt-1">
            <input
              type="text"
              placeholder={`Steer or query ${agent.name}...`}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              className="flex-1 bg-surface-container px-2.5 py-1.5 rounded text-xs font-mono text-on-surface border border-surface-variant/40 focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <button
              type="submit"
              className="px-3 py-1.5 rounded bg-primary text-on-primary font-headline font-bold text-xs flex items-center justify-center hover:bg-primary-container transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>

      {/* Review Gate Action Button */}
      <div className="p-3 border-t border-surface-variant/30">
        <button
          onClick={() =>
            openGate(
              'manual-gate',
              'Active Objective Review & Approval',
              '// Validated in-memory cache architecture\npub struct LruCache { shards: Arc<crossbeam::ShardedRing<K, V>> }',
              'Audited by Maya: 48 passed unit tests, 0 race conditions, 0 memory leaks.',
              'Acceptance criteria confirmed by team. Ready for human verification.'
            )
          }
          className="w-full py-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 rounded-lg font-headline text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-[0_0_12px_rgba(76,215,246,0.15)]"
        >
          <Gavel className="w-4 h-4" />
          <span>Open Human Steering Gate</span>
        </button>
      </div>
    </aside>
  );
};

