import { useEffect, useRef, type FC } from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';

type Routine = {
  agentId: 'manager' | 'researcher' | 'developer' | 'qa';
  destination: 'pantry' | 'whiteboard' | 'meeting';
  travelStatus: string;
  activityStatus: string;
  activityAnimation: 'Sit' | 'Type' | 'Coffee';
  dwellMs: number;
};

const HOME_DESKS: Record<Routine['agentId'], string> = {
  manager: 'desk_david',
  researcher: 'desk_elena',
  developer: 'desk_alex',
  qa: 'desk_maya',
};

// A coordinated rhythm reads as colleagues sharing an office. It deliberately
// avoids competing random timers and pauses immediately for real work.
const OFFICE_RHYTHM: Routine[] = [
  { agentId: 'researcher', destination: 'whiteboard', travelStatus: 'Checking the shared research board...', activityStatus: 'Comparing notes at the whiteboard...', activityAnimation: 'Type', dwellMs: 4200 },
  { agentId: 'developer', destination: 'pantry', travelStatus: 'Taking a short coffee reset...', activityStatus: 'Coffee break — available for hand-off.', activityAnimation: 'Coffee', dwellMs: 3600 },
  { agentId: 'qa', destination: 'meeting', travelStatus: 'Reviewing the test plan at the meeting table...', activityStatus: 'Organising edge cases and test notes...', activityAnimation: 'Type', dwellMs: 4400 },
  { agentId: 'manager', destination: 'whiteboard', travelStatus: 'Reviewing the team board...', activityStatus: 'Preparing the next team check-in...', activityAnimation: 'Sit', dwellMs: 4000 },
];

const TRAVEL_MS = 3800;
const BETWEEN_ROUTINES_MS = 7500;
const wait = (ms: number) => new Promise<void>((resolve) => window.setTimeout(resolve, ms));

/** Coordinates background office life; live workflow events take precedence. */
export const OfficeLife: FC = () => {
  const ambientCirculation = useOfficeStore((state) => state.ambientCirculation);
  const isRunning = useOfficeStore((state) => state.isRunning);
  const routineIndex = useRef(0);

  useEffect(() => {
    if (!ambientCirculation || isRunning) return;

    let cancelled = false;
    const shouldContinue = () => {
      const state = useOfficeStore.getState();
      return !cancelled && state.ambientCirculation && !state.isRunning;
    };

    const runRoutine = async () => {
      await wait(1800);
      while (shouldContinue()) {
        const routine = OFFICE_RHYTHM[routineIndex.current % OFFICE_RHYTHM.length];
        routineIndex.current += 1;

        useOfficeStore.getState().setAgentStatus(routine.agentId, 'Walk', routine.travelStatus);
        useOfficeStore.getState().setAgentMovement(routine.agentId, routine.destination);
        await wait(TRAVEL_MS);
        if (!shouldContinue()) break;

        useOfficeStore.getState().setAgentStatus(routine.agentId, routine.activityAnimation, routine.activityStatus);
        await wait(routine.dwellMs);
        if (!shouldContinue()) break;

        useOfficeStore.getState().setAgentStatus(routine.agentId, 'Walk', 'Heading back to their workstation...');
        useOfficeStore.getState().setAgentMovement(routine.agentId, HOME_DESKS[routine.agentId]);
        await wait(TRAVEL_MS);
        if (!shouldContinue()) break;

        useOfficeStore.getState().setAgentStatus(routine.agentId, 'Sit', 'Standing By');
        await wait(BETWEEN_ROUTINES_MS);
      }
    };

    void runRoutine();
    return () => {
      cancelled = true;
      const state = useOfficeStore.getState();
      if (state.isRunning) {
        // Return any wandering agent to their home desk when a live run begins
        for (const [id, ag] of Object.entries(state.agents)) {
          const homeDesk = HOME_DESKS[id as Routine['agentId']];
          if (homeDesk && ag.targetWaypoint !== homeDesk && !ag.targetWaypoint.startsWith('desk_')) {
            useOfficeStore.getState().setAgentMovement(id, homeDesk);
            useOfficeStore.getState().setAgentStatus(id, 'Walk', 'Returning to workstation for run...');
          }
        }
      }
    };
  }, [ambientCirculation, isRunning]);

  return null;
};
