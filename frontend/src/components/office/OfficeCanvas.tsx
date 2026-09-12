import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows, Html } from '@react-three/drei';

import { useOfficeStore } from '../../store/useOfficeStore';
import { AgentCharacter } from './AgentCharacter';
import { OfficeLife } from './OfficeLife';

// ============================================================================
// STITCH NORDIC STUDIO HUD - 3D ARCHITECTURAL ROOM
// Palette:
//   Floor: Smoked walnut parquet (#211b19), separated from warmer desks
//   Background: Deep Obsidian (#070a10)
//   Left Wall: Acoustic Cedar Slats (#7e5a36 / #926940) + Neon Green EXIT Door
//   Right Wall: Oslo Skyline Panoramic Windows with Cityscape Silhouettes
//   Center Hub: Dual Modern Workstation Pods (North: David & Elena, South: Alex & Maya)
//   West Corner: Carrara Marble Espresso Bar with steam
//   East Corner: Round Nordic Birch Meeting Table with Pendant Light
//   North Wall: Wall-Mounted Glass Whiteboard with Colored Sticky Notes
// ============================================================================

// 1. Light Scandinavian Nordic Bleached Oak / Architectural Sand Floor
const ParquetFloor: React.FC = () => {
  return (
    <group position={[0, 0, 0]}>
      {/* Light Natural Nordic Bleached Oak Foundation */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, -0.01, 0]}>
        <planeGeometry args={[19, 19]} />
        <meshStandardMaterial
          color="#ded5c4"
          roughness={0.5}
          metalness={0.04}
        />
      </mesh>

      {/* Decorative Subtle Slat / Tile Grid Joints */}
      {Array.from({ length: 19 }).map((_, i) => (
        <mesh
          key={i}
          rotation={[-Math.PI / 2, 0, 0]}
          position={[-9 + i * 1.0, 0.001, 0]}
        >
          <planeGeometry args={[0.02, 18.8]} />
          <meshBasicMaterial color="#b8ab96" opacity={0.35} transparent />
        </mesh>
      ))}

      {Array.from({ length: 19 }).map((_, j) => (
        <mesh
          key={j}
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, 0.001, -9 + j * 1.0]}
        >
          <planeGeometry args={[18.8, 0.02]} />
          <meshBasicMaterial color="#b8ab96" opacity={0.35} transparent />
        </mesh>
      ))}

      {/* Meeting Table Area Inset Ring */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[4.8, 0.003, 3.4]}>
        <ringGeometry args={[1.8, 1.84, 32]} />
        <meshBasicMaterial color="#9a7fcb" opacity={0.25} transparent />
      </mesh>

      {/* Coffee Bar Floor Glow Ring */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[-4.8, 0.003, 3.4]}>
        <ringGeometry args={[1.7, 1.74, 32]} />
        <meshBasicMaterial color="#0284c7" opacity={0.2} transparent />
      </mesh>
    </group>
  );
};

