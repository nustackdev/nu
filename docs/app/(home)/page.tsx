import React from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import s from './landing.module.css';

/* ----------------------------------------------------------------------------
 * Inline GitHub mark — lucide dropped brand icons
 * -------------------------------------------------------------------------- */
function GithubMark({ size = 15 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden
    >
      <path d="M12 0.5C5.65 0.5 0.5 5.65 0.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-1.94c-3.2.7-3.87-1.54-3.87-1.54-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.56-.29-5.25-1.28-5.25-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.47.11-3.06 0 0 .97-.31 3.18 1.18a11.05 11.05 0 0 1 5.8 0c2.21-1.49 3.18-1.18 3.18-1.18.63 1.59.23 2.77.11 3.06.74.81 1.19 1.84 1.19 3.1 0 4.43-2.7 5.4-5.27 5.69.41.36.78 1.06.78 2.13v3.16c0 .31.21.67.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35 0.5 12 0.5z" />
    </svg>
  );
}

/* ============================================================================
 * Code highlighting
 * ==========================================================================*/

const KW = new Set([
  'import', 'from', 'as', 'class', 'def', 'return', 'with', 'yield',
  'if', 'else', 'elif', 'for', 'in', 'not', 'and', 'or', 'lambda',
  'True', 'False', 'None', 'await', 'async', 'pass',
]);

