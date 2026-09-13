import React, { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import type { Agent } from '../../types/office';
import { useOfficeStore } from '../../store/useOfficeStore';
import {
  AGENT_RADIUS,
  resolveAgainstObstacles,
  resolveDestinationId,
  resolveSlot,
} from './OfficeGeometry';
import { defaultGraph, type PathPoint } from './WaypointGraph';
import { forEachOtherBody, publishBody, removeBody } from './agentBodies';

interface AgentCharacterProps {
  agent: Agent;
}

// Motion constants. Acceleration is what removes the old teleport feel: the
// previous implementation moved at a constant 2.7 u/s and stopped dead.
const MAX_SPEED = 1.45;
const ACCELERATION = 5.5;
const ARRIVAL_RADIUS = 0.45;
const WAYPOINT_TOLERANCE = 0.12;
const SEPARATION_DISTANCE = AGENT_RADIUS * 2 + 0.11;
const TURN_RATE = 9;

export const AgentCharacter: React.FC<AgentCharacterProps> = ({ agent }) => {
  const groupRef = useRef<THREE.Group>(null);
  const headRef = useRef<THREE.Mesh>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const { raycaster, camera, invalidate } = useThree();

  // Scratch objects, hoisted out of the frame loop. The old code allocated
  // roughly six vectors and quaternions per agent per frame, which at 120fps
  // produced a constant GC sawtooth.
  const scratch = useMemo(
    () => ({
      floorPlane: new THREE.Plane(new THREE.Vector3(0, 1, 0), 0),
      hit: new THREE.Vector3(),
      quaternion: new THREE.Quaternion(),
      axis: new THREE.Vector3(0, 1, 0),
    }),
    [],
  );

  const velocity = useRef({ x: 0, z: 0 });
  const pathRef = useRef<PathPoint[]>([]);
  const arrivedRef = useRef(true);

  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);
  const isRunning = useOfficeStore((state) => state.isRunning);
  const isGateOpen = useOfficeStore((state) => state.gate.isOpen);
  const isDeliveryOpen = useOfficeStore((state) => state.delivery.isOpen);

  const isSelected = selectedAgentId === agent.id;

  const targetSlot = useMemo(
    () => resolveSlot(agent.targetWaypoint, agent.slotId),
    [agent.targetWaypoint, agent.slotId],
  );

  // Place the body at its starting slot once.
  useEffect(() => {
    const slot = resolveSlot(agent.currentWaypoint, agent.slotId);
    groupRef.current?.position.set(slot.x, 0, slot.z);
    return () => removeBody(agent.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent.id]);

  // Recompute the route whenever the destination changes.
  useEffect(() => {
    const position = groupRef.current?.position;
    if (!position) return;

    if (Math.hypot(position.x - targetSlot.x, position.z - targetSlot.z) < ARRIVAL_RADIUS) {
      pathRef.current = [];
      arrivedRef.current = true;
      return;
    }

    pathRef.current = defaultGraph.findPath(
      position.x,
      position.z,
      resolveDestinationId(agent.targetWaypoint),
      agent.slotId,
    );
    arrivedRef.current = false;
    // Wake the render loop: with frameloop="demand" nothing redraws until
    // something asks it to.
    invalidate();
  }, [agent.targetWaypoint, agent.slotId, targetSlot, invalidate]);

  useFrame((state, rawDelta) => {
    const group = groupRef.current;
    if (!group) return;

    // Clamp delta so a backgrounded tab returning to focus cannot teleport
    // everyone across the room in one step.
    const delta = Math.min(rawDelta, 0.05);
    const position = group.position;

    if (isDragging) {
      publishBody(agent.id, { x: position.x, z: position.z, speed: 0 });
      return;
    }

    const waypoint = pathRef.current[0];
    let desiredX = 0;
    let desiredZ = 0;
    let moving = false;

    if (waypoint) {
      const dx = waypoint.x - position.x;
      const dz = waypoint.z - position.z;
      const span = Math.hypot(dx, dz);

      if (span <= WAYPOINT_TOLERANCE) {
        pathRef.current.shift();
      } else {
        moving = true;
        // Ease out over the final stretch rather than stopping instantly.
        const isFinal = pathRef.current.length === 1;
        const speedLimit =
          isFinal && span < ARRIVAL_RADIUS
            ? MAX_SPEED * Math.max(0.18, span / ARRIVAL_RADIUS)
            : MAX_SPEED;

        desiredX = (dx / span) * speedLimit;
        desiredZ = (dz / span) * speedLimit;
      }
    }

    // Mutual separation. Both parties push, so they slide past each other
    // instead of one bulldozing through.
    let pushX = 0;
    let pushZ = 0;
    forEachOtherBody(agent.id, (_id, other) => {
      const dx = position.x - other.x;
      const dz = position.z - other.z;
      const span = Math.hypot(dx, dz);
      if (span > SEPARATION_DISTANCE || span < 1e-5) return;

      const strength = (SEPARATION_DISTANCE - span) / SEPARATION_DISTANCE;
      pushX += (dx / span) * strength * MAX_SPEED * 1.5;
      pushZ += (dz / span) * strength * MAX_SPEED * 1.5;
    });

    desiredX += pushX;
    desiredZ += pushZ;

    // Accelerate toward the desired velocity rather than snapping to it.
    const blend = Math.min(1, ACCELERATION * delta);
    velocity.current.x += (desiredX - velocity.current.x) * blend;
    velocity.current.z += (desiredZ - velocity.current.z) * blend;

    const speed = Math.hypot(velocity.current.x, velocity.current.z);
    if (speed < 0.02 && !waypoint) {
      velocity.current.x = 0;
      velocity.current.z = 0;
    }

    let nextX = position.x + velocity.current.x * delta;
    let nextZ = position.z + velocity.current.z * delta;

    // Furniture is solid. This is applied after movement so no combination of
    // path following and separation can shove a body through a desk.
    [nextX, nextZ] = resolveAgainstObstacles(nextX, nextZ);
    position.x = nextX;
    position.z = nextZ;

    publishBody(agent.id, { x: position.x, z: position.z, speed });

    // Face travel direction while moving, or the slot's declared facing once
    // parked, so people sit facing their monitors.
    const heading =
      speed > 0.12
        ? Math.atan2(velocity.current.x, velocity.current.z)
        : targetSlot.facing;
    scratch.quaternion.setFromAxisAngle(scratch.axis, heading);
    group.quaternion.slerp(scratch.quaternion, 1 - Math.exp(-TURN_RATE * delta));

    const time = state.clock.getElapsedTime();
    if (speed > 0.12) {
      // Bob in step with actual speed, not on a fixed timer.
      group.position.y = Math.abs(Math.sin(time * 7.5)) * 0.045 * (speed / MAX_SPEED);
      if (headRef.current) headRef.current.rotation.x = 0.05;
    } else {
      group.position.y = 0;
      if (headRef.current) {
        headRef.current.rotation.x = agent.animation === 'Type' ? 0.12 : 0;
        headRef.current.rotation.y = 0;
      }
    }

    const stillBusy = speed > 0.02 || pathRef.current.length > 0;
    if (stillBusy) {
      // Keep the demand-driven loop alive only while something is moving.
      invalidate();
    } else if (!arrivedRef.current) {
      arrivedRef.current = true;
    }
  });

  const badgeHeight = 1.25;
  const isAlerting = Boolean(agent.waitState || agent.absence);
  const showLabel = isSelected || isHovered || isAlerting;

  if (agent.isPresent === false) return null;

  return (
    <group
      ref={groupRef}
      onClick={(event) => {
        event.stopPropagation();
        useOfficeStore.getState().setSelectedAgent(agent.id);
      }}
      onPointerDown={(event) => {
        event.stopPropagation();
        // A live run is authoritative; manual repositioning must not fight it.
        if (isRunning) return;
        setIsDragging(true);
        useOfficeStore.getState().setIsDraggingAgent(true);
        useOfficeStore.getState().setSelectedAgent(agent.id);
        (event.target as HTMLElement)?.setPointerCapture?.(event.pointerId);
      }}
      onPointerUp={(event) => {
        event.stopPropagation();
        if (!isDragging) return;
        setIsDragging(false);
        useOfficeStore.getState().setIsDraggingAgent(false);
        if (groupRef.current) {
          useOfficeStore
            .getState()
            .setAgentPosition(agent.id, [
              groupRef.current.position.x,
              0,
              groupRef.current.position.z,
            ]);
        }
      }}
      onPointerMove={(event) => {
        if (!isDragging || !groupRef.current) return;
        event.stopPropagation();
        raycaster.setFromCamera(event.pointer, camera);
        if (!raycaster.ray.intersectPlane(scratch.floorPlane, scratch.hit)) return;

        // Clamp to the room, then push out of furniture. The old handler only
        // clamped, so a body could be dropped inside a desk.
        const clampedX = Math.max(-7.9, Math.min(7.9, scratch.hit.x));
        const clampedZ = Math.max(-7.6, Math.min(7.6, scratch.hit.z));
        const [safeX, safeZ] = resolveAgainstObstacles(clampedX, clampedZ);
        groupRef.current.position.set(safeX, 0, safeZ);
        invalidate();
      }}
      onPointerOver={(event) => {
        event.stopPropagation();
        setIsHovered(true);
        invalidate();
        document.body.style.cursor = isDragging ? 'grabbing' : 'grab';
      }}
      onPointerOut={() => {
        setIsHovered(false);
        invalidate();
        if (!isDragging) document.body.style.cursor = 'default';
      }}
    >
      {/* Selection ring on the floor. */}
      {isSelected && (
        <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.38, 0.44, 28]} />
          <meshBasicMaterial color={agent.color} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/*
        A cheap blob shadow. Real shadow casting for the characters was removed
        along with the per-frame shadow map refresh; this reads almost the same
        for a fraction of the cost.
      */}
      <mesh position={[0, 0.012, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.26, 20]} />
        <meshBasicMaterial color="#05070c" transparent opacity={0.34} />
      </mesh>

      <group position={[0, 0, 0]}>
        <mesh position={[0, 0.025, 0]}>
          <cylinderGeometry args={[0.2, 0.22, 0.05, 20]} />
          <meshStandardMaterial color="#111827" roughness={0.4} metalness={0.6} />
        </mesh>

        <mesh position={[0, 0.34, 0]}>
          <cylinderGeometry args={[0.1, 0.19, 0.58, 20]} />
          <meshStandardMaterial color={agent.color} roughness={0.35} metalness={0.15} />
        </mesh>

        <mesh position={[0, 0.63, 0]}>
          <cylinderGeometry args={[0.105, 0.105, 0.025, 16]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.8} roughness={0.2} />
        </mesh>

        <mesh ref={headRef} position={[0, 0.79, 0]}>
          <sphereGeometry args={[0.16, 20, 20]} />
          <meshStandardMaterial color="#fed7aa" roughness={0.4} />
        </mesh>

        <mesh position={[0, 0.86, -0.02]} rotation={[-0.1, 0, 0]}>
          <sphereGeometry args={[0.155, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
          <meshStandardMaterial color="#1e293b" roughness={0.6} />
        </mesh>
      </group>

      {/*
        Labels are DOM nodes whose transform is rewritten every rendered frame,
        so they are shown only when they carry information: the selected agent,
        the hovered agent, or one that is rate limited or absent. Combined with
        demand rendering, an idle office writes nothing.
      */}
      {showLabel && !isGateOpen && !isDeliveryOpen && (
        <Html
          position={[0, badgeHeight, 0]}
          center
          distanceFactor={12}
          zIndexRange={[0, 0]}
          style={{ pointerEvents: 'none' }}
        >
          <div className="flex flex-col items-center select-none">
            <div
              className="flex items-center gap-1.5 px-2.5 py-0.5 rounded shadow-xl border backdrop-blur-md"
              style={{
                backgroundColor: 'rgba(10, 14, 22, 0.94)',
                borderColor: isSelected ? agent.color : 'rgba(255,255,255,0.12)',
              }}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: agent.color }}
              />
              <span className="text-[11px] font-mono font-bold tracking-wider text-white uppercase">
                {agent.name}
              </span>
            </div>

            {agent.waitState && (
              <div className="mt-1 bg-amber-950/90 text-[9px] font-mono text-amber-200 px-2 py-0.5 rounded border border-amber-500/40 whitespace-nowrap">
                rate limited · {Math.ceil(agent.waitState.retryAfterSeconds)}s
              </div>
            )}

            {agent.absence && (
              <div className="mt-1 bg-rose-950/90 text-[9px] font-mono text-rose-200 px-2 py-0.5 rounded border border-rose-500/40 whitespace-nowrap">
                out · quota{agent.absence.resetAtDisplay ? ` · ${agent.absence.resetAtDisplay}` : ''}
              </div>
            )}

            {!isAlerting && agent.statusBadge && (
              <div className="mt-1 bg-black/90 text-[9px] font-mono text-gray-300 px-2 py-0.5 rounded border border-white/10 max-w-[190px] truncate text-center">
                {agent.statusBadge}
              </div>
            )}
          </div>
        </Html>
      )}
    </group>
  );
};
