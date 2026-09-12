import React from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import { CheckCircle2, XCircle, FolderArchive, Terminal, Copy, Check } from 'lucide-react';

export const DeliveryReportModal: React.FC = () => {
  const delivery = useOfficeStore((state) => state.delivery);
  const closeDelivery = useOfficeStore((state) => state.closeDelivery);
  const [copied, setCopied] = React.useState(false);

  if (!delivery.isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(delivery.summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-surface border border-border rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div
          className={`p-4 flex items-center justify-between border-b ${
            delivery.success
              ? 'bg-emerald-500/10 border-emerald-500/20'
              : 'bg-red-500/10 border-red-500/20'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {delivery.success ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
            <h2 className="font-bold text-base text-white tracking-wide">
              {delivery.success
                ? 'TASK DELIVERED & VERIFIED BY SENIOR DEV'
                : 'EXECUTION FAILED IN SANDBOX'}
            </h2>
          </div>
          <span
            className={`text-xs font-mono px-2.5 py-1 rounded border ${
              delivery.success
                ? 'bg-emerald-950/50 text-emerald-300 border-emerald-500/30'
                : 'bg-red-950/50 text-red-300 border-red-500/30'
            }`}
          >
            {delivery.success ? 'PASSED 100%' : 'FAILED'}
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
              <FolderArchive className="w-4 h-4 text-amber-400" />
              Final Engineering Status Report
            </span>
            <button
              onClick={handleCopy}
              className="text-xs text-gray-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Report'}</span>
            </button>
          </div>

          <div className="bg-background border border-border p-4 rounded-lg text-xs font-mono text-gray-200 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-96 select-text">
            {delivery.summary}
          </div>

          <div className="bg-blue-950/20 border border-blue-800/30 p-3 rounded-lg flex items-center gap-2.5 text-xs text-blue-200">
            <Terminal className="w-4 h-4 text-blue-400 shrink-0" />
            <span>
              All synthesized source files (<code className="text-emerald-300">main.py</code>,{' '}
              <code className="text-emerald-300">test_main.py</code>) and unit test artifacts are persisted inside your run workspace.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-background/50 flex items-center justify-end gap-3">
          <button
            onClick={closeDelivery}
            className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors shadow-lg shadow-blue-900/30"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
};
