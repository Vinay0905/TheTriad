---
name: Nordic Studio HUD
colors:
  surface: '#0f131c'
  surface-dim: '#0f131c'
  surface-bright: '#353942'
  surface-container-lowest: '#0a0e16'
  surface-container-low: '#181c24'
  surface-container: '#1c2028'
  surface-container-high: '#262a33'
  surface-container-highest: '#31353e'
  on-surface: '#dfe2ee'
  on-surface-variant: '#bcc9cd'
  inverse-surface: '#dfe2ee'
  inverse-on-surface: '#2c3039'
  outline: '#869397'
  outline-variant: '#3d494c'
  surface-tint: '#4cd7f6'
  primary: '#4cd7f6'
  on-primary: '#003640'
  primary-container: '#06b6d4'
  on-primary-container: '#00424f'
  inverse-primary: '#00687a'
  secondary: '#e3c198'
  on-secondary: '#412c0f'
  secondary-container: '#5a4223'
  on-secondary-container: '#d1af88'
  tertiary: '#d0bcff'
  on-tertiary: '#3c0091'
  tertiary-container: '#b395ff'
  on-tertiary-container: '#4900ae'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#acedff'
  primary-fixed-dim: '#4cd7f6'
  on-primary-fixed: '#001f26'
  on-primary-fixed-variant: '#004e5c'
  secondary-fixed: '#ffddb6'
  secondary-fixed-dim: '#e3c198'
  on-secondary-fixed: '#2a1800'
  on-secondary-fixed-variant: '#5a4223'
  tertiary-fixed: '#e9ddff'
  tertiary-fixed-dim: '#d0bcff'
  on-tertiary-fixed: '#23005c'
  on-tertiary-fixed-variant: '#5516be'
  background: '#0f131c'
  on-background: '#dfe2ee'
  surface-variant: '#31353e'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  telemetry-code:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: -0.02em
  telemetry-micro:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.05em
  label-caps:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.08em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-mobile: 0.5rem
  margin: 1.5rem
  margin-mobile: 0.75rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

This design system synthesizes the warmth and calm of a physical Scandinavian miniature architectural model with the surgical precision of an autonomous engineering heads-up display. It lives at the intersection of tactile reality and high-density computing: the serene physical world of light birch, oiled oak, and muted petrol architecture is monitored and driven by ultra-clean, crystalline glass telemetry.

The brand personality conveys effortless intelligence, domestic serenity, and uncompromised technical depth. It addresses AI researchers, autonomous systems engineers, and technical leaders who orchestrate fleets of autonomous agents inside spatial virtual offices. 

The emotional response should mirror watching a high-craft automated diorama through a precision optical viewfinder: tactile comfort without clutter, technical density without visual exhaustion, and futuristic capabilities rendered through honest, architectural materials.

## Colors

The palette operates across two deliberate realms: **The Studio Layer** (interior miniature palette) and **The Telemetry Glass Layer** (autonomous HUD).

### Neutral & Glass Layer
- **Deep Obsidian Ground (`#0B0F17`):** The master substrate for overlay panels, sidebars, and contextual inspectors, deployed with 85%–92% opacity and multi-stop backdrop blur.
- **Glass Tint Border (`rgba(255, 255, 255, 0.08)`):** Micro-fine frosted boundaries defining spatial floating containers.
- **Muted Obsidian Surface (`#141A26`):** Secondary nested containers, code blocks, and inactive input trays.

### Scandinavian Interior Accents
- **Nordic Oak (`#D9B78F`):** Used for tactile controls, room identity badges, focus highlights on physical nodes, and agent avatar accents.
- **Petrol Blue (`#1A3C4D`):** Architectural baseline tone used for inactive structural markers, spatial grid lines, and canvas framing.
- **Warm Sunlight (`#FFF5E6`):** High-temperature typographic baseline and high-clarity headline glow.

### Autonomous Status & Telemetry
- **Electric Cyan (`#06B6D4`):** Primary system driver, active compute state, network telemetry routing, and actionable triggers.
- **Emerald Agent Active (`#10B981`):** Autonomous agent idle/working state, successful test runs, and healthy memory threads.
- **Amber Warning (`#F59E0B`):** Process throttle, agent deadlocks, and sandbox regression warnings.
- **Violet Intelligence (`#8B5CF6`):** LLM inference cycles, context compaction, and autonomous decision tree branches.

## Typography

The typographical hierarchy maintains dual clarity: human interface comprehension via **Plus Jakarta Sans** and **Inter**, and automated deterministic telemetry via **JetBrains Mono**.

- **Plus Jakarta Sans** introduces soft humanist geometric curves to high-level system controls, modal titles, agent names, and room tags, preventing the software from reading like a sterile terminal.
- **Inter** ensures distortion-free, legible communication across dense parameter lists, system logs, tooltips, and conversational AI traces.
- **JetBrains Mono** governs all system telemetry, memory offsets, autonomous execution traces, token consumption meters, and code diff panels. It enforces strict column discipline and immediate distinction between human input and machine output.

## Layout & Spacing

The interface employs a **Spatial HUD Canvas Model**: a 3D isometric viewport that stretches 100vw/100vh with non-blocking floating UI layers anchoring to perimeter docking tracks.

