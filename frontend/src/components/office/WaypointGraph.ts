import type { Waypoint } from '../../types/office';
import {
  AGENT_RADIUS,
  DESTINATIONS,
  isInsideObstacle,
  resolveDestinationId,
  resolveSlot,
} from './OfficeGeometry';

/**
 * Routing over the named destinations declared in `OfficeGeometry`.
 *
 * Coordinates are no longer duplicated here: this module derives everything
 * from the geometry module, which is what removed the class of bug where
 * `whiteboard` and `whiteboard_researcher` were the same point and two agents
 * sent to "different" places ended up inside each other.
 *
 * Paths are post-processed with a string-pulling pass, so agents cut corners
 * naturally instead of visibly touching each corridor node in turn.
 */

export interface PathPoint {
  x: number;
  z: number;
  id: string;
}

/** Compatibility view for anything still expecting a flat waypoint table. */
export const OFFICE_WAYPOINTS: Record<string, Waypoint> = Object.fromEntries(
  Object.values(DESTINATIONS).map((destination) => [
    destination.id,
    {
      id: destination.id,
      name: destination.name,
      x: destination.slots[0].x,
      z: destination.slots[0].z,
      capacity: destination.slots.length,
      facing: destination.slots[0].facing,
      neighbors: destination.neighbors,
    },
  ]),
);

const distance = (ax: number, az: number, bx: number, bz: number) =>
  Math.hypot(bx - ax, bz - az);

/** Whether a straight line between two points stays clear of furniture. */
const hasClearLine = (
  ax: number,
  az: number,
  bx: number,
  bz: number,
  radius = AGENT_RADIUS,
): boolean => {
  const span = distance(ax, az, bx, bz);
  const steps = Math.max(2, Math.ceil(span / 0.25));
  for (let step = 0; step <= steps; step += 1) {
    const t = step / steps;
    if (isInsideObstacle(ax + (bx - ax) * t, az + (bz - az) * t, radius)) {
      return false;
    }
  }
  return true;
};

export class WaypointGraph {
  private nodes = DESTINATIONS;

  findNearestWaypoint(x: number, z: number): string {
    let closest = 'corridor_center';
    let best = Infinity;

    for (const destination of Object.values(this.nodes)) {
      // Only consider routing nodes and destinations, using their first slot
      // as the representative position.
      const slot = destination.slots[0];
      const span = distance(x, z, slot.x, slot.z);
      if (span < best) {
        best = span;
        closest = destination.id;
      }
    }
    return closest;
  }

  /** A* over the destination graph. Returns node ids. */
  private findNodePath(startId: string, goalId: string): string[] {
    const start = resolveDestinationId(startId);
    const goal = resolveDestinationId(goalId);

    if (start === goal) return [start];
    if (!this.nodes[start] || !this.nodes[goal]) return [];

    const goalSlot = this.nodes[goal].slots[0];
    const heuristic = (id: string) => {
      const slot = this.nodes[id].slots[0];
      return distance(slot.x, slot.z, goalSlot.x, goalSlot.z);
    };

    const cameFrom = new Map<string, string | null>([[start, null]]);
    const costSoFar = new Map<string, number>([[start, 0]]);
    const frontier: { id: string; priority: number }[] = [
      { id: start, priority: heuristic(start) },
    ];

    while (frontier.length > 0) {
      frontier.sort((a, b) => a.priority - b.priority);
      const current = frontier.shift()!.id;
      if (current === goal) break;

      const currentSlot = this.nodes[current].slots[0];
      for (const nextId of this.nodes[current].neighbors) {
        const next = this.nodes[nextId];
        if (!next) continue;

        const nextSlot = next.slots[0];
        const cost =
          (costSoFar.get(current) ?? 0) +
          distance(currentSlot.x, currentSlot.z, nextSlot.x, nextSlot.z);

        if (!costSoFar.has(nextId) || cost < costSoFar.get(nextId)!) {
          costSoFar.set(nextId, cost);
          cameFrom.set(nextId, current);
          frontier.push({ id: nextId, priority: cost + heuristic(nextId) });
        }
      }
    }

    if (!cameFrom.has(goal)) return [];

    const path: string[] = [];
    let cursor: string | null = goal;
    while (cursor) {
      path.unshift(cursor);
      cursor = cameFrom.get(cursor) ?? null;
    }
    return path[0] === start ? path : [];
  }

  /**
   * Route from a live position to a destination slot, then smooth the result.
   *
   * Smoothing is what stops movement reading as rail-following: any node that
   * can be skipped with an unobstructed straight line is dropped.
   */
  findPath(
    fromX: number,
    fromZ: number,
    goalId: string,
    slotId?: string | null,
  ): PathPoint[] {
    const goal = resolveDestinationId(goalId);
    const goalSlot = resolveSlot(goal, slotId);

    // Short circuit: if the destination is directly visible, walk straight to it.
    if (hasClearLine(fromX, fromZ, goalSlot.x, goalSlot.z)) {
      return [{ x: goalSlot.x, z: goalSlot.z, id: goalSlot.id }];
    }

    const startId = this.findNearestWaypoint(fromX, fromZ);
    const nodeIds = this.findNodePath(startId, goal);

    if (nodeIds.length === 0) {
      // No route found. Head straight there rather than freezing; obstacle
      // resolution keeps the body out of furniture on the way.
      return [{ x: goalSlot.x, z: goalSlot.z, id: goalSlot.id }];
    }

    const points: PathPoint[] = nodeIds.map((id) => {
      const slot = id === goal ? goalSlot : this.nodes[id].slots[0];
      return { x: slot.x, z: slot.z, id: slot.id };
    });

    // String pulling: keep only the corners that are actually required.
    const smoothed: PathPoint[] = [];
    let cursorX = fromX;
    let cursorZ = fromZ;
    let index = 0;

    while (index < points.length) {
      let furthest = index;
      for (let candidate = points.length - 1; candidate > index; candidate -= 1) {
        if (hasClearLine(cursorX, cursorZ, points[candidate].x, points[candidate].z)) {
          furthest = candidate;
          break;
        }
      }
      const chosen = points[furthest];
      smoothed.push(chosen);
      cursorX = chosen.x;
      cursorZ = chosen.z;
      index = furthest + 1;
    }

    return smoothed.length > 0 ? smoothed : points;
  }
}

export const defaultGraph = new WaypointGraph();
