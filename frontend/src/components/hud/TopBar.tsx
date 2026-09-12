import React, { useState } from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import { Play, Loader2, Sparkles, Download } from 'lucide-react';

export const TopBar: React.FC = () => {
  const [inputTask, setInputTask] = useState('');
  const isRunning = useOfficeStore((state) => state.isRunning);
  const setRunning = useOfficeStore((state) => state.setRunning);
  const setObjective = useOfficeStore((state) => state.setObjective);
  const officeClock = useOfficeStore((state) => state.officeClock);
  const officeClosed = officeClock.phase === 'OFF_HOURS';

  const handleStartTask = async (e: React.FormEvent) => {
    e.preventDefault();
    const task = inputTask.trim();
    if (!task || isRunning || officeClosed) return;

    setRunning(true);
    setObjective(task);

    try {
      const res = await fetch('/api/tasks/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Unable to start the task.');
      setRunning(true, data.thread_id);
    } catch (err) {
      console.error('Failed to start task:', err);
      setRunning(false);
    }
  };

  return (
    <header className="h-14 bg-surface-container-lowest/95 backdrop-blur-md border-b border-border px-4 flex items-center justify-between z-20 select-none">
      {/* Search / Objective Bar */}
      <form onSubmit={handleStartTask} className="flex-1 max-w-2xl flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Assign engineering objective (e.g., 'Build a Thread-Safe In-Memory LRU Cache with TTL')..."
            value={inputTask}
            onChange={(e) => setInputTask(e.target.value)}
            disabled={isRunning || officeClosed}
            className="w-full bg-surface-container-low border border-border rounded-lg pl-9 pr-4 py-2 text-xs text-on-surface placeholder-gray-500 focus:outline-none focus:border-primary disabled:opacity-60 transition-colors"
          />
          <Sparkles className="w-4 h-4 text-primary absolute left-3 top-2.5" />
        </div>

        <button
          type="submit"
          disabled={isRunning || officeClosed || !inputTask.trim()}
          className="bg-primary hover:bg-primary-container disabled:opacity-50 text-black px-4 py-2 rounded-lg text-xs font-headline font-bold flex items-center gap-1.5 transition-all shadow-md shadow-primary/20"
        >
          {officeClosed ? (
            <span>Office closed · returns 09:00</span>
          ) : isRunning ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Team Collaborating...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Deploy AI Team</span>
            </>
          )}
        </button>
      </form>

      {/* Telemetry Pills & Dynamic Panel Toggles */}
      <div className="flex items-center gap-2">
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container/80 border border-border text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-mono text-[11px] text-on-surface-variant">NODES:</span>
          <span className="font-mono text-[11px] font-bold text-emerald-400">4/4 LIVE</span>
          <span className="w-px h-3 bg-border mx-1" />
          <span className="font-mono text-[11px] text-on-surface-variant">SANDBOX:</span>
          <span className="font-mono text-[11px] font-semibold text-primary">ARMED</span>
          <span className="w-px h-3 bg-border mx-1" />
          <span className="font-mono text-[11px] text-on-surface-variant">GATE:</span>
          <span className="font-mono text-[11px] font-semibold text-secondary">ENFORCED</span>
        </div>

        {/* Quick Download Latest Run ZIP */}
        <a
          href="/api/runs/download/latest"
          download
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-semibold transition-all hover:scale-105 active:scale-95"
          title="Download latest generated project files (.ZIP)"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export .ZIP</span>
        </a>

        {/* Dynamic Panel Toggles */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => {
              const state = useOfficeStore.getState();
              if (!state.isLeftPanelOpen) {
                state.toggleLeftPanel();
                state.setLeftPanelMinimized(false);
              } else if (state.isLeftPanelMinimized) {
                state.setLeftPanelMinimized(false);
              } else {
                state.setLeftPanelMinimized(true);
              }
            }}
            className={`px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold transition-all ${
              useOfficeStore((state) => state.isLeftPanelOpen && !state.isLeftPanelMinimized)
                ? 'bg-primary/20 text-primary border-primary/50 shadow-[0_0_10px_rgba(76,215,246,0.2)]'
                : 'bg-surface-container text-on-surface-variant border-surface-variant/40 hover:text-on-surface'
            }`}
            title="Toggle / Expand Left Engineering Roster"
          >
            Roster {useOfficeStore((state) => state.isLeftPanelOpen && !state.isLeftPanelMinimized ? '◀' : '▶')}
          </button>
          <button
            onClick={() => {
              const state = useOfficeStore.getState();
              if (!state.isRightPanelOpen) {
                state.toggleRightPanel();
                state.setRightPanelMinimized(false);
              } else if (state.isRightPanelMinimized) {
                state.setRightPanelMinimized(false);
              } else {
                state.setRightPanelMinimized(true);
              }
            }}
            className={`px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold transition-all ${
              useOfficeStore((state) => state.isRightPanelOpen && !state.isRightPanelMinimized)
                ? 'bg-primary/20 text-primary border-primary/50 shadow-[0_0_10px_rgba(76,215,246,0.2)]'
                : 'bg-surface-container text-on-surface-variant border-surface-variant/40 hover:text-on-surface'
            }`}
            title="Toggle / Expand Right Telemetry Dossier"
          >
            Dossier {useOfficeStore((state) => state.isRightPanelOpen && !state.isRightPanelMinimized ? '▶' : '◀')}
          </button>
        </div>
      </div>
    </header>
  );
};
