import { create } from 'zustand';
import type {
  Agent,
  AgentAbsence,
  AgentAnimation,
  AgentWaitState,
  CameraPreset,
  GateState,
  OfficeClock,
  ProjectDelivery,
  ProviderHealth,
  RedGreenPhase,
  TerminalLog,
} from '../types/office';

/**
 * Terminal output is unbounded in principle: a long test run can emit
 * thousands of lines. The previous implementation copied the whole array on
 * every chunk and never trimmed it, which grew memory without limit and
 * re-rendered the dock on each append. Keep a ring buffer instead.
 */
const TERMINAL_LOG_LIMIT = 500;

let terminalLogSequence = 0;

interface OfficeState {
  agents: Record<string, Agent>;
  selectedAgentId: string | null;
  selectedDepartment: string | null;
  terminalLogs: TerminalLog[];
  gate: GateState;
  delivery: ProjectDelivery;
  currentObjective: string;
  isRunning: boolean;
  activeThreadId: string | null;

  /**
   * Issued once by POST /api/tasks/start and required to approve or download
   * this run. Held in memory only: it is never persisted and never arrives
   * over the WebSocket.
   */
  runToken: string | null;

  /** Real backend availability. Replaces the old hardcoded "4/4 LIVE" pill. */
  providerHealth: ProviderHealth;
  /** Whether the websocket is currently connected, for honest status display. */
  isConnected: boolean;
  /** Last error worth showing the operator, e.g. a failed task start. */
  lastError: string | null;

  redStatus: RedGreenPhase;

  isLeftPanelOpen: boolean;
  isLeftPanelMinimized: boolean;
  isRightPanelOpen: boolean;
  isRightPanelMinimized: boolean;
  isDraggingAgent: boolean;
  cameraPreset: CameraPreset;
  officeClock: OfficeClock;

  toggleLeftPanel: () => void;
  setLeftPanelMinimized: (minimized: boolean) => void;
  toggleRightPanel: () => void;
  setRightPanelMinimized: (minimized: boolean) => void;
  setCameraPreset: (preset: CameraPreset) => void;
  setIsDraggingAgent: (dragging: boolean) => void;
  setSelectedAgent: (id: string | null) => void;
  setSelectedDepartment: (dept: string | null) => void;

  setAgentStatus: (agentId: string, animation: AgentAnimation, statusBadge: string) => void;
  setAgentMovement: (agentId: string, toNode: string, slotId?: string | null) => void;
  setAgentPosition: (agentId: string, position: [number, number, number]) => void;
  setAgentWaiting: (agentId: string, wait: AgentWaitState | null) => void;
  setAgentAbsence: (agentId: string, absence: AgentAbsence | null) => void;
  setAgentPresent: (agentId: string, present: boolean) => void;
  setWorkforcePresent: (present: boolean) => void;

  appendTerminalLog: (stream: 'stdout' | 'stderr', chunk: string) => void;
  clearTerminalLogs: () => void;

  openGate: (gate: Partial<GateState> & { threadId: string; task: string }) => void;
  setGateSubmitting: (submitting: boolean) => void;
  setGateError: (error: string | null) => void;
  closeGate: () => void;

  openDelivery: (delivery: Partial<ProjectDelivery> & { threadId: string }) => void;
  closeDelivery: () => void;

  setObjective: (objective: string) => void;
  setRunning: (running: boolean, threadId?: string | null, runToken?: string | null) => void;
  setProviderHealth: (health: ProviderHealth) => void;
  setConnected: (connected: boolean) => void;
  setLastError: (error: string | null) => void;
  setRedStatus: (phase: RedGreenPhase) => void;
  setOfficeClock: (clock: OfficeClock) => void;
  tickLocalClock: () => void;
}

const EMPTY_GATE: GateState = {
  isOpen: false,
  threadId: null,
  task: '',
  codePreview: '',
  qaReport: '',
  digest: '',
  qaStatus: 'UNAVAILABLE',
  redStatus: 'UNVERIFIED',
  files: [],
  commands: [],
  gateKind: 'EXECUTE',
  error: null,
  isSubmitting: false,
};

const EMPTY_DELIVERY: ProjectDelivery = {
  isOpen: false,
  threadId: '',
  success: false,
  summary: '',
  approvalStatus: null,
  exitCode: null,
  failingTestsCount: 0,
  traceUrl: null,
  bundleDigest: null,
};