// 2. North Wall with Glass Whiteboard & Track Lighting
const NorthWall: React.FC<{ position: [number, number, number] }> = ({ position }) => {
  return (
    <group position={position}>
      {/* Wall Substrate (Deep Obsidian Blue #141923) */}
      <mesh position={[0, 2.5, 0]} receiveShadow>
        <boxGeometry args={[18.4, 5.2, 0.25]} />
        <meshStandardMaterial color="#141923" roughness={0.7} />
      </mesh>

      {/* Baseboard */}
      <mesh position={[0, 0.15, 0.13]} receiveShadow>
        <boxGeometry args={[18.4, 0.3, 0.06]} />
        <meshStandardMaterial color="#0b0f17" />
      </mesh>

      {/* Overhead Whiteboard Track Light Bar (Physical Light Source) */}
      <group position={[0, 3.9, 0.4]}>
        {/* Track Rail */}
        <mesh castShadow>
          <boxGeometry args={[4.4, 0.05, 0.05]} />
          <meshStandardMaterial color="#0f172a" metalness={0.8} />
        </mesh>
        {/* Spotlight Heads & Beams */}
        {[-1.3, 0, 1.3].map((x, idx) => (
          <group key={idx} position={[x, -0.06, 0]}>
            <mesh rotation={[0.45, 0, 0]} castShadow>
              <cylinderGeometry args={[0.045, 0.07, 0.12, 16]} />
              <meshStandardMaterial color="#1e293b" metalness={0.7} />
            </mesh>
            {/* Glowing Lens */}
            <mesh position={[0, -0.05, 0.02]} rotation={[0.45, 0, 0]}>
              <circleGeometry args={[0.06, 16]} />
              <meshStandardMaterial color="#fffbeb" emissive="#fff4cc" emissiveIntensity={1.8} />
            </mesh>
            {/* Directed Spotlight onto Whiteboard */}
            <spotLight
              position={[0, 0, 0]}
              target-position={[0, -2.0, -0.25]}
              intensity={1.2}
              distance={4.5}
              angle={Math.PI / 4.5}
              penumbra={0.4}
              color="#fffbeb"
            />
          </group>
        ))}
      </group>

      {/* Architectural Whiteboard */}
      <group position={[0, 2.1, 0.16]}>
        {/* Glass Whiteboard Pane */}
        <mesh castShadow receiveShadow>
          <boxGeometry args={[4.2, 2.1, 0.04]} />
          <meshStandardMaterial
            color="#dfe2ee"
            roughness={0.15}
            metalness={0.1}
            opacity={0.96}
            transparent
          />
        </mesh>
        {/* Aluminum Frame */}
        <mesh position={[0, 1.08, 0.02]} castShadow>
          <boxGeometry args={[4.26, 0.05, 0.06]} />
          <meshStandardMaterial color="#3d494c" metalness={0.8} />
        </mesh>
        <mesh position={[0, -1.08, 0.02]} castShadow>
          <boxGeometry args={[4.26, 0.05, 0.06]} />
          <meshStandardMaterial color="#3d494c" metalness={0.8} />
        </mesh>
        <mesh position={[-2.13, 0, 0.02]} castShadow>
          <boxGeometry args={[0.05, 2.16, 0.06]} />
          <meshStandardMaterial color="#3d494c" metalness={0.8} />
        </mesh>
        <mesh position={[2.13, 0, 0.02]} castShadow>
          <boxGeometry args={[0.05, 2.16, 0.06]} />
          <meshStandardMaterial color="#3d494c" metalness={0.8} />
        </mesh>

        {/* Marker Tray */}
        <mesh position={[0, -1.12, 0.07]} castShadow>
          <boxGeometry args={[3.6, 0.04, 0.14]} />
          <meshStandardMaterial color="#869397" metalness={0.8} />
        </mesh>

        {/* Sticky Notes & Architecture Sketches */}
        <group position={[0, 0, 0.025]}>
          {/* Yellow, Pink, Green Sticky Notes */}
          <mesh position={[-1.4, 0.5, 0]}>
            <planeGeometry args={[0.35, 0.35]} />
            <meshBasicMaterial color="#fef08a" />
          </mesh>
          <mesh position={[-0.95, 0.5, 0]}>
            <planeGeometry args={[0.35, 0.35]} />
            <meshBasicMaterial color="#a7f3d0" />
          </mesh>
          <mesh position={[-0.5, 0.5, 0]}>
            <planeGeometry args={[0.35, 0.35]} />
            <meshBasicMaterial color="#fbcfe8" />
          </mesh>
          {/* Architecture Blueprint Boxes */}
          <mesh position={[0.6, 0.35, 0]}>
            <planeGeometry args={[0.9, 0.55]} />
            <meshBasicMaterial color="#00687a" />
          </mesh>
          <mesh position={[1.6, 0.35, 0]}>
            <planeGeometry args={[0.9, 0.55]} />
            <meshBasicMaterial color="#0284c7" />
          </mesh>
        </group>

        {/* Header Tag Pill */}
        <group position={[0, 1.25, 0.04]}>
          <mesh>
            <boxGeometry args={[2.4, 0.3, 0.03]} />
            <meshStandardMaterial color="#0a0e16" />
          </mesh>
          <mesh position={[0, 0, 0.02]}>
            <planeGeometry args={[2.3, 0.24]} />
            <meshBasicMaterial color="#06b6d4" opacity={0.25} transparent />
          </mesh>
        </group>
      </group>
    </group>
  );
};

/** Server-synchronised clock beside the presentation board. */
const OfficeWallClock: React.FC = () => {
  const clock = useOfficeStore((state) => state.officeClock);
  const offHours = clock.phase === 'OFF_HOURS';

  return (
    <group position={[3.15, 2.5, -7.82]}>
      <mesh castShadow>
        <boxGeometry args={[1.45, 0.78, 0.08]} />
        <meshStandardMaterial color={offHours ? '#221a22' : '#101d25'} metalness={0.45} roughness={0.32} />
      </mesh>
      <Html center transform distanceFactor={12} position={[0, 0, 0.055]} style={{ pointerEvents: 'none' }}>
        <div className={`w-[126px] rounded border px-2 py-1.5 text-center font-mono shadow-xl ${offHours ? 'border-rose-400/40 bg-[#20151f]/95 text-rose-200' : 'border-cyan-300/35 bg-[#0d1922]/95 text-cyan-100'}`}>
          <div className="text-[9px] font-bold tracking-[0.16em]">{offHours ? 'OFF HOURS' : 'TRIAD TIME'}</div>
          <div className="mt-0.5 text-[19px] font-bold leading-none tabular-nums">{clock.displayTime}</div>
          <div className="mt-1 text-[8px] tracking-wide opacity-75">DAY {clock.dayNumber} · {Math.ceil(clock.secondsRemaining / 60)} MIN</div>
        </div>
      </Html>
    </group>
  );
};

