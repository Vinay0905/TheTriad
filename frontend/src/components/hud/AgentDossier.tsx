import React from 'react';
import { AlertTriangle, Clock, DoorOpen, Maximize2, Minimize2, X } from 'lucide-react';
import { useOfficeStore } from '../../store/useOfficeStore';
import type { ProviderRoleHealth } from '../../types/office';

// Which backend role reports health for which desk.
const ROLE_FOR_AGENT: Record<string, string[]> = {
  manager: ['manager_rfc'],
  researcher: ['researcher_audit'],
  developer: ['main.py', 'tdd_contract'],
  qa: ['qa_audit'],
};

/** Live countdown for a rate-limited provider, ticking down once per second. */
const WaitCountdown: React.FC<{ startedAt: number; seconds: number }> = ({
  startedAt,
  seconds,
}) => {
  const [remaining, setRemaining] = React.useState(() =>
    Math.max(0, Math.ceil(seconds - (Date.now() - startedAt) / 1000)),
  );

  React.useEffect(() => {
    const interval = window.setInterval(() => {
      setRemaining(Math.max(0, Math.ceil(seconds - (Date.now() - startedAt) / 1000)));
    }, 1000);
    return () => window.clearInterval(interval);
  }, [startedAt, seconds]);

  return <span className="tabular-nums font-bold">{remaining}s</span>;
};

