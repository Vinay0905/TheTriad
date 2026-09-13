import React from 'react';
import { Html } from '@react-three/drei';
import { useOfficeStore } from '../../store/useOfficeStore';
import { resolveSlot } from './OfficeGeometry';

const HOME_DESKS: Record<string, string> = {
  manager: 'desk_david',
  researcher: 'desk_elena',
  developer: 'desk_alex',
  qa: 'desk_maya',
};

/**
 * A placard on the desk of anyone who has left the office.
 *
 * An absent agent's body is not rendered, so without this the room simply
 * looks like it has fewer people and the reason is invisible. When a free-tier
 * quota runs out, the operator should be able to see at a glance who is gone,
 * why, and when they are expected back.
 */
export const DeskPlacards: React.FC = () => {
  const agents = useOfficeStore((state) => state.agents);

  const absent = Object.values(agents).filter(
    (agent) => agent.isPresent === false && HOME_DESKS[agent.id],
  );

  if (absent.length === 0) return null;

  return (
    <>
      {absent.map((agent) => {
        const slot = resolveSlot(HOME_DESKS[agent.id]);
        return (
          <Html
            key={agent.id}
            position={[slot.x, 0.9, slot.z]}
            center
            distanceFactor={12}
            zIndexRange={[0, 0]}
            style={{ pointerEvents: 'none' }}
          >
            <div className="flex flex-col items-center select-none">
              <div className="bg-rose-950/90 border border-rose-500/40 rounded px-2 py-1 text-center">
                <div className="text-[10px] font-mono font-bold text-rose-200 uppercase tracking-wide">
                  {agent.name} · out
                </div>
                {agent.absence?.resetAtDisplay && (
                  <div className="text-[9px] font-mono text-rose-300/80">
                    back ~{agent.absence.resetAtDisplay}
                  </div>
                )}
                {agent.absence?.coveredBy && (
                  <div className="text-[9px] font-mono text-amber-300">
                    covered by {agent.absence.coveredBy}
                  </div>
                )}
              </div>
            </div>
          </Html>
        );
      })}
    </>
  );
};
