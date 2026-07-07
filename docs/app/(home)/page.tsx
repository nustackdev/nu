import Link from 'next/link';
import s from './landing.module.css';

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

function OperationLine({ y, code }: { y: number; code: string }) {
  return (
    <g>
      <line
        x1={260} y1={y} x2={370} y2={y}
        stroke="var(--nu-ink-3)" strokeWidth={1}
        strokeDasharray="4 3" opacity={0.55}
      />
      <line
        x1={630} y1={y} x2={740} y2={y}
        stroke="var(--nu-ink-3)" strokeWidth={1}
        strokeDasharray="4 3" opacity={0.55}
      />
      {/* arrow tip pointing at the right substrate */}
      <polygon
        points={`732,${y - 3.5} 740,${y} 732,${y + 3.5}`}
        fill="var(--nu-ink-3)" opacity={0.7}
      />
      <rect
        x={370} y={y - 18} width={260} height={36} rx={4}
        fill="var(--color-fd-background)"
        stroke="var(--nu-rule)" strokeWidth={1}
      />
      <text
        x={500} y={y + 5} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize={14}
        fill="var(--nu-ink-2)"
      >
        {code}
      </text>
    </g>
  );
}

function BeforeViz() {
  return (
    <svg viewBox="0 0 1000 340" xmlns="http://www.w3.org/2000/svg"
      className={s.fanoutSvg} role="img"
      aria-label="Today: each substrate has its own API to update a count.">
      <SubstrateLabel x={20} y={13} text="BROWSER TAB" />
      <SubstrateLabel x={20} y={118} text="ON DISK" />
      <SubstrateLabel x={20} y={223} text="IN MEMORY" />

      {/* row 1: browser */}
      <Substrate kind="browser" x={20} y={20} value="0" />
      <Substrate kind="browser" x={740} y={20} value="1" accent />
      <OperationLine y={60} code={`input.value = 1`} />

      {/* row 2: disk */}
      <Substrate kind="disk" x={20} y={125} value="0" />
      <Substrate kind="disk" x={740} y={125} value="1" accent />
      <OperationLine y={165} code={`db.put("count", 1)`} />

      {/* row 3: memory */}
      <Substrate kind="memory" x={20} y={230} value="0" />
      <Substrate kind="memory" x={740} y={230} value="1" accent />
      <OperationLine y={270} code={`d["count"] = 1`} />
    </svg>
  );
}

