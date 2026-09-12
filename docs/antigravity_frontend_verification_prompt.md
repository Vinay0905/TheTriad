# Antigravity verification prompt: office-life flow

```text
You are reviewing the TriadCouncil frontend and FastAPI choreography for a
human-in-the-loop coding-agent product. Verify the implementation; do not make
unrequested architectural changes.

Goal: the 3D office should feel like a normal, active workplace while remaining
truthful about the actual pipeline. Background office-life movement must happen
only between runs. During an active run, server workflow events must take
priority and show this order: Manager scopes -> Researcher investigates ->
Researcher shares at whiteboard -> Developer creates the contract and implements
-> QA reviews beside the developer -> QA and Manager convene at the whiteboard
for human approval.

Inspect first:
- frontend/src/components/office/OfficeLife.tsx
- frontend/src/components/office/AgentCharacter.tsx
- frontend/src/components/office/OfficeCanvas.tsx
- frontend/src/store/useOfficeStore.ts
- frontend/src/hooks/useOfficeSocket.ts
- src/ai_team/server.py

Acceptance checks:
1. With no run active and “Between-run office life” on, exactly one agent at a
   time performs a short, role-appropriate routine, then returns to their desk.
   It must not use independent random timers that cause collisions or conflicting stories.
2. Starting a task stops/cancels ambient routines. Backend WebSocket events are
   then the authoritative source for agent movement and status.
3. The stage choreography follows the stated order and uses waypoint IDs that
   exist in WaypointGraph.ts. No agent is sent through furniture or a missing node.
4. Agent movement reaches its target, updates currentWaypoint, and does not get
   stuck if a workflow event supersedes a background move.
5. When the backend emits PROJECT_COMPLETED, David walks to the `boss_room`
   waypoint before the delivery modal opens. Acknowledging that modal sends him
   back to `desk_david`; only then may between-run office life resume.
6. The BOSS room is visibly distinct in the north-east corner, and all room,
   floor, desk, and accent colors remain visually separated rather than using
   competing full-saturation tones.
7. TypeScript builds cleanly (`npm run build` from frontend) and Python source
   compiles (`python3 -m compileall -q src`).
8. Do not weaken the approval gate, alter server execution permissions, or turn
   decorative movement into a claim of real agent progress.

Return: pass/fail for every check, file-and-line references for failures,
commands run with their true output, and the smallest safe patch only if needed.
```

## Office-clock and personality extension

```text
Additionally verify the office-life simulation.

1. `src/ai_team/spatial/office_clock.py` is server-owned and starts a fresh
   09:00 workday only when the server process starts. Browser refreshes must
   preserve the current simulated time.
2. A 20-real-minute WORKDAY maps linearly from 09:00 to 17:00. OFF_HOURS lasts
   20 real minutes, then a new day starts at 09:00.
3. OFFICE_CLOCK events make the wall clock update in real time. At 17:00 every
   agent walks toward `exit`, then avatars and nameplates disappear. They return
   at the next 09:00. New tasks are rejected during OFF_HOURS.
4. Between runs, Alex takes bounded coffee breaks more often than the other
   habits, David takes short air breaks, Elena checks and shares research, and
   Maya performs persistent QA follow-ups. These routines must pause for a real
   workflow or off-hours.
5. During the live pipeline, David's short air break causes a ready research
   report to visibly wait; it must not be represented as delivered before he
   returns.
6. Run the frontend build and Python compilation. Report exact failures; do not
   weaken the human approval or execution boundary to fix a visual issue.
```
