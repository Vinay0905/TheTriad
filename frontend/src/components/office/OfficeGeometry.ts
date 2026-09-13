/**
 * Single source of truth for office geometry.
 *
 * Previously furniture lived as ~180 hand-placed literals inside
 * `OfficeCanvas.tsx` while navigation coordinates lived independently in
 * `WaypointGraph.ts`. The waypoint file opened with the comment "Strictly
 * Collision-Free Waypoint Graph", but nothing enforced or even checked that,
 * and the two could drift apart silently. Several destinations had *identical*
 * coordinates, which guaranteed two agents would occupy the same point.
 *
 * Both the renderer and the navigation now derive from this module, so the
 * claim is checkable: see `findGeometryProblems()`.
 *
 * Coordinate system: Three.js world space, metres. +x east, +z south, y up.
 * The room spans roughly x [-8.4, 8.4], z [-8.0, 8.0].
 */

export interface Box {
  /** Centre on the x axis. */
  x: number;
  /** Centre on the z axis. */
  z: number;
  /** Full extent along x. */
  width: number;
  /** Full extent along z. */
  depth: number;
  label: string;
}

export interface DestinationSlot {
  id: string;
  x: number;
  z: number;
  /** Facing in radians, matching Math.atan2(dirX, dirZ). */
  facing: number;
}

export interface DestinationDef {
  id: string;
  name: string;
  /** Distinct standing positions. Length is the capacity. */
  slots: DestinationSlot[];
  /** Adjacent nodes for corridor routing. */
  neighbors: string[];
}

/** Half-width of an agent body, used for separation and obstacle clearance. */
export const AGENT_RADIUS = 0.22;

/** Minimum gap the navigation lanes must keep between obstacles. */
export const MIN_CORRIDOR_CLEARANCE = 1.2;

const snap = (value: number): number => Math.round(value * 10) / 10;

const box = (label: string, x: number, z: number, width: number, depth: number): Box => ({
  label,
  x: snap(x),
  z: snap(z),
  width: snap(width),
  depth: snap(depth),
});

// Facing helpers, so seat orientation is declared rather than guessed.
export const FACE_NORTH = Math.PI; // looking toward -z
export const FACE_SOUTH = 0; // looking toward +z
export const FACE_EAST = Math.PI / 2; // looking toward +x
export const FACE_WEST = -Math.PI / 2; // looking toward -x

// ---------------------------------------------------------------------------
// Furniture layout. The renderer positions props from these constants.
// ---------------------------------------------------------------------------

export const LAYOUT = {
  room: { width: 16.8, depth: 16.0 },
  northPod: { x: 0, z: -1.8, width: 4.4, depth: 1.4 },
  southPod: { x: 0, z: 1.8, width: 4.4, depth: 1.4 },
  pantry: { x: -4.8, z: 3.4, width: 3.0, depth: 1.6 },
  meetingTable: { x: 4.8, z: 3.4, radius: 1.55 },
  /** Group origin of the BOSS room; its props are placed relative to this. */
  bossRoom: { x: 5.6, z: -5.55 },
  door: { x: -7.4, z: 2.8 },
} as const;

/**
 * Solid volumes an agent body may not enter.
 *
 * These are derived from the same numbers the renderer uses. The BOSS room in
 * particular is a group at `[5.6, 0, -5.55]` whose partition, two wall
 * segments, desk and chair are positioned locally, so each is translated here
 * rather than approximated. The gap between the two south segments is the
 * doorway David actually walks through.
 */
export const OFFICE_OBSTACLES: Box[] = [
  box('north wall', 0, -8.0, 18.4, 0.3),
  // No wall is modelled on the south side of the room; this is the boundary
  // that stops a dragged body leaving the floor.
  box('south boundary', 0, 8.0, 18.4, 0.3),
  box('west wall', -8.4, 0, 0.3, 18.4),
  box('east wall', 8.4, 0, 0.3, 18.4),

  box('north bench desk', LAYOUT.northPod.x, LAYOUT.northPod.z, LAYOUT.northPod.width, LAYOUT.northPod.depth),
  box('south bench desk', LAYOUT.southPod.x, LAYOUT.southPod.z, LAYOUT.southPod.width, LAYOUT.southPod.depth),

  box('espresso counter', LAYOUT.pantry.x, LAYOUT.pantry.z, LAYOUT.pantry.width, LAYOUT.pantry.depth),
  box(
    'meeting table',
    LAYOUT.meetingTable.x,
    LAYOUT.meetingTable.z,
    LAYOUT.meetingTable.radius * 2,
    LAYOUT.meetingTable.radius * 2,
  ),

  // BOSS room, translated from group-local coordinates.
  box('boss west partition', LAYOUT.bossRoom.x - 2.22, LAYOUT.bossRoom.z, 0.08, 3.7),
  box('boss south wall west', LAYOUT.bossRoom.x - 1.2, LAYOUT.bossRoom.z + 1.82, 1.8, 0.08),
  box('boss south wall east', LAYOUT.bossRoom.x + 1.42, LAYOUT.bossRoom.z + 1.82, 1.25, 0.08),
  box('boss desk', LAYOUT.bossRoom.x + 0.55, LAYOUT.bossRoom.z - 0.62, 2.35, 0.92),
  box('boss guest chair', LAYOUT.bossRoom.x - 0.9, LAYOUT.bossRoom.z + 0.65, 0.62, 0.62),
];

