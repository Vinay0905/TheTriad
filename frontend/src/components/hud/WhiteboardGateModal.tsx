import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Compass,
  FileCode,
  ShieldAlert,
  XCircle,
} from 'lucide-react';
import { useOfficeStore } from '../../store/useOfficeStore';

type Decision = 'approve' | 'abort' | 'steer';

/**
 * The human approval gate.
 *
 * Rules this component exists to enforce:
 *
 * - The modal only closes once the server has *accepted* the decision. It
 *   previously called `closeGate()` without checking `res.ok`, so a rejected
 *   or failed request looked identical to a successful approval.
 * - Escape never approves. It is wired to nothing at all, because a stray
 *   keystroke must not be able to resolve a security decision. Dismissing
 *   requires clicking Abort.
 * - QA status is stated plainly. An unreachable auditor shows as UNAVAILABLE,
 *   never as a pass.
 */
export const WhiteboardGateModal: React.FC = () => {
  const gate = useOfficeStore((state) => state.gate);
  const runToken = useOfficeStore((state) => state.runToken);
  const [guidance, setGuidance] = useState('');

  const dialogRef = useRef<HTMLDivElement>(null);
  const abortButtonRef = useRef<HTMLButtonElement>(null);

  // Focus the least destructive action on open, and trap Tab inside the modal
  // so keyboard users cannot land on the office behind it.
  useEffect(() => {
    if (!gate.isOpen) return;
    abortButtonRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab' || !dialogRef.current) return;

      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), [href], textarea',
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [gate.isOpen]);

  const submit = useCallback(
    async (action: Decision) => {
      const store = useOfficeStore.getState();
      if (!gate.threadId) {
        store.setGateError('This gate has no run attached; refresh and start a new run.');
        return;
      }
      if (!runToken) {
        store.setGateError(
          'No run token in this tab. Only the tab that started the run can approve it.',
        );
        return;
      }

      store.setGateSubmitting(true);
      store.setGateError(null);

      try {
        const res = await fetch('/api/gate/respond', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Run-Token': runToken,
          },
          body: JSON.stringify({
            thread_id: gate.threadId,
            action,
            guidance: action === 'steer' ? guidance : '',
          }),
        });

        if (!res.ok) {
          let detail = `Server returned ${res.status}.`;
          try {
            const body = await res.json();
            if (body?.detail) detail = String(body.detail);
          } catch {
            // Keep the status-code message.
          }
          // Stay open. The operator has not successfully decided anything yet.
          store.setGateError(detail);
          return;
        }

        setGuidance('');
        store.closeGate();

        if (action === 'abort') {
          // Nothing will run, so the office should stop looking busy.
          store.setRunning(false);
        }
      } catch (err) {
        store.setGateError(
          err instanceof Error ? err.message : 'Could not reach the server.',
        );
      }
    },
    [gate.threadId, guidance, runToken],
  );

  if (!gate.isOpen) return null;

  const qaTone =
    gate.qaStatus === 'PASS'
      ? 'text-emerald-300 border-emerald-500/40 bg-emerald-950/30'
      : gate.qaStatus === 'FAIL'
        ? 'text-red-300 border-red-500/40 bg-red-950/30'
        : 'text-amber-300 border-amber-500/40 bg-amber-950/30';

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="gate-title"
        aria-describedby="gate-description"
        className="bg-surface border border-border rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden"
      >
        <div className="bg-amber-500/10 border-b border-amber-500/20 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h2 id="gate-title" className="font-bold text-base text-white tracking-wide">
              HUMAN APPROVAL GATE
            </h2>
          </div>
          <span className="text-xs font-mono bg-black/50 text-amber-300 px-2.5 py-1 rounded border border-amber-500/30">
            Nothing has been written or run
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-sm">
          <p id="gate-description" className="sr-only">
            Approving writes these files and runs these commands in an isolated
            container. Aborting discards the run with no side effects.
          </p>

          <div>
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Objective
            </span>
            <p className="text-white font-medium mt-1">{gate.task}</p>
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div className={`border p-3 rounded-lg ${qaTone}`}>
              <div className="text-[10px] uppercase tracking-wider font-bold mb-1">
                QA status
              </div>
              <div className="font-mono text-sm font-bold">{gate.qaStatus}</div>
              {gate.qaStatus === 'UNAVAILABLE' && (
                <div className="text-[11px] mt-1 opacity-90">
                  The auditor could not be reached. This is not a pass.
                </div>
              )}
            </div>
            <div className="border border-border bg-background/60 p-3 rounded-lg">
              <div className="text-[10px] uppercase tracking-wider font-bold text-gray-400 mb-1">
                Bundle digest (SHA-256)
              </div>
              <div className="font-mono text-[10px] text-gray-300 break-all">
                {gate.digest || 'unavailable'}
              </div>
            </div>
          </div>

          <div className="bg-purple-950/20 border border-purple-800/30 p-3.5 rounded-lg">
            <div className="text-purple-400 font-semibold text-xs uppercase tracking-wider mb-1">
              Maya · auditor notes
            </div>
            <p className="text-xs font-mono text-purple-200/90 leading-relaxed whitespace-pre-wrap">
              {gate.qaReport || 'No auditor notes recorded.'}
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                Files to be written
              </div>
              <ul className="font-mono text-[11px] text-gray-300 space-y-0.5">
                {gate.files.length === 0 ? (
                  <li className="text-gray-500">none</li>
                ) : (
                  gate.files.map((file) => <li key={file}>+ {file}</li>)
                )}
              </ul>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                Commands to be executed
              </div>
              <ul className="font-mono text-[11px] text-gray-300 space-y-0.5">
                {gate.commands.length === 0 ? (
                  <li className="text-gray-500">none</li>
                ) : (
                  gate.commands.map((command) => <li key={command}>$ {command}</li>)
                )}
              </ul>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1.5 font-semibold uppercase tracking-wider">
              <FileCode className="w-4 h-4 text-blue-400" />
              Implementation preview (main.py)
            </div>
            <pre className="bg-background border border-border p-3.5 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto max-h-60 leading-relaxed">
              {gate.codePreview || '# No implementation was produced'}
            </pre>
          </div>

          <div>
            <label
              htmlFor="gate-guidance"
              className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5"
            >
              Steering guidance (required to steer)
            </label>
            <input
              id="gate-guidance"
              type="text"
              placeholder="e.g. 'release the lock in a finally block', 'stdlib only'"
              value={guidance}
              onChange={(event) => setGuidance(event.target.value)}
              disabled={gate.isSubmitting}
              className="w-full bg-background border border-border rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 disabled:opacity-60"
            />
          </div>

          {gate.error && (
            <div
              role="alert"
              className="flex items-start gap-2 bg-red-950/40 border border-red-500/40 text-red-200 p-3 rounded-lg text-xs"
            >
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-red-400" />
              <div>
                <div className="font-semibold">Your decision was not recorded.</div>
                <div className="font-mono mt-0.5 opacity-90">{gate.error}</div>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-border bg-background/50 flex flex-wrap items-center justify-end gap-3">
          <button
            ref={abortButtonRef}
            type="button"
            disabled={gate.isSubmitting}
            onClick={() => submit('abort')}
            className="px-4 py-2 rounded-lg border border-red-500/40 text-red-400 hover:bg-red-500/10 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <XCircle className="w-4 h-4" />
            Abort · write nothing
          </button>

          <button
            type="button"
            disabled={gate.isSubmitting || !guidance.trim()}
            onClick={() => submit('steer')}
            title={guidance.trim() ? undefined : 'Enter guidance to steer'}
            className="px-4 py-2 rounded-lg border border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-40"
          >
            <Compass className="w-4 h-4" />
            Steer the council
          </button>

          <button
            type="button"
            disabled={gate.isSubmitting}
            onClick={() => submit('approve')}
            className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-emerald-900/30 disabled:opacity-50"
          >
            <CheckCircle className="w-4 h-4" />
            {gate.isSubmitting ? 'Submitting...' : 'Approve · run in sandbox'}
          </button>
        </div>
      </div>
    </div>
  );
};