- **Desktop Layout:** Anchored glass rails. The left column (width: 320px) holds the autonomous agent fleet roster and spatial room nodes. The bottom shelf (height: 72px) contains the simulation transport timeline and orchestration playback controls. The right drawer (width: 420px) hosts the contextual code diff viewer, token telemetry, and sandbox console.
- **Breakpoints:**
  - **Desktop (1280px+):** Tri-panel docking active with visible 3D canvas viewport center.
  - **Tablet (768px – 1279px):** Inspector drawers collapse into slide-over floating sheets; HUD controls collapse to micro-icon tracks.
  - **Mobile (< 768px):** Minimalist view: persistent bottom simulation bar with swipe-up glass sheets for agent inspection and terminal output.
- **Spacing Rhythm:** Internal card structures adhere strictly to a 4px base increment (`0.25rem` to `2rem`). HUD elements float with a constant `1.5rem` canvas margin to expose the warm isometric Scandinavian environment underneath.

## Elevation & Depth

Visual hierarchy uses **Glassmorphic Multi-Plane Layering** backed by directional warm ambient lighting originating from the top-left of the 3D studio model.

1. **Layer 0 (Canvas):** The raw WebGL isometric render depicting light birch floors, acoustic felt partitions, and Nordic oak workstations bathed in warm sunlight.
2. **Layer 1 (Floating HUD Panels):** Background set to `rgba(11, 15, 23, 0.88)` with `backdrop-filter: blur(16px)`, outlined by a 1px border of `rgba(255, 245, 230, 0.08)`. Subtle diffuse outer shadow: `0 12px 32px -4px rgba(0, 0, 0, 0.5)`.
3. **Layer 2 (Contextual Popovers & Micro-Inspectors):** Background `rgba(20, 26, 38, 0.94)` with `backdrop-filter: blur(24px)`. Rim-lit highlight on the top edge `rgba(217, 183, 143, 0.25)` to simulate physical downlight reflecting off glass edges.
4. **Layer 3 (Spatial World Badges & Rings):** Micro-UI anchored directly inside the 3D world plane. Zero backdrop blur; uses pure emissive glowing status rings with radial falloff (`0 0 12px var(--color)` at 40% alpha) to highlight active agents and compute clusters.

## Shapes

The design system implements a roundedness scale of `2` (base 8px / `0.5rem`).

- **HUD Main Windows & Drawers:** `rounded-xl` (24px / `1.5rem`) on exposed corners to evoke precision-milled glass slabs.
- **Cards, Nodes, & Console Viewers:** `rounded-lg` (16px / `1.0rem`), framing dense telemetry with balanced softness.
- **Micro-Badges, Controls, & Buttons:** Base `rounded` (8px / `0.5rem`), maintaining crisp, actionable target shapes.
- **Spatial 3D World Markers:** Perfect geometric circles for telemetry status pulses, and precise capsule pills for floating world-space agent tags.

## Components

### Buttons & Interactive Controls
- **Primary Telemetry Trigger:** Cyan fill (`#06B6D4`) with obsidian text (`#0B0F17`), font weight 600. On hover, apply an inner glow `inset 0 0 12px rgba(255, 255, 255, 0.35)` and subtle scale (1.02x).
- **Secondary Studio Control:** Frosted obsidian base (`rgba(255, 255, 255, 0.05)`), border 1px solid `rgba(217, 183, 143, 0.3)`, text warm sunlight (`#FFF5E6`).
- **Simulation Step Controls:** Circular glass buttons (40px) with hairline icons and localized radial feedback ripples.

### Agent Micro-Badges & Status Rings
- **Status Ring:** A 2px outer concentric ring encircling an agent's miniature avatar. Colors: Cyan (compiling), Emerald (idle/listening), Violet (LLM reasoning), Amber (awaiting human verification).
- **HUD Tag:** Capsule badge with `JetBrains Mono` text, translucent dark fill (`rgba(11, 15, 23, 0.7)`), and left-aligned 6px status gem with an infinite breathing opacity pulse (1s duration).

### Terminal & Code Diff Inspector
- **Container:** Dark Obsidian pane (`#0B0F17`) with an inset hairline border (`rgba(255, 255, 255, 0.06)`).
- **Syntax & Telemetry:** Additions rendered in Emerald (`#10B981`) with 10% emerald background tint; deletions rendered in soft coral amber (`#F59E0B`); inference logs rendered in Violet (`#8B5CF6`).
- **Gutter:** Compact line numbering in muted petrol blue (`#1A3C4D`), non-selectable.

### Spatial Cards & Agent Nodes
- **Agent Focus Card:** Frosted obsidian panel displaying the agent's current thought chain, active branch, and memory load bar.
- **Header:** Agent title in `Plus Jakarta Sans` Bold with miniature Nordic Oak (`#D9B78F`) identity indicator.
- **Metrics Grid:** Two-column split featuring `JetBrains Mono` numerical counters with muted micro-labels above.

### Input Fields & Command Bar
- **Autonomous Prompt Input:** Floating bottom-center omnibar with `backdrop-filter: blur(20px)`.
- **States:** Inactive state shows muted sunlight placeholder text; focus state triggers a soft 1px border transition to Electric Cyan (`#06B6D4`) accompanied by an ambient bloom `0 0 20px rgba(6, 182, 212, 0.15)`.
- **Keyboard Shortcuts:** Styled as miniature tactile keycaps using Nordic Oak tints (`rgba(217, 183, 143, 0.15)`), bordered with rounded 4px corners.