// Model labels describe which provider a role is configured to use. Live
// state (rate limited, clocked out) comes from PROVIDER_HEALTH, never hardcoded.
const INITIAL_AGENTS: Record<string, Agent> = {
  manager: {
    id: 'manager',
    nodeId: 'NODE #01',
    name: 'David',
    role: 'Engineering Manager',
    department: 'Management',
    model: 'OpenRouter',
    currentWaypoint: 'desk_david',
    targetWaypoint: 'desk_david',
    animation: 'Sit',
    statusBadge: 'Awaiting objective',
    color: '#e3c198',
    avatarIcon: '🧑‍💼',
    directive: 'Scope the task, set acceptance criteria, verify the preflight bundle, and report the outcome.',
    isPresent: true,
    slotId: null,
    waitState: null,
    absence: null,
  },
  researcher: {
    id: 'researcher',
    nodeId: 'NODE #02',
    name: 'Elena',
    role: 'Research Engineer',
    department: 'Research',
    model: 'Groq',
    currentWaypoint: 'desk_elena',
    targetWaypoint: 'desk_elena',
    animation: 'Sit',
    statusBadge: 'Standing by',
    color: '#d0bcff',
    avatarIcon: '👩‍🔬',
    directive: 'Audit dependency choices and concurrency hazards. Note: no live web search is wired, so findings are unverified.',
    isPresent: true,
    slotId: null,
    waitState: null,
    absence: null,
  },
  developer: {
    id: 'developer',
    nodeId: 'NODE #03',
    name: 'Alex',
    role: 'Senior Developer',
    department: 'Engineering',
    model: 'Groq / Gemini / OpenRouter',
    currentWaypoint: 'desk_alex',
    targetWaypoint: 'desk_alex',
    animation: 'Sit',
    statusBadge: 'Standing by',
    color: '#4cd7f6',
    avatarIcon: '🧑‍💻',
    directive: 'Freeze the test contract, then implement main.py against it. May never modify the tests.',
    isPresent: true,
    slotId: null,
    waitState: null,
    absence: null,
  },
  qa: {
    id: 'qa',
    nodeId: 'NODE #04',
    name: 'Maya',
    role: 'QA & Security Auditor',
    department: 'Quality Assurance',
    model: 'ZhipuAI GLM-4-Flash',
    currentWaypoint: 'desk_maya',
    targetWaypoint: 'desk_maya',
    animation: 'Sit',
    statusBadge: 'Standing by',
    color: '#10b981',
    avatarIcon: '👩‍💻',
    directive: 'Run the AST gate, then adversarially audit for edge cases and races. An unreachable audit is never a pass.',
    isPresent: true,
    slotId: null,
    waitState: null,
    absence: null,
  },
};

const patchAgent = (
  state: OfficeState,
  agentId: string,
  patch: Partial<Agent>,
): Partial<OfficeState> => {
  const agent = state.agents[agentId];
  if (!agent) return {};
  return { agents: { ...state.agents, [agentId]: { ...agent, ...patch } } };
};

