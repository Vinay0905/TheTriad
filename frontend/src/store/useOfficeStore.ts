import { create } from 'zustand';
import { Agent, AgentAnimation, GateState, TerminalLog } from '../types/office';

interface OfficeState {
  agents: Record<string, Agent>;
  selectedAgentId: string | null;
  selectedDepartment: string | null;
  terminalLogs: TerminalLog[];
  gate: GateState;
  currentObjective: string;
  isRunning: boolean;
  activeThreadId: string | null;

  // Actions
  setSelectedAgent: (id: string | null) => void;
  setSelectedDepartment: (dept: string | null) => void;
  setAgentStatus: (agentId: string, animation: AgentAnimation, statusBadge: string) => void;
  setAgentMovement: (agentId: string, toNode: string) => void;
  appendTerminalLog: (stream: 'stdout' | 'stderr', chunk: string) => void;
  clearTerminalLogs: () => void;
  openGate: (threadId: string, task: string, codePreview: string, qaReport: string, digest: string) => void;
  closeGate: () => void;
  setObjective: (objective: string) => void;
  setRunning: (running: boolean, threadId?: string) => void;
}

export const useOfficeStore = create<OfficeState>((set) => ({
  agents: {
    manager: {
      id: 'manager',
      name: 'David',
      role: 'Engineering Manager',
      department: 'Management',
      model: 'OpenRouter (Claude 3.5 Sonnet)',
      currentWaypoint: 'desk_manager',
      targetWaypoint: 'desk_manager',
      animation: 'Sit',
      statusBadge: 'Awaiting Objective',
      color: '#f59e0b', // Amber
      avatarIcon: '🧑💼',
    },
    researcher: {
      id: 'researcher',
      name: 'Elena',
      role: 'Staff Researcher',
      department: 'Research',
      model: 'Gemini 2.5 Flash (Google Search)',
      currentWaypoint: 'desk_researcher',
      targetWaypoint: 'desk_researcher',
      animation: 'Sit',
      statusBadge: 'Standing By',
      color: '#3b82f6', // Blue
      avatarIcon: '👩🔬',
    },
    developer: {
      id: 'developer',
      name: 'Alex',
      role: 'Senior Developer',
      department: 'Engineering',
      model: 'Groq (Llama 3.3 70B)',
      currentWaypoint: 'desk_developer',
      targetWaypoint: 'desk_developer',
      animation: 'Sit',
      statusBadge: 'Standing By',
      color: '#10b981', // Emerald
      avatarIcon: '🧑💻',
    },
    qa: {
      id: 'qa',
      name: 'Maya',
      role: 'QA & Security Auditor',
      department: 'Quality Assurance',
      model: 'ZhipuAI GLM-4.7-Flash (Free)',
      currentWaypoint: 'desk_qa',
      targetWaypoint: 'desk_qa',
      animation: 'Sit',
      statusBadge: 'Standing By',
      color: '#a855f7', // Purple
      avatarIcon: '👩💻',
    },
  },
  selectedAgentId: null,
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
  currentObjective: '',
  isRunning: false,
  activeThreadId: null,

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

  setObjective: (objective) => set({ currentObjective: objective }),
  setRunning: (running, threadId) =>
    set({ isRunning: running, activeThreadId: threadId || null }),
}));
