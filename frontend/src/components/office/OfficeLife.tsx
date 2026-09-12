import { useEffect, useRef, type FC } from 'react';
import { useOfficeStore } from '../../store/useOfficeStore';

type Routine = {
  agentId: 'manager' | 'researcher' | 'developer' | 'qa';
  destination: 'pantry' | 'whiteboard' | 'meeting' | 'exit' | 'desk_alex_review';
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

// Each person has a recognizable, bounded habit. The sequence is deliberate:
// no two colleagues try to occupy the same shared space at once.
const OFFICE_RHYTHM: Routine[] = [
  { agentId: 'researcher', destination: 'whiteboard', travelStatus: 'Checking the shared research board...', activityStatus: 'Comparing notes at the whiteboard...', activityAnimation: 'Type', dwellMs: 4200 },
  { agentId: 'developer', destination: 'pantry', travelStatus: 'Taking a coffee reset...', activityStatus: 'Coffee in hand — available for a hand-off.', activityAnimation: 'Coffee', dwellMs: 4400 },
  { agentId: 'qa', destination: 'desk_alex_review', travelStatus: 'Heading over with one more QA concern...', activityStatus: 'Maya: Asking Alex about another edge case...', activityAnimation: 'Type', dwellMs: 4100 },
  { agentId: 'manager', destination: 'exit', travelStatus: 'Stepping outside for fresh air...', activityStatus: 'David: Out for air — reports will wait.', activityAnimation: 'Sit', dwellMs: 6000 },
  { agentId: 'developer', destination: 'pantry', travelStatus: 'Making a quick espresso...', activityStatus: 'Alex: Refuelling before the next implementation pass.', activityAnimation: 'Coffee', dwellMs: 3600 },
  { agentId: 'qa', destination: 'whiteboard', travelStatus: 'Taking test notes to the whiteboard...', activityStatus: 'Maya: Highlighting a suspicious edge case.', activityAnimation: 'Type', dwellMs: 3900 },
];

const TRAVEL_MS = 3800;
const BETWEEN_ROUTINES_MS = 7500;
const wait = (ms: number) => new Promise<void>((resolve) => window.setTimeout(resolve, ms));

/** Coordinates background office life; live workflow events take precedence. */
export const OfficeLife: FC = () => {
  const ambientCirculation = useOfficeStore((state) => state.ambientCirculation);
  const isRunning = useOfficeStore((state) => state.isRunning);
  const officePhase = useOfficeStore((state) => state.officeClock.phase);
  const routineIndex = useRef(0);

  useEffect(() => {
    if (!ambientCirculation || isRunning || officePhase !== 'WORKDAY') return;

    let cancelled = false;
    const shouldContinue = () => {
      const state = useOfficeStore.getState();
      return !cancelled && state.ambientCirculation && !state.isRunning && state.officeClock.phase === 'WORKDAY';
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

        // When stepping outside through exit, avatar and nameplate leave the room
        if (routine.destination === 'exit') {
          useOfficeStore.getState().setAgentPresent(routine.agentId, false);
        }

        useOfficeStore.getState().setAgentStatus(routine.agentId, routine.activityAnimation, routine.activityStatus);
        await wait(routine.dwellMs);
        if (!shouldContinue()) break;

        // Restore presence when coming back in through the door
        if (routine.destination === 'exit') {
          useOfficeStore.getState().setAgentPresent(routine.agentId, true);
        }

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
            useOfficeStore.getState().setAgentPresent(id, true);
            useOfficeStore.getState().setAgentMovement(id, homeDesk);
            useOfficeStore.getState().setAgentStatus(id, 'Walk', 'Returning to workstation for run...');
          }
        }
      }
    };
  }, [ambientCirculation, isRunning, officePhase]);

  return null;
};