// 3. West Wall with Acoustic Cedar Slats & Illuminated EXIT Door
const WestWall: React.FC<{ position: [number, number, number] }> = ({ position }) => {
  return (
    <group position={position}>
      {/* Wall Substrate */}
      <mesh position={[0, 2.5, 0]} receiveShadow>
        <boxGeometry args={[0.25, 5.2, 18.4]} />
        <meshStandardMaterial color="#141923" roughness={0.7} />
      </mesh>

      {/* Vertical Cedar Acoustic Slats */}
      {Array.from({ length: 16 }).map((_, i) => (
        <mesh
          key={i}
          position={[0.14, 2.5, -6 + i * 0.45]}
          castShadow
        >
          <boxGeometry args={[0.04, 4.8, 0.16]} />
          <meshStandardMaterial
            color={i % 2 === 0 ? '#7e5a36' : '#926940'}
            roughness={0.6}
          />
        </mesh>
      ))}

      {/* Studio Entrance Door with Illuminated EXIT */}
      <group position={[0.14, 1.8, 2.8]}>
        {/* Door Frame */}
        <mesh castShadow>
          <boxGeometry args={[0.06, 3.6, 1.9]} />
          <meshStandardMaterial color="#3d494c" metalness={0.7} />
        </mesh>
        {/* Frosted Glass Door Leaf */}
        <mesh position={[0.02, 0, 0]}>
          <boxGeometry args={[0.02, 3.4, 1.7]} />
          <meshPhysicalMaterial
            color="#4cd7f6"
            transmission={0.8}
            opacity={0.3}
            transparent
            roughness={0.1}
          />
        </mesh>
        {/* Stainless Door Handle */}
        <mesh position={[0.05, 0, 0.7]}>
          <cylinderGeometry args={[0.02, 0.02, 0.8, 12]} />
          <meshStandardMaterial color="#dfe2ee" metalness={0.9} />
        </mesh>
        {/* Illuminated Green EXIT Badge */}
        <group position={[0.05, 1.95, 0]}>
          <mesh>
            <boxGeometry args={[0.04, 0.28, 0.8]} />
            <meshStandardMaterial color="#064e3b" emissive="#10b981" emissiveIntensity={0.6} />
          </mesh>
        </group>
      </group>
    </group>
  );
};

// 4. East Wall: Panoramic Floor-to-Ceiling Oslo Cityscape Windows
const EastWindowWall: React.FC<{ position: [number, number, number] }> = ({ position }) => {
  return (
    <group position={position}>
      {/* Structural Framing Header & Sill */}
      <mesh position={[0, 4.8, 0]} castShadow>
        <boxGeometry args={[0.3, 0.6, 18.4]} />
        <meshStandardMaterial color="#1e2533" />
      </mesh>
      <mesh position={[0, 0.2, 0]} castShadow>
        <boxGeometry args={[0.3, 0.4, 18.4]} />
        <meshStandardMaterial color="#1e2533" />
      </mesh>

      {/* Vertical Mullions */}
      {[-6, -3, 0, 3, 6].map((zPos, idx) => (
        <mesh key={idx} position={[0, 2.5, zPos]} castShadow>
          <boxGeometry args={[0.2, 4.2, 0.12]} />
          <meshStandardMaterial color="#253245" metalness={0.6} />
        </mesh>
      ))}

      {/* Horizontal Transom Bar */}
      <mesh position={[0, 2.5, 0]} castShadow>
        <boxGeometry args={[0.18, 0.1, 18.4]} />
        <meshStandardMaterial color="#1d2737" metalness={0.6} />
      </mesh>

      {/* Glass Pane */}
      <mesh position={[-0.04, 2.5, 0]}>
        <boxGeometry args={[0.02, 4.2, 18.2]} />
        <meshPhysicalMaterial
          color="#acedff"
          transmission={0.88}
          opacity={0.3}
          transparent
          roughness={0.05}
        />
      </mesh>

      {/* Distant Oslo Night Skyline Backdrop */}
      <group position={[2.8, 2.5, 0]} rotation={[0, -Math.PI / 2, 0]}>
        {/* Night Gradient Plane */}
        <mesh position={[0, 0, 0]}>
          <planeGeometry args={[24, 8]} />
          <meshBasicMaterial color="#0c1624" />
        </mesh>
        {/* Skyscraper Silhouettes */}
        {[
          { x: -7, h: 4.5, w: 2.2, color: '#080e18' },
          { x: -4, h: 3.5, w: 1.8, color: '#060c14' },
          { x: -1, h: 5.2, w: 2.4, color: '#080e18' },
          { x: 3, h: 4.0, w: 2.0, color: '#050a10' },
          { x: 6, h: 3.2, w: 1.6, color: '#080e18' },
        ].map((b, i) => (
          <mesh key={i} position={[b.x, -4 + b.h / 2, 0.05]}>
            <planeGeometry args={[b.w, b.h]} />
            <meshBasicMaterial color={b.color} />
          </mesh>
        ))}
      </group>
    </group>
  );
};

