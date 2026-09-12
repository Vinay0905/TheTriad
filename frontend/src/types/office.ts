export type AgentAnimation = 'Idle' | 'Walk' | 'Sit' | 'Type' | 'Coffee';

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
