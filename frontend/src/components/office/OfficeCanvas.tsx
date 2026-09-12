import React, { Suspense, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
import { useOfficeStore } from '../../store/useOfficeStore';
import { AgentCharacter } from './AgentCharacter';

// ============================================================================
// Modern Architectural 3D Office Environment
// Style: High-End Scandinavian Tech Studio / Silicon Valley Miniature
// ============================================================================

const ParquetFloor: React.FC = () => {
  // Generate subtle wood plank grid lines
  return (
    <group position={[0, 0, 0]}>
      {/* Warm Wood Floor Base */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, -0.01, 0]}>
        <planeGeometry args={[18, 18]} />
        <meshStandardMaterial
          color="#d8b48f"
          roughness={0.4}
          metalness={0.05}
        />
      </mesh>

      {/* Decorative Woven Area Rug under Coffee Lounge */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[-4.2, 0.005, 3.2]}>
        <planeGeometry args={[4.2, 3.8]} />
        <meshStandardMaterial
          color="#334155"
          roughness={0.9}
        />
      </mesh>

      {/* Conference Rug */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, 0.005, -5.5]}>
        <circleGeometry args={[2.5, 32]} />
        <meshStandardMaterial
          color="#1e293b"
          roughness={0.85}
        />
      </mesh>
    </group>
  );
};

const AcousticWoodWall: React.FC<{ position: [number, number, number] }> = ({ position }) => {
  // Acoustic vertical timber slat feature wall
  const slats = useMemo(() => {
    const items = [];
    for (let i = -7.5; i <= 7.5; i += 0.35) {
      items.push(i);
    }
    return items;
  }, []);

  return (
    <group position={position}>
      {/* Back Wall Base (Warm White/Greige) */}
      <mesh position={[0, 2.5, 0]} receiveShadow>
        <boxGeometry args={[18, 5, 0.2]} />
        <meshStandardMaterial color="#f1f5f9" roughness={0.7} />
      </mesh>

      {/* Baseboard */}
      <mesh position={[0, 0.15, 0.11]} receiveShadow>
        <boxGeometry args={[18, 0.3, 0.05]} />
        <meshStandardMaterial color="#334155" />
      </mesh>

      {/* Vertical Timber Slats (Accent Area behind Whiteboard & Desks) */}
      <group position={[0, 2.5, 0.11]}>
        {slats.map((x, idx) => (
          <mesh key={idx} position={[x, 0, 0]} castShadow>
            <boxGeometry args={[0.15, 4.8, 0.04]} />
            <meshStandardMaterial color="#9a6e42" roughness={0.5} />
          </mesh>
        ))}
      </group>

      {/* Backlit Company Logo Sign "TRIAD COUNCIL" */}
      <group position={[0, 4.2, 0.15]}>
        <mesh castShadow>
          <boxGeometry args={[4.2, 0.6, 0.06]} />
          <meshStandardMaterial color="#0f172a" roughness={0.3} />
        </mesh>
        {/* Glow backlight */}
        <mesh position={[0, 0, -0.02]}>
          <planeGeometry args={[4.4, 0.8]} />
          <meshBasicMaterial color="#38bdf8" />
        </mesh>
      </group>
    </group>
  );
};