// 5. Dual Modern Workstation Bench Pod (Shared Table for 2 Agents)
const DualBenchPod: React.FC<{
  position: [number, number, number];
  podLabel?: string;
  leftAgent: { name: string; color: string; monitorType: 'ultrawide' | 'dual' };
  rightAgent: { name: string; color: string; monitorType: 'dual' | 'triple' };
  deskColor: string;
  deskPadColor: string;
}> = ({ position, leftAgent, rightAgent, deskColor, deskPadColor }) => {
  return (
    <group position={position}>
      {/* Shared Modern Oak Dual Bench Desk */}
      <mesh position={[0, 0.72, 0]} castShadow receiveShadow>
        <boxGeometry args={[4.4, 0.06, 1.4]} />
        <meshStandardMaterial color={deskColor} roughness={0.46} />
      </mesh>

      {/* Central Cable Spine & Divider Partition */}
      <mesh position={[0, 0.9, 0]}>
        <boxGeometry args={[4.2, 0.28, 0.04]} />
        <meshStandardMaterial color="#1e2533" roughness={0.7} />
      </mesh>

      {/* Matte Black Steel Legs */}
      <mesh position={[-2.1, 0.36, 0]} castShadow>
        <boxGeometry args={[0.06, 0.72, 1.3]} />
        <meshStandardMaterial color="#1c2028" metalness={0.8} />
      </mesh>
      <mesh position={[2.1, 0.36, 0]} castShadow>
        <boxGeometry args={[0.06, 0.72, 1.3]} />
        <meshStandardMaterial color="#1c2028" metalness={0.8} />
      </mesh>
      <mesh position={[0, 0.36, 0]} castShadow>
        <boxGeometry args={[0.06, 0.72, 1.3]} />
        <meshStandardMaterial color="#1c2028" metalness={0.8} />
      </mesh>

      {/* Suspended Architectural Linear Pendant Light Fixture */}
      <group position={[0, 2.5, 0]}>
        {/* Steel Suspension Wire Drops */}
        <mesh position={[-1.5, 0.6, 0]}>
          <cylinderGeometry args={[0.004, 0.004, 1.2, 8]} />
          <meshBasicMaterial color="#94a3b8" />
        </mesh>
        <mesh position={[1.5, 0.6, 0]}>
          <cylinderGeometry args={[0.004, 0.004, 1.2, 8]} />
          <meshBasicMaterial color="#94a3b8" />
        </mesh>
        {/* Minimalist Matte Black Aluminum Linear Housing */}
        <mesh position={[0, 0, 0]} castShadow>
          <boxGeometry args={[3.8, 0.06, 0.12]} />
          <meshStandardMaterial color="#0f172a" metalness={0.8} roughness={0.2} />
        </mesh>
        {/* Downward Frosted LED Diffuser Strip */}
        <mesh position={[0, -0.031, 0]}>
          <boxGeometry args={[3.74, 0.01, 0.09]} />
          <meshStandardMaterial
            color="#fffdf5"
            emissive="#fff8db"
            emissiveIntensity={1.4}
          />
        </mesh>
        {/* Downward Desk Illumination Spotlight */}
        <spotLight
          position={[0, -0.05, 0]}
          intensity={2.2}
          distance={5}
          angle={Math.PI / 3}
          penumbra={0.4}
          color="#fffbeb"
        />
      </group>

      {/* --- LEFT SLOT (e.g., David or Alex) --- */}
      <group position={[-1.2, 0.75, 0]}>
        {/* Felt Desk Pad */}
        <mesh position={[0, 0.005, 0.15]} receiveShadow>
          <boxGeometry args={[1.3, 0.01, 0.6]} />
          <meshStandardMaterial color={deskPadColor} roughness={0.9} />
        </mesh>

        {/* Monitor Rig */}
        <group position={[0, 0, -0.3]}>
          <mesh position={[0, 0.38, 0]} castShadow>
            <boxGeometry args={[1.0, 0.5, 0.04]} />
            <meshStandardMaterial color="#090d16" roughness={0.4} />
          </mesh>
          {/* Glowing Code Display */}
          <mesh position={[0, 0.38, 0.022]}>
            <planeGeometry args={[0.96, 0.46]} />
            <meshStandardMaterial
              color={leftAgent.color}
              emissive={leftAgent.color}
              emissiveIntensity={0.65}
            />
          </mesh>
          {/* Articulated Stand */}
          <mesh position={[0, 0.1, 0]}>
            <cylinderGeometry args={[0.02, 0.02, 0.2, 12]} />
            <meshStandardMaterial color="#0b0f17" metalness={0.8} />
          </mesh>
        </group>

        {/* Keyboard & Mouse */}
        <mesh position={[0, 0.02, 0.22]} castShadow>
          <boxGeometry args={[0.42, 0.018, 0.15]} />
          <meshStandardMaterial color="#0f172a" roughness={0.3} />
        </mesh>
        <mesh position={[0.3, 0.02, 0.22]} castShadow>
          <boxGeometry args={[0.08, 0.02, 0.12]} />
          <meshStandardMaterial color="#0f172a" roughness={0.3} />
        </mesh>
      </group>

      {/* --- RIGHT SLOT (e.g., Elena or Maya) --- */}
      <group position={[1.2, 0.75, 0]}>
        {/* Felt Desk Pad */}
        <mesh position={[0, 0.005, 0.15]} receiveShadow>
          <boxGeometry args={[1.3, 0.01, 0.6]} />
          <meshStandardMaterial color={deskPadColor} roughness={0.9} />
        </mesh>

        {/* Dual Vertical Displays */}
        <group position={[-0.26, 0, -0.3]} rotation={[0, 0.15, 0]}>
          <mesh position={[0, 0.38, 0]} castShadow>
            <boxGeometry args={[0.48, 0.55, 0.04]} />
            <meshStandardMaterial color="#090d16" roughness={0.4} />
          </mesh>
          <mesh position={[0, 0.38, 0.022]}>
            <planeGeometry args={[0.44, 0.51]} />
            <meshStandardMaterial
              color={rightAgent.color}
              emissive={rightAgent.color}
              emissiveIntensity={0.65}
            />
          </mesh>
          <mesh position={[0, 0.08, 0]}>
            <cylinderGeometry args={[0.018, 0.018, 0.16, 12]} />
            <meshStandardMaterial color="#0b0f17" metalness={0.8} />
          </mesh>
        </group>

        <group position={[0.26, 0, -0.3]} rotation={[0, -0.15, 0]}>
          <mesh position={[0, 0.38, 0]} castShadow>
            <boxGeometry args={[0.48, 0.55, 0.04]} />
            <meshStandardMaterial color="#090d16" roughness={0.4} />
          </mesh>
          <mesh position={[0, 0.38, 0.022]}>
            <planeGeometry args={[0.44, 0.51]} />
            <meshStandardMaterial
              color={rightAgent.color}
              emissive={rightAgent.color}
              emissiveIntensity={0.65}
            />
          </mesh>
          <mesh position={[0, 0.08, 0]}>
            <cylinderGeometry args={[0.018, 0.018, 0.16, 12]} />
            <meshStandardMaterial color="#0b0f17" metalness={0.8} />
          </mesh>
        </group>

        {/* Keyboard & Mouse */}
        <mesh position={[0, 0.02, 0.22]} castShadow>
          <boxGeometry args={[0.42, 0.018, 0.15]} />
          <meshStandardMaterial color="#0f172a" roughness={0.3} />
        </mesh>
        <mesh position={[0.3, 0.02, 0.22]} castShadow>
          <boxGeometry args={[0.08, 0.02, 0.12]} />
          <meshStandardMaterial color="#0f172a" roughness={0.3} />
        </mesh>
      </group>

    </group>
  );
};