function renderLine(text: string, key: number): React.ReactNode {
  let code = text;
  let comment: string | null = null;
  const hashIdx = text.indexOf('#');
  if (hashIdx >= 0) {
    const before = text.slice(0, hashIdx);
    const quotes =
      (before.match(/"/g) || []).length + (before.match(/'/g) || []).length;
    if (quotes % 2 === 0) {
      code = before;
      comment = text.slice(hashIdx);
    }
  }
  const tokenRe =
    /(\s+|"[^"]*"|'[^']*'|>>|<<|==|!=|<=|>=|\w+|.)/g;
  const parts: React.ReactNode[] = [];
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = tokenRe.exec(code)) !== null) {
    const tok = m[0];
    if (KW.has(tok)) {
      parts.push(<span key={i++} className={s.codeKw}>{tok}</span>);
    } else if (/^["'].*["']$/.test(tok)) {
      parts.push(<span key={i++} className={s.codeSt}>{tok}</span>);
    } else if (tok === '>>' || tok === '<<') {
      parts.push(<span key={i++} className={s.codeOp}>{tok}</span>);
    } else {
      parts.push(<span key={i++}>{tok}</span>);
    }
  }
  if (comment !== null) {
    parts.push(<span key={i++} className={s.codeCm}>{comment}</span>);
  }
  return <span key={key}>{parts}{'\n'}</span>;
}

function Code({ src }: { src: string }) {
  const lines = src.replace(/\n$/, '').split('\n');
  return <pre className={s.code}>{lines.map((l, i) => renderLine(l, i))}</pre>;
}

/* Terminal-style code with line-number gutter — used inside quickstart steps. */
function GutterCode({ src }: { src: string }) {
  const lines = src.replace(/\n$/, '').split('\n');
  return (
    <pre className={s.gutterCode}>
      {lines.map((l, i) => (
        <span key={i} className={s.gutterLine}>
          <span className={s.gutterNum}>{String(i + 1).padStart(2, '0')}</span>
          <span className={s.gutterSep}>│</span>
          <span className={s.gutterText}>{renderLine(l, i)}</span>
        </span>
      ))}
    </pre>
  );
}

/* ============================================================================
 * SVG helpers
 * ==========================================================================*/

/** Corner tick marks on any SVG rect — spec-drawing crop marks. */
function CornerTicks({
  x, y, w, h, size = 6, color = 'var(--nu-accent)',
}: { x: number; y: number; w: number; h: number; size?: number; color?: string }) {
  const t = size;
  return (
    <g stroke={color} strokeWidth={1} fill="none" opacity={0.85}>
      <path d={`M ${x} ${y + t} L ${x} ${y} L ${x + t} ${y}`} />
      <path d={`M ${x + w - t} ${y} L ${x + w} ${y} L ${x + w} ${y + t}`} />
      <path d={`M ${x} ${y + h - t} L ${x} ${y + h} L ${x + t} ${y + h}`} />
      <path d={`M ${x + w - t} ${y + h} L ${x + w} ${y + h} L ${x + w} ${y + h - t}`} />
    </g>
  );
}

/* ============================================================================
 * Fan-out visual: one move, three substrates
 * ==========================================================================*/

function Substrate({
  kind, x, y, value, accent = false,
}: {
  kind: 'browser' | 'disk' | 'memory';
  x: number;
  y: number;
  value: string;
  accent?: boolean;
}) {
  const stroke = accent ? 'var(--nu-accent)' : 'var(--nu-rule)';
  const sw = accent ? 1.6 : 1;
  const valueFill = accent ? 'var(--nu-accent)' : 'var(--nu-ink-2)';
  const valueWeight = accent ? 700 : 500;
  const line = accent ? 'var(--nu-accent-line)' : 'var(--nu-rule)';
  const dotFill = accent ? 'var(--nu-accent)' : 'var(--nu-ink-3)';
  const valueOpacity = accent ? 1 : 0.75;
  const softText = accent ? 'var(--nu-accent)' : 'var(--nu-ink-3)';

  if (kind === 'browser') {
    return (
      <g>
        <rect x={x} y={y} width={240} height={80} rx={6}
          fill="var(--color-fd-background)" stroke={stroke} strokeWidth={sw} />
        {/* header divider */}
        <line x1={x} y1={y + 26} x2={x + 240} y2={y + 26}
          stroke={line} strokeWidth={0.75} opacity={0.7} />
        {/* window dots */}
        <circle cx={x + 12} cy={y + 13} r={2.6} fill={dotFill} opacity={0.55} />
        <circle cx={x + 22} cy={y + 13} r={2.6} fill={dotFill} opacity={0.55} />
        <circle cx={x + 32} cy={y + 13} r={2.6} fill={dotFill} opacity={0.55} />
        {/* address bar */}
        <rect x={x + 46} y={y + 6} width={188} height={14} rx={2}
          fill="var(--nu-code-bg-2)" stroke={line} strokeWidth={0.5} />
        {/* lock */}
        <rect x={x + 52} y={y + 10} width={5} height={5} rx={1}
          fill="none" stroke={softText} strokeWidth={0.8} />
        <path d={`M ${x + 53.5} ${y + 10} v -1.5 a 1 1 0 0 1 2 0 v 1.5`}
          stroke={softText} strokeWidth={0.6} fill="none" />
        {/* url */}
        <text x={x + 62} y={y + 17}
          fontFamily="ui-monospace, monospace" fontSize={8.5}
          fill={softText} letterSpacing="0.02em">
          nu://counter
        </text>
        {/* value */}
        <text x={x + 120} y={y + 62} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={19} fill="var(--nu-ink)"
          opacity={valueOpacity}>
          count:{' '}
          <tspan fill={valueFill} fontWeight={valueWeight}>{value}</tspan>
        </text>
      </g>
    );
  }

  if (kind === 'disk') {
    const cx = x + 120;
    const top = y + 16;
    const bot = y + 62;
    const rx = 92, ry = 8;
    return (
      <g>
        {/* body fill */}
        <rect x={cx - rx} y={top} width={2 * rx} height={bot - top}
          fill="var(--color-fd-background)" stroke="none" />
        {/* bottom bulge */}
        <path d={`M ${cx - rx} ${bot} A ${rx} ${ry} 0 0 0 ${cx + rx} ${bot}`}
          fill="var(--color-fd-background)" stroke={stroke} strokeWidth={sw} />
        {/* sides */}
        <line x1={cx - rx} y1={top} x2={cx - rx} y2={bot} stroke={stroke} strokeWidth={sw} />
        <line x1={cx + rx} y1={top} x2={cx + rx} y2={bot} stroke={stroke} strokeWidth={sw} />
        {/* top ellipse */}
        <ellipse cx={cx} cy={top} rx={rx} ry={ry}
          fill="var(--color-fd-background)" stroke={stroke} strokeWidth={sw} />
        {/* platter grooves — two concentric */}
        <path d={`M ${cx - rx * 0.94} ${top + 10} A ${rx * 0.94} ${ry * 0.9} 0 0 0 ${cx + rx * 0.94} ${top + 10}`}
          fill="none" stroke={stroke} strokeWidth={0.55} opacity={0.45} />
        <path d={`M ${cx - rx * 0.72} ${top + 16} A ${rx * 0.72} ${ry * 0.75} 0 0 0 ${cx + rx * 0.72} ${top + 16}`}
          fill="none" stroke={stroke} strokeWidth={0.5} opacity={0.35} />
        {/* spindle */}
        <circle cx={cx} cy={top + 20} r={1.7} fill={stroke} opacity={0.7} />
        <circle cx={cx} cy={top + 20} r={4} fill="none" stroke={stroke} strokeWidth={0.4} opacity={0.4} />
        {/* value */}
        <text x={cx} y={y + 62} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={18} fill="var(--nu-ink)"
          opacity={valueOpacity}>
          count:{' '}
          <tspan fill={valueFill} fontWeight={valueWeight}>{value}</tspan>
        </text>
      </g>
    );
  }

  // memory — register / brace framing
  return (
    <g>
      <rect x={x} y={y} width={240} height={80} rx={6}
        fill="var(--color-fd-background)" stroke={stroke} strokeWidth={sw} />
      {/* address gutter */}
      <text x={x + 12} y={y + 15}
        fontFamily="ui-monospace, monospace" fontSize={8.5}
        letterSpacing="0.16em" fill={softText}>
        0x00
      </text>
      <line x1={x + 12} y1={y + 20} x2={x + 46} y2={y + 20}
        stroke={line} strokeWidth={0.5} opacity={0.6} />
      {/* braces via text */}
      <text x={x + 120} y={y + 54} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize={22} fill="var(--nu-ink)"
        opacity={valueOpacity}>
        {'{ count: '}
        <tspan fill={valueFill} fontWeight={valueWeight}>{value}</tspan>
        {' }'}
      </text>
      {/* size marker */}
      <text x={x + 228} y={y + 74} textAnchor="end"
        fontFamily="ui-monospace, monospace" fontSize={8.5}
        letterSpacing="0.16em" fill={softText}>
        i64
      </text>
    </g>
  );
}

function SubstrateLabel({ x, y, text }: { x: number; y: number; text: string }) {
  return (
    <g>
      <rect x={x - 3} y={y - 9} width={2} height={10} fill="var(--nu-accent)" opacity={0.7} />
      <text x={x + 6} y={y}
        fontFamily="ui-monospace, monospace" fontSize={10}
        letterSpacing="0.28em" fill="var(--nu-ink-3)">
        {text}
      </text>
    </g>
  );
}

function TransitionViz() {
  const rowY = [90, 250, 410];
  const midY = 250;
  const mLeft = 440;
  const mRight = 640;
  const arrowTip = (px: number, py: number) => (
    <polygon
      points={`${px - 6},${py - 4} ${px},${py} ${px - 6},${py + 4}`}
      fill="var(--nu-accent)" opacity={0.7}
    />
  );
  const oldApis = [
    'input.value = 1',
    'db.put("count", 1)',
    'd["count"] = 1',
  ];
  return (
    <svg viewBox="0 0 1000 480" xmlns="http://www.w3.org/2000/svg"
      className={s.fanoutSvg} role="img"
      aria-label="Three fragmented APIs today collapse into one Nu interaction that reaches all substrates."
    >
      <defs>
        <radialGradient id="pillGlow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="var(--nu-accent)" stopOpacity="0.20" />
          <stop offset="100%" stopColor="var(--nu-accent)" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* row labels */}
      <SubstrateLabel x={20} y={43} text="BROWSER TAB" />
      <SubstrateLabel x={20} y={203} text="ON DISK" />
      <SubstrateLabel x={20} y={363} text="IN MEMORY" />

      {/* left substrates (before: 0) */}
      <Substrate kind="browser" x={20} y={50} value="0" />
      <Substrate kind="disk" x={20} y={210} value="0" />
      <Substrate kind="memory" x={20} y={370} value="0" />

      {/* the collapse — 3 old APIs converge into the central node */}
      <g fill="none" stroke="var(--nu-accent)" strokeWidth={1.4} opacity={0.55}>
        <path d={`M 260 ${rowY[0]} C 340 ${rowY[0]} 360 ${midY} ${mLeft} ${midY}`} />
        <path d={`M 260 ${rowY[1]} L ${mLeft} ${midY}`} />
        <path d={`M 260 ${rowY[2]} C 340 ${rowY[2]} 360 ${midY} ${mLeft} ${midY}`} />
      </g>

      {/* old API labels — anchored to end just before the central node.
          rows 1/2 sit above their curve; row 3 below to clear the ascending curve. */}
      {oldApis.map((api, i) => {
        const y = i === 2 ? rowY[i] + 18 : rowY[i] - 10;
        return (
          <text
            key={i}
            x={mLeft - 20}
            y={y}
            textAnchor="end"
            fontFamily="ui-monospace, monospace"
            fontSize={12}
            fill="var(--nu-ink-3)"
            style={{ textDecoration: 'line-through' }}
          >
            {api}
          </text>
        );
      })}

      {/* central node — where 3 APIs collapse into 1 Interaction */}
      <g>
        <ellipse cx={(mLeft + mRight) / 2} cy={midY + 8} rx={140} ry={70}
          fill="url(#pillGlow)" />
        <rect x={mLeft} y={210} width={mRight - mLeft} height={80} rx={6}
          fill="var(--nu-accent-soft)" stroke="var(--nu-accent)" strokeWidth={1.6} />
        <CornerTicks x={mLeft} y={210} w={mRight - mLeft} h={80} size={7} />
        <text x={(mLeft + mRight) / 2} y={197} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={10}
          letterSpacing="0.28em" fill="var(--nu-accent)">
          NU.RUN · ONE INTERACTION
        </text>
        <text x={(mLeft + mRight) / 2} y={257} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={20} fontWeight={700}
          fill="var(--nu-accent)">
          Add(CounterRef, 1)
        </text>
        <line x1={mLeft + 40} y1={273} x2={mRight - 40} y2={273}
          stroke="var(--nu-accent-line)" strokeWidth={1} />
      </g>

      {/* fan-out — one Interaction reaches all three substrates */}
      <g fill="none" stroke="var(--nu-accent)" strokeWidth={1.4} opacity={0.55}
         strokeDasharray="5 4">
        <path d={`M ${mRight} ${midY} C 700 ${midY} 700 ${rowY[0]} 754 ${rowY[0]}`} />
        <path d={`M ${mRight} ${midY} L 754 ${rowY[1]}`} />
        <path d={`M ${mRight} ${midY} C 700 ${midY} 700 ${rowY[2]} 754 ${rowY[2]}`} />
      </g>
      {arrowTip(760, rowY[0])}
      {arrowTip(760, rowY[1])}
      {arrowTip(760, rowY[2])}

      {/* right substrates (after: 1, accent) */}
      <Substrate kind="browser" x={760} y={50} value="1" accent />
      <Substrate kind="disk" x={760} y={210} value="1" accent />
      <Substrate kind="memory" x={760} y={370} value="1" accent />
    </svg>
  );
}

