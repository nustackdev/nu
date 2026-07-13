import { type ReactNode } from 'react';
import { BrowserChrome } from '@/components/marks/primitives/BrowserChrome';
import { DiskStack } from '@/components/marks/primitives/DiskStack';
import s from './HeroViz.module.css';

/**
 * HeroViz — hero interaction-model visualization.
 *
 * Fused asymmetric card:
 *   LEFT   nested Nu code tree with right-gutter hints
 *   RIGHT  fabric-clean SVG scene — browser tab rendering 42, wired down
 *          into a 3-disk rocksdb drum
 *
 * The wrap, divider, and dotted right substrate all live in the CSS module.
 */
export function HeroViz() {
  return (
    <div className={s.wrap}>
      <LeftTree />
      <div className={s.right}>
        <RightScene />
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * LeftTree — nested DOM containers with right-gutter hints.
 *
 * Palette pulled from the silver-woven fabric hues:
 *   sage   → virtuals (state)     — Counter shape, refs
 *   teal   → ui                   — Dashboard shape, ui bind
 *   plum   → invisibles           — ForeverDo, ReactForever, Delay
 *   amber  → ray                  — nu.Parallel (the whole app)
 *
 * Every container has a hint that visually lives in a right-gutter column,
 * connected to its container by a dotted arrow. Hints are absolutely
 * positioned within `.tree` (which reserves the gutter as padding-right),
 * so nested-container hints auto-align to the same right edge as top-level
 * ones — their y is taken from static flow.
 * -------------------------------------------------------------------------- */
function LeftTree() {
  return (
    <div className={s.tree}>
      {/* --- Counter shape --- */}
      <Container role="virtuals" tag="state" hint="eg rocksdb">
        <Line>
          <span className={s.kw}>class</span>{' '}
          <span className={s.tVirtuals}>Counter</span>
          <span className={s.dim}>(nu.Shape):</span>
        </Line>
        <Line indent>
          <span className={s.ident}>n</span>
          <span className={s.dim}>: </span>
          <span className={s.tVirtuals}>nu.v.IntRef</span>
        </Line>
      </Container>

      {/* --- Dashboard shape --- */}
      <Container role="ui" tag="ui" hint="refs ARE the widgets">
        <Line>
          <span className={s.kw}>class</span>{' '}
          <span className={s.tUi}>Dashboard</span>
          <span className={s.dim}>(nu.ui.Page):</span>
        </Line>
        <Line indent>
          <span className={s.ident}>count</span>
          <span className={s.dim}>: </span>
          <span className={s.tUi}>nu.ui.TextRef</span>
        </Line>
      </Container>

      {/* --- App: nu.Parallel, deeply nested --- */}
      <Container role="ray" tag="app" hint="two flows in parallel">
        <Line>
          <span className={s.ident}>app</span>
          <span className={s.dim}> = </span>
          <span className={s.tRay}>nu.Parallel</span>
          <span className={s.dim}>(</span>
        </Line>

        {/* tick flow */}
        <Container role="invisibles" tag="tick" hint="loop forever">
          <Line>
            <span className={s.tInvisibles}>nu.ForeverDo</span>
            <span className={s.dim}>(</span>
          </Line>

          <Container role="virtuals" tag="inc" hint="add 1 to state" tight>
            <Line>
              <span className={s.tVirtuals}>Counter.n</span>
              <span className={s.dim}>.inc()</span>
            </Line>
          </Container>

          <div className={s.op}>&gt;&gt;</div>

          <Container role="invisibles" tag="wait" hint="delay 1 second" tight>
            <Line>
              <span className={s.tInvisibles}>nu.Delay</span>
              <span className={s.dim}>(</span>
              <span className={s.num}>1.0</span>
              <span className={s.dim}>)</span>
            </Line>
          </Container>

          <Line>
            <span className={s.dim}>)</span>
          </Line>
        </Container>

        {/* live flow */}
        <Container role="invisibles" tag="live" hint="wake on change, write ui">
          <Line>
            <span className={s.tInvisibles}>nu.ReactForever</span>
            <span className={s.dim}>(</span>
          </Line>

          <Container role="virtuals" tag="subscribe" hint="which ref" tight>
            <Line>
              <span className={s.tVirtuals}>Counter.n</span>
              <span className={s.dim}>.on_change(),</span>
            </Line>
          </Container>

          <Container role="ui" tag="bind" hint="ui reads state, live" tight>
            <Line>
              <span className={s.tUi}>Dashboard.count</span>
              <span className={s.dim}>.set(</span>
              <span className={s.tVirtuals}>Counter.n</span>
              <span className={s.dim}>)</span>
            </Line>
          </Container>

          <Line>
            <span className={s.dim}>)</span>
          </Line>
        </Container>
      </Container>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Container — one real DOM box.
 *   role  → hue (border + wash + tag chip)
 *   tag   → small chip in the header
 *   hint  → absolutely positioned in `.tree`'s right gutter, dotted arrow
 *
 * The hint is the FIRST child so its static-flow y aligns with the top of
 * the container. `position: absolute; right: 0` pins it to `.tree`'s right
 * edge regardless of nesting depth.
 * -------------------------------------------------------------------------- */
function Container({
  role,
  tag,
  hint,
  tight,
  children,
}: {
  role: 'virtuals' | 'ui' | 'invisibles' | 'ray';
  tag: string;
  hint: string;
  tight?: boolean;
  children: ReactNode;
}) {
  const cls = tight ? `${s.container} ${s.containerTight}` : s.container;
  return (
    <div className={cls} data-role={role}>
      <div className={s.hint}>
        <HintArrow />
        <span className={s.tagChip}>{tag}</span>
        <span className={s.hintText}>{hint}</span>
      </div>
      <div className={s.body}>{children}</div>
    </div>
  );
}

function Line({ indent, children }: { indent?: boolean; children: ReactNode }) {
  return <div className={indent ? s.lineIndent : s.line}>{children}</div>;
}

function HintArrow() {
  return (
    <svg className={s.arrow} width="42" height="10" viewBox="0 0 42 10" aria-hidden>
      <line
        x1="0"
        y1="5"
        x2="34"
        y2="5"
        stroke="currentColor"
        strokeWidth="1"
        strokeDasharray="1.8 2.4"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
      <path
        d="M 32 2 L 38 5 L 32 8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

/* ============================================================================
 * RightScene — fabric-clean SVG. Browser chrome (shared primitive) renders 42,
 * dashed wire connects down to a rocksdb platter-stack (shared primitive).
 * Flat hairlines, no gradients, single accent-wash on the n = 42 chip. Accent
 * hue is silver-woven steel-blue (--nu-accent* is remapped to --nu-fab-steel
 * on the wrap in HeroViz.module.css).
 * ==========================================================================*/
function RightScene() {
  const ink = 'var(--nu-ink)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const ruleSoft = 'var(--nu-rule-2)';
  const accent = 'var(--nu-accent)';
  const mono = 'var(--font-mono)';

  const W = 340;
  /* H trimmed to end right below the last label so the SVG never adds
     empty vertical space when scaled to column width. */
  const H = 470;

  const bx = 20, by = 20, bw = W - 40, bh = 240;
  const wireY1 = by + bh + 16;
  const wireY2 = 348;
  const dCx = W / 2;
  const dTopY = 366;
  const platterGap = 22;
  const platters = 4;
  const dBottomY = dTopY + (platters - 1) * platterGap;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Dashboard rendered live in a browser tab showing 42, wired down into a rocksdb persistence disk."
    >
      {/* ===== Browser chrome (shared primitive) ===== */}
      <BrowserChrome x={bx} y={by} width={bw} height={bh} url="nu://dashboard" live />

      {/* Browser body content */}
      <text x={bx + 14} y={by + 52} style={{ fill: ink4, fontFamily: mono, fontSize: 9.5, letterSpacing: '0.24em' }}>
        dashboard
      </text>
      <line x1={bx + 14} y1={by + 58} x2={bx + bw - 14} y2={by + 58} stroke={ruleSoft} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      <text x={dCx} y={by + 168} textAnchor="middle" style={{ fill: ink, fontFamily: 'var(--font-display)', fontSize: 100, fontWeight: 800, letterSpacing: '-0.04em' }}>
        42
      </text>
      <text x={dCx} y={by + 200} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em' }}>
        dashboard.count
      </text>

      {/* ===== Wire browser → disk ===== */}
      <line x1={dCx} y1={wireY1} x2={dCx} y2={wireY2} stroke={ink4} strokeWidth={1} strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
      <text x={dCx + 10} y={(wireY1 + wireY2) / 2 + 3} style={{ fill: ink3, fontFamily: mono, fontSize: 9, letterSpacing: '0.22em' }}>
        set
      </text>

      {/* ===== Rocksdb disk (shared primitive, 4-platter stack) ===== */}
      <DiskStack
        cx={dCx}
        topY={dTopY}
        platters={platters}
        platterGap={platterGap}
        rx={68}
        ry={13}
        chip={{ text: 'n = 42', gap: 1 }}
      />

      {/* Labels under drum */}
      <text x={dCx} y={dBottomY + 26} textAnchor="middle" style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.28em', fontWeight: 700 }}>
        rocksdb
      </text>
      <text x={dCx} y={dBottomY + 44} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em' }}>
        persisted · survives restart
      </text>
    </svg>
  );
}
