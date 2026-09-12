import React, { useRef, useEffect, useState, useMemo } from 'react';
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
  const [isHovered, setIsHovered] = useState(false);

  const setSelectedAgent = useOfficeStore((state) => state.setSelectedAgent);
  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);

  const isSelected = selectedAgentId === agent.id;

  // Path traversal queue
  const pathQueueRef = useRef<{ x: number; z: number; id: string }[]>([]);
  const currentTargetRef = useRef<{ x: number; z: number; id: string } | null>(null);

  // Initialize position to starting waypoint
  useEffect(() => {
    const wp = OFFICE_WAYPOINTS[agent.currentWaypoint] || { x: 0, z: 0 };
    if (groupRef.current) {
      groupRef.current.position.set(wp.x, 0, wp.z);
    }
  }, []);

  // Compute A* waypoint path when target changes
  useEffect(() => {
    if (agent.currentWaypoint !== agent.targetWaypoint) {
      const path = defaultGraph.findPath(agent.currentWaypoint, agent.targetWaypoint);
      if (path.length > 1) {
        path.shift(); // Remove origin
        pathQueueRef.current = path;
        currentTargetRef.current = path[0] || null;
      }
    }
  }, [agent.currentWaypoint, agent.targetWaypoint]);

  // Frame kinematics loop (Constant linear speed + rotation slerp)
  useFrame((state, delta) => {
    if (!groupRef.current) return;

    const time = state.clock.getElapsedTime();
    const pos = groupRef.current.position;

    // 1. Waypoint movement (Constant speed 2.7 units/sec)
    if (currentTargetRef.current) {
      const target = currentTargetRef.current;
      const targetPos = new THREE.Vector3(target.x, 0, target.z);
      const dist = pos.distanceTo(targetPos);
      const step = 2.7 * delta;

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

        // Smooth rotation slerp facing movement direction
        const targetAngle = Math.atan2(dir.x, dir.z);
        const targetQuat = new THREE.Quaternion().setFromAxisAngle(
          new THREE.Vector3(0, 1, 0),
          targetAngle
        );
        groupRef.current.quaternion.slerp(targetQuat, 1 - Math.exp(-14 * delta));
      }
    }

    // 2. Procedural Animation States
    const isWalking = !!currentTargetRef.current;
    if (isWalking) {
      // Natural walking arm swing + subtle vertical bounce
      if (leftArmRef.current) leftArmRef.current.rotation.x = Math.sin(time * 8.5) * 0.45;
      if (rightArmRef.current) rightArmRef.current.rotation.x = -Math.sin(time * 8.5) * 0.45;
      groupRef.current.position.y = Math.abs(Math.sin(time * 8.5)) * 0.08;
    } else if (agent.animation === 'Type') {
      // Dynamic typing at keyboard
      groupRef.current.position.y = 0;
      if (leftArmRef.current) leftArmRef.current.rotation.x = -1.15 + Math.sin(time * 16) * 0.18;
      if (rightArmRef.current) rightArmRef.current.rotation.x = -1.15 + Math.cos(time * 16) * 0.18;
      if (headRef.current) headRef.current.rotation.x = 0.18 + Math.sin(time * 2.5) * 0.04;
    } else {
      // Subtle idle breathing & looking around
      groupRef.current.position.y = 0;
      if (leftArmRef.current) leftArmRef.current.rotation.x = Math.sin(time * 1.5) * 0.05;
      if (rightArmRef.current) rightArmRef.current.rotation.x = -Math.sin(time * 1.5) * 0.05;
      if (headRef.current) headRef.current.rotation.y = Math.sin(time * 0.7) * 0.15;
    }
  });

  // Staggered label height per role to prevent overlapping pills
  const badgeHeight = useMemo(() => {
    switch (agent.id) {
      case 'manager':
        return 2.15;
      case 'researcher':
        return 1.95;
      case 'developer':
        return 2.05;
      case 'qa':
        return 1.9;
      default:
        return 2.0;
    }
  }, [agent.id]);

  return (
    <group
      ref={groupRef}
      onClick={(e) => {
        e.stopPropagation();
        setSelectedAgent(agent.id);
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setIsHovered(true);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        setIsHovered(false);
        document.body.style.cursor = 'default';
      }}
    >
      {/* Selection Spotlight Halo Ring */}
      {isSelected && (
        <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.6, 0.72, 32]} />
          <meshBasicMaterial color={agent.color} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Stylized Modern Character Geometry */}
      <group position={[0, 0.72, 0]}>
        {/* Main Body / Torso (Tailored clothing) */}
        <mesh position={[0, 0.26, 0]} castShadow receiveShadow>
          <capsuleGeometry args={[0.22, 0.38, 8, 16]} />
          <meshStandardMaterial
            color={agent.color}
            roughness={0.4}
            metalness={0.1}
          />
        </mesh>

        {/* Collar / Shirt Accent */}
        <mesh position={[0, 0.44, 0.05]}>
          <boxGeometry args={[0.16, 0.1, 0.18]} />
          <meshStandardMaterial color="#ffffff" roughness={0.3} />
        </mesh>

        {/* Head */}
        <mesh ref={headRef} position={[0, 0.65, 0]} castShadow>
          <sphereGeometry args={[0.18, 24, 24]} />
          <meshStandardMaterial color="#fed7aa" roughness={0.5} />
        </mesh>

        {/* Hair / Headgear */}
        <mesh position={[0, 0.74, -0.02]} castShadow>
          <sphereGeometry args={[0.17, 16, 16]} />
          <meshStandardMaterial color="#1e293b" roughness={0.7} />
        </mesh>

        {/* Developer Over-Ear Headphones (For Alex) */}
        {agent.id === 'developer' && (
          <group position={[0, 0.66, 0]}>
            <mesh position={[-0.2, 0, 0]}>
              <cylinderGeometry args={[0.06, 0.06, 0.05, 12]} />
              <meshStandardMaterial color="#0f172a" metalness={0.8} />
            </mesh>
            <mesh position={[0.2, 0, 0]}>
              <cylinderGeometry args={[0.06, 0.06, 0.05, 12]} />
              <meshStandardMaterial color="#0f172a" metalness={0.8} />
            </mesh>
            {/* Headband */}
            <mesh position={[0, 0.16, 0]}>
              <torusGeometry args={[0.19, 0.02, 8, 16, Math.PI]} />
              <meshStandardMaterial color="#0f172a" metalness={0.8} />
            </mesh>
          </group>
        )}

        {/* Glasses (For Researcher Elena & Manager David) */}
        {(agent.id === 'researcher' || agent.id === 'manager') && (
          <group position={[0, 0.66, 0.16]}>
            <mesh position={[-0.07, 0, 0]}>
              <ringGeometry args={[0.035, 0.05, 16]} />
              <meshBasicMaterial color="#0f172a" />
            </mesh>
            <mesh position={[0.07, 0, 0]}>
              <ringGeometry args={[0.035, 0.05, 16]} />
              <meshBasicMaterial color="#0f172a" />
            </mesh>
            <mesh position={[0, 0, 0]}>
              <boxGeometry args={[0.04, 0.01, 0.01]} />
              <meshBasicMaterial color="#0f172a" />
            </mesh>
          </group>
        )}

        {/* Left Arm */}
        <group ref={leftArmRef} position={[-0.29, 0.42, 0]}>
          <mesh position={[0, -0.2, 0]} castShadow>
            <cylinderGeometry args={[0.06, 0.06, 0.36, 12]} />
            <meshStandardMaterial color={agent.color} roughness={0.4} />
          </mesh>
          {/* Hand */}
          <mesh position={[0, -0.4, 0]}>
            <sphereGeometry args={[0.05, 12, 12]} />
            <meshStandardMaterial color="#fed7aa" />
          </mesh>
        </group>

        {/* Right Arm */}
        <group ref={rightArmRef} position={[0.29, 0.42, 0]}>
          <mesh position={[0, -0.2, 0]} castShadow>
            <cylinderGeometry args={[0.06, 0.06, 0.36, 12]} />
            <meshStandardMaterial color={agent.color} roughness={0.4} />
          </mesh>
          {/* Hand */}
          <mesh position={[0, -0.4, 0]}>
            <sphereGeometry args={[0.05, 12, 12]} />
            <meshStandardMaterial color="#fed7aa" />
          </mesh>
        </group>

        {/* Legs / Trousers (Dark Charcoal) */}
        <mesh position={[-0.12, -0.32, 0]} castShadow>
          <cylinderGeometry args={[0.07, 0.07, 0.48, 12]} />
          <meshStandardMaterial color="#1e293b" roughness={0.7} />
        </mesh>
        <mesh position={[0.12, -0.32, 0]} castShadow>
          <cylinderGeometry args={[0.07, 0.07, 0.48, 12]} />
          <meshStandardMaterial color="#1e293b" roughness={0.7} />
        </mesh>

        {/* Shoes (Clean White / Leather) */}
        <mesh position={[-0.12, -0.58, 0.04]} castShadow>
          <boxGeometry args={[0.09, 0.06, 0.18]} />
          <meshStandardMaterial color="#f8fafc" roughness={0.3} />
        </mesh>
        <mesh position={[0.12, -0.58, 0.04]} castShadow>
          <boxGeometry args={[0.09, 0.06, 0.18]} />
          <meshStandardMaterial color="#f8fafc" roughness={0.3} />
        </mesh>
      </group>

      {/* Anti-Collision Clean Floating Badge */}
      <Html position={[0, badgeHeight, 0]} center distanceFactor={13}>
        <div
          className={`flex flex-col items-center pointer-events-none transition-all duration-200 ${
            isSelected || isHovered ? 'scale-110 z-30' : 'scale-100 opacity-90'
          }`}
        >
          {/* Main Agent Pill */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full shadow-xl border backdrop-blur-md transition-colors"
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.88)',
              borderColor: isSelected ? agent.color : 'rgba(255, 255, 255, 0.15)',
            }}
          >
            <span className="text-xs">{agent.avatarIcon}</span>
            <span className="text-xs font-semibold text-white tracking-wide">
              {agent.name}
            </span>
            <span
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ backgroundColor: agent.color }}
            />
          </div>

          {/* Expanded Status Bubble (Shows if active, hovered, or selected) */}
          {(isSelected || isHovered || (agent.statusBadge && agent.statusBadge !== 'Standing By' && agent.statusBadge !== 'Awaiting Objective')) && (
            <div className="mt-1 bg-black/85 backdrop-blur-md text-[10px] font-mono text-gray-200 px-2.5 py-0.5 rounded-md border border-white/10 max-w-[180px] truncate text-center shadow-lg animate-in fade-in zoom-in-95 duration-150">
              {agent.statusBadge}
            </div>
          )}
        </div>
      </Html>
    </group>
  );
};
