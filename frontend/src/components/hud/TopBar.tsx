import React, { useState } from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import { Play, Loader2, Sparkles } from 'lucide-react';

export const TopBar: React.FC = () => {
  const [inputTask, setInputTask] = useState('');
  const isRunning = useOfficeStore((state) => state.isRunning);
  const setRunning = useOfficeStore((state) => state.setRunning);
  const setObjective = useOfficeStore((state) => state.setObjective);

  const handleStartTask = async (e: React.FormEvent) => {
    e.preventDefault();
    const task = inputTask.trim();
    if (!task || isRunning) return;

    setRunning(true);
    setObjective(task);

    try {
      const res = await fetch('/api/tasks/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task }),
      });
      const data = await res.json();
      setRunning(true, data.thread_id);
    } catch (err) {
      console.error('Failed to start task:', err);
      setRunning(false);
    }
  };

  return (
    <header className="h-14 bg-surface/90 backdrop-blur border-b border-border px-4 flex items-center justify-between z-20 select-none">
      {/* Search / Objective Bar */}
      <form onSubmit={handleStartTask} className="flex-1 max-w-2xl flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Assign engineering objective (e.g., 'Build a Thread-Safe In-Memory LRU Cache with TTL')..."
            value={inputTask}
            onChange={(e) => setInputTask(e.target.value)}
            disabled={isRunning}
            className="w-full bg-background border border-border rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-60"
          />
          <Sparkles className="w-4 h-4 text-amber-400 absolute left-3 top-2.5" />
        </div>

        <button
          type="submit"
          disabled={isRunning || !inputTask.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md"
        >
          {isRunning ? (
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

      {/* Status Badges */}
      <div className="flex items-center gap-3 text-xs font-mono">
        <div className="flex items-center gap-1.5 text-gray-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>Local Sandbox Ready</span>
        </div>
      </div>
    </header>
  );
};
