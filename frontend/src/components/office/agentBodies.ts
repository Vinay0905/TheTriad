/**
 * A frame-local registry of where every agent body currently is.
 *
 * Agents previously moved in straight lines with no awareness of each other,
 * so two colleagues routed through the same corridor walked through one
 * another. Each character publishes its position here every frame and reads
 * its neighbours back, which is enough for mutual separation. With four
 * bodies the naive all-pairs scan is free.
 *
 * This is deliberately module-level mutable state rather than React state:
 * it is read and written inside the render loop, and putting it in the store
 * would trigger a re-render per frame.
 */

export interface BodyState {
  x: number;
  z: number;
  /** Current speed. Kept so avoidance can be tuned against real motion. */
  speed: number;
}

const bodies = new Map<string, BodyState>();

export const publishBody = (id: string, state: BodyState): void => {
  bodies.set(id, state);
};

export const removeBody = (id: string): void => {
  bodies.delete(id);
};

export const forEachOtherBody = (
  selfId: string,
  visit: (id: string, state: BodyState) => void,
): void => {
  for (const [id, state] of bodies) {
    if (id !== selfId) visit(id, state);
  }
};
