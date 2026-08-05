import type { ReactNode } from 'react';
import s from './marks.module.css';
import { BrowserChrome } from './primitives/BrowserChrome';
import { DiskStack } from './primitives/DiskStack';

/**
 * FabricGlyphs — one small SVG per fabric surface.
 *
 * Each glyph is a 480x220 canvas so the rows line up in FabricsSection.
 * Deliberately quieter than app mocks — these advertise a substrate shape,
 * not a running screen. Palette follows the row's silver-woven hue via
 * --site-accent[-2] scope override in FabricsSection.module.css.
 */

const MONO = 'var(--font-mono)';
const RULE = 'var(--site-rule)';
const RULE_SOFT = 'var(--site-rule-2)';
const INK = 'var(--site-ink)';
const INK3 = 'var(--site-ink-3)';
const INK4 = 'var(--site-ink-4)';
const ACCENT = 'var(--site-accent)';
const ACCENT_WASH = 'var(--site-accent-wash)';
const ACCENT2 = 'var(--site-accent-2)';
const ACCENT2_WASH = 'var(--site-accent-2-wash)';

const V = { w: 480, h: 220 } as const;

function Frame({ children, aria }: { children: ReactNode; aria: string }) {
  return (
    <svg
      viewBox={`0 0 ${V.w} ${V.h}`}
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label={aria}
    >
      {children}
    </svg>
  );
}

/* ------------------------------- mem --------------------------------------- */
/** RAM-chip glyph — one lit cell hints "live in process". */
export function MemGlyph() {
  const cx = V.w / 2;
  const cy = V.h / 2;
  const chipW = 260;
  const chipH = 96;
  const x0 = cx - chipW / 2;
  const y0 = cy - chipH / 2;
  const cols = 8;
  const rows = 3;
  const cellW = (chipW - 24) / cols;
  const cellH = (chipH - 24) / rows;
  const litCol = 5;
  const litRow = 1;

  return (
    <Frame aria="Memory chip glyph: a grid of cells with one lit cell, denoting the in-process mem substrate.">
      {/* eyebrow */}
      <text
        x={x0}
        y={y0 - 14}
        style={{ fill: INK4, fontFamily: MONO, fontSize: 10, letterSpacing: '0.24em' }}
      >
        substrate
      </text>
      {/* chip body */}
      <rect
        x={x0}
        y={y0}
        width={chipW}
        height={chipH}
        fill="none"
        stroke={RULE}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {/* leads */}
      {Array.from({ length: 10 }).map((_, i) => {
        const lx = x0 + 20 + i * ((chipW - 40) / 9);
        return (
          <g key={i}>
            <line
              x1={lx}
              y1={y0}
              x2={lx}
              y2={y0 - 8}
              stroke={INK4}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
            <line
              x1={lx}
              y1={y0 + chipH}
              x2={lx}
              y2={y0 + chipH + 8}
              stroke={INK4}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          </g>
        );
      })}
      {/* cells */}
      {Array.from({ length: rows }).map((_, r) =>
        Array.from({ length: cols }).map((_, c) => {
          const isLit = r === litRow && c === litCol;
          return (
            <rect
              key={`${r}-${c}`}
              x={x0 + 12 + c * cellW}
              y={y0 + 12 + r * cellH}
              width={cellW - 4}
              height={cellH - 4}
              fill={isLit ? ACCENT2_WASH : 'none'}
              stroke={isLit ? ACCENT2 : RULE_SOFT}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
              className={isLit ? s.blink : undefined}
            />
          );
        }),
      )}
      {/* label */}
      <text
        x={cx}
        y={y0 + chipH + 32}
        textAnchor="middle"
        style={{
          fill: ACCENT2,
          fontFamily: MONO,
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: '0.24em',
        }}
      >
        mem
      </text>
    </Frame>
  );
}