/* ============================================================================
 * Deep-dive showcase: three fabrics, before → after
 * ==========================================================================*/

function VizFrame({ children }: { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 480 180"
      xmlns="http://www.w3.org/2000/svg"
      className={s.vizSvg}
      role="img"
    >
      {children}
    </svg>
  );
}

function ArrowBand({ label }: { label: string }) {
  return (
    <g>
      <line
        x1="200" y1="90" x2="278" y2="90"
        stroke="var(--nu-accent)"
        strokeWidth="1.5"
        strokeDasharray="5 3"
        opacity="0.75"
      />
      <polygon points="278,85 290,90 278,95" fill="var(--nu-accent)" />
      <text
        x="239" y="76" textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="12"
        fill="var(--nu-accent)"
        letterSpacing="0.04em"
      >
        {label}
      </text>
      <text
        x="239" y="108" textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="10"
        fill="var(--nu-ink-3)"
        letterSpacing="0.2em"
      >
        NU.RUN
      </text>
    </g>
  );
}

function PanelFrame({
  x,
  label,
  accent,
  children,
}: {
  x: number;
  label: string;
  accent?: boolean;
  children: React.ReactNode;
}) {
  return (
    <g>
      <rect
        x={x}
        y="20"
        width="180"
        height="140"
        rx="5"
        fill="var(--color-fd-background)"
        stroke={accent ? 'var(--nu-accent)' : 'var(--nu-rule)'}
        strokeWidth={accent ? '1.6' : '1'}
      />
      <text
        x={x + 14}
        y="42"
        fontFamily="ui-monospace, monospace"
        fontSize="10"
        letterSpacing="0.24em"
        fill={accent ? 'var(--nu-accent)' : 'var(--nu-ink-3)'}
      >
        {label}
      </text>
      {accent ? <CornerTicks x={x} y={20} w={180} h={140} size={6} /> : null}
    </g>
  );
}

function MemViz() {
  return (
    <VizFrame>
      <PanelFrame x={10} label="CONTEXT V0">
        <text
          x="100" y="115" textAnchor="middle"
          fontFamily="ui-monospace, monospace"
          fontSize="22" fill="var(--nu-ink-2)"
        >
          {'{ }'}
        </text>
      </PanelFrame>
      <ArrowBand label="store(1)" />
      <PanelFrame x={290} label="CONTEXT V1" accent>
        <text
          x="380" y="115" textAnchor="middle"
          fontFamily="ui-monospace, monospace"
          fontSize="18" fill="var(--nu-ink)"
        >
          {'{ "value": '}
          <tspan fill="var(--nu-accent)" fontWeight="700">1</tspan>
          {' }'}
        </text>
      </PanelFrame>
    </VizFrame>
  );
}

