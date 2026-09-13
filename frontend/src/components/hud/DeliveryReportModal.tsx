import React from 'react';
import {
  Ban,
  Check,
  CheckCircle2,
  Copy,
  Download,
  XCircle,
} from 'lucide-react';
import { useOfficeStore } from '../../store/useOfficeStore';

export const DeliveryReportModal: React.FC = () => {
  const delivery = useOfficeStore((state) => state.delivery);
  const runToken = useOfficeStore((state) => state.runToken);
  const [copied, setCopied] = React.useState(false);

  if (!delivery.isOpen) return null;

  const aborted = delivery.approvalStatus && delivery.approvalStatus !== 'APPROVED';

  // A browser download is a plain navigation and cannot set a header, so the
  // run token travels as a query parameter on this one endpoint.
  const downloadUrl =
    delivery.threadId && runToken
      ? `/api/runs/${delivery.threadId}/download?token=${encodeURIComponent(runToken)}`
      : null;

  const handleCopy = () => {
    navigator.clipboard.writeText(delivery.summary);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const handleAcknowledge = () => {
    const store = useOfficeStore.getState();
    store.closeDelivery();
    store.setAgentStatus('manager', 'Walk', 'David: Returning to his desk...');
    store.setAgentMovement('manager', 'desk_david');
    store.setRunning(false);
  };

  // Three outcomes, not two. An aborted run is neither a success nor a
  // sandbox failure, and must not be shown as either.
  const tone = aborted
    ? {
        banner: 'bg-amber-500/10 border-amber-500/20',
        icon: <Ban className="w-5 h-5 text-amber-400" />,
        title: 'RUN ABORTED — NOTHING WAS EXECUTED',
        pill: 'bg-amber-950/50 text-amber-300 border-amber-500/30',
        pillText: delivery.approvalStatus ?? 'ABORTED',
      }
    : delivery.success
      ? {
          banner: 'bg-emerald-500/10 border-emerald-500/20',
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
          title: 'TESTS PASSED IN THE SANDBOX',
          pill: 'bg-emerald-950/50 text-emerald-300 border-emerald-500/30',
          pillText: 'EXIT 0',
        }
      : {
          banner: 'bg-red-500/10 border-red-500/20',
          icon: <XCircle className="w-5 h-5 text-red-400" />,
          title: 'TESTS FAILED IN THE SANDBOX',
          pill: 'bg-red-950/50 text-red-300 border-red-500/30',
          pillText:
            delivery.exitCode === null || delivery.exitCode === undefined
              ? 'NO EXIT CODE'
              : `EXIT ${delivery.exitCode}`,
        };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="delivery-title"
        className="bg-surface border border-border rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden"
      >
        <div className={`p-4 flex items-center justify-between border-b ${tone.banner}`}>
          <div className="flex items-center gap-2.5">
            {tone.icon}
            <h2
              id="delivery-title"
              className="font-bold text-base text-white tracking-wide"
            >
              {tone.title}
            </h2>
          </div>
          <span className={`text-xs font-mono px-2.5 py-1 rounded border ${tone.pill}`}>
            {tone.pillText}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-sm">
          {/* Evidence, not a percentage. */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2 rounded bg-background border border-border">
              <div className="text-[9px] uppercase text-gray-500">Approval</div>
              <div className="font-bold text-gray-200 mt-0.5">
                {delivery.approvalStatus ?? 'unknown'}
              </div>
            </div>
            <div className="p-2 rounded bg-background border border-border">
              <div className="text-[9px] uppercase text-gray-500">Exit code</div>
              <div className="font-bold text-gray-200 mt-0.5">
                {delivery.exitCode ?? '—'}
              </div>
            </div>
            <div className="p-2 rounded bg-background border border-border">
              <div className="text-[9px] uppercase text-gray-500">Failing tests</div>
              <div className="font-bold text-gray-200 mt-0.5">
                {delivery.failingTestsCount ?? 0}
              </div>
            </div>
            <div className="p-2 rounded bg-background border border-border">
              <div className="text-[9px] uppercase text-gray-500">Digest</div>
              <div
                className="font-bold text-gray-200 mt-0.5 truncate"
                title={delivery.bundleDigest ?? undefined}
              >
                {delivery.bundleDigest ? `${delivery.bundleDigest.slice(0, 10)}…` : '—'}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Final report
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="text-xs text-gray-400 hover:text-white flex items-center gap-1 px-2 py-1"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          <div className="bg-background border border-border p-4 rounded-lg text-xs font-mono text-gray-200 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-96 select-text">
            {delivery.summary}
          </div>

          {delivery.traceUrl && (
            <a
              href={delivery.traceUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-block text-xs font-mono text-blue-300 hover:text-blue-200 underline"
            >
              Open the full trace
            </a>
          )}
        </div>

        <div className="p-4 border-t border-border bg-background/50 flex items-center justify-between gap-3">
          {aborted ? (
            <span className="text-xs font-mono text-gray-500">
              No workspace was written, so there is nothing to download.
            </span>
          ) : downloadUrl ? (
            <a
              href={downloadUrl}
              download
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-emerald-900/30"
            >
              <Download className="w-4 h-4" />
              <span>Download workspace (.zip)</span>
            </a>
          ) : (
            <span className="text-xs font-mono text-gray-500">
              Download needs the run token from the tab that started this run.
            </span>
          )}

          <button
            type="button"
            onClick={handleAcknowledge}
            className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-900/30"
          >
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
};
