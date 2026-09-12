export type AgentAnimation = 'Idle' | 'Walk' | 'Sit' | 'Type' | 'Coffee';

export type CameraPreset = 'room' | 'pantry' | 'desks' | 'whiteboard' | 'meeting';

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
  contextBudget?: string;
  speed?: string;
  cost?: string;
  customPosition?: [number, number, number] | null;
  isPresent?: boolean;
}

export interface OfficeClock {
  phase: 'WORKDAY' | 'OFF_HOURS';
  displayTime: string;
  dayNumber: number;
  secondsRemaining: number;
}

export interface Waypoint {
  id: string;
  name: string;
  x: number;
  z: number;
  neighbors: string[];
}

export interface GateState {
  isOpen: boolean;
  threadId: string | null;
  task: string;
  codePreview: string;
  qaReport: string;
  digest: string;
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
}