function VirtualsViz() {
  return (
    <VizFrame>
      <PanelFrame x={10} label="CONTEXT V0">
        <text
          x="100" y="82" textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize="11"
          letterSpacing="0.18em" fill="var(--nu-ink-3)"
        >
          ROCKSDB
        </text>
        <line
          x1="30" y1="94" x2="170" y2="94"
          stroke="var(--nu-rule)" strokeWidth="1"
        />
        <text
          x="100" y="128" textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize="15"
          fill="var(--nu-ink-2)" opacity="0.65"
        >
          ∅
        </text>
      </PanelFrame>
      <ArrowBand label="store(1)" />
      <PanelFrame x={290} label="CONTEXT V1" accent>
        <text
          x="380" y="82" textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize="11"
          letterSpacing="0.18em" fill="var(--nu-accent)"
        >
          ROCKSDB
        </text>
        <line
          x1="310" y1="94" x2="450" y2="94"
          stroke="var(--nu-accent-line)" strokeWidth="1"
        />
        <text
          x="380" y="126" textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize="13"
          fill="var(--nu-ink)"
        >
          Counter/value =
          {' '}
          <tspan fill="var(--nu-accent)" fontWeight="700">1</tspan>
        </text>
      </PanelFrame>
    </VizFrame>
  );
}

function NudleViz() {
  return (
    <VizFrame>
      <PanelFrame x={10} label="CONTEXT V0">
        {/* browser chrome */}
        <circle cx="26" cy="60" r="2.4" fill="var(--nu-ink-3)" opacity="0.55" />
        <circle cx="34" cy="60" r="2.4" fill="var(--nu-ink-3)" opacity="0.55" />
        <circle cx="42" cy="60" r="2.4" fill="var(--nu-ink-3)" opacity="0.55" />
        <line
          x1="52" y1="60" x2="180" y2="60"
          stroke="var(--nu-rule)" strokeWidth="1"
        />
        {/* content */}
        <text
          x="100" y="105" textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize="9"
          letterSpacing="0.24em" fill="var(--nu-ink-3)"
        >
          COUNT
        </text>
        <text
          x="100" y="140" textAnchor="middle"
          fontFamily="ui-monospace, monospace"
          fontSize="32" fontWeight="700" fill="var(--nu-ink-2)"
          opacity="0.55"
        >
          0
        </text>
      </PanelFrame>
      <ArrowBand label="store(1)" />
      <PanelFrame x={290} label="CONTEXT V1" accent>
        {/* browser chrome */}
        <circle cx="306" cy="60" r="2.4" fill="var(--nu-accent)" opacity="0.75" />
        <circle cx="314" cy="60" r="2.4" fill="var(--nu-accent)" opacity="0.75" />
        <circle cx="322" cy="60" r="2.4" fill="var(--nu-accent)" opacity="0.75" />
        <line
          x1="332" y1="60" x2="460" y2="60"
          stroke="var(--nu-accent-line)" strokeWidth="1"
        />
        {/* content */}
        <text
          x="380" y="105" textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize="9"
          letterSpacing="0.24em" fill="var(--nu-accent)"
        >
          COUNT
        </text>
        <text
          x="380" y="140" textAnchor="middle"
          fontFamily="ui-monospace, monospace"
          fontSize="32" fontWeight="700" fill="var(--nu-accent)"
        >
          1
        </text>
      </PanelFrame>
    </VizFrame>
  );
}

const CTX_ROWS: Array<{
  name: string;
  hint: React.ReactNode;
  code: string;
  viz: React.ReactNode;
}> = [
  {
    name: 'nu.mem',
    hint: (
      <>
        the Context is a <b>Python dict</b>.
      </>
    ),
    code: `class Counter(nu.Shape):
    value: nu.mem.IntRef

ctx = nu.Context().bind(dict, {}, Counter)

nu.run(Counter.value.store(1), ctx)`,
    viz: <MemViz />,
  },
  {
    name: 'nu.virtuals',
    hint: (
      <>
        the Context is <b>RocksDB on disk</b>.
      </>
    ),
    code: `class Counter(nu.Shape):
    value: nu.virtuals.IntRef

ctx = nu.Context().bind(Navigator, rocksdb)

nu.run(Counter.value.store(1), ctx)`,
    viz: <VirtualsViz />,
  },
  {
    name: 'nu.nudle',
    hint: (
      <>
        the Context is a <b>live browser tab</b>.
      </>
    ),
    code: `class Dashboard(nu.nudle.Page):
    count: nu.nudle.TextRef

ctx = nu.Context().bind(nd.Server, tab)

nu.run(Dashboard.count.store(1), ctx)`,
    viz: <NudleViz />,
  },
];

/* ============================================================================
 * Getting-started steps
 * ==========================================================================*/

