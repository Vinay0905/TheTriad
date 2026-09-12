// ---------------------------------------------------------------------------
// FROZEN CONTRACT. This file mirrors src/ai_team/domain/contracts.py.
// Change both sides together or the office desynchronises from the backend.
// ---------------------------------------------------------------------------

export type AgentAnimation =
  | 'Idle'
  | 'Walk'
  | 'Sit'
  | 'Type'
  | 'Coffee'
  | 'Think'
  | 'Wait';

export type CameraPreset = 'room' | 'pantry' | 'desks' | 'whiteboard' | 'meeting';

/** Behaviour arbitration order. A scheduled break never preempts a gate presentation. */
export type BehaviorPriority =
  | 'PIPELINE_CRITICAL'
  | 'PROVIDER_STATE'
  | 'SCHEDULED_BREAK'
  | 'AMBIENT_IDLE';

export type ProviderState =
  | 'OK'
  | 'RATE_LIMITED'
  | 'QUOTA_EXHAUSTED'
  | 'AUTH_FAILED'
  | 'OFFLINE';

export type RedGreenPhase = 'RED' | 'GREEN' | 'UNVERIFIED';

export type QaStatus = 'PASS' | 'FAIL' | 'UNAVAILABLE';

export interface ProviderRoleHealth {
  role: string;
  provider: string;
  model: string;
  state: ProviderState;
  reset_at_display?: string | null;
  detail: string;
}

/** Live provider availability. Replaces the hardcoded "NODES: 4/4 LIVE" telemetry. */
export interface ProviderHealth {
  roles: ProviderRoleHealth[];
  sandboxAvailable: boolean;
  sandboxBackend: string;
}

/** A transient rate limit, rendered as a person waiting rather than a crash. */
export interface AgentWaitState {
  provider: string;
  model: string;
  reason: string;
  retryAfterSeconds: number;
  waitStartedAt: number;
  attempt: number;
  maxAttempts: number;
}

/** A hard quota exhaustion. The agent walks out and the desk shows a placard. */
export interface AgentAbsence {
  provider: string;
  reason: string;
  resetAtDisplay?: string | null;
  coveredBy?: string | null;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  department: string;
  model: string;
  currentWaypoint: string;
  targetWaypoint: string;
  animation: AgentAnimation;
  statusBadge: string;
  color: string;
  avatarIcon: string;
  nodeId?: string;
  directive?: string;
  customPosition?: [number, number, number] | null;
  isPresent?: boolean;

  /** Reserved sub-slot within targetWaypoint, so two agents never share a seat. */
  slotId?: string | null;
  /** Set while the agent's provider is rate-limited; drives the countdown bubble. */
  waitState?: AgentWaitState | null;
  /** Set while the agent is clocked out on an exhausted quota. */
  absence?: AgentAbsence | null;

  // NOTE (A6): contextBudget / speed / cost were fabricated telemetry and are
  // deliberately absent. Derive anything shown here from ProviderHealth.
}

export interface OfficeClock {
  phase: 'WORKDAY' | 'OFF_HOURS';
  displayTime: string;
  dayNumber: number;
  secondsRemaining: number;
}

/**
 * A named destination. Under C2 the navmesh owns routing, so `neighbors` is
 * legacy and optional: destinations are points validated against the navmesh,
 * not nodes in a hand-maintained graph.
 */
export interface Waypoint {
  id: string;
  name: string;
  x: number;
  z: number;
  /** Distinct sub-slots for shared destinations (pantry, whiteboard, meeting table). */
  capacity?: number;
  /** Which way to face on arrival, in radians. Undefined means face travel direction. */
  facing?: number;
  neighbors?: string[];
}

export interface GateState {
  isOpen: boolean;
  threadId: string | null;
  task: string;
  codePreview: string;
  qaReport: string;
  digest: string;
  /** QA may be UNAVAILABLE. It must never be presented as PASS. */
  qaStatus: QaStatus;
  redStatus: RedGreenPhase;
  files: string[];
  commands: string[];
  /** EXECUTE is the hard gate; RED_VERIFICATION is the cheaper pre-implementation gate. */
  gateKind: 'EXECUTE' | 'RED_VERIFICATION';
  /** Submission error, so the modal can stay open instead of closing on failure. */
  error: string | null;
  isSubmitting: boolean;
}

export interface TerminalLog {
  id: string;
  stream: 'stdout' | 'stderr';
  chunk: string;
  timestamp: number;
}

export interface ProjectDelivery {
  isOpen: boolean;
  threadId: string;
  success: boolean;
  summary: string;
  approvalStatus?: string | null;
  exitCode?: number | null;
  failingTestsCount?: number;
  traceUrl?: string | null;
  bundleDigest?: string | null;
}

// ---------------------------------------------------------------------------
// WebSocket event union. Mirrors OfficeEvent in contracts.py exactly.
// ---------------------------------------------------------------------------

export type OfficeEvent =
  | {
      event_type: 'AGENT_MOVE';
      agent_id: string;
      from_node: string;
      to_node: string;
      action: string;
      slot_id?: string | null;
      reason?: string;
      priority?: BehaviorPriority;
    }
  | {
      event_type: 'AGENT_STATUS';
      agent_id: string;
      status_text: string;
      animation: AgentAnimation;
    }
  | {
      event_type: 'AGENT_WAITING';
      agent_id: string;
      provider: string;
      model: string;
      reason: string;
      retry_after_seconds: number;
      attempt: number;
      max_attempts: number;
    }
  | {
      event_type: 'AGENT_CLOCK_OUT';
      agent_id: string;
      provider: string;
      reason: string;
      reset_at_display?: string | null;
      covered_by?: string | null;
    }
  | {
      event_type: 'AGENT_CLOCK_IN';
      agent_id: string;
      provider: string;
      reason?: string;
    }
  | {
      event_type: 'AGENT_BREAK';
      agent_id: string;
      break_type: 'COFFEE' | 'AIR' | 'LUNCH' | 'STRETCH' | 'READING';
      destination: string;
      duration_sim_minutes: number;
      returning: boolean;
    }
  | {
      event_type: 'PROVIDER_HEALTH';
      roles: ProviderRoleHealth[];
      sandbox_available: boolean;
      sandbox_backend: string;
    }
  | {
      event_type: 'RED_GREEN_STATUS';
      thread_id: string;
      phase: RedGreenPhase;
      detail: string;
      failing_tests_count: number;
      tdd_digest: string;
    }
  | {
      event_type: 'WHITEBOARD_GATE';
      thread_id: string;
      task: string;
      code_preview: string;
      qa_report: string;
      bundle_digest: string;
      qa_status: QaStatus;
      red_status: RedGreenPhase;
      files: string[];
      commands: string[];
      gate_kind: 'EXECUTE' | 'RED_VERIFICATION';
    }
  | {
      event_type: 'TERMINAL_LOG';
      stream: 'stdout' | 'stderr';
      chunk: string;
    }
  | {
      event_type: 'PROJECT_COMPLETED';
      thread_id: string;
      success: boolean;
      summary: string;
      approval_status?: string | null;
      exit_code?: number | null;
      failing_tests_count?: number;
      trace_url?: string | null;
      bundle_digest?: string | null;
    }
  | {
      event_type: 'OFFICE_CLOCK';
      phase: 'WORKDAY' | 'OFF_HOURS';
      display_time: string;
      day_number: number;
      seconds_remaining: number;
    }
  | {
      event_type: 'OFFICE_SCHEDULE_TICK';
      sim_minutes_since_open: number;
      display_time: string;
      day_number: number;
    };
