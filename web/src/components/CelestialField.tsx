"use client";

import { useEffect, useRef } from "react";

/**
 * The engraved orrery behind everything.
 *
 * SVG rather than WebGL, and that is the whole reason this replaced the
 * starfield: the brief calls for faint fine-line orbital rings, and WebGL
 * cannot draw a crisp hairline — `lineWidth` is capped at 1 device pixel in
 * every major implementation and lines alias badly. SVG strokes stay sharp at
 * any density, cost nothing to composite, and print.
 *
 * Three depth layers parallax against the pointer at different rates and
 * counter-rotate on very long cycles. Everything sits under 12% opacity so it
 * never competes with the text it sits behind.
 */

const SIGNS = 12;
const TICKS = 72;

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)] as const;
}

export default function CelestialField() {
  const graticule = useRef<SVGGElement>(null);
  const orbits = useRef<SVGGElement>(null);
  const motes = useRef<SVGGElement>(null);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let frame = 0;
    let tx = 0;
    let ty = 0;

    const onMove = (e: PointerEvent) => {
      // Normalised to [-1, 1] from the viewport centre.
      tx = (e.clientX / window.innerWidth) * 2 - 1;
      ty = (e.clientY / window.innerHeight) * 2 - 1;
      if (!frame) frame = requestAnimationFrame(apply);
    };

    let cx = 0;
    let cy = 0;
    const apply = () => {
      frame = 0;
      // Ease toward the pointer so the field glides rather than snaps.
      cx += (tx - cx) * 0.08;
      cy += (ty - cy) * 0.08;
      const set = (el: SVGGElement | null, depth: number) => {
        if (el) el.style.transform = `translate(${cx * depth}px, ${cy * depth}px)`;
      };
      set(graticule.current, 9);
      set(orbits.current, 20);
      set(motes.current, 34);
      if (Math.abs(tx - cx) > 0.001 || Math.abs(ty - cy) > 0.001) {
        frame = requestAnimationFrame(apply);
      }
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      className="celestial-field pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      {/* Daytime sky: a pale warm wash lifting toward the horizon. */}
      <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_50%_-20%,#FFFFFF_0%,#F7F6FB_38%,#EFF1F8_68%,#FAF9F6_100%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(60%_50%_at_85%_10%,rgba(216,163,60,.10),transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(55%_45%_at_10%_75%,rgba(139,92,214,.08),transparent_65%)]" />

      <svg
        viewBox="0 0 1000 1000"
        preserveAspectRatio="xMidYMid slice"
        className="absolute inset-0 h-full w-full"
      >
        <defs>
          <radialGradient id="fade" cx="50%" cy="50%" r="50%">
            <stop offset="55%" stopColor="#fff" stopOpacity="1" />
            <stop offset="100%" stopColor="#fff" stopOpacity="0" />
          </radialGradient>
          <mask id="softEdge">
            <rect width="1000" height="1000" fill="url(#fade)" />
          </mask>
        </defs>

        <g mask="url(#softEdge)">
          {/* ── Astrolabe graticule ─────────────────────────────────── */}
          <g ref={graticule} className="origin-center animate-spin-slow">
            {[130, 205, 280, 355, 430].map((r) => (
              <circle
                key={r}
                cx={500}
                cy={500}
                r={r}
                fill="none"
                stroke="var(--ring-ink)"
                strokeWidth={0.8}
              />
            ))}
            {/* Twelve sign divisions. */}
            {Array.from({ length: SIGNS }, (_, i) => {
              const a = (i * 360) / SIGNS;
              const [x1, y1] = polar(500, 500, 130, a);
              const [x2, y2] = polar(500, 500, 430, a);
              return (
                <line
                  key={a}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="var(--ring-ink)"
                  strokeWidth={0.7}
                />
              );
            })}
            {/* Five-degree ticks on the outer limb. */}
            {Array.from({ length: TICKS }, (_, i) => {
              const a = (i * 360) / TICKS;
              const [x1, y1] = polar(500, 500, 430, a);
              const [x2, y2] = polar(500, 500, i % 6 === 0 ? 446 : 438, a);
              return (
                <line
                  key={`t${a}`}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="var(--ring-gold)"
                  strokeWidth={0.9}
                />
              );
            })}
          </g>

          {/* ── Orbital ellipses, counter-rotating ──────────────────── */}
          <g ref={orbits} className="origin-center animate-spin-slower">
            {[
              { rx: 300, ry: 118, rot: 0 },
              { rx: 380, ry: 152, rot: 34 },
              { rx: 455, ry: 186, rot: 68 },
              { rx: 250, ry: 98, rot: 102 },
              { rx: 520, ry: 210, rot: 136 },
            ].map((o) => (
              <ellipse
                key={`${o.rx}-${o.rot}`}
                cx={500}
                cy={500}
                rx={o.rx}
                ry={o.ry}
                fill="none"
                stroke="var(--ring-ink)"
                strokeWidth={0.75}
                transform={`rotate(${o.rot} 500 500)`}
              />
            ))}
          </g>

          {/* ── Planet motes riding the orbits ──────────────────────── */}
          <g ref={motes}>
            {[
              { x: 800, y: 500, r: 4.5, c: "#D8A33C", o: 0.3 },
              { x: 235, y: 452, r: 3, c: "#8B5CD6", o: 0.26 },
              { x: 612, y: 258, r: 2.4, c: "#0A1128", o: 0.16 },
              { x: 402, y: 742, r: 3.6, c: "#D8A33C", o: 0.22 },
              { x: 742, y: 690, r: 2.2, c: "#8B5CD6", o: 0.2 },
            ].map((m) => (
              <circle
                key={`${m.x}-${m.y}`}
                cx={m.x}
                cy={m.y}
                r={m.r}
                fill={m.c}
                opacity={m.o}
                className="animate-breathe"
              />
            ))}
          </g>
        </g>
      </svg>
    </div>
  );
}