export const AgentDossier: React.FC = () => {
  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);
  const isRightPanelOpen = useOfficeStore((state) => state.isRightPanelOpen);
  const isRightPanelMinimized = useOfficeStore((state) => state.isRightPanelMinimized);
  const setRightPanelMinimized = useOfficeStore((state) => state.setRightPanelMinimized);
  const toggleRightPanel = useOfficeStore((state) => state.toggleRightPanel);
  const providerHealth = useOfficeStore((state) => state.providerHealth);

  const agent = useOfficeStore((state) =>
    selectedAgentId ? state.agents[selectedAgentId] : null,
  );

  if (!isRightPanelOpen || !agent) return null;

  const roles: ProviderRoleHealth[] = providerHealth.roles.filter((role) =>
    (ROLE_FOR_AGENT[agent.id] ?? []).includes(role.role),
  );

  if (isRightPanelMinimized) {
    return (
      <div className="absolute right-4 bottom-14 z-30 bg-surface-container-lowest/95 border border-surface-variant/40 p-2.5 rounded-xl shadow-2xl flex items-center gap-3 backdrop-blur-xl">
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
          <span className="font-headline text-xs font-bold text-on-surface">
            {agent.name}
          </span>
          <span className="text-[10px] font-mono text-on-surface-variant truncate max-w-[150px]">
            {agent.statusBadge}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setRightPanelMinimized(false)}
            className="p-1 text-on-surface-variant hover:text-on-surface rounded"
            title="Maximise dossier"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={toggleRightPanel}
            className="p-1 text-on-surface-variant hover:text-red-400 rounded"
            title="Close panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <aside className="w-80 bg-surface-container-lowest/95 backdrop-blur-xl border-l border-surface-variant/30 flex flex-col shrink-0 z-20 shadow-2xl">
      <div className="p-3.5 border-b border-surface-variant/30 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center font-headline font-bold text-xs shadow-md shrink-0"
            style={{ backgroundColor: agent.color, color: '#0a0e16' }}
          >
            {agent.name.charAt(0)}
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-headline text-xs font-bold text-on-surface">
                {agent.name}
              </span>
              <span
                className="px-1.5 rounded font-mono text-[9px] font-bold"
                style={{ backgroundColor: `${agent.color}25`, color: agent.color }}
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
            type="button"
            onClick={() => setRightPanelMinimized(true)}
            className="p-1 rounded bg-surface-container hover:bg-surface-bright text-on-surface-variant"
            title="Minimise"
          >
            <Minimize2 className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={toggleRightPanel}
            className="p-1 rounded bg-surface-container hover:bg-surface-bright text-on-surface-variant"
            title="Close"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
        {/* Provider state, when the agent is not simply working. */}
        {agent.waitState && (
          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/40 text-amber-200 text-[11px] font-mono flex items-start gap-2">
            <Clock className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
            <div>
              <div className="font-bold uppercase tracking-wide text-[10px]">
                Rate limited · retrying in{' '}
                <WaitCountdown
                  startedAt={agent.waitState.waitStartedAt}
                  seconds={agent.waitState.retryAfterSeconds}
                />
              </div>
              <div className="mt-0.5 opacity-90">
                {agent.waitState.provider} · attempt {agent.waitState.attempt} of{' '}
                {agent.waitState.maxAttempts}
              </div>
            </div>
          </div>
        )}

        {agent.absence && (
          <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/40 text-rose-200 text-[11px] font-mono flex items-start gap-2">
            <DoorOpen className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <div className="font-bold uppercase tracking-wide text-[10px]">
                Clocked out · quota exhausted
              </div>
              <div className="mt-0.5 opacity-90">{agent.absence.reason}</div>
              {agent.absence.resetAtDisplay && (
                <div className="mt-0.5">Back around {agent.absence.resetAtDisplay}</div>
              )}
              {agent.absence.coveredBy && (
                <div className="mt-0.5 text-amber-300">
                  Covered by {agent.absence.coveredBy}
                </div>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 gap-2 text-xs font-mono">
          <div className="p-2 rounded bg-surface-container border border-surface-variant/30">
            <span className="text-[9px] text-on-surface-variant uppercase">
              Configured provider
            </span>
            <div className="font-bold text-on-surface mt-0.5 truncate">{agent.model}</div>
          </div>
          <div className="p-2 rounded bg-surface-container border border-surface-variant/30">
            <span className="text-[9px] text-on-surface-variant uppercase">
              Current activity
            </span>
            <div className="font-bold text-on-surface mt-0.5">{agent.statusBadge}</div>
          </div>
        </div>

        {/* Observed backend health for this desk. Empty until a run touches it. */}
        <div className="flex flex-col gap-1.5">
          <span className="font-mono text-[10px] text-on-surface-variant uppercase font-semibold">
            Observed backend state
          </span>
          {roles.length === 0 ? (
            <div className="p-2.5 rounded bg-surface-container-lowest border border-surface-variant/40 text-[10.5px] font-mono text-gray-500">
              No calls observed yet this session.
            </div>
          ) : (
            roles.map((role) => (
              <div
                key={role.role}
                className="p-2 rounded bg-surface-container-lowest border border-surface-variant/40 text-[10.5px] font-mono"
              >
                <div className="flex items-center justify-between">
                  <span className="text-on-surface-variant">
                    {role.role.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={
                      role.state === 'OK' ? 'text-emerald-400' : 'text-amber-400'
                    }
                  >
                    {role.state}
                  </span>
                </div>
                <div className="text-gray-500 mt-0.5 truncate">{role.model}</div>
                {role.detail && (
                  <div className="text-gray-400 mt-0.5 truncate">{role.detail}</div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="p-2.5 rounded-lg bg-surface-container/70 border border-surface-variant/40 flex flex-col gap-1">
          <span className="font-mono text-[10px] text-primary uppercase font-bold">
            Role directive
          </span>
          <p className="font-mono text-[10.5px] text-on-surface-variant leading-relaxed">
            {agent.directive}
          </p>
        </div>

        {/*
          There is no chat here. Agents are graph nodes, not conversational
          endpoints: there is no backend channel to send a message to, and the
          previous version displayed invented replies on a timer. An honest
          empty state is better than fabricated dialogue.

          The manual "open gate" button was also removed. It fabricated a
          gate payload with a bogus thread id, so approving it would have
          posted a decision for a run that did not exist. The gate opens only
          when the graph actually suspends.
        */}
        <div className="p-2.5 rounded-lg bg-surface-container-lowest border border-surface-variant/40 text-[10.5px] font-mono text-gray-500 flex items-start gap-2">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-gray-500" />
          <span>
            Direct interrogation is not wired. Agents are pipeline nodes, and the
            approval gate opens only when the graph suspends.
          </span>
        </div>
      </div>
    </aside>
  );
};