const PanoramicWindowWall: React.FC<{ position: [number, number, number] }> = ({ position }) => {
  return (
    <group position={position}>
      {/* Left Solid Wall Ends */}
      <mesh position={[0, 2.5, -6.5]} receiveShadow>
        <boxGeometry args={[0.3, 5, 5]} />
        <meshStandardMaterial color="#f1f5f9" roughness={0.7} />
      </mesh>
      <mesh position={[0, 2.5, 6.5]} receiveShadow>
        <boxGeometry args={[0.3, 5, 5]} />
        <meshStandardMaterial color="#f1f5f9" roughness={0.7} />
      </mesh>

      {/* Window Header & Sill */}
      <mesh position={[0, 4.6, 0]} castShadow>
        <boxGeometry args={[0.3, 0.8, 8]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      <mesh position={[0, 0.3, 0]} castShadow>
        <boxGeometry args={[0.35, 0.6, 8]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>

      {/* Black Window Mullions / Frames */}
      <mesh position={[0, 2.5, -2]} castShadow>
        <boxGeometry args={[0.15, 3.8, 0.1]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>
      <mesh position={[0, 2.5, 2]} castShadow>
        <boxGeometry args={[0.15, 3.8, 0.1]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>
      <mesh position={[0, 2.5, 0]} castShadow>
        <boxGeometry args={[0.15, 0.1, 8]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>

      {/* Glass Pane with subtle reflection and sky tint */}
      <mesh position={[-0.05, 2.5, 0]}>
        <planeGeometry args={[8, 3.8]} />
        <meshPhysicalMaterial
          color="#bae6fd"
          transmission={0.85}
          opacity={0.35}
          transparent
          roughness={0.05}
          ior={1.5}
        />
      </mesh>

      {/* Outside City Sky Backdrop */}
      <mesh position={[-3.5, 2.5, 0]} rotation={[0, Math.PI / 2, 0]}>
        <planeGeometry args={[20, 10]} />
        <meshBasicMaterial color="#e0f2fe" />
      </mesh>
    </group>
  );
};

const ModernWorkstation: React.FC<{
  position: [number, number, number];
  rotation?: [number, number, number];
  deskColor?: string;
  nameTag?: string;
}> = ({ position, rotation = [0, 0, 0], deskColor = '#f8fafc' }) => (
  <group position={position} rotation={rotation}>
    {/* Desk Tabletop (Light Oak / Clean White with Chamfered Edges) */}
    <mesh position={[0, 0.72, 0]} castShadow receiveShadow>
      <boxGeometry args={[1.7, 0.05, 0.95]} />
      <meshStandardMaterial color={deskColor} roughness={0.3} />
    </mesh>

    {/* Modern Metal A-Frame Legs (Matte Black) */}
    <mesh position={[-0.72, 0.35, 0]} castShadow>
      <boxGeometry args={[0.04, 0.7, 0.8]} />
      <meshStandardMaterial color="#1e293b" metalness={0.8} roughness={0.3} />
    </mesh>
    <mesh position={[0.72, 0.35, 0]} castShadow>
      <boxGeometry args={[0.04, 0.7, 0.8]} />
      <meshStandardMaterial color="#1e293b" metalness={0.8} roughness={0.3} />
    </mesh>

    {/* Felt Desk Mat / Pad */}
    <mesh position={[0, 0.75, 0.05]} receiveShadow>
      <boxGeometry args={[1.2, 0.01, 0.55]} />
      <meshStandardMaterial color="#334155" roughness={0.8} />
    </mesh>

    {/* Dual Curved Ultra-Wide Monitors */}
    <group position={[-0.32, 0.75, -0.22]} rotation={[0, 0.15, 0]}>
      {/* Screen Frame */}
      <mesh position={[0, 0.35, 0]} castShadow>
        <boxGeometry args={[0.7, 0.42, 0.03]} />
        <meshStandardMaterial color="#090d16" roughness={0.4} />
      </mesh>
      {/* Code Screen Glow */}
      <mesh position={[0, 0.35, 0.016]}>
        <planeGeometry args={[0.66, 0.38]} />
        <meshStandardMaterial
          color="#38bdf8"
          emissive="#0284c7"
          emissiveIntensity={0.7}
        />
      </mesh>
      {/* Articulating Arm Stand */}
      <mesh position={[0, 0.08, 0]}>
        <cylinderGeometry args={[0.018, 0.018, 0.16, 12]} />
        <meshStandardMaterial color="#0f172a" metalness={0.8} />
      </mesh>
    </group>

    <group position={[0.32, 0.75, -0.22]} rotation={[0, -0.15, 0]}>
      <mesh position={[0, 0.35, 0]} castShadow>
        <boxGeometry args={[0.7, 0.42, 0.03]} />
        <meshStandardMaterial color="#090d16" roughness={0.4} />
      </mesh>
      <mesh position={[0, 0.35, 0.016]}>
        <planeGeometry args={[0.66, 0.38]} />
        <meshStandardMaterial
          color="#10b981"
          emissive="#059669"
          emissiveIntensity={0.6}
        />
      </mesh>
      <mesh position={[0, 0.08, 0]}>
        <cylinderGeometry args={[0.018, 0.018, 0.16, 12]} />
        <meshStandardMaterial color="#0f172a" metalness={0.8} />
      </mesh>
    </group>

    {/* Mechanical Keyboard with Backlight */}
    <mesh position={[0, 0.76, 0.12]} castShadow>
      <boxGeometry args={[0.38, 0.018, 0.14]} />
      <meshStandardMaterial color="#0f172a" roughness={0.3} />
    </mesh>
    {/* Wireless Mouse */}
    <mesh position={[0.28, 0.76, 0.12]} castShadow>
      <boxGeometry args={[0.07, 0.02, 0.11]} />
      <meshStandardMaterial color="#0f172a" roughness={0.3} />
    </mesh>

    {/* Ceramic Coffee Mug on Coaster */}
    <group position={[-0.48, 0.75, 0.1]}>
      <mesh position={[0, 0.005, 0]}>
        <cylinderGeometry args={[0.06, 0.06, 0.01, 16]} />
        <meshStandardMaterial color="#78350f" />
      </mesh>
      <mesh position={[0, 0.05, 0]} castShadow>
        <cylinderGeometry args={[0.045, 0.04, 0.08, 16]} />
        <meshStandardMaterial color="#f8fafc" roughness={0.2} />
      </mesh>
    </group>

    {/* Herman Miller-Style Ergonomic Mesh Chair */}
    <group position={[0, 0, 0.65]}>
      {/* Contoured Mesh Seat */}
      <mesh position={[0, 0.46, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.5, 0.07, 0.48]} />
        <meshStandardMaterial color="#1e293b" roughness={0.6} />
      </mesh>
      {/* Mesh High-Back Lumbar Support */}
      <mesh position={[0, 0.82, 0.22]} rotation={[-0.1, 0, 0]} castShadow>
        <boxGeometry args={[0.46, 0.65, 0.05]} />
        <meshStandardMaterial color="#0f172a" roughness={0.5} />
      </mesh>
      {/* Armrests */}
      <mesh position={[-0.24, 0.62, 0.05]} castShadow>
        <boxGeometry args={[0.05, 0.04, 0.28]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>
      <mesh position={[0.24, 0.62, 0.05]} castShadow>
        <boxGeometry args={[0.05, 0.04, 0.28]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>
      {/* Gas Lift Pneumatic Cylinder */}
      <mesh position={[0, 0.23, 0]}>
        <cylinderGeometry args={[0.025, 0.025, 0.42, 12]} />
        <meshStandardMaterial color="#64748b" metalness={0.9} />
      </mesh>
      {/* 5-Star Caster Base */}
      <mesh position={[0, 0.04, 0]}>
        <cylinderGeometry args={[0.3, 0.3, 0.04, 5]} />
        <meshStandardMaterial color="#1e293b" metalness={0.8} />
      </mesh>
    </group>
  </group>
);

const ArchitecturalWhiteboard: React.FC<{ position: [number, number, number] }> = ({ position }) => (
  <group position={position}>
    {/* Large Frosted Glass Whiteboard Surface with Aluminium Standoffs */}
    <mesh position={[0, 1.8, 0]} castShadow>
      <boxGeometry args={[3.8, 2.0, 0.06]} />
      <meshStandardMaterial
        color="#ffffff"
        roughness={0.1}
        metalness={0.1}
      />
    </mesh>
    {/* Top Accent Header Bar */}
    <mesh position={[0, 2.82, 0.02]} castShadow>
      <boxGeometry args={[3.84, 0.06, 0.08]} />
      <meshStandardMaterial color="#0f172a" />
    </mesh>

    {/* Sticky Notes & Architecture Diagram Boxes */}
    <group position={[0, 1.8, 0.035]}>
      {/* Yellow Sticky Notes */}
      <mesh position={[-1.2, 0.4, 0]}>
        <planeGeometry args={[0.28, 0.28]} />
        <meshBasicMaterial color="#fef08a" />
      </mesh>
      <mesh position={[-0.85, 0.4, 0]}>
        <planeGeometry args={[0.28, 0.28]} />
        <meshBasicMaterial color="#fbcfe8" />
      </mesh>
      <mesh position={[-0.5, 0.4, 0]}>
        <planeGeometry args={[0.28, 0.28]} />
        <meshBasicMaterial color="#bbf7d0" />
      </mesh>

      {/* Architecture Boxes (Simulated TDD / Flow Blueprint) */}
      <mesh position={[0.4, 0.3, 0]}>
        <planeGeometry args={[0.75, 0.45]} />
        <meshBasicMaterial color="#e0f2fe" />
      </mesh>
      <mesh position={[1.3, 0.3, 0]}>
        <planeGeometry args={[0.75, 0.45]} />
        <meshBasicMaterial color="#dcfce7" />
      </mesh>
      <mesh position={[0.85, -0.4, 0]}>
        <planeGeometry args={[0.9, 0.45]} />
        <meshBasicMaterial color="#fef3c7" />
      </mesh>
    </group>

    {/* Marker Tray */}
    <mesh position={[0, 0.78, 0.06]} castShadow>
      <boxGeometry args={[3.2, 0.04, 0.12]} />
      <meshStandardMaterial color="#475569" metalness={0.8} />
    </mesh>
  </group>
);

const DesignerLounge: React.FC<{ position: [number, number, number] }> = ({ position }) => (
  <group position={position}>
    {/* Modular Scandinavian Sectional Sofa (Warm Teal/Petrol Blue) */}
    <group position={[0, 0, 0]}>
      <mesh position={[0, 0.25, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.2, 0.32, 0.95]} />
        <meshStandardMaterial color="#0369a1" roughness={0.75} />
      </mesh>
      <mesh position={[0, 0.65, -0.4]} castShadow>
        <boxGeometry args={[2.2, 0.5, 0.22]} />
        <meshStandardMaterial color="#0369a1" roughness={0.75} />
      </mesh>
      {/* Decorative Throw Cushions */}
      <mesh position={[-0.7, 0.52, -0.22]} rotation={[0.2, 0.2, 0]}>
        <boxGeometry args={[0.35, 0.35, 0.12]} />
        <meshStandardMaterial color="#f59e0b" roughness={0.8} />
      </mesh>
      <mesh position={[0.7, 0.52, -0.22]} rotation={[0.2, -0.2, 0]}>
        <boxGeometry args={[0.35, 0.35, 0.12]} />
        <meshStandardMaterial color="#f8fafc" roughness={0.8} />
      </mesh>
    </group>

    {/* Marble Round Coffee Table */}
    <group position={[0, 0, 1.1]}>
      <mesh position={[0, 0.32, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.55, 0.55, 0.04, 32]} />
        <meshStandardMaterial color="#f8fafc" roughness={0.2} />
      </mesh>
      <mesh position={[0, 0.15, 0]}>
        <cylinderGeometry args={[0.04, 0.04, 0.3, 12]} />
        <meshStandardMaterial color="#0f172a" metalness={0.8} />
      </mesh>
      <mesh position={[0, 0.01, 0]}>
        <cylinderGeometry args={[0.3, 0.3, 0.02, 24]} />
        <meshStandardMaterial color="#0f172a" metalness={0.8} />
      </mesh>
    </group>

    {/* Espresso Bar Credenza */}
    <group position={[-2.4, 0, 0]} rotation={[0, Math.PI / 2, 0]}>
      <mesh position={[0, 0.45, 0]} castShadow receiveShadow>
        <boxGeometry args={[1.5, 0.9, 0.6]} />
        <meshStandardMaterial color="#1e293b" roughness={0.4} />
      </mesh>
      {/* Italian Espresso Machine */}
      <mesh position={[0, 1.05, 0]} castShadow>
        <boxGeometry args={[0.45, 0.35, 0.38]} />
        <meshStandardMaterial color="#e2e8f0" metalness={0.9} roughness={0.1} />
      </mesh>
      {/* Glowing Coffee On-LED */}
      <mesh position={[0.16, 1.1, 0.2]}>
        <sphereGeometry args={[0.018, 8, 8]} />
        <meshBasicMaterial color="#22c55e" />
      </mesh>
    </group>
  </group>
);

const PottedFiddleLeafFig: React.FC<{ position: [number, number, number] }> = ({ position }) => (
  <group position={position}>
    {/* Ribbed Ceramic Pot */}
    <mesh position={[0, 0.35, 0]} castShadow>
      <cylinderGeometry args={[0.32, 0.24, 0.7, 24]} />
      <meshStandardMaterial color="#fafaf9" roughness={0.3} />
    </mesh>
    {/* Soil */}
    <mesh position={[0, 0.68, 0]}>
      <cylinderGeometry args={[0.3, 0.3, 0.04, 16]} />
      <meshStandardMaterial color="#3f2e1e" roughness={0.9} />
    </mesh>
    {/* Main Stem */}
    <mesh position={[0, 1.2, 0]}>
      <cylinderGeometry args={[0.035, 0.045, 1.1, 8]} />
      <meshStandardMaterial color="#57412b" roughness={0.8} />
    </mesh>
    {/* Sculpted Large Broad Leaves */}
    {[
      { y: 0.9, r: 0.4, rot: 0.2 },
      { y: 1.15, r: 0.45, rot: 1.8 },
      { y: 1.35, r: 0.5, rot: 3.4 },
      { y: 1.55, r: 0.48, rot: 4.9 },
      { y: 1.75, r: 0.42, rot: 1.1 },
    ].map((leaf, idx) => (
      <group key={idx} position={[0, leaf.y, 0]} rotation={[0.3, leaf.rot, 0.4]}>
        <mesh position={[0.25, 0, 0]} castShadow>
          <boxGeometry args={[0.42, 0.015, 0.28]} />
          <meshStandardMaterial color="#15803d" roughness={0.5} />
        </mesh>
      </group>
    ))}
  </group>
);

export const OfficeCanvas: React.FC = () => {
  const agents = useOfficeStore((state) => state.agents);

  return (
    <div className="w-full h-full relative bg-[#090d16]">
      <Canvas
        shadows
        camera={{ position: [11, 13, 14], fov: 32 }}
        className="w-full h-full"
      >
        {/* Warm Ambient Fill Lighting */}
        <ambientLight intensity={1.1} color="#f8fafc" />

        {/* Angled Directional Sunlight streaming from window */}
        <directionalLight
          position={[-14, 18, 8]}
          intensity={2.2}
          color="#fffbeb"
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
          shadow-camera-far={45}
          shadow-camera-left={-12}
          shadow-camera-right={12}
          shadow-camera-top={12}
          shadow-camera-bottom={-12}
          shadow-bias={-0.0001}
        />

        {/* Soft Ceiling Downlight Fill */}
        <pointLight position={[0, 8, 0]} intensity={0.8} color="#fef08a" distance={20} />

        <Suspense fallback={null}>
          {/* Flooring & Rugs */}
          <ParquetFloor />

          {/* Architectural Walls */}
          <AcousticWoodWall position={[0, 0, -8.0]} />
          <PanoramicWindowWall position={[-8.5, 0, 0]} />

          {/* 4 Modern Workstations with Dual Monitors */}
          <ModernWorkstation
            position={[0, 0, -2.5]}
            deskColor="#f8fafc"
            nameTag="David (Manager)"
          />
          <ModernWorkstation
            position={[-3.8, 0, -1.0]}
            deskColor="#fef08a"
            nameTag="Elena (Researcher)"
          />
          <ModernWorkstation
            position={[3.8, 0, -1.0]}
            deskColor="#f8fafc"
            nameTag="Alex (Developer)"
          />
          <ModernWorkstation
            position={[3.8, 0, 1.8]}
            deskColor="#f8fafc"
            nameTag="Maya (QA Auditor)"
          />

          {/* Whiteboard & Presentation Zone */}
          <ArchitecturalWhiteboard position={[0, 0, -7.0]} />

          {/* Coffee Bar & Designer Lounge */}
          <DesignerLounge position={[-4.5, 0, 3.8]} />

          {/* Greenery / Indoor Plants */}
          <PottedFiddleLeafFig position={[-7.2, 0, -6.5]} />
          <PottedFiddleLeafFig position={[7.0, 0, -6.8]} />
          <PottedFiddleLeafFig position={[-7.2, 0, 6.5]} />
          <PottedFiddleLeafFig position={[7.0, 0, 6.5]} />

          {/* Render Active Autonomous Agents */}
          {Object.values(agents).map((agent) => (
            <AgentCharacter key={agent.id} agent={agent} />
          ))}

          {/* Soft Ground Contact Shadows */}
          <ContactShadows
            position={[0, 0, 0]}
            opacity={0.65}
            scale={18}
            blur={1.8}
            far={10}
            resolution={1024}
            color="#090d16"
          />

          {/* Smooth Orbit Camera Rig */}
          <OrbitControls
            enableDamping
            dampingFactor={0.05}
            maxPolarAngle={Math.PI / 2.2}
            minDistance={8}
            maxDistance={28}
            target={[0, 0.8, 0]}
          />
        </Suspense>
      </Canvas>
    </div>
  );
};