export const useOfficeStore = create<OfficeState>((set) => ({
  agents: INITIAL_AGENTS,
  selectedAgentId: 'developer',
  selectedDepartment: null,
  terminalLogs: [],
  gate: EMPTY_GATE,
  delivery: EMPTY_DELIVERY,
  currentObjective: '',
  isRunning: false,
  activeThreadId: null,
  runToken: null,
  providerHealth: { roles: [], sandboxAvailable: false, sandboxBackend: 'docker' },
  isConnected: false,
  lastError: null,
  redStatus: 'UNVERIFIED',

  isLeftPanelOpen: true,
  isLeftPanelMinimized: false,
  isRightPanelOpen: true,
  isRightPanelMinimized: false,
  isDraggingAgent: false,
  cameraPreset: 'room',
  officeClock: {
    phase: 'WORKDAY',
    displayTime: '09:00',
    dayNumber: 1,
    secondsRemaining: 1200,
  },

  toggleLeftPanel: () => set((state) => ({ isLeftPanelOpen: !state.isLeftPanelOpen })),
  setLeftPanelMinimized: (minimized) => set({ isLeftPanelMinimized: minimized }),
  toggleRightPanel: () => set((state) => ({ isRightPanelOpen: !state.isRightPanelOpen })),
  setRightPanelMinimized: (minimized) => set({ isRightPanelMinimized: minimized }),
  setCameraPreset: (preset) => set({ cameraPreset: preset }),
  setIsDraggingAgent: (dragging) => set({ isDraggingAgent: dragging }),
  setSelectedAgent: (id) => set({ selectedAgentId: id }),
  setSelectedDepartment: (dept) => set({ selectedDepartment: dept }),

  setAgentStatus: (agentId, animation, statusBadge) =>
    set((state) => patchAgent(state, agentId, { animation, statusBadge })),

  setAgentMovement: (agentId, toNode, slotId = null) =>
    set((state) =>
      patchAgent(state, agentId, {
        targetWaypoint: toNode,
        // Kept in step with the target so the store stays coherent. Live
        // positions are not mirrored here on purpose: writing them would mean
        // a store update, and therefore a React render, on every frame.
        currentWaypoint: toNode,
        animation: 'Walk',
        slotId,
        // An authoritative move supersedes any manual drag.
        customPosition: null,
        // Walking through the door is the visual for leaving.
        isPresent: toNode !== 'exit',
      }),
    ),

  setAgentPosition: (agentId, position) =>
    set((state) => patchAgent(state, agentId, { customPosition: position })),

  setAgentWaiting: (agentId, wait) =>
    set((state) => patchAgent(state, agentId, { waitState: wait })),

  setAgentAbsence: (agentId, absence) =>
    set((state) =>
      patchAgent(state, agentId, {
        absence,
        // Clearing an absence brings them back through the door.
        isPresent: absence ? false : true,
      }),
    ),

  setAgentPresent: (agentId, present) =>
    set((state) => patchAgent(state, agentId, { isPresent: present })),

  setWorkforcePresent: (present) =>
    set((state) => ({
      agents: Object.fromEntries(
        Object.entries(state.agents).map(([id, agent]) => [
          id,
          { ...agent, isPresent: present },
        ]),
      ),
    })),

  appendTerminalLog: (stream, chunk) =>
    set((state) => {
      terminalLogSequence += 1;
      const next = [
        ...state.terminalLogs,
        { id: `log-${terminalLogSequence}`, stream, chunk, timestamp: Date.now() },
      ];
      return {
        terminalLogs:
          next.length > TERMINAL_LOG_LIMIT ? next.slice(next.length - TERMINAL_LOG_LIMIT) : next,
      };
    }),

  clearTerminalLogs: () => set({ terminalLogs: [] }),

  openGate: (gate) =>
    set((state) => ({
      gate: {
        ...EMPTY_GATE,
        ...gate,
        redStatus: gate.redStatus ?? state.redStatus,
        isOpen: true,
      },
    })),

  setGateSubmitting: (submitting) =>
    set((state) => ({ gate: { ...state.gate, isSubmitting: submitting } })),

  setGateError: (error) =>
    set((state) => ({ gate: { ...state.gate, error, isSubmitting: false } })),

  closeGate: () => set({ gate: EMPTY_GATE }),

  openDelivery: (delivery) =>
    set({ delivery: { ...EMPTY_DELIVERY, ...delivery, isOpen: true } }),

  closeDelivery: () => set({ delivery: EMPTY_DELIVERY }),

  setObjective: (objective) => set({ currentObjective: objective }),

  setRunning: (running, threadId, runToken) =>
    set((state) => ({
      isRunning: running,
      activeThreadId: running ? threadId ?? state.activeThreadId : null,
      // Keep the token after a run finishes so the ZIP stays downloadable.
      runToken: runToken !== undefined ? runToken : state.runToken,
    })),

  setProviderHealth: (providerHealth) => set({ providerHealth }),
  setConnected: (isConnected) => set({ isConnected }),
  setLastError: (lastError) => set({ lastError }),
  setRedStatus: (redStatus) =>
    set((state) => ({ redStatus, gate: { ...state.gate, redStatus } })),

  setOfficeClock: (officeClock) => set({ officeClock }),

  tickLocalClock: () =>
    set((state) => {
      const { phase, dayNumber, secondsRemaining } = state.officeClock;
      const nextRemaining = Math.max(0, secondsRemaining - 1);

      // The server publishes authoritative time every few seconds; this only
      // interpolates between those so the display does not appear frozen.
      const WORKDAY_SECS = 1200;
      const WORKDAY_SIM_MINUTES = 480;

      let displayTime = state.officeClock.displayTime;
      if (phase === 'WORKDAY') {
        const elapsed = Math.max(0, WORKDAY_SECS - nextRemaining);
        const simMinutes = Math.min(
          WORKDAY_SIM_MINUTES,
          Math.floor((elapsed / WORKDAY_SECS) * WORKDAY_SIM_MINUTES),
        );
        const total = 9 * 60 + simMinutes;
        displayTime = `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(
          total % 60,
        ).padStart(2, '0')}`;
      } else {
        displayTime = '17:00';
      }

      return {
        officeClock: { phase, dayNumber, secondsRemaining: nextRemaining, displayTime },
      };
    }),
}));