// ---------------------------------------------------------------------------
// Destinations. Every slot is a distinct point, which is the structural fix
// for two agents merging into one body.
// ---------------------------------------------------------------------------

const single = (
  id: string,
  name: string,
  x: number,
  z: number,
  facing: number,
  neighbors: string[],
): DestinationDef => ({
  id,
  name,
  slots: [{ id: `${id}#0`, x: snap(x), z: snap(z), facing }],
  neighbors,
});

export const DESTINATIONS: Record<string, DestinationDef> = {
  // Desks. Seats sit just clear of the bench footprint, facing the monitors.
  desk_david: single('desk_david', "David's desk", -1.2, -0.8, FACE_NORTH, ['corridor_center', 'aisle_north_west']),
  desk_elena: single('desk_elena', "Elena's desk", 1.2, -0.8, FACE_NORTH, ['corridor_center', 'aisle_north_east']),
  desk_alex: single('desk_alex', "Alex's desk", -1.2, 0.8, FACE_SOUTH, ['corridor_center', 'aisle_south_west']),
  desk_maya: single('desk_maya', "Maya's desk", 1.2, 0.8, FACE_SOUTH, ['corridor_center', 'aisle_south_east']),

  // A distinct spot beside Alex, so a peer review does not overlap his chair.
  desk_alex_review: single(
    'desk_alex_review',
    "Beside Alex's desk",
    -2.0,
    0.8,
    FACE_EAST,
    ['aisle_south_west', 'corridor_center'],
  ),

  // Two people can use the espresso bar at once, shoulder to shoulder.
  pantry: {
    id: 'pantry',
    name: 'Espresso bar',
    slots: [
      { id: 'pantry#0', x: -5.4, z: 1.9, facing: FACE_SOUTH },
      { id: 'pantry#1', x: -4.2, z: 1.9, facing: FACE_SOUTH },
    ],
    neighbors: ['corridor_west', 'aisle_south_west'],
  },

  // Three separate whiteboard stations. These were previously all (0, -5.4).
  whiteboard_manager: single('whiteboard_manager', 'Whiteboard (manager)', -1.5, -7.2, FACE_NORTH, ['corridor_north']),
  whiteboard_researcher: single('whiteboard_researcher', 'Whiteboard (presenter)', 0, -7.2, FACE_NORTH, ['corridor_north']),
  whiteboard_qa: single('whiteboard_qa', 'Whiteboard (QA)', 1.5, -7.2, FACE_NORTH, ['corridor_north']),

  // Four seats around the table, each outside its radius.
  //
  // The seats are chained through ring nodes rather than all connected to the
  // northern junction. A direct edge from the junction to the west, east, or
  // south seat would cut straight across the tabletop.
  meeting_david: single('meeting_david', 'Meeting table (north)', 4.8, 1.5, FACE_SOUTH, ['aisle_south_east']),
  meeting_ring_west: single('meeting_ring_west', 'Beside the table (west)', 2.9, 1.5, FACE_SOUTH, [
    'aisle_south_east',
    'meeting_alex',
    'meeting_ring_south',
  ]),
  meeting_ring_east: single('meeting_ring_east', 'Beside the table (east)', 6.7, 1.5, FACE_SOUTH, [
    'aisle_south_east',
    'meeting_elena',
  ]),
  meeting_ring_south: single('meeting_ring_south', 'Beside the table (south)', 2.9, 5.3, FACE_EAST, [
    'meeting_ring_west',
    'meeting_maya',
  ]),
  meeting_alex: single('meeting_alex', 'Meeting table (west)', 2.9, 3.4, FACE_EAST, ['meeting_ring_west']),
  meeting_elena: single('meeting_elena', 'Meeting table (east)', 6.7, 3.4, FACE_WEST, ['meeting_ring_east']),
  meeting_maya: single('meeting_maya', 'Meeting table (south)', 4.8, 5.3, FACE_NORTH, ['meeting_ring_south']),

  // The BOSS room is entered through the southern doorway, so the approach is
  // south of it rather than across the glazed west partition.
  boss_foyer: single('boss_foyer', 'BOSS room doorway', 5.9, -2.6, FACE_NORTH, [
    'corridor_east',
    'boss_room',
  ]),
  boss_room: single('boss_room', 'BOSS room', 5.9, -4.6, FACE_NORTH, ['boss_foyer']),

  // The door is a threshold several people can pass through.
  exit: {
    id: 'exit',
    name: 'Studio door',
    slots: [
      { id: 'exit#0', x: -7.4, z: 2.4, facing: FACE_WEST },
      { id: 'exit#1', x: -7.4, z: 3.2, facing: FACE_WEST },
      { id: 'exit#2', x: -6.8, z: 2.4, facing: FACE_WEST },
      { id: 'exit#3', x: -6.8, z: 3.2, facing: FACE_WEST },
    ],
    neighbors: ['corridor_west'],
  },

  // Open-floor routing nodes. All lie in lanes at least 1.2m clear.
  corridor_center: single('corridor_center', 'Central runway', 0, 0, FACE_SOUTH, [
    'desk_david',
    'desk_elena',
    'desk_alex',
    'desk_maya',
    'desk_alex_review',
    'corridor_west',
    'corridor_east',
  ]),
  corridor_west: single('corridor_west', 'West aisle', -3.4, 0, FACE_SOUTH, [
    'corridor_center',
    'aisle_north_west',
    'aisle_south_west',
    'pantry',
    'exit',
  ]),
  corridor_east: single('corridor_east', 'East aisle', 3.4, 0, FACE_SOUTH, [
    'corridor_center',
    'aisle_north_east',
    'aisle_south_east',
    'boss_foyer',
  ]),
  corridor_north: single('corridor_north', 'North gallery', 0, -4.4, FACE_NORTH, [
    'aisle_north_west',
    'aisle_north_east',
    'whiteboard_manager',
    'whiteboard_researcher',
    'whiteboard_qa',
  ]),
  aisle_north_west: single('aisle_north_west', 'North-west junction', -3.4, -4.4, FACE_SOUTH, [
    'corridor_west',
    'corridor_north',
  ]),
  // Kept clear of the BOSS room's glazed partition at x ~= 3.38.
  aisle_north_east: single('aisle_north_east', 'North-east junction', 2.6, -4.4, FACE_SOUTH, [
    'corridor_east',
    'corridor_north',
  ]),
  // `desk_alex_review` is reached from the central runway, not from here: a
  // direct line would pass through the south bench.
  aisle_south_west: single('aisle_south_west', 'South-west junction', -3.4, 1.9, FACE_SOUTH, [
    'corridor_west',
    'pantry',
  ]),
  // Kept north of the meeting table's footprint.
  aisle_south_east: single('aisle_south_east', 'South-east junction', 3.4, 1.0, FACE_SOUTH, [
    'corridor_east',
    'meeting_david',
    'meeting_ring_west',
    'meeting_ring_east',
  ]),
};

