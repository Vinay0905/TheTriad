import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { Agent } from '../../types/office';
import { defaultGraph, OFFICE_WAYPOINTS } from './WaypointGraph';
import { useOfficeStore } from '../../store/useOfficeStore';

interface AgentCharacterProps {
  agent: Agent;
}

export const AgentCharacter: React.FC<AgentCharacterProps> = ({ agent }) => {
  const groupRef = useRef<THREE.Group>(null);
  const headRef = useRef<THREE.Mesh>(null);
  const leftArmRef = useRef<THREE.Group>(null);
  const rightArmRef = useRef<THREE.Group>(null);
  const setSelectedAgent = useOfficeStore((state) => state.setSelectedAgent);
  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);

  const isSelected = selectedAgentId === agent.id;

  // Path following queue
  const pathQueueRef = useRef<{ x: number; z: number; id: string }[]>([]);
  const currentTargetRef = useRef<{ x: number; z: number; id: string } | null>(null);

  // Initialize position to initial waypoint
  useEffect(() => {
    const wp = OFFICE_WAYPOINTS[agent.currentWaypoint] || { x: 0, z: 0 };
    if (groupRef.current) {
      groupRef.current.position.set(wp.x, 0, wp.z);
    }
  }, []);

  // Compute waypoint path when target changes
  useEffect(() => {
    if (agent.currentWaypoint !== agent.targetWaypoint) {
      const path = defaultGraph.findPath(agent.currentWaypoint, agent.targetWaypoint);
      if (path.length > 1) {
        path.shift(); // Remove starting node
        pathQueueRef.current = path;
        currentTargetRef.current = path[0] || null;
      }
    }
  }, [agent.currentWaypoint, agent.targetWaypoint]);

  // Frame loop: kinematic translation, turning, and procedural animation
  useFrame((state, delta) => {
    if (!groupRef.current) return;

    const time = state.clock.getElapsedTime();
    const pos = groupRef.current.position;

    // 1. Waypoint movement controller (Constant speed 2.6 units/sec)
    if (currentTargetRef.current) {
      const target = currentTargetRef.current;
      const targetPos = new THREE.Vector3(target.x, 0, target.z);
      const dist = pos.distanceTo(targetPos);
      const step = 2.6 * delta;

      if (dist <= step) {
        pos.copy(targetPos);
        pathQueueRef.current.shift();
        if (pathQueueRef.current.length > 0) {
          currentTargetRef.current = pathQueueRef.current[0];
        } else {
          currentTargetRef.current = null;
        }
      } else {
        const dir = targetPos.clone().sub(pos).normalize();
        pos.addScaledVector(dir, step);

        // Smooth rotation towards target direction
        const targetAngle = Math.atan2(dir.x, dir.z);
        const targetQuat = new THREE.Quaternion().setFromAxisAngle(
          new THREE.Vector3(0, 1, 0),
          targetAngle
        );
        groupRef.current.quaternion.slerp(targetQuat, 1 - Math.exp(-12 * delta));
      }
    }

    // 2. Procedural Animation states (Idle, Walk, Type, Sit)
    const isWalking = !!currentTargetRef.current;
    if (isWalking) {
      // Natural walking swing
      if (leftArmRef.current) leftArmRef.current.rotation.x = Math.sin(time * 8) * 0.4;
      if (rightArmRef.current) rightArmRef.current.rotation.x = -Math.sin(time * 8) * 0.4;
      groupRef.current.position.y = Math.abs(Math.sin(time * 8)) * 0.06;
    } else if (agent.animation === 'Type') {
      // Fast typing motion
      groupRef.current.position.y = 0;
      if (leftArmRef.current) leftArmRef.current.rotation.x = -1.1 + Math.sin(time * 16) * 0.15;
      if (rightArmRef.current) rightArmRef.current.rotation.x = -1.1 + Math.cos(time * 16) * 0.15;
      if (headRef.current) headRef.current.rotation.x = 0.15 + Math.sin(time * 2) * 0.03;
    } else {
      // Subtle idle breathing
      groupRef.current.position.y = 0;
      if (leftArmRef.current) leftArmRef.current.rotation.x = Math.sin(time * 1.5) * 0.05;
      if (rightArmRef.current) rightArmRef.current.rotation.x = -Math.sin(time * 1.5) * 0.05;
      if (headRef.current) headRef.current.rotation.y = Math.sin(time * 0.8) * 0.1;
    }
  });

  return (
    <group
      ref={groupRef}
      onClick={(e) => {
        e.stopPropagation();
        setSelectedAgent(agent.id);
      }}
      cursor="pointer"
    >
      {/* Selection Spotlight Ring */}
      {isSelected && (
        <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.55, 0.65, 32]} />
          <meshBasicMaterial color={agent.color} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Humanoid Character Geometry */}
      <group position={[0, 0.7, 0]}>
        {/* Torso */}
        <mesh position={[0, 0.25, 0]} castShadow receiveShadow>
          <capsuleGeometry args={[0.22, 0.35, 8, 16]} />
          <meshStandardMaterial color={agent.color} roughness={0.4} />
        </mesh>

        {/* Head */}
        <mesh ref={headRef} position={[0, 0.62, 0]} castShadow>
          <sphereGeometry args={[0.18, 24, 24]} />
          <meshStandardMaterial color="#fed7aa" roughness={0.6} />
        </mesh>

        {/* Hair / Cap */}
        <mesh position={[0, 0.72, -0.02]}>
          <sphereGeometry args={[0.16, 16, 16]} />
          <meshStandardMaterial color="#1f2937" roughness={0.8} />
        </mesh>

        {/* Left Arm */}
        <group ref={leftArmRef} position={[-0.28, 0.4, 0]}>
          <mesh position={[0, -0.2, 0]} castShadow>
            <cylinderGeometry args={[0.06, 0.06, 0.35, 12]} />
            <meshStandardMaterial color={agent.color} roughness={0.5} />
          </mesh>
        </group>

        {/* Right Arm */}
        <group ref={rightArmRef} position={[0.28, 0.4, 0]}>
          <mesh position={[0, -0.2, 0]} castShadow>
            <cylinderGeometry args={[0.06, 0.06, 0.35, 12]} />
            <meshStandardMaterial color={agent.color} roughness={0.5} />
          </mesh>
        </group>

        {/* Legs */}
        <mesh position={[-0.11, -0.3, 0]} castShadow>
          <cylinderGeometry args={[0.07, 0.07, 0.45, 12]} />
          <meshStandardMaterial color="#374151" roughness={0.7} />
        </mesh>
        <mesh position={[0.11, -0.3, 0]} castShadow>
          <cylinderGeometry args={[0.07, 0.07, 0.45, 12]} />
          <meshStandardMaterial color="#374151" roughness={0.7} />
        </mesh>
      </group>

      {/* Floating 3D Status Badge */}
      <Html position={[0, 1.85, 0]} center distanceFactor={14}>
        <div className="flex flex-col items-center pointer-events-none select-none">
          <div className="bg-surface/90 backdrop-blur border border-border px-2.5 py-1 rounded-full shadow-lg flex items-center gap-1.5 whitespace-nowrap">
            <span className="text-xs">{agent.avatarIcon}</span>
            <span className="text-xs font-semibold text-white">{agent.name}</span>
            <span
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ backgroundColor: agent.color }}
            />
          </div>
          {agent.statusBadge && (
            <div className="mt-1 bg-black/75 backdrop-blur text-[10px] text-gray-300 px-2 py-0.5 rounded border border-white/10 max-w-[160px] truncate text-center">
              {agent.statusBadge}
            </div>
          )}
        </div>
      </Html>
    </group>
  );
};
