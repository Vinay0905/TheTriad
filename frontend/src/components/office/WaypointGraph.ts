import { Waypoint } from '../../types/office';

export const OFFICE_WAYPOINTS: Record<string, Waypoint> = {
  desk_manager: {
    id: 'desk_manager',
    name: "David's Desk (Manager)",
    x: 0.0,
    z: -2.5,
    neighbors: ['hallway_north', 'whiteboard'],
  },
  desk_researcher: {
    id: 'desk_researcher',
    name: "Elena's Pod (Researcher)",
    x: -3.5,
    z: -1.0,
    neighbors: ['hallway_west'],
  },
  desk_developer: {
    id: 'desk_developer',
    name: "Alex's Desk (Developer)",
    x: 3.5,
    z: -1.0,
    neighbors: ['hallway_east', 'desk_qa'],
  },
  desk_qa: {
    id: 'desk_qa',
    name: "Maya's Pod (QA Auditor)",
    x: 3.5,
    z: 1.5,
    neighbors: ['desk_developer', 'hallway_east'],
  },
  whiteboard: {
    id: 'whiteboard',
    name: 'Architecture Whiteboard',
    x: 0.0,
    z: -5.0,
    neighbors: ['desk_manager', 'hallway_north'],
  },
  coffee_lounge: {
    id: 'coffee_lounge',
    name: 'Break Lounge & Coffee Bar',
    x: -3.5,
    z: 3.0,
    neighbors: ['hallway_south', 'hallway_west'],
  },
  hallway_center: {
    id: 'hallway_center',
    name: 'Central Aisle',
    x: 0.0,
    z: 0.0,
    neighbors: ['hallway_north', 'hallway_south', 'hallway_west', 'hallway_east'],
  },
  hallway_north: {
    id: 'hallway_north',
    name: 'North Aisle',
    x: 0.0,
    z: -3.0,
    neighbors: ['hallway_center', 'desk_manager', 'whiteboard'],
  },
  hallway_south: {
    id: 'hallway_south',
    name: 'South Aisle',
    x: 0.0,
    z: 2.5,
    neighbors: ['hallway_center', 'coffee_lounge'],
  },
  hallway_west: {
    id: 'hallway_west',
    name: 'West Aisle',
    x: -2.0,
    z: 0.0,
    neighbors: ['hallway_center', 'desk_researcher', 'coffee_lounge'],
  },
  hallway_east: {
    id: 'hallway_east',
    name: 'East Aisle',
    x: 2.0,
    z: 0.0,
    neighbors: ['hallway_center', 'desk_developer', 'desk_qa'],
  },
};

export class WaypointGraph {
  private waypoints: Record<string, Waypoint>;

  constructor(waypoints = OFFICE_WAYPOINTS) {
    this.waypoints = waypoints;
  }

  findPath(startId: string, goalId: string): Waypoint[] {
    if (!this.waypoints[startId] || !this.waypoints[goalId]) return [];
    if (startId === goalId) return [this.waypoints[startId]];

    const cameFrom = new Map<string, string | null>();
    cameFrom.set(startId, null);

    const costSoFar = new Map<string, number>();
    costSoFar.set(startId, 0);

    const heuristic = (a: Waypoint, b: Waypoint) =>
      Math.hypot(b.x - a.x, b.z - a.z);

    const priorityQueue = [{ id: startId, priority: 0 }];

    while (priorityQueue.length > 0) {
      priorityQueue.sort((a, b) => a.priority - b.priority);
      const current = priorityQueue.shift()!.id;

      if (current === goalId) break;

      const currentNode = this.waypoints[current];

      for (const nextId of currentNode.neighbors) {
        const nextNode = this.waypoints[nextId];
        if (!nextNode) continue;

        const newCost = (costSoFar.get(current) ?? 0) + heuristic(currentNode, nextNode);

        if (!costSoFar.has(nextId) || newCost < costSoFar.get(nextId)!) {
          costSoFar.set(nextId, newCost);
          const priority = newCost + heuristic(nextNode, this.waypoints[goalId]);
          priorityQueue.push({ id: nextId, priority });
          cameFrom.set(nextId, current);
        }
      }
    }

    const path: Waypoint[] = [];
    let curr: string | null = goalId;
    while (curr) {
      const wp = this.waypoints[curr];
      if (!wp) break;
      path.unshift(wp);
      curr = cameFrom.get(curr) ?? null;
    }
    return path;
  }
}

export const defaultGraph = new WaypointGraph();