function FanoutViz() {
  const rowY = [60, 165, 270];
  const midY = 165;
  const mLeft = 400;
  const mRight = 640;
  const arrowTip = (px: number, py: number, dir: 1 | -1 = 1) => (
    <polygon
      points={`${px - 6 * dir},${py - 4} ${px},${py} ${px - 6 * dir},${py + 4}`}
      fill="var(--nu-accent)" opacity={0.6}
    />
  );
  return (
    <svg viewBox="0 0 1000 340" xmlns="http://www.w3.org/2000/svg"
      className={s.fanoutSvg} role="img"
      aria-label="One interaction applied across three substrates: a browser tab, a value on disk, and a value in memory.">
      <defs>
        <radialGradient id="pillGlow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="var(--nu-accent)" stopOpacity="0.20" />
          <stop offset="100%" stopColor="var(--nu-accent)" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* row labels (left) */}
      <SubstrateLabel x={20} y={13} text="BROWSER TAB" />
      <SubstrateLabel x={20} y={118} text="ON DISK" />
      <SubstrateLabel x={20} y={223} text="IN MEMORY" />

      {/* connectors — inbound (left → middle) solid, outbound (middle → right) dashed */}
      <g fill="none" stroke="var(--nu-accent)" strokeWidth={1.4} opacity={0.55}>
        <path d={`M 260 ${rowY[0]} C 330 ${rowY[0]} 330 ${midY} ${mLeft} ${midY}`} />
        <path d={`M 260 ${rowY[1]} L ${mLeft} ${midY}`} />
        <path d={`M 260 ${rowY[2]} C 330 ${rowY[2]} 330 ${midY} ${mLeft} ${midY}`} />
      </g>
      <g fill="none" stroke="var(--nu-accent)" strokeWidth={1.4} opacity={0.55}
         strokeDasharray="5 4">
        <path d={`M ${mRight} ${midY} C 710 ${midY} 710 ${rowY[0]} 754 ${rowY[0]}`} />
        <path d={`M ${mRight} ${midY} L 754 ${rowY[1]}`} />
        <path d={`M ${mRight} ${midY} C 710 ${midY} 710 ${rowY[2]} 754 ${rowY[2]}`} />
      </g>
      {/* arrow tips landing on the right substrates */}
      {arrowTip(760, rowY[0])}
      {arrowTip(760, rowY[1])}
      {arrowTip(760, rowY[2])}

      {/* left substrates: initial */}
      <Substrate kind="browser" x={20} y={20} value="0" />
      <Substrate kind="disk" x={20} y={125} value="0" />
      <Substrate kind="memory" x={20} y={230} value="0" />

      {/* middle: the interaction — dimensional treatment */}
      <g>
        <ellipse cx={(mLeft + mRight) / 2} cy={midY + 8} rx={140} ry={70}
          fill="url(#pillGlow)" />
        <rect x={mLeft} y={125} width={mRight - mLeft} height={80} rx={6}
          fill="var(--nu-accent-soft)" stroke="var(--nu-accent)" strokeWidth={1.6} />
        <CornerTicks x={mLeft} y={125} w={mRight - mLeft} h={80} size={7} />
        <text x={(mLeft + mRight) / 2} y={112} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={10}
          letterSpacing="0.28em" fill="var(--nu-accent)">
          NU.RUN · ONE INTERACTION
        </text>
        <text x={(mLeft + mRight) / 2} y={172} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={20} fontWeight={700}
          fill="var(--nu-accent)">
          Add(CounterRef, 1)
        </text>
        {/* underline */}
        <line x1={mLeft + 40} y1={188} x2={mRight - 40} y2={188}
          stroke="var(--nu-accent-line)" strokeWidth={1} />
      </g>

      {/* right substrates: updated */}
      <Substrate kind="browser" x={760} y={20} value="1" accent />
      <Substrate kind="disk" x={760} y={125} value="1" accent />
      <Substrate kind="memory" x={760} y={230} value="1" accent />
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
  pin: React.ReactNode;
  title: string;
  code: string;
  twist: React.ReactNode;
  twistBody: React.ReactNode;
}> = [
  {
    n: 'step 01',
    numeral: '01',
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
 * Page
 * ==========================================================================*/

export default function HomePage() {
  return (
    <div className={s.root}>
      <div className={s.shell}>

        {/* ---------- hero ---------- */}
        <header className={s.hero}>
          <div className={s.heroL}>
            <div className={s.heroMeta}>
              <span>nustackdev</span>
              <span className={s.heroMetaSep} />
              <span>v0.1.0</span>
              <span className={s.heroMetaSep} />
              <span className={s.heroMetaDot}>alpha · active</span>
              <span className={s.heroMetaFill} />
              <span>py 3.12+</span>
            </div>

            <div className={s.heroWordmarkWrap}>
              <h1 className={s.wordmark}>
                <span>N</span>
                <span className={s.wordmarkAccent}>U</span>
                <span className={s.wordmarkVer}>0.1.0</span>
              </h1>
            </div>

            <p className={s.lede}>
              <span className={s.ledeAccent}>References</span>, and a way to{' '}
              <span className={s.ledeAccent}>Interact</span> with them.
            </p>
            <p className={s.heroBody}>
              A python library. The model, in pure python — <b>Refs</b>,{' '}
              <b>Interactions</b>, and ready-made <b>Fabrics</b>. Not a
              framework, not a DSL. One import.
            </p>

            <div className={s.heroLCropB} aria-hidden />
          </div>

          <div className={s.heroR}>
            <div className={s.heroRTop}>
              <div className={s.installRow}>
                <span className={s.installPrompt}>$</span>
                <span className={s.installCmd}>pip install nu</span>
                <span className={s.installTag}>latest · 0.1.0</span>
              </div>
              <div className={s.termWrap}>
                <div className={s.termChrome}>
                  <span className={s.termDots}>
                    <i /><i /><i />
                  </span>
                  <span className={s.termFile}>hello.py</span>
                  <span className={s.termLang}>py</span>
                </div>
                <div className={s.helloRow}>
                  <Code src={`import nu\n\nnu.run(nu.print("hello"))`} />
                </div>
              </div>
            </div>
            <div className={s.actions}>
              <a className={s.actionLink} href="#">
                <span className={s.actionKey}>gh</span>
                <span className={s.actionLabel}>open on github</span>
                <span className={s.actionArrow} aria-hidden>→</span>
              </a>
              <Link className={s.actionLink} href="/docs">
                <span className={s.actionKey}>doc</span>
                <span className={s.actionLabel}>read the docs</span>
                <span className={s.actionArrow} aria-hidden>→</span>
              </Link>
              <a className={s.actionLink} href="#">
                <span className={s.actionKey}>hi</span>
                <span className={s.actionLabel}>hello world on github</span>
                <span className={s.actionArrow} aria-hidden>→</span>
              </a>
            </div>
          </div>
        </header>

        {/* ---------- the model ---------- */}
        <section className={s.modelSec} id="model">
          <div className={s.modelHead}>
            <span className={s.modelLabel}>the model</span>
            <h2 className={s.modelThesis}>
              Values, and a way to change them.
            </h2>
          </div>

          {/* today: three different APIs */}
          <div className={s.compareBlock}>
            <div className={s.compareHead}>
              <div className={s.compareIndex}>
                <span className={s.compareNum}>01</span>
                <span className={s.compareTag}>today</span>
              </div>
              <h3 className={s.compareTitle}>Every substrate — its own API.</h3>
            </div>
            <div className={s.fanoutWrap}>
              <BeforeViz />
            </div>
          </div>

          {/* with nu: one interaction */}
          <div className={s.compareBlock}>
            <div className={`${s.compareHead}`}>
              <div className={`${s.compareIndex} ${s.compareIndexAccent}`}>
                <span className={s.compareNum}>02</span>
                <span className={`${s.compareTag} ${s.compareTagAccent}`}>with nu</span>
              </div>
              <h3 className={s.compareTitle}>One interaction — any substrate.</h3>
            </div>
            <div className={s.fanoutWrap}>
              <FanoutViz />
            </div>
          </div>

          <p className={s.modelCaption}>
            A field on a browser tab, a value on disk, a number in memory —
            <b> Nu updates all three with one move.</b>
          </p>
        </section>

        {/* ---------- deep dive: fabrics ---------- */}
        <section className={s.deepSec} id="fabrics">
          <div className={s.deepHead}>
            <span className={s.deepLabel}>the deep dive</span>
            <h2 className={s.deepTitle}>
              Three fabrics. Same shape.
            </h2>
            <p className={s.deepIntro}>
              That move you just saw has a name: it&apos;s an{' '}
              <b>Interaction</b>. The addresses it acts on are <b>Refs</b>. The
              world they resolve inside is a <b>Fabric</b>. Same Refs, same
              Interactions, three fabrics — watch the diff on the right.
            </p>
          </div>
          <div className={s.showcaseRows}>
            {CTX_ROWS.map((r, i) => (
              <article key={r.name} className={s.ctxRow}>
                <div className={s.ctxRowHead}>
                  <span className={s.ctxName}>{r.name}</span>
                  <p className={s.ctxHint}>{r.hint}</p>
                  <span className={s.ctxIndex}>fabric {String(i + 1).padStart(2, '0')} / 03</span>
                </div>
                <div className={s.ctxCode}>
                  <Code src={r.code} />
                </div>
                <div className={s.ctxViz}>{r.viz}</div>
              </article>
            ))}
          </div>
        </section>

        {/* ---------- getting started ---------- */}
        <section className={s.stepsSec} id="start">
          <div className={s.stepsHead}>
            <div>
              <div className={s.stepsLabel}>getting started</div>
              <h2 className={s.stepsTitle}>Six steps. All the way to a shipped app.</h2>
            </div>
            <div className={s.stepsProgress}>
              <b>06</b> steps · <b>~5</b> min read
            </div>
          </div>
          <div className={s.stepsList}>
            {STEPS.map((st) => (
              <article key={st.n} className={s.step}>
                <div className={s.stepHead}>
                  <span className={s.stepNumeral}>{st.numeral}</span>
                  <div className={s.stepMeta}>
                    <span className={s.stepN}>{st.n}</span>
                    <h3 className={s.stepTitle}>{st.title}</h3>
                  </div>
                  <span className={s.stepPin}>{st.pin}</span>
                </div>
                <div className={s.stepBody}>
                  <Code src={st.code} />
                </div>
                <div className={s.stepTwist}>
                  <div className={s.twistLabel}>the twist</div>
                  <p className={s.twistLine}>{st.twist}</p>
                  <p className={s.twistBody}>{st.twistBody}</p>
                </div>
              </article>
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
