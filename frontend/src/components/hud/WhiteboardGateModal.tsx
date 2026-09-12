import React, { useState } from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import { ShieldAlert, CheckCircle, XCircle, Compass, FileCode } from 'lucide-react';

export const WhiteboardGateModal: React.FC = () => {
  const gate = useOfficeStore((state) => state.gate);
  const closeGate = useOfficeStore((state) => state.closeGate);
  const [guidance, setGuidance] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!gate.isOpen) return null;

  const handleDecision = async (action: 'approve' | 'abort' | 'steer') => {
    setIsSubmitting(true);
    try {
      await fetch('/api/gate/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: gate.threadId,
          action,
          guidance: action === 'steer' ? guidance : undefined,
        }),
      });
      closeGate();
    } catch (err) {
      console.error('Failed to submit gate decision:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-surface border border-border rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-amber-500/10 border-b border-amber-500/20 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h2 className="font-bold text-base text-white tracking-wide">
              HUMAN STEERING GATE (Approval Boundary)
            </h2>
          </div>
          <span className="text-xs font-mono bg-black/50 text-amber-300 px-2.5 py-1 rounded border border-amber-500/30">
            SHA-256 Digest Locked
          </span>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-sm">
          <div>
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Objective
            </span>
            <p className="text-white font-medium mt-1">{gate.task}</p>
          </div>

          {/* QA Report from Maya */}
          <div className="bg-purple-950/20 border border-purple-800/30 p-3.5 rounded-lg">
            <div className="flex items-center gap-2 text-purple-400 font-semibold text-xs uppercase tracking-wider mb-1">
              <span>👩💻 Maya (QA & Security Auditor Report)</span>
            </div>
            <p className="text-xs font-mono text-purple-200/90 leading-relaxed">
              {gate.qaReport || 'Verified structural integrity against edge cases.'}
            </p>
          </div>

          {/* Code Preview */}
          <div>
            <div className="flex items-center justify-between text-xs text-gray-400 mb-1.5">
              <span className="font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <FileCode className="w-4 h-4 text-blue-400" />
                Synthesized Code Preview (main.py)
              </span>
              <span className="font-mono text-[11px] text-gray-500">
                Sandboxed Workspace
              </span>
            </div>
            <pre className="bg-background border border-border p-3.5 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto max-h-60 leading-relaxed">
              {gate.codePreview || '# No source code preview available'}
            </pre>
          </div>

          {/* Steer with guidance input */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
              Steer Architectural Guidance (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. 'Ensure lock releases cleanly in finally block', 'Use pure stdlib'..."
              value={guidance}
              onChange={(e) => setGuidance(e.target.value)}
              className="w-full bg-background border border-border rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-border bg-background/50 flex items-center justify-end gap-3">
          <button
            disabled={isSubmitting}
            onClick={() => handleDecision('abort')}
            className="px-4 py-2 rounded-lg border border-red-500/40 text-red-400 hover:bg-red-500/10 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <XCircle className="w-4 h-4" />
            Abort Run
          </button>

          {guidance.trim() && (
            <button
              disabled={isSubmitting}
              onClick={() => handleDecision('steer')}
              className="px-4 py-2 rounded-lg border border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Compass className="w-4 h-4" />
              Steer Council
            </button>
          )}

          <button
            disabled={isSubmitting}
            onClick={() => handleDecision('approve')}
            className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-emerald-900/30"
          >
            <CheckCircle className="w-4 h-4" />
            Approve & Execute in Sandbox
          </button>
        </div>
      </div>
    </div>
  );
};
