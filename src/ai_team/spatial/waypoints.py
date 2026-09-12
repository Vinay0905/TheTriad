"""Discrete 3D Waypoint coordinates and topology for the virtual office."""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Waypoint:
    id: str
    name: str
    x: float
    z: float
    neighbors: Tuple[str, ...]


# 3D Ground coordinates (x, z) in Three.js world space
OFFICE_WAYPOINTS: Dict[str, Waypoint] = {
    # Desk Locations
    "desk_manager": Waypoint(
        id="desk_manager",
        name="David's Desk (Manager)",
        x=0.0,
        z=-2.5,
        neighbors=("hallway_north", "whiteboard"),
    ),
    "desk_researcher": Waypoint(
        id="desk_researcher",
        name="Elena's Pod (Researcher)",
        x=-3.5,
        z=-1.0,
        neighbors=("hallway_west",),
    ),
    "desk_developer": Waypoint(
        id="desk_developer",
        name="Alex's Desk (Developer)",
        x=3.5,
        z=-1.0,
        neighbors=("hallway_east", "desk_qa"),
    ),
    "desk_qa": Waypoint(
        id="desk_qa",
        name="Maya's Pod (QA Auditor)",
        x=3.5,
        z=1.5,
        neighbors=("desk_developer", "hallway_east"),
    ),
    # Interactive Focal Zones
    "whiteboard": Waypoint(
        id="whiteboard",
        name="Architecture Whiteboard",
        x=0.0,
        z=-5.0,
        neighbors=("desk_manager", "hallway_north"),
    ),
    "coffee_lounge": Waypoint(
        id="coffee_lounge",
        name="Break Lounge & Coffee Bar",
        x=-3.5,
        z=3.0,
        neighbors=("hallway_south", "hallway_west"),
    ),
    # Hallway Intersections (Collision-Free Routing)
    "hallway_center": Waypoint(
        id="hallway_center",
        name="Central Aisle",
        x=0.0,
        z=0.0,
        neighbors=("hallway_north", "hallway_south", "hallway_west", "hallway_east"),
    ),
    "hallway_north": Waypoint(
        id="hallway_north",
        name="North Aisle",
        x=0.0,
        z=-3.0,
        neighbors=("hallway_center", "desk_manager", "whiteboard"),
    ),
    "hallway_south": Waypoint(
        id="hallway_south",
        name="South Aisle",
        x=0.0,
        z=2.5,
        neighbors=("hallway_center", "coffee_lounge"),
    ),
    "hallway_west": Waypoint(
        id="hallway_west",
        name="West Aisle",
        x=-2.0,
        z=0.0,
        neighbors=("hallway_center", "desk_researcher", "coffee_lounge"),
    ),
    "hallway_east": Waypoint(
        id="hallway_east",
        name="East Aisle",
        x=2.0,
        z=0.0,
        neighbors=("hallway_center", "desk_developer", "desk_qa"),
    ),
}
