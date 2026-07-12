import { Fragment, useId, type ReactNode, type CSSProperties } from 'react';
import s from './HeroViz.module.css';

/**
 * HeroViz — the interaction-model visualization for the hero.
 *
 * LEFT: nested colored Nu code containers, hints in a right gutter joined by
 *       dotted arrows. Every Nu primitive gets its own container + hint.
 *   Counter shape (state · virtuals · rocksdb)
 *   Dashboard shape (ui shape)
 *   app = nu.Parallel(...) — two flows, deep nesting:
 *     nu.ForeverDo( Counter.n.inc() >> nu.Delay(1.0) )
 *     nu.ReactForever( on_change, Dashboard.count.set(Counter.n) )
 *
 * RIGHT: inline SVG — browser tab rendering Dashboard live (count = 42),
 *        wired into a 3-disk rocksdb persistence drum. Flat design, hairline
 *        borders, dot-grid body. Same style vocab as NuspaceMock.
 *
 * `nu.Parallel(...)` is a stand-in for `tick | live` so parallel-ness gets
 * its own labeled container. Half-real, half-conceptual.
 */
export function HeroViz() {
  return (
    <div className={s.wrap}>
      <div className={s.tree}>
        {/* Counter shape (2 lines) */}
        <Row role="state" depth={0} hint="virtuals fabric, backed by rocksdb">
          <span className={s.kw2}>class</span>
          {' '}
          <span className={s.name}>Counter</span>
          <span className={s.dim}>(nu.Shape):</span>
          {'\n    '}
          <span className={s.ident}>n</span>
          <span className={s.dim}>: </span>
          <span className={s.tagState}>nu.v.IntRef</span>
        </Row>

        {/* Dashboard shape (2 lines) */}
        <Row role="ui" depth={0} hint="UI shape — refs ARE the widgets">
          <span className={s.kw}>class</span>
          {' '}
          <span className={s.name}>Dashboard</span>
          <span className={s.dim}>(nu.ui.Page):</span>
          {'\n    '}
          <span className={s.ident}>count</span>
          <span className={s.dim}>: </span>
          <span className={s.tagUi}>nu.ui.TextRef</span>
        </Row>

        {/* App outer — nu.Parallel */}
        <Row role="flow" depth={0} hint="two flows in parallel — the whole app">
          <span className={s.ident}>app</span>
          <span className={s.dim}> = </span>
          <span className={s.name}>nu.Parallel</span>
          <span className={s.dim}>(</span>
        </Row>

        {/* ForeverDo */}
        <Row role="state" depth={1} hint="runs its child forever">
          <span className={s.kw2}>nu.ForeverDo</span>
          <span className={s.dim}>(</span>
        </Row>

        {/* Inc leaf */}
        <Row role="state" depth={2} hint="add 1 to state">
          <span className={s.tagState}>Counter.n</span>
          <span className={s.dim}>.inc()</span>
        </Row>

        <Op depth={2}>{'>>'}</Op>

        {/* Delay leaf */}
        <Row role="state" depth={2} hint="wait 1 second">
          <span className={s.kw2}>nu.Delay</span>
          <span className={s.dim}>(</span>
          <span className={s.num}>1.0</span>
          <span className={s.dim}>)</span>
        </Row>

        <Close depth={1}>{')'}</Close>

        {/* ReactForever */}
        <Row role="ui" depth={1} hint="wakes when the ref changes">
          <span className={s.kw}>nu.ReactForever</span>
          <span className={s.dim}>(</span>
        </Row>

        {/* Subscribe leaf */}
        <Row role="state" depth={2} hint="the ref to subscribe to">
          <span className={s.tagState}>Counter.n</span>
          <span className={s.dim}>.on_change(),</span>
        </Row>

        {/* Bind leaf (money line) */}
        <Row role="ui" depth={2} hint="UI reads state, live">
          <span className={s.tagUi}>Dashboard.count</span>
          <span className={s.dim}>.set(</span>
          <span className={s.tagState}>Counter.n</span>
          <span className={s.dim}>)</span>
        </Row>

        <Close depth={1}>{')'}</Close>
        <Close depth={0}>{')'}</Close>
      </div>

      <RightScene />
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Row — one container + hint pair, occupies a single grid row.
 * -------------------------------------------------------------------------- */
function Row({
  role,
  depth,
  hint,
  children,
}: {
  role: 'state' | 'ui' | 'flow';
  depth: number;
  hint: string;
  children: ReactNode;
}) {
  const style = { '--depth': depth } as CSSProperties;
  return (
    <Fragment>
      <div className={s.body} data-role={role} style={style}>
        <pre className={s.code}>{children}</pre>
      </div>
      <div className={s.hint} data-role={role}>
        <HintArrow />
        <span className={s.hintText}>{hint}</span>
      </div>
    </Fragment>
  );
}

function Op({ depth, children }: { depth: number; children: ReactNode }) {
  const style = { '--depth': depth } as CSSProperties;
  return (
    <Fragment>
      <div className={s.op} style={style}>{children}</div>
      <div className={s.spacer} />
    </Fragment>
  );
}

function Close({ depth, children }: { depth: number; children: ReactNode }) {
  const style = { '--depth': depth } as CSSProperties;
  return (
    <Fragment>
      <div className={s.close} style={style}>{children}</div>
      <div className={s.spacer} />
    </Fragment>
  );
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
 * RightScene — flat-design browser tab + 3-disk rocksdb drum.
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
  const H = 520;

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