const STEPS: Array<{
  n: string;
  numeral: string;
  file: string;
  pin: React.ReactNode;
  title: string;
  code: string;
  twist: React.ReactNode;
  twistBody: React.ReactNode;
}> = [
  {
    n: 'step 01',
    numeral: '01',
    file: 'reads.py',
    pin: <><b>ref</b>&nbsp;·&nbsp;address</>,
    title: 'It reads.',
    code: `import nu
import nu.mem as nm

class Order(nu.Shape):
    price: nm.FloatRef
    qty:   nm.IntRef

data = {"price": 185.5, "qty": 10}
ctx  = nu.Context().bind(dict, data, Order)

nu.run(Order.price, ctx)   # 185.5`,
    twist: <><b>Order.price is a Ref, not a value.</b></>,
    twistBody: (
      <>
        A Ref is an <b>address</b> into the world. The value only appears when
        the Context evaluates it. Refs travel through your program; values only
        exist at the edges.
      </>
    ),
  },
  {
    n: 'step 02',
    numeral: '02',
    file: 'computes.py',
    pin: <><b>tree</b>&nbsp;·&nbsp;defer</>,
    title: 'It computes.',
    code: `notional = Order.price * Order.qty

nu.run(notional, ctx)      # 1855.0`,
    twist: <><b>* built a tree</b>, it didn&apos;t multiply.</>,
    twistBody: (
      <>
        Every Python operator on a Ref is a <b>constructor</b>. Nothing computes
        until <code>nu.run</code> hands the tree to a Context. The tree carries
        the recipe; the Context is the kitchen.
      </>
    ),
  },
  {
    n: 'step 03',
    numeral: '03',
    file: 'writes.py',
    pin: <><b>cmd</b>&nbsp;·&nbsp;write</>,
    title: 'It writes.',
    code: `nu.run(Order.price.store(200.0), ctx)

nu.run(Order.price, ctx)   # 200.0`,
    twist: <><b>.store() is a Command</b>, not a call.</>,
    twistBody: (
      <>
        Every write is a term in the tree. Reads too. The world only moves
        inside <code>nu.run</code> — outside of it, your code is data.
      </>
    ),
  },
  {
    n: 'step 04',
    numeral: '04',
    file: 'persists.py',
    pin: <><b>swap</b>&nbsp;·&nbsp;disk</>,
    title: 'It persists.',
    code: `import nu.virtuals as nv     # ← the one change

class Order(nu.Shape):
    price: nv.FloatRef
    qty:   nv.IntRef

# every expression above still runs.
# storage is RocksDB now.`,
    twist: <><b>Same tree. Different Context.</b></>,
    twistBody: (
      <>
        Swap <code>nm</code> for <code>nv</code> and the same program runs on
        disk — transactional, snapshotted, observable. The Shape didn&apos;t
        change. The Context under it did.
      </>
    ),
  },
  {
    n: 'step 05',
    numeral: '05',
    file: 'composes.py',
    pin: <><b>&gt;&gt;</b>&nbsp;·&nbsp;<b>|</b></>,
    title: 'It composes.',
    code: `app = (
    Order.price.store(200.0)
    >> Order.qty.store(50)
    >> nu.Print("notional", Order.price * Order.qty)
)

nu.run(app, ctx)           # notional 10000.0`,
    twist: <><b>&gt;&gt; sequences.</b>&nbsp;&nbsp;<b>| runs in parallel.</b></>,
    twistBody: (
      <>
        Two operators for the whole language of composition. Every Nu program —
        reads, writes, control flow, IO — is one tree, built with <code>&gt;&gt;</code>{' '}
        and <code>|</code>.
      </>
    ),
  },
  {
    n: 'step 06',
    numeral: '06',
    file: 'ships.py',
    pin: <><b>ship</b>&nbsp;·&nbsp;prod</>,
    title: 'It ships.',
    code: `import nu
import nu.virtuals as nv
import nu.nudle as nd

class Counter(nu.Shape):
    value: nv.IntRef

class Dashboard(nd.Page):
    heading: nd.HeadingRef
    count:   nd.TextRef
    history: nd.LineChart

app = (
    Dashboard.heading.store("counter live")
    >> nu.ForeverDo(
        nv.Snapshot(
            Dashboard.count.store(Counter.value)
            | Dashboard.history.append(Counter.value, Counter.value)
        )
        >> nv.Transaction(Counter.value.store(Counter.value + 1))
        >> nu.Delay(1.0),
    )
)

nd.serve(app, ctx)         # a browser tab lights up`,
    twist: <><b>Same primitives.</b> Two Contexts at once.</>,
    twistBody: (
      <>
        One program binds RocksDB and a browser at once — persistent counter,
        live chart, reactive updates, no framework. This is production Nu.
      </>
    ),
  },
];

const FEATURES: Array<{
  name: string;
  title: string;
  body: string;
  code: string;
}> = [
  {
    name: 'parallel',
    title: 'Compose in parallel with |.',
    body: 'Any subtree can run concurrently. The model tells the runtime what is safe.',
    code: `nu.run(
    nu.Print(1) | nu.Print(2) | nu.Print(3),
    ctx,
)`,
  },
  {
    name: 'streams',
    title: 'Lazy streams, chained, reduced.',
    body: 'Map, Filter, and reductions stack without materializing intermediates.',
    code: `i = nu.IntAttrRef("item")

total = nu.Sum(nu.Collect(
    nu.Map(nu.Iter(range(100)), transform=i * i),
))`,
  },
  {
    name: 'spans',
    title: 'Transactions are a wrapper.',
    body: 'Spans wrap any subtree without rewriting it. Same shape: retry, timeout, snapshot.',
    code: `nv.Transaction(
    Counter.value.store(0),
    Counter.value.inc(),
    Counter.value.inc(),
)`,
  },
  {
    name: 'inspect',
    title: 'Your program is data.',
    body: 'Render, serialize, transform. Nothing runs until you say run.',
    code: `from nu_inspect import render_nu

print(render_nu(app))
# Run(
#   Print(Mul(Order.price, Order.qty))
# )`,
  },
];

/* ============================================================================
 * Watch this run — the 30-LOC live example
 * ==========================================================================*/

