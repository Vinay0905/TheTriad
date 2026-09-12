import React, { useRef, useEffect, useState, useMemo } from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
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
  const beaconRef = useRef<THREE.Group>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);


  const { raycaster, camera } = useThree();
  const floorPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), []);
  const planeIntersection = useMemo(() => new THREE.Vector3(), []);

  const setSelectedAgent = useOfficeStore((state) => state.setSelectedAgent);
  const selectedAgentId = useOfficeStore((state) => state.selectedAgentId);
  const setIsDraggingAgent = useOfficeStore((state) => state.setIsDraggingAgent);
  const setAgentPosition = useOfficeStore((state) => state.setAgentPosition);
  const isRunning = useOfficeStore((state) => state.isRunning);

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
    const targetWp = OFFICE_WAYPOINTS[agent.targetWaypoint];
    if (!targetWp) return;

    // Check if physically already at target destination
    if (groupRef.current) {
      const currentPos = groupRef.current.position;
      const targetPos = new THREE.Vector3(targetWp.x, 0, targetWp.z);
      if (currentPos.distanceTo(targetPos) < 0.15) {
        pathQueueRef.current = [];
        currentTargetRef.current = null;
        if (agent.currentWaypoint !== agent.targetWaypoint) {
          useOfficeStore.setState((state) => {
            const ag = state.agents[agent.id];
            if (!ag) return state;
            return {
              agents: {
                ...state.agents,
                [agent.id]: { ...ag, currentWaypoint: agent.targetWaypoint },
              },
            };
          });
        }
        return;
      }
    }

    // Determine start node: if moving mid-flight, use nearest waypoint to current 3D position
    let startNodeId = agent.currentWaypoint;
    if (groupRef.current) {
      const currentPos = groupRef.current.position;
      startNodeId = defaultGraph.findNearestWaypoint(currentPos.x, currentPos.z);
    }

    const path = defaultGraph.findPath(startNodeId, agent.targetWaypoint);
    if (path.length > 0) {
      // If already at or very close to the first node in path, advance to next
      if (groupRef.current && path.length > 1) {
        const firstPos = new THREE.Vector3(path[0].x, 0, path[0].z);
        if (groupRef.current.position.distanceTo(firstPos) < 0.25) {
          path.shift();
        }
      }
      pathQueueRef.current = path;
      currentTargetRef.current = path[0] || null;
    } else {
      // Fallback direct move to target waypoint
      pathQueueRef.current = [];
      currentTargetRef.current = { x: targetWp.x, z: targetWp.z, id: agent.targetWaypoint };
    }
  }, [agent.targetWaypoint]);

  // Frame kinematics loop (Constant linear speed + rotation slerp)
  useFrame((state, delta) => {
    if (!groupRef.current) return;

    const time = state.clock.getElapsedTime();
    const pos = groupRef.current.position;

    // Animate Selection Beacon / Arrow (Floating Bobbing Pointer)
    if (beaconRef.current) {
      beaconRef.current.position.y = badgeHeight + 1.1 + Math.sin(time * 5.0) * 0.12;
      beaconRef.current.rotation.y += delta * 2.2;
    }

    // Skip waypoint motion while user is dragging character
    if (isDragging) return;

    // 1. Waypoint movement (Constant speed 2.7 units/sec)
    if (currentTargetRef.current) {
      const target = currentTargetRef.current;
      const targetPos = new THREE.Vector3(target.x, 0, target.z);
      const dist = pos.distanceTo(targetPos);
      const step = 2.7 * delta;

      if (dist <= step) {
        pos.copy(targetPos);
        pathQueueRef.current.shift();
        const nextTarget = pathQueueRef.current[0] || null;
        currentTargetRef.current = nextTarget;

        // Arrived at waypoint step - keep currentWaypoint truthfully updated
        useOfficeStore.setState((state) => {
          const ag = state.agents[agent.id];
          if (!ag) return state;
          return {
            agents: {
              ...state.agents,
              [agent.id]: {
                ...ag,
                currentWaypoint: target.id,
              },
            },
          };
        });
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

    // 2. Procedural Animation States for Architectural Figurine
    const isWalking = !!currentTargetRef.current;
    if (isWalking) {
      // Subtle vertical bobbing during movement
      groupRef.current.position.y = Math.abs(Math.sin(time * 7.5)) * 0.05;
      if (headRef.current) headRef.current.rotation.x = 0.05;
    } else if (agent.animation === 'Type') {
      // Focused working posture
      groupRef.current.position.y = 0;
      if (headRef.current) headRef.current.rotation.x = 0.12 + Math.sin(time * 3.0) * 0.03;
    } else {
      // Idle standing with subtle head rotation
      groupRef.current.position.y = 0;
      if (headRef.current) {
        headRef.current.rotation.x = 0;
        headRef.current.rotation.y = Math.sin(time * 0.8) * 0.12;
      }
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
      onPointerDown={(e) => {
        e.stopPropagation();
        // A real workflow is authoritative: observation and selection stay
        // available, but manual repositioning cannot contradict its movement.
        if (isRunning) return;
        setIsDragging(true);
        setIsDraggingAgent(true);
        setSelectedAgent(agent.id);
        (e.target as HTMLElement)?.setPointerCapture?.(e.pointerId);
      }}
      onPointerUp={(e) => {
        e.stopPropagation();
        if (isDragging) {
          setIsDragging(false);
          setIsDraggingAgent(false);
          if (groupRef.current) {
            setAgentPosition(agent.id, [
              groupRef.current.position.x,
              0,
              groupRef.current.position.z,
            ]);
          }
        }
      }}
      onPointerMove={(e) => {
        if (!isDragging || !groupRef.current) return;
        e.stopPropagation();
        raycaster.setFromCamera(e.pointer, camera);
        if (raycaster.ray.intersectPlane(floorPlane, planeIntersection)) {
          // Clamp position within office bounds
          const clampedX = Math.max(-7.5, Math.min(7.5, planeIntersection.x));
          const clampedZ = Math.max(-7.5, Math.min(7.5, planeIntersection.z));
          groupRef.current.position.set(clampedX, 0, clampedZ);
        }
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setIsHovered(true);
        document.body.style.cursor = isDragging ? 'grabbing' : 'grab';
      }}
      onPointerOut={() => {
        setIsHovered(false);
        if (!isDragging) {
          document.body.style.cursor = 'default';
        }
      }}
    >
      {/* 1. Downward 3D Animated Simple Pointer (Clean & Minimalist) */}
      {isSelected && (
        <group ref={beaconRef} position={[0, 1.22, 0]}>
          {/* Simple Inverted Floating Cone Arrow pointing down */}
          <mesh rotation={[Math.PI, 0, 0]} castShadow>
            <coneGeometry args={[0.10, 0.24, 16]} />
            <meshStandardMaterial
              color={agent.color}
              emissive={agent.color}
              emissiveIntensity={1.5}
              roughness={0.1}
            />
          </mesh>
          {/* Subtle Beacon Halo Ring */}
          <mesh position={[0, 0.14, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <torusGeometry args={[0.16, 0.015, 8, 24]} />
            <meshBasicMaterial color={agent.color} />
          </mesh>
        </group>
      )}


      {/* 2. Concentric Neon Halo Rings on floor (Stitch 1:1) */}
      {isSelected && (
        <group position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          {/* Inner Sharp Ring */}
          <mesh>
            <ringGeometry args={[0.38, 0.44, 32]} />
            <meshBasicMaterial color={agent.color} side={THREE.DoubleSide} />
          </mesh>
          {/* Outer Faint Concentric Ring */}
          <mesh>
            <ringGeometry args={[0.54, 0.58, 32]} />
            <meshBasicMaterial color={agent.color} opacity={0.4} transparent side={THREE.DoubleSide} />
          </mesh>
        </group>
      )}

      {/* 3. Nordic Architectural Peg Figurine / Meeple (Stitch 1:1 Design) */}
      <group position={[0, 0, 0]}>
        {/* Weighted Circular Base Plinth */}
        <mesh position={[0, 0.025, 0]} castShadow receiveShadow>
          <cylinderGeometry args={[0.20, 0.22, 0.05, 32]} />
          <meshStandardMaterial color="#111827" roughness={0.4} metalness={0.6} />
        </mesh>

        {/* Elegant Tapered Conical Meeple Body */}
        <mesh position={[0, 0.34, 0]} castShadow receiveShadow>
          <cylinderGeometry args={[0.10, 0.19, 0.58, 32]} />
          <meshStandardMaterial
            color={agent.color}
            roughness={0.3}
            metalness={0.2}
          />
        </mesh>

        {/* Polished Metallic Collar Accent */}
        <mesh position={[0, 0.63, 0]}>
          <cylinderGeometry args={[0.105, 0.105, 0.025, 32]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.8} roughness={0.2} />
        </mesh>

        {/* Natural Beechwood / Porcelain Head */}
        <mesh ref={headRef} position={[0, 0.79, 0]} castShadow>
          <sphereGeometry args={[0.16, 32, 32]} />
          <meshStandardMaterial color="#fed7aa" roughness={0.4} />
        </mesh>

        {/* Sleek Minimalist Architectural Cap */}
        <mesh position={[0, 0.86, -0.02]} rotation={[-0.1, 0, 0]} castShadow>
          <sphereGeometry args={[0.155, 24, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
          <meshStandardMaterial color="#1e293b" roughness={0.6} />
        </mesh>

        {/* Subtle Tech Accents per role */}
        {agent.id === 'developer' && (
          /* Sleek Over-Ear Studio Ring for Alex */
          <group position={[0, 0.79, 0]}>
            <mesh position={[0, 0.08, 0]}>
              <torusGeometry args={[0.17, 0.018, 8, 24, Math.PI]} />
              <meshStandardMaterial color="#0f172a" metalness={0.8} />
            </mesh>
            <mesh position={[-0.17, 0, 0]}>
              <cylinderGeometry args={[0.04, 0.04, 0.03, 12]} />
              <meshStandardMaterial color="#06b6d4" emissive="#06b6d4" emissiveIntensity={0.5} />
            </mesh>
            <mesh position={[0.17, 0, 0]}>
              <cylinderGeometry args={[0.04, 0.04, 0.03, 12]} />
              <meshStandardMaterial color="#06b6d4" emissive="#06b6d4" emissiveIntensity={0.5} />
            </mesh>
          </group>
        )}
      </group>

      {/* 4. Floor Nameplate Badge (Direct Stitch 1:1 Minimalist Tag) */}
      <Html position={[0, 0.05, 0.38]} center distanceFactor={14} style={{ pointerEvents: 'none' }}>
        <div className="flex flex-col items-center select-none">
          {/* Main Dark Pill Nameplate */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded shadow-xl border backdrop-blur-md transition-all duration-200 ${
              isSelected || isHovered ? 'scale-110 ring-1 ring-white/30' : 'opacity-90'
            }`}
            style={{

              backgroundColor: 'rgba(10, 14, 22, 0.94)',
              borderColor: isSelected ? agent.color : 'rgba(255, 255, 255, 0.12)',
              boxShadow: isSelected ? `0 0 12px ${agent.color}50` : '0 2px 8px rgba(0,0,0,0.6)',
            }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: agent.color,
                boxShadow: `0 0 6px ${agent.color}`,
              }}
            />
            <span className="text-[11px] font-mono font-bold tracking-wider text-white uppercase">
              {agent.name}
            </span>
          </div>

          {/* Minimal 1-line Status Subtitle when Active */}
          {agent.statusBadge && agent.statusBadge !== 'Standing By' && agent.statusBadge !== 'Awaiting Objective' && (
            <div
              className="mt-1 bg-black/90 backdrop-blur-md text-[9px] font-mono text-gray-300 px-2 py-0.5 rounded border border-white/10 max-w-[170px] truncate text-center shadow-lg"
              style={{ borderColor: `${agent.color}40` }}
            >
              {agent.statusBadge}
            </div>
          )}
        </div>
      </Html>
    </group>
  );
};
