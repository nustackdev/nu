import { useId, type ReactNode } from 'react';
import s from './HeroViz.module.css';

/**
 * HeroViz — hero interaction-model visualization.
 *
 * LEFT: real DOM-nested containers (container inside container inside container).
 *   Palette pulled from the silver-woven fabric hues:
 *     sage   → virtuals (state)     — Counter shape, refs
 *     teal   → ui                   — Dashboard shape, ui bind
 *     plum   → invisibles           — ForeverDo, ReactForever, Delay
 *     amber  → ray                  — nu.Parallel (the whole app)
 *
 * Every container has a hint that visually lives in a right-gutter column,
 * connected to its container by a dotted arrow. Hints are absolutely
 * positioned within `.tree` (which reserves the gutter as padding-right),
 * so nested-container hints auto-align to the same right edge as top-level
 * ones — their y is taken from static flow.
 *
 * RIGHT: inline SVG — Dashboard live in a browser tab (count = 42) wired
 *        down into a 3-disk rocksdb persistence drum.
 */
export function HeroViz() {
  return (
    <div className={s.wrap}>
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

          <Line>
            <span className={s.dim}>)</span>
          </Line>
        </Container>
      </div>

      <RightScene />
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
 * RightScene — flat-design browser tab + 3-disk rocksdb drum. (Unchanged.)
 * ==========================================================================*/
function RightScene() {
  const gid = useId();
  const dotId = `heroviz-dots-${gid}`;
  const diskGradId = `heroviz-disk-${gid}`;

  const ink = 'var(--nu-ink)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const accent = 'var(--nu-accent)';
  const accent2 = 'var(--nu-accent-2)';
  const bg = 'var(--color-fd-background)';
  const codeBg = 'var(--nu-code-bg-2)';
  const mono = 'var(--font-mono)';

  const W = 340;
  const H = 466;

  const bx = 8, by = 8, bw = W - 16, bh = 260;

  const dCx = W / 2;
  const dRx = 62;
  const dRy = 12;
  const diskBody = 20;
  const disks = 3;
  const dTopY = 340;
  const dBottomY = dTopY + disks * diskBody;

  return (
    <div className={s.right}>
      <svg
        className={s.rightSvg}
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Dashboard rendered live in a browser tab showing the count 42, wired down into a 3-disk rocksdb persistence drum."
      >
        <defs>
          <pattern id={dotId} width="8" height="8" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="0.65" fill={ruleSoft} />
          </pattern>
          <linearGradient id={diskGradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#dde1e8" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#bcc2ce" stopOpacity="0.14" />
          </linearGradient>
        </defs>

        {/* ==================== BROWSER WINDOW ==================== */}
        <rect
          x={bx} y={by} width={bw} height={bh} rx={4}
          fill={bg} stroke={rule} strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <line
          x1={bx} y1={by + 28} x2={bx + bw} y2={by + 28}
          stroke={rule} strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        {[0, 1, 2].map((i) => (
          <circle key={i} cx={bx + 12 + i * 10} cy={by + 14} r={2.6} fill={ink4} />
        ))}
        <rect
          x={bx + 60} y={by + 6} width={bw - 128} height={16}
          fill={codeBg} stroke={ruleSoft} strokeWidth={0.5}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={bx + 70} y={by + 18}
          style={{ fill: ink3, fontFamily: mono, fontSize: 9.5, letterSpacing: '0.06em' }}
        >
          nu://dashboard
        </text>
        <circle cx={bx + bw - 42} cy={by + 14} r={2.6} fill={accent2} className="blink" />
        <text
          x={bx + bw - 34} y={by + 18}
          style={{ fill: accent2, fontFamily: mono, fontSize: 9, letterSpacing: '0.26em' }}
        >
          live
        </text>

        {/* Body dot grid */}
        <rect
          x={bx + 1} y={by + 29} width={bw - 2} height={bh - 30}
          fill={`url(#${dotId})`} opacity={0.6}
        />

        {/* Body content — eyebrow, heading, big flat 42, caption */}
        <text
          x={bx + 20} y={by + 58}
          style={{ fill: accent, fontFamily: mono, fontSize: 9, letterSpacing: '0.26em' }}
        >
          DASHBOARD
        </text>
        <line
          x1={bx + 20} y1={by + 66} x2={bx + bw - 20} y2={by + 66}
          stroke={ruleSoft} strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={bx + 20} y={by + 90}
          style={{ fill: ink, fontFamily: mono, fontSize: 13, fontWeight: 700, letterSpacing: '0.02em' }}
        >
          counter
        </text>
        <text
          x={bx + bw / 2} y={by + 190} textAnchor="middle"
          style={{
            fill: ink,
            fontFamily: 'var(--font-display)',
            fontSize: 96, fontWeight: 800, letterSpacing: '-0.04em',
          }}
        >
          42
        </text>
        <text
          x={bx + bw / 2} y={by + 218} textAnchor="middle"
          style={{ fill: ink3, fontFamily: mono, fontSize: 10.5, letterSpacing: '0.02em' }}
        >
          Dashboard.count
        </text>

        {/* ==================== CONNECTOR (browser → drum) ==================== */}
        <line
          x1={dCx} y1={by + bh} x2={dCx} y2={dTopY - dRy - 4}
          stroke={ink4} strokeWidth={1} strokeDasharray="2 3"
          vectorEffect="non-scaling-stroke"
        />
        <circle
          cx={dCx}
          cy={by + bh + 14}
          r={3}
          fill={accent2}
          stroke={ruleSoft}
          strokeWidth={0.8}
          vectorEffect="non-scaling-stroke"
        />

        {/* ==================== ROCKSDB — 3-DISK STACK ==================== */}
        {Array.from({ length: disks }).map((_, i) => {
          const y1 = dTopY + i * diskBody;
          const y2 = y1 + diskBody;
          return (
            <g key={i}>
              <path
                d={`M ${dCx - dRx} ${y1} L ${dCx - dRx} ${y2} A ${dRx} ${dRy} 0 0 0 ${dCx + dRx} ${y2} L ${dCx + dRx} ${y1} Z`}
                fill={`url(#${diskGradId})`}
                stroke={rule}
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
              <ellipse
                cx={dCx}
                cy={y1}
                rx={dRx}
                ry={dRy}
                fill={`url(#${diskGradId})`}
                stroke={rule}
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
            </g>
          );
        })}

        {/* n = 42 chip on middle disk face */}
        <rect
          x={dCx - 30}
          y={dTopY + diskBody + diskBody / 2 - 10}
          width={60}
          height={20}
          rx={3}
          fill={codeBg}
          stroke={rule}
          strokeWidth={0.6}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={dCx}
          y={dTopY + diskBody + diskBody / 2 + 4}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: mono, fontSize: 12, fontWeight: 700, letterSpacing: '0.04em' }}
        >
          n = 42
        </text>

        {/* Labels under drum */}
        <text
          x={dCx}
          y={dBottomY + 26}
          textAnchor="middle"
          style={{ fill: accent2, fontFamily: mono, fontSize: 10, letterSpacing: '0.28em', fontWeight: 700 }}
        >
          ROCKSDB
        </text>
        <text
          x={dCx}
          y={dBottomY + 44}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em' }}
        >
          persisted · survives restart
        </text>
        <text
          x={dCx}
          y={dBottomY + 60}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.02em' }}
        >
          no serializer · no REST · no glue
        </text>
      </svg>
    </div>
  );
}