function DashboardMock() {
  /* chart lives inside the HISTORY panel: x=170..440, y=110..190
     usable interior with padding: x=182..428, y=128..182 */
  const chartPoints: Array<[number, number]> = [
    [182, 178], [200, 176], [218, 172], [236, 168], [254, 162],
    [272, 158], [290, 152], [308, 146], [326, 141], [344, 138],
    [362, 134], [380, 132], [398, 130], [416, 128], [428, 128],
  ];
  const pathD = chartPoints
    .map((p, i) => (i === 0 ? `M ${p[0]} ${p[1]}` : `L ${p[0]} ${p[1]}`))
    .join(' ');
  const areaD = `${pathD} L 428 184 L 182 184 Z`;
  return (
    <svg viewBox="0 0 460 300" xmlns="http://www.w3.org/2000/svg"
      className={s.watchMockSvg} role="img" aria-label="Live dashboard: counter and history chart">
      <defs>
        <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--nu-accent)" stopOpacity="0.28" />
          <stop offset="100%" stopColor="var(--nu-accent)" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* browser chrome */}
      <rect x={0} y={0} width={460} height={300} rx={8}
        fill="var(--color-fd-background)" stroke="var(--nu-rule)" strokeWidth={1} />
      <line x1={0} y1={36} x2={460} y2={36} stroke="var(--nu-rule)" strokeWidth={1} />
      <circle cx={18} cy={18} r={3.5} fill="var(--nu-ink-4)" />
      <circle cx={30} cy={18} r={3.5} fill="var(--nu-ink-4)" />
      <circle cx={42} cy={18} r={3.5} fill="var(--nu-ink-4)" />
      <rect x={70} y={9} width={340} height={18} rx={3}
        fill="var(--nu-code-bg-2)" stroke="var(--nu-rule)" strokeWidth={0.5} />
      <text x={80} y={22} fontFamily="ui-monospace, monospace" fontSize={10}
        fill="var(--nu-ink-3)">
        nu://counter
      </text>

      {/* title */}
      <text x={20} y={60} fontFamily="ui-monospace, monospace" fontSize={10}
        letterSpacing="0.24em" fill="var(--nu-ink-3)">
        NUDLE BRACKET COUNTER
      </text>

      {/* heading */}
      <text x={20} y={94}
        fontFamily="ui-monospace, monospace" fontSize={18} fontWeight={700}
        fill="var(--nu-accent)">
        counter live
      </text>

      {/* big count value */}
      <rect x={20} y={110} width={130} height={80} rx={6}
        fill="var(--nu-accent-soft)" stroke="var(--nu-accent-line)" strokeWidth={1} />
      <text x={35} y={128} fontFamily="ui-monospace, monospace" fontSize={9}
        letterSpacing="0.24em" fill="var(--nu-accent)">
        COUNT
      </text>
      <text x={85} y={172} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize={38} fontWeight={800}
        fill="var(--nu-accent)">
        42
      </text>

      {/* chart panel */}
      <rect x={170} y={110} width={270} height={80} rx={6}
        fill="var(--nu-code-bg-2)" stroke="var(--nu-rule)" strokeWidth={1} />
      <text x={185} y={128} fontFamily="ui-monospace, monospace" fontSize={9}
        letterSpacing="0.24em" fill="var(--nu-ink-3)">
        HISTORY
      </text>
      <path d={areaD} fill="url(#chartFill)" />
      <path d={pathD} fill="none" stroke="var(--nu-accent)" strokeWidth={1.6} />
      {chartPoints.filter((_, i) => i % 3 === 0).map((p, i) => (
        <circle key={i} cx={p[0]} cy={p[1]} r={1.6} fill="var(--nu-accent)" />
      ))}

      {/* footer strip — subtle rule + tag */}
      <line x1={20} y1={230} x2={440} y2={230} stroke="var(--nu-rule-2)" strokeWidth={1} />
      <text x={20} y={252} fontFamily="ui-monospace, monospace" fontSize={10}
        fill="var(--nu-ink-3)">
        <tspan fill="var(--nu-accent)">●</tspan> live · rocksdb · 1s tick
      </text>
      <text x={440} y={252} textAnchor="end"
        fontFamily="ui-monospace, monospace" fontSize={10}
        letterSpacing="0.24em" fill="var(--nu-ink-4)">
        NUDLE
      </text>
    </svg>
  );
}

type WatchBeat = {
  num: string;
  kind: string;
  lines: string;
  title: string;
  body: React.ReactNode;
  code: string;
};

const WATCH_BEATS: WatchBeat[] = [
  {
    num: '01',
    kind: 'shapes',
    lines: 'L 1 – 15',
    title: 'Declare the world.',
    body: (
      <>
        <b>Counter</b> is one IntRef, headed for RocksDB. <b>Dashboard</b> is a
        Page — heading, count, history — headed for a browser tab.
      </>
    ),
    code: `import nu

class Counter(nu.Shape):
    value: nu.v.IntRef

class Dashboard(nu.nd.Page):
    heading: nu.nd.HeadingRef
    count: nu.nd.TextRef
    history: nu.nd.LineChart

class App(nu.nd.Index):
    title: nu.nd.TitleRef
    nav: nu.nd.NavRef
    pages = nu.nd.Pages({"/": Dashboard})`,
  },
  {
    num: '02',
    kind: 'the loop',
    lines: 'L 17 – 20',
    title: 'A forever bracket.',
    body: (
      <>
        <b>IfDo</b> initializes on cold start. <b>ForeverDo</b> increments the
        counter every second — for as long as the app runs.
      </>
    ),
    code: `counter = (
    nu.IfDo(Counter.value.missing(), Counter.value.store(0))
    >> nu.ForeverDo(Counter.value.inc() >> nu.Delay(1.0))
)`,
  },
  {
    num: '03',
    kind: 'reactivity',
    lines: 'L 22 – 31',
    title: 'A reactive mirror.',
    body: (
      <>
        <b>ReactForever</b> watches <b>Counter.value</b>. Every change stores
        into the dashboard&apos;s count and appends a point to the history
        chart.
      </>
    ),
    code: `ui = (
    App.title.store("nudle bracket counter")
    >> Dashboard.heading.store("counter live")
    >> nu.ReactForever(
        Counter.value.on_change(),
        Dashboard.count.store(Counter.value)
        | Dashboard.history.append(Counter.value, Counter.value),
    )
)`,
  },
  {
    num: '04',
    kind: 'the bind',
    lines: 'L 33 – 40',
    title: 'One bracket. Then run.',
    body: (
      <>
        <b>nu.With</b> pins refs to fabrics: RocksDB for <b>Counter</b>, a
        browser tab for <b>Dashboard</b>. The counter loop runs in the middle.
        Then <b>nu.run</b>.
      </>
    ),
    code: `app = nu.With(
    nu.v.presets.rocksdb_navigator_inmemory(".dbtest"),
    nu.nd.presets.server(ui),
    body=counter,
)

nu.run(nu.v.auto_flow_atomic(app))`,
  },
];