// 6. Private BOSS Room (North-East Corner)
const BossRoom: React.FC = () => {
  return (
    <group position={[5.6, 0, -5.55]}>
      {/* A distinct, quieter material zone keeps this room legible from the main office. */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.012, 0]} receiveShadow>
        <planeGeometry args={[4.65, 3.8]} />
        <meshStandardMaterial color="#172526" roughness={0.86} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.018, 0]}>
        <ringGeometry args={[0.72, 0.76, 32]} />
        <meshBasicMaterial color="#d8b778" opacity={0.46} transparent />
      </mesh>

      {/* West glazed partition and a southern doorway: David visibly enters, rather than disappearing. */}
      <mesh position={[-2.22, 2.0, 0]} castShadow>
        <boxGeometry args={[0.08, 4.0, 3.7]} />
        <meshStandardMaterial color="#263744" metalness={0.55} roughness={0.35} />
      </mesh>
      <mesh position={[-2.17, 2.0, 0]}>
        <boxGeometry args={[0.018, 3.65, 3.25]} />
        <meshPhysicalMaterial color="#8fb5c4" transmission={0.35} opacity={0.2} transparent roughness={0.16} />
      </mesh>
      <mesh position={[-1.2, 2.0, 1.82]} castShadow>
        <boxGeometry args={[1.8, 4.0, 0.08]} />
        <meshStandardMaterial color="#263744" metalness={0.45} roughness={0.42} />
      </mesh>
      <mesh position={[1.42, 2.0, 1.82]} castShadow>
        <boxGeometry args={[1.25, 4.0, 0.08]} />
        <meshStandardMaterial color="#263744" metalness={0.45} roughness={0.42} />
      </mesh>

      {/* Private desk, guest chair, and warm task light. */}
      <mesh position={[0.55, 0.82, -0.62]} castShadow receiveShadow>
        <boxGeometry args={[2.35, 0.10, 0.92]} />
        <meshStandardMaterial color="#6a5034" roughness={0.4} />
      </mesh>
      <mesh position={[0.55, 0.42, -0.62]} castShadow>
        <boxGeometry args={[0.08, 0.82, 0.82]} />
        <meshStandardMaterial color="#17202a" metalness={0.7} roughness={0.28} />
      </mesh>
      <mesh position={[0.55, 1.18, -0.98]} castShadow>
        <boxGeometry args={[0.96, 0.52, 0.05]} />
        <meshStandardMaterial color="#090f17" roughness={0.28} />
      </mesh>
      <mesh position={[0.55, 1.18, -0.948]}>
        <planeGeometry args={[0.90, 0.46]} />
        <meshStandardMaterial color="#d8b778" emissive="#d8b778" emissiveIntensity={0.32} />
      </mesh>
      <mesh position={[-0.9, 0.35, 0.65]} castShadow>
        <cylinderGeometry args={[0.27, 0.31, 0.7, 20]} />
        <meshStandardMaterial color="#314657" roughness={0.62} />
      </mesh>

      {/* The label gives the user a clear private delivery destination. */}
      <group position={[-1.95, 3.35, 1.87]}>
        <mesh>
          <boxGeometry args={[1.32, 0.42, 0.04]} />
          <meshStandardMaterial color="#10191d" metalness={0.4} roughness={0.35} />
        </mesh>
        <mesh position={[0, 0, 0.025]}>
          <planeGeometry args={[1.18, 0.26]} />
          <meshBasicMaterial color="#d8b778" opacity={0.7} transparent />
        </mesh>
        <Html center transform distanceFactor={12} position={[0, 0, 0.06]} style={{ pointerEvents: 'none' }}>
          <div className="font-mono text-[10px] font-bold tracking-[0.22em] text-[#d8b778] whitespace-nowrap">BOSS</div>
        </Html>
      </group>
      <pointLight position={[-0.2, 3.2, 0.2]} intensity={1.05} color="#f6dfae" distance={5.5} />
    </group>
  );
};

