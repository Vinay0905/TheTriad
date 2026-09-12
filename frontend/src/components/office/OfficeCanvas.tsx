import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
import { useOfficeStore } from '../../store/useOfficeStore';
import { AgentCharacter } from './AgentCharacter';

const DeskWithComputer: React.FC<{
  position: [number, number, number];
  rotation?: [number, number, number];
  label: string;
}> = ({ position, rotation = [0, 0, 0], label }) => (
  <group position={position} rotation={rotation}>
    {/* Desk Surface */}
    <mesh position={[0, 0.72, 0]} castShadow receiveShadow>
      <boxGeometry args={[1.6, 0.05, 0.9]} />
      <meshStandardMaterial color="#334155" roughness={0.3} />
    </mesh>
    {/* Desk Legs */}
    <mesh position={[-0.7, 0.35, 0.35]} castShadow>
      <cylinderGeometry args={[0.03, 0.03, 0.7, 8]} />
      <meshStandardMaterial color="#64748b" metalness={0.8} />
    </mesh>
    <mesh position={[0.7, 0.35, 0.35]} castShadow>
      <cylinderGeometry args={[0.03, 0.03, 0.7, 8]} />
      <meshStandardMaterial color="#64748b" metalness={0.8} />
    </mesh>
    <mesh position={[-0.7, 0.35, -0.35]} castShadow>
      <cylinderGeometry args={[0.03, 0.03, 0.7, 8]} />
      <meshStandardMaterial color="#64748b" metalness={0.8} />
    </mesh>
    <mesh position={[0.7, 0.35, -0.35]} castShadow>
      <cylinderGeometry args={[0.03, 0.03, 0.7, 8]} />
      <meshStandardMaterial color="#64748b" metalness={0.8} />
    </mesh>

    {/* Monitor */}
    <group position={[0, 0.75, -0.2]}>
      <mesh position={[0, 0.3, 0]} castShadow>
        <boxGeometry args={[0.8, 0.45, 0.04]} />
        <meshStandardMaterial color="#0f172a" roughness={0.5} />
      </mesh>
      {/* Glowing Screen */}
      <mesh position={[0, 0.3, 0.022]}>
        <planeGeometry args={[0.74, 0.4]} />
        <meshStandardMaterial
          color="#38bdf8"
          emissive="#0284c7"
          emissiveIntensity={0.6}
        />
      </mesh>
      {/* Stand */}
      <mesh position={[0, 0.05, 0]}>
        <cylinderGeometry args={[0.02, 0.02, 0.1, 8]} />
        <meshStandardMaterial color="#475569" />
      </mesh>
      <mesh position={[0, 0.01, 0]}>
        <cylinderGeometry args={[0.12, 0.12, 0.02, 16]} />
        <meshStandardMaterial color="#475569" />
      </mesh>
    </group>

    {/* Keyboard & Mouse */}
    <mesh position={[0, 0.75, 0.15]}>
      <boxGeometry args={[0.4, 0.01, 0.14]} />
      <meshStandardMaterial color="#1e293b" />
    </mesh>
    <mesh position={[0.28, 0.75, 0.15]}>
      <boxGeometry args={[0.07, 0.015, 0.1]} />
      <meshStandardMaterial color="#1e293b" />
    </mesh>

    {/* Office Chair */}
    <group position={[0, 0, 0.65]}>
      <mesh position={[0, 0.45, 0]} castShadow>
        <boxGeometry args={[0.45, 0.06, 0.45]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      <mesh position={[0, 0.75, 0.2]} castShadow>
        <boxGeometry args={[0.45, 0.55, 0.05]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      <mesh position={[0, 0.2, 0]}>
        <cylinderGeometry args={[0.03, 0.03, 0.4, 8]} />
        <meshStandardMaterial color="#64748b" metalness={0.7} />
      </mesh>
    </group>
  </group>
);

const Whiteboard: React.FC<{ position: [number, number, number] }> = ({
  position,
}) => (
  <group position={position}>
    {/* Board Frame */}
    <mesh position={[0, 1.6, 0]} castShadow>
      <boxGeometry args={[3.2, 1.8, 0.08]} />
      <meshStandardMaterial color="#475569" roughness={0.4} />
    </mesh>
    {/* White Surface */}
    <mesh position={[0, 1.6, 0.042]}>
      <planeGeometry args={[3.0, 1.6]} />
      <meshStandardMaterial color="#f8fafc" roughness={0.1} />
    </mesh>
    {/* Legs */}
    <mesh position={[-1.4, 0.6, 0]} castShadow>
      <cylinderGeometry args={[0.04, 0.04, 1.2, 8]} />
      <meshStandardMaterial color="#64748b" metalness={0.6} />
    </mesh>
    <mesh position={[1.4, 0.6, 0]} castShadow>
      <cylinderGeometry args={[0.04, 0.04, 1.2, 8]} />
      <meshStandardMaterial color="#64748b" metalness={0.6} />
    </mesh>
  </group>
);

const CoffeeLounge: React.FC<{ position: [number, number, number] }> = ({
  position,
}) => (
  <group position={position}>
    {/* Sofa */}
    <mesh position={[0, 0.35, 0]} castShadow>
      <boxGeometry args={[1.8, 0.3, 0.8]} />
      <meshStandardMaterial color="#475569" roughness={0.7} />
    </mesh>
    <mesh position={[0, 0.75, -0.35]} castShadow>
      <boxGeometry args={[1.8, 0.5, 0.2]} />
      <meshStandardMaterial color="#475569" roughness={0.7} />
    </mesh>
    {/* Coffee Table */}
    <mesh position={[0, 0.25, 0.8]} castShadow>
      <cylinderGeometry args={[0.45, 0.45, 0.3, 24]} />
      <meshStandardMaterial color="#334155" roughness={0.4} />
    </mesh>
    {/* Coffee Mug */}
    <mesh position={[0.1, 0.43, 0.8]}>
      <cylinderGeometry args={[0.05, 0.04, 0.08, 12]} />
      <meshStandardMaterial color="#f59e0b" />
    </mesh>
  </group>
);

const Plant: React.FC<{ position: [number, number, number] }> = ({ position }) => (
  <group position={position}>
    <mesh position={[0, 0.3, 0]} castShadow>
      <cylinderGeometry args={[0.2, 0.15, 0.6, 16]} />
      <meshStandardMaterial color="#e2e8f0" />
    </mesh>
    <mesh position={[0, 0.75, 0]} castShadow>
      <sphereGeometry args={[0.35, 12, 12]} />
      <meshStandardMaterial color="#22c55e" roughness={0.8} />
    </mesh>
  </group>
);

export const OfficeCanvas: React.FC = () => {
  const agents = useOfficeStore((state) => state.agents);

  return (
    <div className="w-full h-full relative bg-[#0b0f17]">
      <Canvas
        shadows
        camera={{ position: [11, 13, 14], fov: 32 }}
        className="w-full h-full"
      >
        <ambientLight intensity={0.65} />
        <directionalLight
          position={[12, 20, 10]}
          intensity={1.2}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
          shadow-camera-far={40}
          shadow-camera-left={-10}
          shadow-camera-right={10}
          shadow-camera-top={10}
          shadow-camera-bottom={-10}
        />
        <hemisphereLight args={['#93c5fd', '#1e293b', 0.4]} />

        <Suspense fallback={null}>
          {/* Main Floor */}
          <mesh
            position={[0, -0.01, 0]}
            rotation={[-Math.PI / 2, 0, 0]}
            receiveShadow
          >
            <planeGeometry args={[16, 16]} />
            <meshStandardMaterial color="#1e293b" roughness={0.5} />
          </mesh>

          {/* Grid lines floor accent */}
          <gridHelper args={[16, 16, '#334155', '#1e293b']} position={[0, 0, 0]} />

          {/* Back Wall */}
          <mesh position={[0, 2.5, -7.5]} receiveShadow>
            <boxGeometry args={[16, 5, 0.2]} />
            <meshStandardMaterial color="#0f172a" roughness={0.6} />
          </mesh>

          {/* Left Wall */}
          <mesh position={[-7.5, 2.5, 0]} receiveShadow>
            <boxGeometry args={[0.2, 5, 16]} />
            <meshStandardMaterial color="#0f172a" roughness={0.6} />
          </mesh>

          {/* Office Furniture */}
          <DeskWithComputer
            position={[0, 0, -2.5]}
            label="David (Manager)"
          />
          <DeskWithComputer
            position={[-3.5, 0, -1.0]}
            label="Elena (Researcher)"
          />
          <DeskWithComputer
            position={[3.5, 0, -1.0]}
            label="Alex (Developer)"
          />
          <DeskWithComputer
            position={[3.5, 0, 1.5]}
            label="Maya (QA Auditor)"
          />

          <Whiteboard position={[0, 0, -6.5]} />
          <CoffeeLounge position={[-4.5, 0, 3.5]} />

          <Plant position={[-6, 0, -6]} />
          <Plant position={[6, 0, -6]} />
          <Plant position={[-6, 0, 6]} />

          {/* Render Active Agents */}
          {Object.values(agents).map((agent) => (
            <AgentCharacter key={agent.id} agent={agent} />
          ))}

          {/* Contact Shadows */}
          <ContactShadows
            position={[0, 0, 0]}
            opacity={0.6}
            scale={16}
            blur={1.5}
            far={10}
            resolution={512}
            color="#000000"
          />

          <OrbitControls
            enableDamping
            dampingFactor={0.05}
            maxPolarAngle={Math.PI / 2.15}
            minDistance={8}
            maxDistance={25}
            target={[0, 0.5, 0]}
          />
        </Suspense>
      </Canvas>
    </div>
  );
};