/* ============================================================================
 * Pillars — "and by the way"
 * ==========================================================================*/

const PILLARS: Array<{ name: string; title: string; body: string }> = [
  {
    name: 'acid',
    title: 'ACID by default.',
    body: 'Any subtree can wrap in nv.Transaction. Retries and snapshots come free with the fabric.',
  },
  {
    name: 'distributed',
    title: 'One bracket, many machines.',
    body: 'nu.ray binds Ray. The same program runs across a cluster with the same call.',
  },
  {
    name: 'infinite',
    title: 'Infinite streams, sampled.',
    body: 'kh57 lets you append forever and read a fair sample. Charts stay bounded, data does not.',
  },
  {
    name: 'no limits',
    title: 'No framework. No DSL.',
    body: 'Pure python semantics. Your editor, your types, your debugger. Nothing hidden.',
  },
];

/* ============================================================================
 * Page
 * ==========================================================================*/

export default function HomePage() {
  return (
    <div className={s.root}>
      <div className={s.shell}>

        {/* ---------- hero: centered wordmark on a glow, one CTA ---------- */}
        <header className={s.hero}>
          <div className={s.heroGlow} aria-hidden />
          <div className={s.heroCentered}>
            <div className={s.heroEyebrow}>
              <span className={s.heroEyebrowDot} />
              <span>v0.1.0 · alpha · active · py 3.12+</span>
            </div>
            <h1 className={s.wordmark}>
              <span>N</span>
              <span className={s.wordmarkAccent}>U</span>
            </h1>
            <p className={s.tagline}>
              Compose <span className={s.ledeAccent}>any tool</span> in pure
              python.
            </p>
            <p className={s.subTagline}>
              Nu turns any tool into a program of <b>Refs</b> and{' '}
              <b>Interactions</b> you compose like data. Built on{' '}
              <Link className={s.subTagLink} href="/docs/model">
                the interaction model
              </Link>
              .
            </p>
            <a className={s.heroCta} href="https://github.com/nustackdev/nu">
              <span className={s.heroCtaIcon}><GithubMark size={17} /></span>
              <span className={s.heroCtaLabel}>open on github</span>
              <ArrowRight size={16} className={s.heroCtaArrow} aria-hidden />
            </a>
          </div>
        </header>

        {/* ---------- watch this example — vertical rows, code left / expl right ---------- */}
        <section className={s.section} id="watch">
          <div className={s.sectionLabel}>watch this example</div>
          <h2 className={s.sectionTitle}>Thirty lines. One bracket.</h2>
          <p className={s.sectionIntro}>
            A persistent counter, a live browser dashboard.
            <b> Same Refs, three Fabrics, one bracket.</b>
          </p>
          <div className={s.rowsWrap}>
            {WATCH_BEATS.map((b) => (
              <div key={b.num} className={s.row}>
                <div className={s.rowInner}>
                  <div className={s.rowCode}>
                    <Code src={b.code} />
                  </div>
                  <article className={s.rowExpl}>
                    <span className={s.flatIndex}>[{b.num}]</span>
                    <span className={s.flatKind}>{b.kind}</span>
                    <h3 className={s.flatCellTitle}>{b.title}</h3>
                    <p className={s.flatCellBody}>{b.body}</p>
                  </article>
                </div>
              </div>
            ))}
            <div className={s.row}>
              <div className={`${s.rowInner} ${s.rowInnerSolo}`}>
                <div className={s.rowMock}>
                  <DashboardMock />
                </div>
              </div>
            </div>
            <div className={s.row}>
              <div className={`${s.rowInner} ${s.rowInnerSolo}`}>
                <article className={s.rowExpl}>
                  <span className={s.flatIndex}>[05]</span>
                  <span className={s.flatKind}>the result</span>
                  <h3 className={s.flatCellTitle}>
                    A live browser tab, updating every second.
                  </h3>
                  <p className={s.flatCellBody}>
                    The counter loop ticks in the background. Every mutation
                    lands on the tab as text and as a point on the chart. No
                    framework, no glue, no sockets. It just runs.
                  </p>
                </article>
              </div>
            </div>
          </div>
        </section>

        {/* ---------- the model — single wide viz cell ---------- */}
        <section className={s.section} id="model">
          <div className={s.sectionLabel}>the model</div>
          <h2 className={s.sectionTitle}>Values, and a way to change them.</h2>
          <p className={s.sectionIntro}>
            A field on a browser tab, a value on disk, a number in memory.
            <b> Nu updates all three with one move.</b>
          </p>
          <div className={`${s.flatGrid} ${s.flatGridCols1}`}>
            <div className={`${s.flatCell} ${s.flatCellViz}`}>
              <TransitionViz />
            </div>
          </div>
        </section>

        {/* ---------- and by the way — pillars ---------- */}
        <section className={s.section} id="pillars">
          <div className={s.sectionLabel}>and by the way</div>
          <h2 className={s.sectionTitle}>The same 30-line program is also…</h2>
          <div className={`${s.flatGrid} ${s.flatGridCols4}`}>
            {PILLARS.map((p, i) => (
              <article key={p.name} className={s.flatCell}>
                <span className={s.flatIndex}>[{String(i + 1).padStart(2, '0')}]</span>
                <span className={s.flatKind}>{p.name}</span>
                <h3 className={s.flatCellTitle}>{p.title}</h3>
                <p className={s.flatCellBody}>{p.body}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ---------- three fabrics — 3 rows × (name | code | viz) ---------- */}
        <section className={s.section} id="fabrics">
          <div className={s.sectionLabel}>three fabrics</div>
          <h2 className={s.sectionTitle}>Three fabrics. Same shape.</h2>
          <p className={s.sectionIntro}>
            That move you just saw has a name: it&apos;s an <b>Interaction</b>.
            The addresses it acts on are <b>Refs</b>. The world they resolve
            inside is a <b>Fabric</b>. Same Refs, same Interactions, three
            fabrics — watch the diff.
          </p>
          <div className={`${s.flatGrid} ${s.flatGridFabric}`}>
            {CTX_ROWS.map((r, i) => (
              <React.Fragment key={r.name}>
                <div className={`${s.flatCell} ${s.flatCellName}`}>
                  <span className={s.flatIndex}>
                    fabric {String(i + 1).padStart(2, '0')} / 03
                  </span>
                  <span className={s.flatCellNameLabel}>{r.name}</span>
                  <p className={s.flatCellBody}>{r.hint}</p>
                </div>
                <div className={`${s.flatCell} ${s.flatCellCodeSlot}`}>
                  <Code src={r.code} />
                </div>
                <div className={`${s.flatCell} ${s.flatCellViz}`}>{r.viz}</div>
              </React.Fragment>
            ))}
          </div>
        </section>

        {/* ---------- getting started — vertical rows, code left / twist right ---------- */}
        <section className={s.qsSec} id="start">
          <div className={s.qsHead}>
            <div>
              <div className={s.qsLabel}>getting started</div>
              <h2 className={s.qsTitle}>Six steps. All the way to a shipped app.</h2>
            </div>
            <div className={s.qsMeta}>
              <b>06</b> steps · <b>~5</b> min read
            </div>
          </div>

          <div className={s.rowsWrap}>
            {STEPS.map((st) => (
              <div key={st.n} className={s.row}>
                <div className={s.rowInner}>
                  <div className={s.rowCode}>
                    <GutterCode src={st.code} />
                  </div>
                  <article
                    id={`step-${st.numeral}`}
                    className={s.rowExpl}
                  >
                    <span className={s.flatIndex}>[{st.numeral}]</span>
                    <span className={s.qsKind}>{st.pin}</span>
                    <h3 className={s.qsCellTitle}>{st.title}</h3>
                    <p className={s.qsTwist}>
                      <span className={s.qsTwistLead}>{st.twist}</span>{' '}
                      {st.twistBody}
                    </p>
                  </article>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ---------- batteries ---------- */}
        <section className={s.section} id="batteries">
          <div className={s.sectionLabel}>batteries</div>
          <h2 className={s.sectionTitle}>Contexts and operators you can pick up now.</h2>

          <div className={s.catalogGroup}>
            <p className={s.catalogGroupLabel}>ready contexts</p>
            <p className={s.catalogGroupHint}>
              The Contexts Nu ships with today. Adding one is small: implement
              the address protocol, plug it into a Context.
            </p>
            <div className={s.catalogGrid}>
              <Tile
                index="01"
                name="nu.mem"
                title="In-memory dict."
                body="Dict-backed. Sketches, tests, ephemeral state."
                status="stable"
              />
              <Tile
                index="02"
                name="nu.virtuals"
                title="Persistent, transactional."
                body="RocksDB. Snapshots, transactions, observers, ordered scans."
                status="alpha · active"
              />
              <Tile
                index="03"
                name="nu.nudle"
                title="A browser tab as a Context."
                body="Refs become UI. Mutations land on the tab."
                status="alpha · active"
              />
            </div>
          </div>

          <div className={s.catalogGroup}>
            <p className={s.catalogGroupLabel}>operators &amp; primitives</p>
            <p className={s.catalogGroupHint}>
              Small pieces that come from the model — parallelism, streams,
              transactions, inspection. They fall out, not layered on.
            </p>
            <div className={s.featureGrid}>
              {FEATURES.map((f, i) => (
                <div key={f.name} className={s.feature}>
                  <span className={s.featureIndex}>
                    [{String(i + 1).padStart(2, '0')}]
                  </span>
                  <span className={s.featureName}>{f.name}</span>
                  <h3 className={s.featureTitle}>{f.title}</h3>
                  <p className={s.featureBody}>{f.body}</p>
                  <pre className={s.featureCode}>{f.code}</pre>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ---------- footer ---------- */}
        <footer className={s.footer}>
          <div className={s.footerCell}>
            <span className={s.footerCellHead}>project</span>
            <span className={s.footerBrand}>
              n<em>u</em>
              <span className={s.footerVer}>v0.1.0</span>
            </span>
            <span className={s.footerCellBody}>
              built by <a href="https://github.com/nustackdev">nustackdev</a>
            </span>
          </div>
          <div className={s.footerCell}>
            <span className={s.footerCellHead}>read</span>
            <span className={s.footerCellBody}>
              <Link href="/docs">the docs →</Link>
            </span>
            <span className={s.footerCellBody}>
              <a href="#model">the model</a>
            </span>
            <span className={s.footerCellBody}>
              <a href="#start">getting started</a>
            </span>
          </div>
          <div className={s.footerCell}>
            <span className={s.footerCellHead}>elsewhere</span>
            <span className={s.footerCellBody}>
              <a href="https://github.com/nustackdev">github</a>
            </span>
            <span className={s.footerCellBody}>
              <a href="#batteries">batteries</a>
            </span>
          </div>
        </footer>

      </div>
    </div>
  );
}

/* ============================================================================
 * Tile
 * ==========================================================================*/

function Tile({
  index,
  name,
  title,
  body,
  status,
  wip,
}: {
  index: string;
  name: string;
  title: string;
  body: string;
  status: string;
  wip?: boolean;
}) {
  return (
    <div className={s.tile}>
      <span className={s.tileIndex}>[{index}]</span>
      <div className={s.tileName}>{name}</div>
      <h3 className={s.tileTitle}>{title}</h3>
      <p className={s.tileBody}>{body}</p>
      <div className={`${s.tileStatus} ${wip ? s.tileStatusWip : ''}`}>
        {status}
      </div>
    </div>
  );
}