// 7. Carrara Marble Espresso Pantry Lab (West Corner)
const EspressoPantry: React.FC<{ position: [number, number, number] }> = ({ position }) => {
  return (
    <group position={position}>
      {/* L-Shaped Kitchen Cabinetry Base */}
      <group position={[0, 0, 0]}>
        {/* Main Counter */}
        <mesh position={[0, 0.45, 0]} castShadow receiveShadow>
          <boxGeometry args={[2.4, 0.9, 0.9]} />
          <meshStandardMaterial color="#251a10" roughness={0.7} />
        </mesh>
        {/* Carrara Marble Countertop */}
        <mesh position={[0, 0.92, 0]} castShadow receiveShadow>
          <boxGeometry args={[2.5, 0.06, 0.95]} />
          <meshStandardMaterial color="#dfe2ee" roughness={0.2} metalness={0.1} />
        </mesh>
      </group>

      {/* Italian Espresso Machine with LED & Steam */}
      <group position={[-0.4, 0.95, 0]}>
        <mesh position={[0, 0.25, 0]} castShadow>
          <boxGeometry args={[0.5, 0.4, 0.4]} />
          <meshStandardMaterial color="#37474f" metalness={0.8} roughness={0.2} />
        </mesh>
        {/* Chrome Portafilters & Drip Tray */}
        <mesh position={[0, 0.05, 0.22]}>
          <boxGeometry args={[0.42, 0.04, 0.15]} />
          <meshStandardMaterial color="#dfe2ee" metalness={0.9} />
        </mesh>
        {/* Machine Indicator Light */}
        <mesh position={[0.18, 0.38, 0.21]}>
          <sphereGeometry args={[0.02, 8, 8]} />
          <meshBasicMaterial color="#10b981" />
        </mesh>
        {/* Coffee Mug */}
        <mesh position={[-0.08, 0.12, 0.22]}>
          <cylinderGeometry args={[0.04, 0.035, 0.08, 12]} />
          <meshStandardMaterial color="#fafaf9" />
        </mesh>
      </group>

      {/* Water Cooler Dispenser */}
      <group position={[0.65, 0.95, 0]}>
        <mesh position={[0, 0.3, 0]} castShadow>
          <boxGeometry args={[0.3, 0.55, 0.3]} />
          <meshStandardMaterial color="#dfe2ee" />
        </mesh>
        <mesh position={[0, 0.65, 0]}>
          <cylinderGeometry args={[0.12, 0.12, 0.32, 16]} />
          <meshPhysicalMaterial color="#38bdf8" transmission={0.7} transparent opacity={0.5} />
        </mesh>
      </group>
      {/* Overhead Pantry Minimalist Pendant Light (Physical Light Source) */}
      <group position={[0, 2.8, 0]}>
        <mesh position={[0, 0.45, 0]}>
          <cylinderGeometry args={[0.004, 0.004, 0.9, 8]} />
          <meshBasicMaterial color="#94a3b8" />
        </mesh>
        <mesh position={[0, 0, 0]} castShadow>
          <coneGeometry args={[0.22, 0.28, 20]} />
          <meshStandardMaterial color="#1e293b" metalness={0.7} />
        </mesh>
        <mesh position={[0, -0.1, 0]}>
          <sphereGeometry args={[0.06, 12, 12]} />
          <meshStandardMaterial color="#fef3c7" emissive="#f59e0b" emissiveIntensity={2.0} />
        </mesh>
        <spotLight
          position={[0, -0.12, 0]}
          target-position={[0, -1.6, 0]}
          intensity={1.8}
          distance={4.5}
          angle={Math.PI / 3}
          penumbra={0.5}
          color="#fef3c7"
        />
      </group>
    </group>
  );
};

