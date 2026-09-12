import { create } from 'zustand';
import { Agent, AgentAnimation, GateState, TerminalLog, ProjectDelivery, CameraPreset } from '../types/office';

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
  
  // Dynamic Panel States
  isLeftPanelOpen: boolean;
  isLeftPanelMinimized: boolean;
  isRightPanelOpen: boolean;
  isRightPanelMinimized: boolean;
  isDraggingAgent: boolean;
  cameraPreset: CameraPreset;
  ambientCirculation: boolean;

  // Actions
  toggleLeftPanel: () => void;
  setLeftPanelMinimized: (minimized: boolean) => void;
  toggleRightPanel: () => void;
  setRightPanelMinimized: (minimized: boolean) => void;
  setCameraPreset: (preset: CameraPreset) => void;
  toggleAmbientCirculation: () => void;
  setIsDraggingAgent: (dragging: boolean) => void;
  setSelectedAgent: (id: string | null) => void;
  setSelectedDepartment: (dept: string | null) => void;
  setAgentStatus: (agentId: string, animation: AgentAnimation, statusBadge: string) => void;
  setAgentMovement: (agentId: string, toNode: string) => void;
  setAgentPosition: (agentId: string, position: [number, number, number]) => void;
  appendTerminalLog: (stream: 'stdout' | 'stderr', chunk: string) => void;
  clearTerminalLogs: () => void;
  openGate: (threadId: string, task: string, codePreview: string, qaReport: string, digest: string) => void;
  closeGate: () => void;
  openDelivery: (threadId: string, success: boolean, summary: string) => void;
  closeDelivery: () => void;
  setObjective: (objective: string) => void;
  setRunning: (running: boolean, threadId?: string) => void;
}

