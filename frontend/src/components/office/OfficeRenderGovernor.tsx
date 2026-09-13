import React, { useEffect, useRef, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Html } from '@react-three/drei';

/**
 * Render-cost governance.
 *
 * The office is a static room: furniture never moves, and only four small
 * characters do. It was nonetheless re-rendering continuously — at 120fps on a
 * ProMotion display — with a 2048² shadow pass and a 1024² contact-shadow
 * depth-plus-blur pass every single frame. That is what made laptops hot.
 *
 * Three fixes live here:
 *
 * - The shadow map is baked once instead of refreshed per frame.
 * - Rendering pauses entirely while the tab is hidden.
 * - An optional overlay reports real draw calls, so the cost is measured
 *   rather than asserted. Enable it with `?perf=1`.
 */

/** Bake the static shadow map once, then stop refreshing it. */
export const StaticShadowBake: React.FC = () => {
  const gl = useThree((state) => state.gl);
  const invalidate = useThree((state) => state.invalidate);
  const baked = useRef(0);

  useFrame(() => {
    // Allow a couple of frames so every prop has been submitted once.
    if (baked.current < 2) {
      baked.current += 1;
      gl.shadowMap.autoUpdate = true;
      gl.shadowMap.needsUpdate = true;
      invalidate();
      return;
    }
    if (gl.shadowMap.autoUpdate) {
      gl.shadowMap.autoUpdate = false;
    }
  });

  return null;
};

/** Stop drawing and simulating while the tab is in the background. */
export const VisibilityGovernor: React.FC = () => {
  const invalidate = useThree((state) => state.invalidate);

  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        invalidate();
      }
    };
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => document.removeEventListener('visibilitychange', onVisibilityChange);
  }, [invalidate]);

  return null;
};

export const perfOverlayEnabled = (): boolean => {
  try {
    return new URLSearchParams(window.location.search).has('perf');
  } catch {
    return false;
  }
};

/**
 * Live renderer statistics. Capture these before and after a change rather
 * than trusting a prediction: `calls` is the number that matters most.
 */
export const PerfOverlay: React.FC = () => {
  const gl = useThree((state) => state.gl);
  const [stats, setStats] = useState({
    calls: 0,
    triangles: 0,
    geometries: 0,
    textures: 0,
    frameMs: 0,
    fps: 0,
  });

  const accumulator = useRef({ frames: 0, elapsed: 0, lastPublish: 0 });

  useFrame((_state, delta) => {
    const acc = accumulator.current;
    acc.frames += 1;
    acc.elapsed += delta;

    if (acc.elapsed >= 0.5) {
      setStats({
        calls: gl.info.render.calls,
        triangles: gl.info.render.triangles,
        geometries: gl.info.memory.geometries,
        textures: gl.info.memory.textures,
        frameMs: (acc.elapsed / acc.frames) * 1000,
        fps: acc.frames / acc.elapsed,
      });
      acc.frames = 0;
      acc.elapsed = 0;
    }
  });

  return (
    <Html fullscreen zIndexRange={[40, 40]} style={{ pointerEvents: 'none' }}>
      <div className="fixed bottom-3 left-3 bg-black/85 border border-cyan-500/40 rounded-lg px-3 py-2 font-mono text-[10px] text-cyan-200 leading-relaxed pointer-events-none">
        <div className="text-cyan-400 font-bold mb-0.5">RENDER</div>
        <div>draw calls: {stats.calls}</div>
        <div>triangles: {stats.triangles.toLocaleString()}</div>
        <div>geometries: {stats.geometries}</div>
        <div>textures: {stats.textures}</div>
        <div>
          frame: {stats.frameMs.toFixed(1)}ms ({stats.fps.toFixed(0)} fps)
        </div>
        <div className="text-cyan-500/70 mt-0.5">0 fps when idle is correct</div>
      </div>
    </Html>
  );
};
