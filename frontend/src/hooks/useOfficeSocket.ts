import { useEffect, useRef } from 'react';
import { useOfficeStore } from '../store/useOfficeStore';

export const useOfficeSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const {
    setAgentStatus,
    setAgentMovement,
    appendTerminalLog,
    openGate,
    setRunning,
  } = useOfficeStore();

  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;
    let pingInterval: NodeJS.Timeout;

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/office`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ [Office WebSocket] Connected to server.');
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'PING' }));
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          switch (data.event_type) {
            case 'AGENT_MOVE':
              setAgentMovement(data.agent_id, data.to_node);
              break;

            case 'AGENT_STATUS':
              setAgentStatus(data.agent_id, data.animation, data.status_text);
              break;

            case 'WHITEBOARD_GATE':
              openGate(
                data.thread_id,
                data.task,
                data.code_preview,
                data.qa_report,
                data.bundle_digest
              );
              break;

            case 'TERMINAL_LOG':
              appendTerminalLog(data.stream, data.chunk);
              break;

            case 'PROJECT_COMPLETED':
              setRunning(false);
              appendTerminalLog(
                'stdout',
                `\n[PROJECT COMPLETED] ${data.summary}`
              );
              break;

            default:
              break;
          }
        } catch (err) {
          console.error('[Office WebSocket Error] Message parsing error:', err);
        }
      };

      ws.onclose = () => {
        console.warn('⚠️ [Office WebSocket] Disconnected. Reconnecting in 2s...');
        clearInterval(pingInterval);
        reconnectTimeout = setTimeout(connect, 2000);
      };

      ws.onerror = (err) => {
        console.error('[Office WebSocket Error]', err);
        ws.close();
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      clearInterval(pingInterval);
      wsRef.current?.close();
    };
  }, [setAgentStatus, setAgentMovement, appendTerminalLog, openGate, setRunning]);
};
