import { useEffect, useRef } from 'react';
import { useOfficeStore } from '../store/useOfficeStore';

export const useOfficeSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const deliveryTimerRef = useRef<number | null>(null);
  const clockOutTimerRef = useRef<number | null>(null);
  const {
    setAgentStatus,
    setAgentMovement,
    appendTerminalLog,
    openGate,
    setRunning,
    setOfficeClock,
    setWorkforcePresent,
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
              // Delivery is a human moment, not an instant status flip. David
              // walks into the private BOSS room before the report is opened.
              setAgentStatus('manager', 'Walk', 'David: Bringing the verified delivery to BOSS...');
              setAgentMovement('manager', 'boss_room');
              appendTerminalLog(
                'stdout',
                `\n[PROJECT COMPLETED] ${data.summary}`
              );
              if (deliveryTimerRef.current !== null) window.clearTimeout(deliveryTimerRef.current);
              deliveryTimerRef.current = window.setTimeout(() => {
                useOfficeStore.getState().setAgentStatus(
                  'manager',
                  'Sit',
                  'David: Waiting for BOSS acknowledgement.',
                );
                useOfficeStore.getState().openDelivery(
                  data.thread_id,
                  data.success,
                  data.summary,
                );
                deliveryTimerRef.current = null;
              }, 4200);
              break;

            case 'OFFICE_CLOCK':
              setOfficeClock({
                phase: data.phase,
                displayTime: data.display_time,
                dayNumber: data.day_number,
                secondsRemaining: data.seconds_remaining,
              });
              if (data.phase === 'OFF_HOURS') {
                const anyoneStillPresent = Object.values(useOfficeStore.getState().agents)
                  .some((agent) => agent.isPresent !== false);
                if (anyoneStillPresent && clockOutTimerRef.current === null) {
                  clockOutTimerRef.current = window.setTimeout(() => {
                    useOfficeStore.getState().setWorkforcePresent(false);
                    clockOutTimerRef.current = null;
                  }, 4300);
                }
              } else {
                if (clockOutTimerRef.current !== null) window.clearTimeout(clockOutTimerRef.current);
                if (Object.values(useOfficeStore.getState().agents).some((agent) => agent.isPresent === false)) {
                  setWorkforcePresent(true);
                }
              }
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
      if (deliveryTimerRef.current !== null) window.clearTimeout(deliveryTimerRef.current);
      if (clockOutTimerRef.current !== null) window.clearTimeout(clockOutTimerRef.current);
      wsRef.current?.close();
    };
  }, [setAgentStatus, setAgentMovement, appendTerminalLog, openGate, setRunning, setOfficeClock, setWorkforcePresent]);
};