/** Legacy ids that used to be separate waypoints at duplicate coordinates. */
export const DESTINATION_ALIASES: Record<string, string> = {
  desk_manager: 'desk_david',
  desk_researcher: 'desk_elena',
  desk_developer: 'desk_alex',
  desk_qa: 'desk_maya',
  coffee_lounge: 'pantry',
  whiteboard: 'whiteboard_researcher',
  meeting: 'meeting_alex',
};

export const resolveDestinationId = (id: string): string =>
  DESTINATIONS[id] ? id : (DESTINATION_ALIASES[id] ?? 'corridor_center');

/** Resolve a `"pantry#1"` slot id, or the first free-standing slot of a node. */
export const resolveSlot = (
  destinationId: string,
  slotId?: string | null,
): DestinationSlot => {
  const destination = DESTINATIONS[resolveDestinationId(destinationId)];
  if (slotId) {
    const match = destination.slots.find((slot) => slot.id === slotId);
    if (match) return match;
  }
  return destination.slots[0];
};

// ---------------------------------------------------------------------------
// Collision helpers
// ---------------------------------------------------------------------------

const overlap = (box_: Box, x: number, z: number, radius: number) => {
  const halfWidth = box_.width / 2 + radius;
  const halfDepth = box_.depth / 2 + radius;
  const dx = x - box_.x;
  const dz = z - box_.z;
  return Math.abs(dx) < halfWidth && Math.abs(dz) < halfDepth
    ? { dx, dz, halfWidth, halfDepth }
    : null;
};

