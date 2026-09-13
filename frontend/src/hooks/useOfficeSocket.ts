import { useEffect, useRef } from 'react';
import { useOfficeStore } from '../store/useOfficeStore';
import type { OfficeEvent } from '../types/office';

const RECONNECT_DELAY_MS = 2000;
const PING_INTERVAL_MS = 15000;
const DELIVERY_WALK_MS = 3600;

/**
 * The single WebSocket connection to the office.
 *
 * Two deliberate choices here:
 *
 * - The hook subscribes to nothing. Every handler reaches the store through
 *   `getState()`, so terminal output and clock ticks cannot re-render this
 *   component. Destructuring the store, as the previous version did, meant a
 *   re-render on literally every state change.
 * - `cancelled` guards the reconnect. Without it, React StrictMode's
 *   mount/unmount/mount left an orphaned socket that kept its ping interval
 *   alive and kept scheduling reconnects forever.
 */
export const useOfficeSocket = () => {
  const deliveryTimerRef = useRef<number | null>(null);

  // Interpolates the clock between the server's coarse updates.
  useEffect(() => {
    const interval = window.setInterval(() => {
      if (document.visibilityState === 'visible') {
        useOfficeStore.getState().tickLocalClock();
      }
    }, 1000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    let cancelled = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;
    let pingTimer: number | undefined;

    const handle = (event: OfficeEvent) => {
      const store = useOfficeStore.getState();

      switch (event.event_type) {
        case 'AGENT_MOVE':
          store.setAgentMovement(event.agent_id, event.to_node, event.slot_id ?? null);
          break;

        case 'AGENT_STATUS':
          store.setAgentStatus(event.agent_id, event.animation, event.status_text);
          break;

        case 'AGENT_WAITING':
          // A rate limit reads as a person waiting, with a live countdown.
          store.setAgentWaiting(event.agent_id, {
            provider: event.provider,
            model: event.model,
            reason: event.reason,
            retryAfterSeconds: event.retry_after_seconds,
            waitStartedAt: Date.now(),
            attempt: event.attempt,
            maxAttempts: event.max_attempts,
          });
          store.setAgentStatus(event.agent_id, 'Wait', event.reason);
          break;

        case 'AGENT_CLOCK_OUT':
          store.setAgentWaiting(event.agent_id, null);
          store.setAgentAbsence(event.agent_id, {
            provider: event.provider,
            reason: event.reason,
            resetAtDisplay: event.reset_at_display ?? null,
            coveredBy: event.covered_by ?? null,
          });
          store.setAgentStatus(event.agent_id, 'Walk', event.reason);
          break;

        case 'AGENT_CLOCK_IN':
          store.setAgentAbsence(event.agent_id, null);
          store.setAgentWaiting(event.agent_id, null);
          break;

        case 'AGENT_BREAK':
          // Movement already arrives via AGENT_MOVE; this only annotates why.
          store.setAgentStatus(
            event.agent_id,
            event.break_type === 'COFFEE' ? 'Coffee' : 'Walk',
            event.returning ? 'Heading back to their desk...' : event.destination,
          );
          break;

        case 'PROVIDER_HEALTH':
          store.setProviderHealth({
            roles: event.roles,
            sandboxAvailable: event.sandbox_available,
            sandboxBackend: event.sandbox_backend,
          });
          break;

        case 'RED_GREEN_STATUS':
          store.setRedStatus(event.phase);
          break;

        case 'TERMINAL_LOG':
          store.appendTerminalLog(event.stream, event.chunk);
          break;

        case 'WHITEBOARD_GATE':
          store.openGate({
            threadId: event.thread_id,
            task: event.task,
            codePreview: event.code_preview,
            qaReport: event.qa_report,
            digest: event.bundle_digest,
            qaStatus: event.qa_status,
            redStatus: event.red_status,
            files: event.files,
            commands: event.commands,
            gateKind: event.gate_kind,
          });
          break;

        case 'PROJECT_COMPLETED': {
          // Delivery is a moment, not an instant flip: David walks the result
          // into the BOSS room before the report opens.
          store.setAgentStatus('manager', 'Walk', 'David: Taking the outcome to BOSS...');
          store.appendTerminalLog('stdout', `\n[RUN COMPLETE] ${event.summary}`);

          if (deliveryTimerRef.current !== null) {
            window.clearTimeout(deliveryTimerRef.current);
          }
          deliveryTimerRef.current = window.setTimeout(() => {
            useOfficeStore.getState().openDelivery({
              threadId: event.thread_id,
              success: event.success,
              summary: event.summary,
              approvalStatus: event.approval_status ?? null,
              exitCode: event.exit_code ?? null,
              failingTestsCount: event.failing_tests_count ?? 0,
              traceUrl: event.trace_url ?? null,
              bundleDigest: event.bundle_digest ?? null,
            });
            deliveryTimerRef.current = null;
          }, DELIVERY_WALK_MS);
          break;
        }

        case 'OFFICE_CLOCK':
          store.setOfficeClock({
            phase: event.phase,
            displayTime: event.display_time,
            dayNumber: event.day_number,
            secondsRemaining: event.seconds_remaining,
          });
          break;

        case 'OFFICE_SCHEDULE_TICK':
          // Presence is driven by AGENT_MOVE; nothing to do but stay in sync.
          break;

        default:
          break;
      }
    };

    const connect = () => {
      if (cancelled) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      socket = new WebSocket(`${protocol}//${window.location.host}/ws/office`);

      socket.onopen = () => {
        if (cancelled) {
          socket?.close();
          return;
        }
        useOfficeStore.getState().setConnected(true);
        pingTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'PING' }));
          }
        }, PING_INTERVAL_MS);
      };

      socket.onmessage = (message) => {
        if (cancelled) return;
        try {
          handle(JSON.parse(message.data) as OfficeEvent);
        } catch (err) {
          console.error('[Office] Unparseable event:', err);
        }
      };

      socket.onclose = () => {
        window.clearInterval(pingTimer);
        if (cancelled) return;
        useOfficeStore.getState().setConnected(false);
        reconnectTimer = window.setTimeout(connect, RECONNECT_DELAY_MS);
      };

      socket.onerror = () => {
        socket?.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      window.clearTimeout(reconnectTimer);
      window.clearInterval(pingTimer);
      if (deliveryTimerRef.current !== null) {
        window.clearTimeout(deliveryTimerRef.current);
        deliveryTimerRef.current = null;
      }
      socket?.close();
      socket = null;
    };
  }, []);
};