/* ----------------------------- virtuals ------------------------------------ */
/** Disk stack with backend swap-plates. */
export function VirtualsGlyph() {
  const cx = V.w / 2;
  const cy = V.h / 2 - 6;

  return (
    <Frame aria="Virtuals glyph: a stacked-disk substrate with four labeled backend swap-plates — rocksdb, lmdb, acid-inmem, text.">
      {/* eyebrow */}
      <text
        x={40}
        y={28}
        style={{ fill: INK4, fontFamily: MONO, fontSize: 10, letterSpacing: '0.24em' }}
      >
        substrate · shapes
      </text>

      {/* disk stack (shared primitive) — 4 platters, tkv label in body */}
      <DiskStack
        cx={cx}
        topY={cy - 34}
        platters={4}
        platterGap={22}
        rx={36}
        ry={7}
        bodyLabel={{ text: 'kv', fontSize: 13 }}
      />

      {/* backend swap-plates */}
      {(['rocksdb', 'lmdb', 'acid-inmem', 'text'] as const).map((b, i) => {
        const px = 40 + i * 105;
        const active = i === 0;
        return (
          <g key={b}>
            <rect
              x={px}
              y={V.h - 46}
              width={92}
              height={26}
              rx={3}
              fill={active ? ACCENT2_WASH : 'transparent'}
              stroke={active ? ACCENT2 : RULE_SOFT}
              strokeWidth={1}
              strokeDasharray={active ? undefined : '3 3'}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={px + 46}
              y={V.h - 29}
              textAnchor="middle"
              style={{
                fill: active ? ACCENT2 : INK3,
                fontFamily: MONO,
                fontSize: 10.5,
                fontWeight: active ? 700 : 500,
                letterSpacing: '0.18em',
              }}
            >
              {b}
            </text>
          </g>
        );
      })}
    </Frame>
  );
}