// 7. Round Nordic Birch Meeting Table with Pendant Lamp (East Corner)
const RoundMeetingTable: React.FC<{ position: [number, number, number] }> = ({ position }) => {
  return (
    <group position={position}>
      {/* Round Nordic Birch Tabletop */}
      <mesh position={[0, 0.74, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[1.3, 1.3, 0.06, 32]} />
        <meshStandardMaterial color="#cfb188" roughness={0.3} />
      </mesh>
      {/* Central Cable Disc */}
      <mesh position={[0, 0.775, 0]}>
        <cylinderGeometry args={[0.18, 0.18, 0.01, 24]} />
        <meshStandardMaterial color="#2b2014" />
      </mesh>
      {/* Center Fluted Pedestal Base */}
      <mesh position={[0, 0.36, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.22, 0.38, 0.72, 24]} />
        <meshStandardMaterial color="#9c7952" roughness={0.5} />
      </mesh>


      {/* Hanging Low Minimalist Cone Pendant Light (Physical Light Source) */}
      <group position={[0, 3.2, 0]}>
        <mesh position={[0, -0.8, 0]}>
          <cylinderGeometry args={[0.008, 0.008, 1.6, 8]} />
          <meshBasicMaterial color="#869397" />
        </mesh>
        <mesh position={[0, -1.6, 0]} rotation={[0, 0, 0]} castShadow>
          <coneGeometry args={[0.3, 0.38, 24]} />
          <meshStandardMaterial color="#1e293b" metalness={0.7} roughness={0.3} />
        </mesh>
        {/* Glowing Bulb inside fixture */}
        <mesh position={[0, -1.72, 0]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#fffbeb" emissive="#fef3c7" emissiveIntensity={2.2} />
        </mesh>
        {/* Warm Spotlight on table */}
        <spotLight
          position={[0, -1.74, 0]}
          target-position={[0, 0, 0]}
          intensity={2.4}
          distance={5.5}
          angle={Math.PI / 3.5}
          penumbra={0.4}
          color="#fef3c7"
        />
      </group>
    </group>
  );
};

export const OfficeCanvas: React.FC = () => {
  const agents = useOfficeStore((state) => state.agents);

  const isDraggingAgent = useOfficeStore((state) => state.isDraggingAgent);
  const controlsRef = React.useRef<any>(null);

  // Free Roam Zoom In/Out helper
  const handleZoom = (factor: number) => {
    if (controlsRef.current) {
      const controls = controlsRef.current;
      const camera = controls.object;
      if (camera) {
        camera.position.x *= factor;
        camera.position.y *= factor;
        camera.position.z *= factor;
        controls.update();
      }
    }
  };

  // Reset Camera to standard isometric angle
  const handleResetCamera = () => {
    if (controlsRef.current) {
      const controls = controlsRef.current;
      controls.target.set(0, 0.6, 0);
      controls.object.position.set(10, 13, 14);
      controls.update();
    }
  };

  return (
    <div className="w-full h-full relative bg-[#070a10] overflow-hidden select-none">
      {/* Stitch Top Center Floating HUD Controls */}
      <div className="absolute top-3.5 left-1/2 -translate-x-1/2 z-20 flex items-center gap-3 bg-[#0a0e16]/85 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 shadow-2xl">
        <div className="flex items-center gap-2 pr-2.5 border-r border-white/10">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_#22d3ee]" />
          <span className="text-[11px] font-mono font-bold tracking-wider text-gray-200">
            SCANDINAVIAN OPEN AI STUDIO
          </span>
          <span className="text-[9px] font-mono text-gray-400 bg-white/5 px-2 py-0.5 rounded border border-white/5 uppercase">
            DRAG OR COMMAND AGENTS
          </span>
        </div>

        {/* Free Roam Zoom & Reset Toolbar */}
        <div className="flex items-center gap-1 font-mono">
          <button
            onClick={() => handleZoom(1.2)}
            className="w-6 h-6 rounded bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs flex items-center justify-center border border-white/5 transition-colors active:scale-95"
            title="Zoom Out"
          >
            -
          </button>
          <button
            onClick={() => handleZoom(0.8)}
            className="w-6 h-6 rounded bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs flex items-center justify-center border border-white/5 transition-colors active:scale-95"
            title="Zoom In"
          >
            +
          </button>
          <button
            onClick={handleResetCamera}
            className="px-2 h-6 rounded bg-white/5 hover:bg-cyan-500/20 text-gray-300 hover:text-cyan-300 text-[10px] tracking-wider font-semibold border border-white/5 hover:border-cyan-500/30 transition-colors uppercase active:scale-95"
            title="Reset View"
          >
            RESET
          </button>
        </div>
      </div>

      <Canvas
        shadows
        camera={{ position: [10, 13, 14], fov: 32 }}
        className="w-full h-full cursor-grab active:cursor-grabbing"
      >
        {/* Warm Sunlight & Stellar Radiance Illumination */}
        <ambientLight intensity={0.9} color="#fff8ed" />

        {/* Primary Radiant Sunlight / Star Light from East Window Wall */}
        <directionalLight
          position={[12, 16, 7]}
          intensity={3.4}
          color="#fff5db"
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
          shadow-camera-far={40}
          shadow-camera-near={0.5}
          shadow-camera-left={-10}
          shadow-camera-right={10}
          shadow-camera-top={10}
          shadow-camera-bottom={-10}
          shadow-bias={-0.0002}
          shadow-normalBias={0.02}
        />

        {/* Overhead Atrium Studio Downlight */}
        <pointLight position={[0, 8.5, 0]} intensity={1.6} color="#fffbeb" distance={22} />

        {/* Studio Warm Rim Highlights */}
        <pointLight position={[-4.8, 4.5, 3.4]} intensity={1.1} color="#67e8f9" distance={12} />
        <pointLight position={[4.8, 4.0, 3.4]} intensity={1.3} color="#fde68a" distance={12} />

        <Suspense fallback={null}>
          <OfficeLife />
          {/* 1. Oak Parquet Floor */}
          <ParquetFloor />

          {/* 2. Walls */}
          <NorthWall position={[0, 0, -8.0]} />
          <OfficeWallClock />
          <WestWall position={[-8.4, 0, 0]} />
          <EastWindowWall position={[8.4, 0, 0]} />

          {/* 3. Center Dual Workstation Pods */}
          {/* North Pod: David & Elena */}
          <DualBenchPod
            position={[0, 0, -1.8]}
            podLabel="NORTH BENCH // DAVID & ELENA"
            leftAgent={{ name: 'David', color: '#e3c198', monitorType: 'ultrawide' }}
            rightAgent={{ name: 'Elena', color: '#d0bcff', monitorType: 'dual' }}
            deskColor="#5a422d"
            deskPadColor="#263240"
          />

          {/* South Pod: Alex & Maya */}
          <DualBenchPod
            position={[0, 0, 1.8]}
            podLabel="SOUTH BENCH // ALEX & MAYA"
            leftAgent={{ name: 'Alex', color: '#4cd7f6', monitorType: 'ultrawide' }}
            rightAgent={{ name: 'Maya', color: '#10b981', monitorType: 'dual' }}
            deskColor="#2d4652"
            deskPadColor="#172934"
          />

          {/* 4. Private delivery room for the human BOSS */}
          <BossRoom />

          {/* 5. Pantry & Espresso Bar (West Corner) */}
          <EspressoPantry position={[-4.8, 0, 3.4]} />

          {/* 6. Round Meeting Table (East Corner) */}
          <RoundMeetingTable position={[4.8, 0, 3.4]} />

          {/* 7. Active Autonomous Characters */}
          {Object.values(agents).filter((agent) => agent.isPresent !== false).map((agent) => (
            <AgentCharacter key={agent.id} agent={agent} />
          ))}

          {/* Soft Ground Contact Shadows */}
          <ContactShadows
            position={[0, 0, 0]}
            opacity={0.7}
            scale={20}
            blur={1.8}
            far={10}
            resolution={1024}
            color="#070a10"
          />

          {/* 100% Free Roam Orbit Controls (Pan, Rotate, Zoom from any angle) */}
          <OrbitControls
            ref={controlsRef}
            enabled={!isDraggingAgent}
            enableDamping
            dampingFactor={0.06}
            rotateSpeed={0.8}
            panSpeed={0.8}
            zoomSpeed={0.9}
            maxPolarAngle={Math.PI / 2.05}
            minDistance={4}
            maxDistance={40}
            target={[0, 0.6, 0]}
            makeDefault
          />
        </Suspense>
      </Canvas>
    </div>
  );
};
