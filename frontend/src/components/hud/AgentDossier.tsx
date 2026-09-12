import React, { useState } from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import { X, Send, Cpu, MapPin, Activity, Terminal } from 'lucide-react';

export const AgentDossier: React.FC = () => {
  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);
  const setSelectedAgent = useOfficeStore((state) => state.setSelectedAgent);
  const agent = useOfficeStore((state) =>
    selectedAgentId ? state.agents[selectedAgentId] : null
  );

  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<
    { sender: 'user' | 'agent'; text: string }[]
  >([]);

  if (!agent) return null;

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userText = chatInput.trim();
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setChatInput('');

    // Simulated contextual response from agent's perspective
    setTimeout(() => {
      let reply = '';
      if (agent.id === 'manager') {
        reply = `I am currently coordinating the team's RFC and will ensure acceptance criteria are locked before Alex writes code.`;
      } else if (agent.id === 'researcher') {
        reply = `I am auditing documentation via Google Search to ensure we don't use deprecated APIs.`;
      } else if (agent.id === 'developer') {
        reply = `I'm adhering strictly to the TDD test harness. Concurrency and clean standard-library interfaces are my top priority.`;
      } else {
        reply = `I'm scrutinizing edge cases with GLM-4.7-Flash. No code touches the sandbox until I verify boundary stability.`;
      }
      setMessages((prev) => [...prev, { sender: 'agent', text: reply }]);
    }, 600);
  };

  return (
    <div className="w-84 bg-surface/95 backdrop-blur border-l border-border h-full flex flex-col z-20 shadow-2xl animate-in slide-in-from-right duration-200">
      {/* Dossier Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-2xl p-2 rounded-lg bg-background border border-border">
            {agent.avatarIcon}
          </div>
          <div>
            <h2 className="font-bold text-white text-base leading-tight">
              {agent.name}
            </h2>
            <p className="text-xs text-gray-400">{agent.role}</p>
          </div>
        </div>
        <button
          onClick={() => setSelectedAgent(null)}
          className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-surfaceHover transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Meta Specs */}
      <div className="p-4 space-y-3 border-b border-border text-xs">
        <div className="flex items-center gap-2 text-gray-300">
          <Cpu className="w-4 h-4 text-blue-400 shrink-0" />
          <span className="text-gray-400">Model:</span>
          <span className="font-mono text-white truncate">{agent.model}</span>
        </div>

        <div className="flex items-center gap-2 text-gray-300">
          <MapPin className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="text-gray-400">Location:</span>
          <span className="font-mono text-white">{agent.currentWaypoint}</span>
        </div>

        <div className="flex items-center gap-2 text-gray-300">
          <Activity className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="text-gray-400">Activity:</span>
          <span className="font-semibold text-white uppercase tracking-wider">
            {agent.animation}
          </span>
        </div>
      </div>

      {/* Live Status Card */}
      <div className="p-4 border-b border-border">
        <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
          Current Live Task
        </div>
        <div className="bg-background/80 border border-border p-3 rounded-lg text-xs font-mono text-gray-200 leading-relaxed">
          {agent.statusBadge || 'Idle, awaiting instructions.'}
        </div>
      </div>

      {/* Direct Inter-Employee Chat */}
      <div className="flex-1 flex flex-col p-4 min-h-0">
        <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
          Direct Employee Query
        </div>

        <div className="flex-1 overflow-y-auto space-y-2 mb-3 pr-1 text-xs">
          {messages.length === 0 ? (
            <p className="text-gray-500 italic text-center mt-6">
              Ask {agent.name} directly about their active architecture or design choices.
            </p>
          ) : (
            messages.map((m, idx) => (
              <div
                key={idx}
                className={`p-2.5 rounded-lg max-w-[85%] ${
                  m.sender === 'user'
                    ? 'ml-auto bg-blue-600/90 text-white'
                    : 'bg-surfaceHover border border-border text-gray-200'
                }`}
              >
                {m.text}
              </div>
            ))
          )}
        </div>

        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            placeholder={`Ask ${agent.name}...`}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-500 text-white p-2 rounded-lg transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