export const isInsideObstacle = (x: number, z: number, radius = AGENT_RADIUS): boolean =>
  OFFICE_OBSTACLES.some((item) => overlap(item, x, z, radius) !== null);

/**
 * Push a position out of any furniture it has entered, along the shallowest
 * axis. Applied both to path movement and to manual dragging, which
 * previously only clamped to the room bounds and let a body pass through a
 * desk.
 */
export const resolveAgainstObstacles = (
  x: number,
  z: number,
  radius = AGENT_RADIUS,
): [number, number] => {
  let outX = x;
  let outZ = z;

  // Two passes, so being pushed out of one box cannot leave the body inside
  // an adjacent one.
  for (let pass = 0; pass < 2; pass += 1) {
    for (const item of OFFICE_OBSTACLES) {
      const hit = overlap(item, outX, outZ, radius);
      if (!hit) continue;

      const pushX = hit.halfWidth - Math.abs(hit.dx);
      const pushZ = hit.halfDepth - Math.abs(hit.dz);

      if (pushX < pushZ) {
        outX = item.x + Math.sign(hit.dx || 1) * hit.halfWidth;
      } else {
        outZ = item.z + Math.sign(hit.dz || 1) * hit.halfDepth;
      }
    }
  }

  return [outX, outZ];
};

// ---------------------------------------------------------------------------
// Self-check, exercised by a unit test rather than trusted from a comment.
// ---------------------------------------------------------------------------

/** Ids that exist purely to route traffic, and so must stay genuinely clear. */
const CORRIDOR_IDS = [
  'corridor_center',
  'corridor_west',
  'corridor_east',
  'corridor_north',
  'aisle_north_west',
  'aisle_north_east',
  'aisle_south_west',
  'aisle_south_east',
];

/** Shortest distance from a point to the outside of a box, 0 if inside. */
const distanceToBox = (item: Box, x: number, z: number): number => {
  const dx = Math.max(Math.abs(x - item.x) - item.width / 2, 0);
  const dz = Math.max(Math.abs(z - item.z) - item.depth / 2, 0);
  return Math.hypot(dx, dz);
};

export const findGeometryProblems = (): string[] => {
  const problems: string[] = [];
  const seen = new Map<string, string>();

  // Navigation lanes must be wide enough for two people to pass. This is the
  // mechanical version of "the tables are aligned".
  for (const id of CORRIDOR_IDS) {
    const destination = DESTINATIONS[id];
    if (!destination) {
      problems.push(`corridor ${id} is missing`);
      continue;
    }
    const slot = destination.slots[0];
    let nearest = Infinity;
    let nearestLabel = '';
    for (const item of OFFICE_OBSTACLES) {
      const gap = distanceToBox(item, slot.x, slot.z);
      if (gap < nearest) {
        nearest = gap;
        nearestLabel = item.label;
      }
    }
    if (nearest < MIN_CORRIDOR_CLEARANCE / 2) {
      problems.push(
        `${id} has only ${nearest.toFixed(2)}m clearance from "${nearestLabel}" ` +
          `(needs ${(MIN_CORRIDOR_CLEARANCE / 2).toFixed(2)}m)`,
      );
    }
  }

  for (const destination of Object.values(DESTINATIONS)) {
    for (const slot of destination.slots) {
      const key = `${slot.x.toFixed(2)},${slot.z.toFixed(2)}`;
      const existing = seen.get(key);
      if (existing) {
        problems.push(`${slot.id} shares coordinates with ${existing}`);
      } else {
        seen.set(key, slot.id);
      }

      if (isInsideObstacle(slot.x, slot.z)) {
        const blocking = OFFICE_OBSTACLES.find(
          (item) => overlap(item, slot.x, slot.z, AGENT_RADIUS) !== null,
        );
        problems.push(`${slot.id} sits inside "${blocking?.label ?? 'furniture'}"`);
      }
    }

    for (const neighbor of destination.neighbors) {
      if (!DESTINATIONS[neighbor]) {
        problems.push(`${destination.id} lists unknown neighbour ${neighbor}`);
      }
    }
  }

  return problems;
};