export const useOfficeStore = create<OfficeState>((set) => ({
  agents: {
    manager: {
      id: 'manager',
      nodeId: 'NODE #01',
      name: 'David',
      role: 'Engineering Director',
      department: 'Management',
      model: 'OpenRouter (Claude 3.5 Sonnet)',
      currentWaypoint: 'desk_david',
      targetWaypoint: 'desk_david',
      animation: 'Sit',
      statusBadge: 'Awaiting Objective',
      color: '#e3c198', // Nordic Secondary Amber
      avatarIcon: '🧑💼',
      directive: 'Supervise sprint burn rate, manage dependencies across subgraphs, and enforce human confirmation gates.',
      contextBudget: '98,200 / 200k',
      speed: '62.1 tok/s',
      cost: '$5.18',
    },
    researcher: {
      id: 'researcher',
      nodeId: 'NODE #02',
      name: 'Elena',
      role: 'Staff AI Researcher',
      department: 'Research',
      model: 'Groq (openai/gpt-oss-120b)',
      currentWaypoint: 'desk_elena',
      targetWaypoint: 'desk_elena',
      animation: 'Sit',
      statusBadge: 'Standing By',
      color: '#d0bcff', // Nordic Tertiary Lavender
      avatarIcon: '👩🔬',
      directive: 'Formulate mathematical proofs for vector clustering, measure p99 embedding latency, and synthesize empirical benchmarks.',
      contextBudget: '185,410 / 200k',
      speed: '44.8 tok/s',
      cost: '$2.80',
    },
    developer: {
      id: 'developer',
      nodeId: 'NODE #03',
      name: 'Alex',
      role: 'Staff Systems Architect',
      department: 'Engineering',
      model: 'Groq (Llama 3.3 70B)',
      currentWaypoint: 'desk_alex',
      targetWaypoint: 'desk_alex',
      animation: 'Sit',
      statusBadge: 'Standing By',
      color: '#4cd7f6', // Nordic Primary Neon Cyan
      avatarIcon: '🧑💻',
      directive: 'Zero-copy concurrency rules. Avoid mutex contention; prioritize atomic crossbeam ring buffer.',
      contextBudget: '142,890 / 200k',
      speed: '78.4 tok/s',
      cost: '$3.42',
    },
    qa: {
      id: 'qa',
      nodeId: 'NODE #04',
      name: 'Maya',
      role: 'Staff QA & Security Auditor',
      department: 'Quality Assurance',
      model: 'ZhipuAI GLM-4.7-Flash (Free)',
      currentWaypoint: 'desk_maya',
      targetWaypoint: 'desk_maya',
      animation: 'Sit',
      statusBadge: 'Standing By',
      color: '#10b981', // Emerald Security Green
      avatarIcon: '👩💻',
      directive: 'Perform fuzz testing against gRPC boundaries, inspect memory allocators for leaks, and prevent unvetted dependencies.',
      contextBudget: '64,120 / 200k',
      speed: '91.0 tok/s',
      cost: '$1.45',
    },
  },
  selectedAgentId: 'developer', // Default focus on Alex as in Stitch design
  selectedDepartment: null,
  terminalLogs: [],
  gate: {
    isOpen: false,
    threadId: null,
    task: '',
    codePreview: '',
    qaReport: '',
    digest: '',
  },
  delivery: {
    isOpen: false,
    threadId: '',
    success: true,
    summary: '',
  },
  currentObjective: '',
  isRunning: false,
  activeThreadId: null,

  // Panel States
  isLeftPanelOpen: true,
  isLeftPanelMinimized: false,
  isRightPanelOpen: true,
  isRightPanelMinimized: false,
  isDraggingAgent: false,
  cameraPreset: 'room',
  ambientCirculation: true,

  toggleLeftPanel: () => set((state) => ({ isLeftPanelOpen: !state.isLeftPanelOpen })),
  setLeftPanelMinimized: (minimized) => set({ isLeftPanelMinimized: minimized }),
  toggleRightPanel: () => set((state) => ({ isRightPanelOpen: !state.isRightPanelOpen })),
  setRightPanelMinimized: (minimized) => set({ isRightPanelMinimized: minimized }),
  setCameraPreset: (preset) => set({ cameraPreset: preset }),
  toggleAmbientCirculation: () => set((state) => ({ ambientCirculation: !state.ambientCirculation })),
  setIsDraggingAgent: (dragging) => set({ isDraggingAgent: dragging }),
  toggleSidebar: () => set((state) => ({ isLeftPanelOpen: !state.isLeftPanelOpen })),
  setSidebarCollapsed: (collapsed: boolean) => set({ isLeftPanelMinimized: collapsed }),

  setSelectedAgent: (id) => set({ selectedAgentId: id }),
  setSelectedDepartment: (dept) => set({ selectedDepartment: dept }),

  setAgentStatus: (agentId, animation, statusBadge) =>
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;
      return {
        agents: {
          ...state.agents,
          [agentId]: { ...agent, animation, statusBadge },
        },
      };
    }),

  setAgentMovement: (agentId, toNode) =>
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;
      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            targetWaypoint: toNode,
            animation: 'Walk',
            customPosition: null, // Clear manual drag position when autonomous movement begins
          },
        },
      };
    }),

  setAgentPosition: (agentId, position) =>
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;
      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            customPosition: position,
          },
        },
      };
    }),

  appendTerminalLog: (stream, chunk) =>
    set((state) => ({
      terminalLogs: [
        ...state.terminalLogs,
        {
          id: Math.random().toString(36).substring(2, 9),
          stream,
          chunk,
          timestamp: Date.now(),
        },
      ],
    })),

  clearTerminalLogs: () => set({ terminalLogs: [] }),

  openGate: (threadId, task, codePreview, qaReport, digest) =>
    set({
      gate: {
        isOpen: true,
        threadId,
        task,
        codePreview,
        qaReport,
        digest,
      },
    }),

  closeGate: () =>
    set({
      gate: {
        isOpen: false,
        threadId: null,
        task: '',
        codePreview: '',
        qaReport: '',
        digest: '',
      },
    }),

  openDelivery: (threadId, success, summary) =>
    set({
      delivery: {
        isOpen: true,
        threadId,
        success,
        summary,
      },
    }),

  closeDelivery: () =>
    set({
      delivery: {
        isOpen: false,
        threadId: '',
        success: true,
        summary: '',
      },
    }),

  setObjective: (objective) => set({ currentObjective: objective }),
  setRunning: (running, threadId) =>
    set({ isRunning: running, activeThreadId: threadId || null }),
}));
