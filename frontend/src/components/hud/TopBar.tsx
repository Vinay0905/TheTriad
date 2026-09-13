import React, { useState } from 'react';
import { AlertTriangle, Clock, Loader2, Play, Sparkles } from 'lucide-react';
import { useOfficeStore } from '../../store/useOfficeStore';
import type { ProviderState } from '../../types/office';

const STATE_TONE: Record<ProviderState, string> = {
  OK: 'text-emerald-400',
  RATE_LIMITED: 'text-amber-400',
  QUOTA_EXHAUSTED: 'text-rose-400',
  AUTH_FAILED: 'text-rose-400',
  OFFLINE: 'text-gray-500',
};

export const TopBar: React.FC = () => {
  const [inputTask, setInputTask] = useState('');
  const isRunning = useOfficeStore((state) => state.isRunning);
  const officeClock = useOfficeStore((state) => state.officeClock);
  const providerHealth = useOfficeStore((state) => state.providerHealth);
  const isConnected = useOfficeStore((state) => state.isConnected);
  const lastError = useOfficeStore((state) => state.lastError);

  const officeClosed = officeClock.phase === 'OFF_HOURS';

  // Derived from PROVIDER_HEALTH, not hardcoded. Until a run has exercised a
  // role the backend reports nothing about it, so "roles" is legitimately
  // empty at startup rather than optimistically "4/4 LIVE".
  const healthyRoles = providerHealth.roles.filter((role) => role.state === 'OK').length;
  const degraded = providerHealth.roles.filter((role) => role.state !== 'OK');

  const handleStartTask = async (event: React.FormEvent) => {
    event.preventDefault();
    const task = inputTask.trim();
    if (!task || isRunning || officeClosed) return;

    const store = useOfficeStore.getState();
    store.setLastError(null);
    store.setObjective(task);
    store.setRunning(true);

    try {
      const res = await fetch('/api/tasks/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task }),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data?.detail || `Server returned ${res.status}.`);
      }

      // The token is returned once, to this tab only. It is what authorises
      // approving and downloading this run.
      store.setRunning(true, data.thread_id, data.run_token ?? null);
      store.clearTerminalLogs();
    } catch (err) {
      // Previously the spinner kept spinning forever on a failed start.
      store.setRunning(false);
      store.setLastError(err instanceof Error ? err.message : 'Could not start the run.');
    }
  };

  return (
    <header className="h-14 bg-surface-container-lowest/95 backdrop-blur-md border-b border-border px-4 flex items-center justify-between z-20 select-none">
      <form onSubmit={handleStartTask} className="flex-1 max-w-2xl flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Assign an engineering objective (e.g. 'Build a thread-safe LRU cache with TTL')..."
            value={inputTask}
            onChange={(event) => setInputTask(event.target.value)}
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
              <span>Council working...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Deploy council</span>
            </>
          )}
        </button>
      </form>

      <div className="flex items-center gap-2">
        {lastError && (
          <div
            role="alert"
            className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/40 text-rose-300 text-[11px] font-mono max-w-xs"
            title={lastError}
          >
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">{lastError}</span>
          </div>
        )}

        {/* Real telemetry. Every value here comes from the backend. */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container/80 border border-border text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-gray-500'
            }`}
          />
          <span className="font-mono text-[11px] text-on-surface-variant">LINK:</span>
          <span
            className={`font-mono text-[11px] font-bold ${
              isConnected ? 'text-emerald-400' : 'text-gray-400'
            }`}
          >
            {isConnected ? 'UP' : 'DOWN'}
          </span>

          <span className="w-px h-3 bg-border mx-1" />
          <span className="font-mono text-[11px] text-on-surface-variant">ROLES:</span>
          <span
            className="font-mono text-[11px] font-bold"
            title={
              degraded.length
                ? degraded
                    .map((role) => `${role.role}: ${role.state} (${role.model})`)
                    .join('\n')
                : 'All observed roles responding'
            }
          >
            {providerHealth.roles.length === 0 ? (
              <span className="text-gray-400">IDLE</span>
            ) : (
              <span className={degraded.length ? 'text-amber-400' : 'text-emerald-400'}>
                {healthyRoles}/{providerHealth.roles.length} OK
              </span>
            )}
          </span>

          <span className="w-px h-3 bg-border mx-1" />
          <span className="font-mono text-[11px] text-on-surface-variant">SANDBOX:</span>
          <span
            className={`font-mono text-[11px] font-semibold ${
              providerHealth.sandboxAvailable ? 'text-primary' : 'text-rose-400'
            }`}
            title={
              providerHealth.sandboxAvailable
                ? `${providerHealth.sandboxBackend} is reachable`
                : `${providerHealth.sandboxBackend} is unavailable; execution will be refused`
            }
          >
            {providerHealth.sandboxAvailable ? 'READY' : 'UNAVAILABLE'}
          </span>
        </div>

        {degraded.length > 0 && (
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px] font-mono">
            {degraded.map((role) => (
              <span key={role.role} className={STATE_TONE[role.state]}>
                {role.role.replace(/_/g, ' ')}
                {role.reset_at_display ? ` · back ${role.reset_at_display}` : ''}
              </span>
            ))}
          </div>
        )}

        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-mono font-semibold transition-all ${
            officeClosed
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-200'
          }`}
          title={`Simulated workday 09:00-17:00 in 20 real minutes. Remaining: ${Math.ceil(
            officeClock.secondsRemaining / 60,
          )}m`}
        >
          <Clock
            className={`w-3.5 h-3.5 ${officeClosed ? 'text-rose-400' : 'text-cyan-400'}`}
          />
          <span className="tabular-nums tracking-wider text-[11px] font-bold">
            {officeClock.displayTime}
          </span>
          <span className="text-[10px] opacity-75">
            {officeClosed ? 'OFF-HOURS' : `D${officeClock.dayNumber}`}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <PanelToggle side="left" />
          <PanelToggle side="right" />
        </div>
      </div>
    </header>
  );
};

const PanelToggle: React.FC<{ side: 'left' | 'right' }> = ({ side }) => {
  const isOpen = useOfficeStore((state) =>
    side === 'left' ? state.isLeftPanelOpen : state.isRightPanelOpen,
  );
  const isMinimized = useOfficeStore((state) =>
    side === 'left' ? state.isLeftPanelMinimized : state.isRightPanelMinimized,
  );

  const expanded = isOpen && !isMinimized;
  const label = side === 'left' ? 'Roster' : 'Dossier';

  const onClick = () => {
    const state = useOfficeStore.getState();
    const toggle = side === 'left' ? state.toggleLeftPanel : state.toggleRightPanel;
    const setMinimized =
      side === 'left' ? state.setLeftPanelMinimized : state.setRightPanelMinimized;

    if (!isOpen) {
      toggle();
      setMinimized(false);
    } else if (isMinimized) {
      setMinimized(false);
    } else {
      setMinimized(true);
    }
  };

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={expanded}
      className={`px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold transition-all ${
        expanded
          ? 'bg-primary/20 text-primary border-primary/50'
          : 'bg-surface-container text-on-surface-variant border-surface-variant/40 hover:text-on-surface'
      }`}
      title={`Toggle the ${label.toLowerCase()} panel`}
    >
      {label} {side === 'left' ? (expanded ? '◀' : '▶') : expanded ? '▶' : '◀'}
    </button>
  );
};