/* ---------------------------- invisibles ----------------------------------- */
/** Two nodes with a dashed remote link + tiny proxy netref. */
export function InvisiblesGlyph() {
  const y = V.h / 2;
  const leftX = 100;
  const rightX = V.w - 100;

  return (
    <Frame aria="Invisibles glyph: two nodes connected by a dashed remote link, a small proxy pill hovers over the wire.">
      {/* eyebrow */}
      <text
        x={40}
        y={28}
        style={{ fill: INK4, fontFamily: MONO, fontSize: 10, letterSpacing: '0.24em' }}
      >
        distribution
      </text>

      {/* left node — the real object */}
      <g>
        <rect
          x={leftX - 40}
          y={y - 30}
          width={80}
          height={60}
          rx={3}
          fill="none"
          stroke={INK3}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={leftX}
          y={y - 4}
          textAnchor="middle"
          style={{ fill: INK, fontFamily: MONO, fontSize: 12, fontWeight: 700, letterSpacing: '0.16em' }}
        >
          object
        </text>
        <text
          x={leftX}
          y={y + 14}
          textAnchor="middle"
          style={{ fill: INK4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          server
        </text>
      </g>

      {/* right node — the caller */}
      <g>
        <rect
          x={rightX - 40}
          y={y - 30}
          width={80}
          height={60}
          rx={3}
          fill="none"
          stroke={INK3}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={rightX}
          y={y - 4}
          textAnchor="middle"
          style={{ fill: INK, fontFamily: MONO, fontSize: 12, fontWeight: 700, letterSpacing: '0.16em' }}
        >
          caller
        </text>
        <text
          x={rightX}
          y={y + 14}
          textAnchor="middle"
          style={{ fill: INK4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          client
        </text>
      </g>

      {/* remote wire */}
      <line
        x1={leftX + 40}
        y1={y}
        x2={rightX - 40}
        y2={y}
        stroke={ACCENT2}
        strokeWidth={1}
        strokeDasharray="3 3"
        vectorEffect="non-scaling-stroke"
        opacity={0.75}
      />
      {/* proxy netref pill riding the wire */}
      <g>
        <rect
          x={V.w / 2 - 34}
          y={y - 12}
          width={68}
          height={22}
          rx={3}
          fill={ACCENT2_WASH}
          stroke={ACCENT2}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={V.w / 2}
          y={y + 3}
          textAnchor="middle"
          style={{ fill: ACCENT2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em', fontWeight: 700 }}
        >
          proxy
        </text>
      </g>
    </Frame>
  );
}

/* -------------------------------- ray -------------------------------------- */
/** Cluster grid of worker nodes with one lit head. */
export function RayGlyph() {
  const cols = 6;
  const rows = 3;
  const gap = 22;
  const size = 22;
  const totalW = cols * size + (cols - 1) * gap;
  const totalH = rows * size + (rows - 1) * gap;
  const x0 = (V.w - totalW) / 2;
  const y0 = (V.h - totalH) / 2 + 6;
  const litIdx = new Set([3, 7, 11, 15]);

  return (
    <Frame aria="Ray glyph: a grid of worker nodes with a few lit, denoting distributed compute across the cluster.">
      {/* eyebrow */}
      <text
        x={40}
        y={28}
        style={{ fill: INK4, fontFamily: MONO, fontSize: 10, letterSpacing: '0.24em' }}
      >
        compute
      </text>

      {Array.from({ length: rows * cols }).map((_, i) => {
        const r = Math.floor(i / cols);
        const c = i % cols;
        const lit = litIdx.has(i);
        return (
          <g key={i}>
            <rect
              x={x0 + c * (size + gap)}
              y={y0 + r * (size + gap)}
              width={size}
              height={size}
              fill={lit ? ACCENT2_WASH : 'none'}
              stroke={lit ? ACCENT2 : RULE_SOFT}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
              className={lit && i === 7 ? s.blink : undefined}
            />
          </g>
        );
      })}

      {/* thin connectors between lit nodes suggest scheduling */}
      {[
        [3, 7],
        [7, 11],
        [11, 15],
      ].map(([a, b], k) => {
        const ar = Math.floor(a / cols);
        const ac = a % cols;
        const br = Math.floor(b / cols);
        const bc = b % cols;
        return (
          <line
            key={k}
            x1={x0 + ac * (size + gap) + size / 2}
            y1={y0 + ar * (size + gap) + size / 2}
            x2={x0 + bc * (size + gap) + size / 2}
            y2={y0 + br * (size + gap) + size / 2}
            stroke={ACCENT2}
            strokeWidth={1}
            strokeDasharray="3 3"
            vectorEffect="non-scaling-stroke"
            opacity={0.55}
          />
        );
      })}
    </Frame>
  );
}

/* --------------------------------- ui -------------------------------------- */
/** Browser chrome with a live Ref chip bound to a rendered value. */
export function UiGlyph() {
  const wx = 60;
  const wy = 34;
  const ww = V.w - 120;
  const wh = V.h - 68;

  return (
    <Frame aria="UI glyph: a browser chrome renders a live value that is bound to a Nu Ref.">
      {/* eyebrow */}
      <text
        x={wx}
        y={wy - 12}
        style={{ fill: INK4, fontFamily: MONO, fontSize: 10, letterSpacing: '0.24em' }}
      >
        rendering
      </text>

      {/* browser window (shared primitive) */}
      <BrowserChrome x={wx} y={wy} width={ww} height={wh} />

      {/* live value */}
      <text
        x={wx + ww / 2}
        y={wy + wh / 2 + 6}
        textAnchor="middle"
        style={{
          fill: INK,
          fontFamily: MONO,
          fontSize: 32,
          fontWeight: 700,
          letterSpacing: '0.02em',
        }}
      >
        42
      </text>

      {/* bound ref pill under the value */}
      <g>
        <rect
          x={wx + ww / 2 - 44}
          y={wy + wh / 2 + 18}
          width={88}
          height={20}
          rx={3}
          fill={ACCENT_WASH}
          stroke={ACCENT}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={wx + ww / 2}
          y={wy + wh / 2 + 32}
          textAnchor="middle"
          style={{
            fill: ACCENT,
            fontFamily: MONO,
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: '0.22em',
          }}
        >
          counter_ref
        </text>
      </g>
    </Frame>
  );
}
