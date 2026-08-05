import { type ReactNode } from 'react';
import { BrowserChrome } from './primitives/BrowserChrome';
import { DiskStack } from './primitives/DiskStack';
import { Chip } from '../Chip';
import { VizFrame } from '../VizFrame';
import s from './HeroDemoMark.module.css';

/**
 * HeroDemoMark — the composed hero demo visual:
 *   LEFT   nested Nu code tree with right-gutter hints (Counter, Dashboard,
 *          nu.Parallel with tick + live flows)
 *   MID    chevron bridge (right-pointing on desktop, down-pointing on mobile)
 *   RIGHT  glass VizFrame with browser tab rendering `42` wired down into a
 *          kv-storage platter stack (BrowserChrome + DiskStack primitives)
 *
 * Lifted from app/old_home/_hero/HeroViz.tsx. Accent hue on the runtime scene
 * is steel-blue (baked into the VizFrame's `hue="steel"`).
 */
export function HeroDemoMark({ className }: { className?: string }) {
  const cls = [s.wrap, className].filter(Boolean).join(' ');
  return (
    <div className={cls}>
      <LeftTree />
      <div className={s.bridge} aria-hidden>
        <svg className={s.bridgeDesk} viewBox="0 0 20 50" preserveAspectRatio="none">
          <polyline
            points="2,2 18,25 2,48"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <svg className={s.bridgeMob} viewBox="0 0 50 20" preserveAspectRatio="none">
          <polyline
            points="2,2 25,18 48,2"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>
      <VizFrame surface="glass" hue="steel" className={s.right}>
        <RightScene />
      </VizFrame>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
function LeftTree() {
  return (
    <div className={s.tree}>
      <Container role="virtuals" tag="state" hint="kv storage">
        <Line>
          <span className={s.kw}>class</span>{' '}
          <span className={s.tVirtuals}>Counter</span>
          <span className={s.dim}>(nu.Shape):</span>
        </Line>
        <Line indent>
          <span className={s.ident}>val</span>
          <span className={s.dim}>: </span>
          <span className={s.tVirtuals}>nu.v.IntRef</span>
        </Line>
      </Container>

      <Container role="ui" tag="ui" hint="refs as widgets">
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

      <Container role="ray" tag="app" hint="two flows in parallel">
        <Line>
          <span className={s.ident}>app</span>
          <span className={s.dim}> = </span>
          <span className={s.tRay}>nu.Parallel</span>
          <span className={s.dim}>(</span>
        </Line>

        <Container role="invisibles" tag="tick" hint="loop forever">
          <Line>
            <span className={s.tInvisibles}>nu.ForeverDo</span>
            <span className={s.dim}>(</span>
          </Line>

          <Container role="virtuals" tag="inc" hint="add 1 to state" tight>
            <Line>
              <span className={s.tVirtuals}>Counter.val</span>
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

        <Container role="invisibles" tag="live" hint="wake on change">
          <Line>
            <span className={s.tInvisibles}>nu.ReactForever</span>
            <span className={s.dim}>(</span>
          </Line>

          <Container role="virtuals" tag="subscribe" hint="which ref" tight>
            <Line>
              <span className={s.tVirtuals}>Counter.val</span>
              <span className={s.dim}>.on_change(),</span>
            </Line>
          </Container>

          <Container role="ui" tag="bind" hint="update ui state" tight>
            <Line>
              <span className={s.tUi}>Dashboard.count</span>
              <span className={s.dim}>.set(</span>
              <span className={s.tVirtuals}>Counter.val</span>
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
  );
}

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
        <Chip size="sm">{tag}</Chip>
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
 * RightScene — browser chrome renders 42, dashed wire connects down to
 * kv-storage platter stack. Accent = steel-blue (via VizFrame hue="steel").
 * ==========================================================================*/
function RightScene() {
  const ink = 'var(--site-ink)';
  const ink3 = 'var(--site-ink-3)';
  const ink4 = 'var(--site-ink-4)';
  const ruleSoft = 'var(--site-rule-2)';
  const accent = 'var(--site-accent)';
  const mono = 'var(--font-mono)';

  const W = 340;
  const H = 445;

  const bw = 255, bh = 204;
  const bx = (W - bw) / 2, by = 20;
  const wireY1 = by + bh;
  const dCx = W / 2;
  const dTopY = 316;
  const platterGap = 22;
  const platters = 4;
  const dBottomY = dTopY + (platters - 1) * platterGap;
  const chipTopY = dTopY + 1.5 * platterGap - 11;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Dashboard rendered in a browser tab showing 42, wired down into a kv-storage persistence disk."
    >
      <BrowserChrome x={bx} y={by} width={bw} height={bh} url="nu://dashboard" />

      <text x={bx + 12} y={by + 44} style={{ fill: ink4, fontFamily: mono, fontSize: 8, letterSpacing: '0.24em' }}>
        dashboard
      </text>
      <line x1={bx + 12} y1={by + 50} x2={bx + bw - 12} y2={by + 50} stroke={ruleSoft} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      <text x={dCx} y={by + 143} textAnchor="middle" style={{ fill: ink, fontFamily: 'var(--font-display)', fontSize: 85, fontWeight: 800, letterSpacing: '-0.04em' }}>
        42
      </text>
      <text x={dCx} y={by + 170} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.02em' }}>
        dashboard.count
      </text>

      <circle cx={dCx} cy={wireY1} r={2} fill={accent} />
      <line
        x1={dCx}
        y1={wireY1}
        x2={dCx}
        y2={chipTopY}
        stroke={accent}
        strokeWidth={1}
        strokeDasharray="2 4"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
        opacity={0.8}
      />
      <circle cx={dCx} cy={chipTopY} r={2} fill={accent} />

      <DiskStack
        cx={dCx}
        topY={dTopY}
        platters={platters}
        platterGap={platterGap}
        rx={68}
        ry={13}
        chip={{ text: 'val = 42', gap: 1 }}
      />

      <text x={dCx} y={dBottomY + 26} textAnchor="middle" style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.28em', fontWeight: 700 }}>
        kv storage
      </text>
      <text x={dCx} y={dBottomY + 44} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em' }}>
        persisted · survives restart
      </text>
    </svg>
  );
}
