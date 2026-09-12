import { Waypoint } from '../../types/office';

// ============================================================================
// Strictly Collision-Free Waypoint Graph
// Geometry bounds:
// - North Pod (David & Elena desks): x in [-2.5, 2.5], z in [-2.6, -1.0]
// - South Pod (Alex & Maya desks): x in [-2.5, 2.5], z in [1.0, 2.6]
// - Pantry & Coffee Bar: x in [-6.5, -3.5], z in [2.6, 5.5]
// - Meeting Table: x in [3.2, 6.0], z in [2.4, 5.2]
// - Whiteboard: x in [-3.0, 3.0], z in [-7.0, -5.8]
//
// All navigation corridors run exclusively along wide open 2m+ floor lanes:
// - Central Grand Runway: z = 0 (between Pod 1 & Pod 2)
// - West Corridor: x = -2.8 (between Pods and Pantry)
// - East Corridor: x = 2.8 (between Pods and Meeting Table)
// - North Runway: z = -4.0 (between North Pod and Whiteboard)
// - South Runway: z = 4.2 (open circulation behind Pod 2)
// ============================================================================

export const OFFICE_WAYPOINTS: Record<string, Waypoint> = {
  // 1. Workstation Desk Slots (Squarely inside chair footprint facing screens)
  desk_david: {
    id: 'desk_david',
    name: "David's Desk (North Pod L)",
    x: -1.2,
    z: -1.15,
    neighbors: ['corridor_center', 'aisle_north_west'],
  },
  desk_elena: {
    id: 'desk_elena',
    name: "Elena's Desk (North Pod R)",
    x: 1.2,
    z: -1.15,
    neighbors: ['corridor_center', 'aisle_north_east'],
  },
  desk_alex: {
    id: 'desk_alex',
    name: "Alex's Desk (South Pod L)",
    x: -1.2,
    z: 2.45,
    neighbors: ['aisle_south_west', 'corridor_south'],
  },
  desk_maya: {
    id: 'desk_maya',
    name: "Maya's Desk (South Pod R)",
    x: 1.2,
    z: 2.45,
    neighbors: ['aisle_south_east', 'corridor_south'],
  },

  // Backwards compatibility mappings
  desk_manager: {
    id: 'desk_manager',
    name: "David's Desk",
    x: -1.2,
    z: -1.15,
    neighbors: ['corridor_center', 'aisle_north_west'],
  },
  desk_researcher: {
    id: 'desk_researcher',
    name: "Elena's Desk",
    x: 1.2,
    z: -1.15,
    neighbors: ['corridor_center', 'aisle_north_east'],
  },
  desk_developer: {
    id: 'desk_developer',
    name: "Alex's Desk",
    x: -1.2,
    z: 2.45,
    neighbors: ['aisle_south_west', 'corridor_south'],
  },
  desk_qa: {
    id: 'desk_qa',
    name: "Maya's Desk",
    x: 1.2,
    z: 2.45,
    neighbors: ['aisle_south_east', 'corridor_south'],
  },

  // 2. Main Room Destination Zones (Open floor standing areas, never inside furniture)
  pantry: {
    id: 'pantry',
    name: 'Espresso Bar & Pantry',
    x: -4.8,
    z: 1.8, // Clear open aisle in front of espresso bar counter
    neighbors: ['aisle_south_west', 'corridor_west'],
  },
  coffee_lounge: {
    id: 'coffee_lounge',
    name: 'Espresso Bar & Pantry',
    x: -4.8,
    z: 1.8,
    neighbors: ['aisle_south_west', 'corridor_west'],
  },
  whiteboard: {
    id: 'whiteboard',
    name: 'Architecture Whiteboard (Center)',
    x: 0.0,
    z: -5.4, // Open aisle in front of whiteboard wall
    neighbors: ['corridor_north', 'whiteboard_manager', 'whiteboard_qa'],
  },
  whiteboard_manager: {
    id: 'whiteboard_manager',
    name: 'Architecture Whiteboard (Manager Station L)',
    x: -1.4,
    z: -5.4,
    neighbors: ['corridor_north', 'whiteboard'],
  },
  whiteboard_qa: {
    id: 'whiteboard_qa',
    name: 'Architecture Whiteboard (QA Station R)',
    x: 1.4,
    z: -5.4,
    neighbors: ['corridor_north', 'whiteboard'],
  },
  whiteboard_researcher: {
    id: 'whiteboard_researcher',
    name: 'Architecture Whiteboard (Researcher Presenter)',
    x: 0.0,
    z: -5.4,
    neighbors: ['corridor_north', 'whiteboard'],
  },
  desk_alex_review: {
    id: 'desk_alex_review',
    name: "Alex's Desk (Peer Review Slot)",
    x: -0.35,
    z: 2.45,
    neighbors: ['corridor_south', 'aisle_south_west'],
  },
  meeting: {
    id: 'meeting',
    name: 'Nordic Meeting Table',
    x: 3.3, // West chair slot of meeting table in open space (NOT inside tabletop)
    z: 3.4,
    neighbors: ['aisle_south_east', 'corridor_east'],
  },
  boss_foyer: {
    id: 'boss_foyer',
    name: 'BOSS Room Foyer',
    x: 5.85,
    z: -3.8,
    neighbors: ['corridor_north', 'boss_room'],
  },
  boss_room: {
    id: 'boss_room',
    name: 'BOSS Room',
    x: 5.55,
    z: -5.25,
    neighbors: ['boss_foyer'],
  },

  // 3. Clear Open-Floor Arteries (Zero equipment collision)
  corridor_center: {
    id: 'corridor_center',
    name: 'Central Grand Runway',
    x: 0.0,
    z: 0.0,
    neighbors: [
      'desk_david',
      'desk_manager',
      'desk_elena',
      'desk_researcher',
      'corridor_west',
      'corridor_east',
    ],
  },
  corridor_west: {
    id: 'corridor_west',
    name: 'West Studio Aisle',
    x: -2.9,
    z: 0.0,
    neighbors: ['corridor_center', 'aisle_north_west', 'aisle_south_west', 'pantry', 'coffee_lounge'],
  },
  corridor_east: {
    id: 'corridor_east',
    name: 'East Studio Aisle',
    x: 2.9,
    z: 0.0,
    neighbors: ['corridor_center', 'aisle_north_east', 'aisle_south_east', 'meeting'],
  },
  corridor_north: {
    id: 'corridor_north',
    name: 'North Gallery Aisle',
    x: 0.0,
    z: -3.8,
    neighbors: [
      'aisle_north_west',
      'aisle_north_east',
      'whiteboard',
      'whiteboard_manager',
      'whiteboard_qa',
      'whiteboard_researcher',
      'boss_foyer',
    ],
  },
  corridor_south: {
    id: 'corridor_south',
    name: 'South Circulation Aisle',
    x: 0.0,
    z: 2.45,
    neighbors: [
      'aisle_south_west',
      'aisle_south_east',
      'desk_alex',
      'desk_developer',
      'desk_alex_review',
      'desk_maya',
      'desk_qa',
    ],
  },
  aisle_north_west: {
    id: 'aisle_north_west',
    name: 'North-West Junction',
    x: -2.9,
    z: -3.8,
    neighbors: ['corridor_west', 'corridor_north', 'desk_david', 'desk_manager'],
  },
  aisle_north_east: {
    id: 'aisle_north_east',
    name: 'North-East Junction',
    x: 2.9,
    z: -3.8,
    neighbors: ['corridor_east', 'corridor_north', 'desk_elena', 'desk_researcher'],
  },
  aisle_south_west: {
    id: 'aisle_south_west',
    name: 'South-West Pantry Junction',
    x: -2.9,
    z: 1.8,
    neighbors: [
      'corridor_west',
      'pantry',
      'coffee_lounge',
      'corridor_south',
      'desk_alex',
      'desk_developer',
      'desk_alex_review',
    ],
  },
  aisle_south_east: {
    id: 'aisle_south_east',
    name: 'South-East Meeting Junction',
    x: 2.9,
    z: 1.8,
    neighbors: ['corridor_east', 'meeting', 'corridor_south', 'desk_maya', 'desk_qa'],
  },
};

export class WaypointGraph {
  private waypoints: Record<string, Waypoint>;

  constructor(waypoints = OFFICE_WAYPOINTS) {
    this.waypoints = waypoints;
  }

  findNearestWaypoint(x: number, z: number): string {
    let closestId = 'corridor_center';
    let minDistance = Infinity;
    for (const [id, wp] of Object.entries(this.waypoints)) {
      const dist = Math.hypot(wp.x - x, wp.z - z);
      if (dist < minDistance) {
        minDistance = dist;
        closestId = id;
      }
    }
    return closestId;
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
      if (!currentNode || !currentNode.neighbors) continue;

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

    if (!cameFrom.has(goalId)) return [];

    const path: Waypoint[] = [];
    let curr: string | null = goalId;
    while (curr) {
      const wp = this.waypoints[curr];
      if (!wp) break;
      path.unshift(wp);
      curr = cameFrom.get(curr) ?? null;
    }
    return path.length > 0 && path[0].id === startId ? path : [];
  }
}

export const defaultGraph = new WaypointGraph();
