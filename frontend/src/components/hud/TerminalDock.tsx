import React, { useState } from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';
import { Terminal, ChevronUp, ChevronDown, Trash2 } from 'lucide-react';

export const TerminalDock: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const terminalLogs = useOfficeStore((state) => state.terminalLogs);
  const clearTerminalLogs = useOfficeStore((state) => state.clearTerminalLogs);

  return (
    <div
      className={`bg-surface/95 backdrop-blur border-t border-border transition-all duration-200 flex flex-col z-20 shadow-2xl ${
        isExpanded ? 'h-64' : 'h-10'
      }`}
    >
      {/* Dock Bar Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="h-10 px-4 flex items-center justify-between cursor-pointer border-b border-border/50 hover:bg-surfaceHover/50 select-none"
      >
        <div className="flex items-center gap-2 text-xs font-mono text-gray-300">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-white">Execution Sandbox Terminal</span>
          <span className="text-gray-500">|</span>
          <span className="text-[11px] text-gray-400">
            {terminalLogs.length} line{terminalLogs.length !== 1 ? 's' : ''} captured
          </span>
        </div>

        <div className="flex items-center gap-3">
          {isExpanded && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearTerminalLogs();
              }}
              className="p-1 text-gray-400 hover:text-red-400 transition-colors"
              title="Clear Terminal"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>

      {/* Terminal Body */}
      {isExpanded && (
        <div className="flex-1 p-3 overflow-y-auto font-mono text-xs bg-background text-gray-200 space-y-1 select-text">
          {terminalLogs.length === 0 ? (
            <div className="text-gray-500 italic py-4 text-center">
              No sandbox output. Run a task to stream unit test execution logs.
            </div>
          ) : (
            terminalLogs.map((log) => (
              <div
                key={log.id}
                className={`whitespace-pre-wrap leading-relaxed ${
                  log.stream === 'stderr' ? 'text-red-400' : 'text-emerald-300'
                }`}
              >
                {log.chunk}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
