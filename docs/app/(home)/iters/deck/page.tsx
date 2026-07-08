'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { ArrowRight, ChevronDown } from 'lucide-react';
import s from './page.module.css';

/* ----------------------------------------------------------------------------
 * GitHub mark
 * -------------------------------------------------------------------------- */
function GithubMark({ size = 18 }: { size?: number }) {
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
  const tokenRe = /(\s+|"[^"]*"|'[^']*'|>>|<<|==|!=|<=|>=|\w+|.)/g;
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
 * Reveal-on-scroll hook
 * ==========================================================================*/
function useReveal<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            setVisible(true);
            observer.disconnect();
            break;
          }
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -8% 0px' },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return { ref, visible };
}

/* ============================================================================
 * Watch beats — copy verbatim from reference
 * ==========================================================================*/
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
        Page, heading, count, history, headed for a browser tab.
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
        counter every second, for as long as the app runs.
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
 * Dashboard mock (the result)
 * ==========================================================================*/
function DashboardMock() {
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
    <svg
      viewBox="0 0 460 300"
      xmlns="http://www.w3.org/2000/svg"
      className={s.dashMock}
      role="img"
      aria-label="Live dashboard mock"
    >
      <defs>
        <linearGradient id="deckChartFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--nu-accent)" stopOpacity="0.28" />
          <stop offset="100%" stopColor="var(--nu-accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={460} height={300} rx={10}
        fill="var(--color-fd-background)" stroke="var(--nu-rule)" strokeWidth={1} />
      <line x1={0} y1={36} x2={460} y2={36} stroke="var(--nu-rule)" strokeWidth={1} />
      <circle cx={18} cy={18} r={3.5} fill="var(--nu-ink-4)" />
      <circle cx={30} cy={18} r={3.5} fill="var(--nu-ink-4)" />
      <circle cx={42} cy={18} r={3.5} fill="var(--nu-ink-4)" />
      <rect x={70} y={9} width={340} height={18} rx={3}
        fill="var(--nu-code-bg-2)" stroke="var(--nu-rule)" strokeWidth={0.5} />
      <text x={80} y={22} fontFamily="ui-monospace, monospace" fontSize={10}
        fill="var(--nu-ink-3)">nu://counter</text>

      <text x={20} y={60} fontFamily="ui-monospace, monospace" fontSize={10}
        letterSpacing="0.24em" fill="var(--nu-ink-3)">NUDLE BRACKET COUNTER</text>

      <text x={20} y={94}
        fontFamily="ui-monospace, monospace" fontSize={18} fontWeight={700}
        fill="var(--nu-accent)">counter live</text>

      <rect x={20} y={110} width={130} height={80} rx={6}
        fill="var(--nu-accent-soft)" stroke="var(--nu-accent-line)" strokeWidth={1} />
      <text x={35} y={128} fontFamily="ui-monospace, monospace" fontSize={9}
        letterSpacing="0.24em" fill="var(--nu-accent)">COUNT</text>
      <text x={85} y={172} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize={38} fontWeight={800}
        fill="var(--nu-accent)">42</text>

      <rect x={170} y={110} width={270} height={80} rx={6}
        fill="var(--nu-code-bg-2)" stroke="var(--nu-rule)" strokeWidth={1} />
      <text x={185} y={128} fontFamily="ui-monospace, monospace" fontSize={9}
        letterSpacing="0.24em" fill="var(--nu-ink-3)">HISTORY</text>
      <path d={areaD} fill="url(#deckChartFill)" />
      <path d={pathD} fill="none" stroke="var(--nu-accent)" strokeWidth={1.6} />
      {chartPoints.filter((_, i) => i % 3 === 0).map((p, i) => (
        <circle key={i} cx={p[0]} cy={p[1]} r={1.6} fill="var(--nu-accent)" />
      ))}

      <line x1={20} y1={230} x2={440} y2={230} stroke="var(--nu-rule-2)" strokeWidth={1} />
      <text x={20} y={252} fontFamily="ui-monospace, monospace" fontSize={10}
        fill="var(--nu-ink-3)">
        <tspan fill="var(--nu-accent)">●</tspan> live · rocksdb · 1s tick
      </text>
      <text x={440} y={252} textAnchor="end"
        fontFamily="ui-monospace, monospace" fontSize={10}
        letterSpacing="0.24em" fill="var(--nu-ink-4)">NUDLE</text>
    </svg>
  );
}

/* ============================================================================
 * Model schematic — hero-scale fan-out
 * ==========================================================================*/
function ModelSchematic() {
  const rowY = [110, 300, 490];
  const midY = 300;
  const mLeft = 500;
  const mRight = 780;
  const rightNodeX = 900;

  const oldApis = [
    'input.value = 1',
    'db.put("count", 1)',
    'd["count"] = 1',
  ];
  const subLabels = ['BROWSER TAB', 'ON DISK', 'IN MEMORY'];
  const arrowTip = (px: number, py: number) => (
    <polygon
      points={`${px - 10},${py - 7} ${px},${py} ${px - 10},${py + 7}`}
      fill="var(--nu-accent)"
    />
  );

  return (
    <svg
      viewBox="0 0 1280 620"
      xmlns="http://www.w3.org/2000/svg"
      className={s.modelSchematic}
      role="img"
      aria-label="Three old APIs collapse into one Nu interaction that fans out to browser, disk, and memory."
    >
      <defs>
        <radialGradient id="deckPillGlow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="var(--nu-accent)" stopOpacity="0.35" />
          <stop offset="100%" stopColor="var(--nu-accent)" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* left column: old API calls */}
      {oldApis.map((api, i) => (
        <g key={i}>
          <text
            x={40}
            y={rowY[i] - 34}
            fontFamily="ui-monospace, monospace"
            fontSize={13}
            letterSpacing="0.28em"
            fill="var(--nu-ink-3)"
          >
            {subLabels[i]}
          </text>
          <rect
            x={40}
            y={rowY[i] - 22}
            width={340}
            height={54}
            rx={8}
            fill="var(--color-fd-background)"
            stroke="var(--nu-rule)"
            strokeWidth={1}
          />
          <text
            x={60}
            y={rowY[i] + 12}
            fontFamily="ui-monospace, monospace"
            fontSize={17}
            fill="var(--nu-ink-2)"
            style={{ textDecoration: 'line-through' }}
          >
            {api}
          </text>
        </g>
      ))}

      {/* converging paths to the central node */}
      <g fill="none" stroke="var(--nu-accent)" strokeWidth={1.8} opacity={0.6}>
        <path d={`M 380 ${rowY[0]} C 440 ${rowY[0]} 460 ${midY} ${mLeft} ${midY}`} />
        <path d={`M 380 ${rowY[1]} L ${mLeft} ${midY}`} />
        <path d={`M 380 ${rowY[2]} C 440 ${rowY[2]} 460 ${midY} ${mLeft} ${midY}`} />
      </g>

      {/* central node */}
      <g>
        <ellipse cx={(mLeft + mRight) / 2} cy={midY + 8} rx={220} ry={110}
          fill="url(#deckPillGlow)" />
        <rect x={mLeft} y={midY - 55} width={mRight - mLeft} height={110} rx={12}
          fill="var(--nu-accent-soft)" stroke="var(--nu-accent)" strokeWidth={2} />
        <text x={(mLeft + mRight) / 2} y={midY - 68} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={13}
          letterSpacing="0.32em" fill="var(--nu-accent)">
          NU.RUN · ONE INTERACTION
        </text>
        <text x={(mLeft + mRight) / 2} y={midY + 8} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={28} fontWeight={800}
          fill="var(--nu-accent)">
          Add(CounterRef, 1)
        </text>
        <line x1={mLeft + 60} y1={midY + 30} x2={mRight - 60} y2={midY + 30}
          stroke="var(--nu-accent-line)" strokeWidth={1.5} />
      </g>

      {/* fan-out paths */}
      <g fill="none" stroke="var(--nu-accent)" strokeWidth={1.8} opacity={0.6}
         strokeDasharray="8 6">
        <path d={`M ${mRight} ${midY} C 840 ${midY} 850 ${rowY[0]} ${rightNodeX - 10} ${rowY[0]}`} />
        <path d={`M ${mRight} ${midY} L ${rightNodeX - 10} ${rowY[1]}`} />
        <path d={`M ${mRight} ${midY} C 840 ${midY} 850 ${rowY[2]} ${rightNodeX - 10} ${rowY[2]}`} />
      </g>
      {arrowTip(rightNodeX - 5, rowY[0])}
      {arrowTip(rightNodeX - 5, rowY[1])}
      {arrowTip(rightNodeX - 5, rowY[2])}

      {/* right column: substrate outcomes */}
      {['count: 1', 'count: 1', '{ count: 1 }'].map((val, i) => (
        <g key={i}>
          <text
            x={rightNodeX + 10}
            y={rowY[i] - 34}
            fontFamily="ui-monospace, monospace"
            fontSize={13}
            letterSpacing="0.28em"
            fill="var(--nu-accent)"
          >
            {subLabels[i]}
          </text>
          <rect
            x={rightNodeX + 10}
            y={rowY[i] - 22}
            width={330}
            height={54}
            rx={8}
            fill="var(--nu-accent-soft)"
            stroke="var(--nu-accent)"
            strokeWidth={1.6}
          />
          <text
            x={rightNodeX + 30}
            y={rowY[i] + 12}
            fontFamily="ui-monospace, monospace"
            fontSize={17}
            fontWeight={700}
            fill="var(--nu-accent)"
          >
            {val}
          </text>
        </g>
      ))}
    </svg>
  );
}

/* ============================================================================
 * Slides
 * ==========================================================================*/
function HeroSlide() {
  return (
    <section className={`${s.slide} ${s.heroSlide}`}>
      <div className={s.heroGlow} aria-hidden />
      <div className={s.heroInner}>
        <p className={s.heroMeta}>v0.1.0 · alpha · py 3.12+</p>
        <h1 className={s.wordmark}>
          <span className={s.wordmarkN}>N</span>
          <span className={s.wordmarkU}>U</span>
        </h1>
        <p className={s.heroTagline}>
          Compose any tool in pure python.
        </p>
        <p className={s.heroSub}>
          Nu turns any tool into a program of <b>Refs</b> and{' '}
          <b>Interactions</b> you compose like data. Built on{' '}
          <Link className={s.heroSubLink} href="/docs/model">
            the interaction model
          </Link>
          .
        </p>
        <a className={s.heroCta} href="https://github.com/nustackdev/nu">
          <GithubMark size={20} />
          <span>open on github</span>
          <ArrowRight size={18} className={s.heroCtaArrow} aria-hidden />
        </a>
      </div>
      <ChevronDown className={s.chevronDown} size={44} aria-hidden />
    </section>
  );
}

function WatchIntroSlide() {
  const { ref, visible } = useReveal<HTMLDivElement>();
  return (
    <section className={`${s.slide} ${s.introSlide}`}>
      <div
        ref={ref}
        className={`${s.introInner} ${visible ? s.reveal : ''}`}
      >
        <p className={s.introEyebrow}>watch this example</p>
        <h2 className={s.introTitle}>
          Thirty lines.
          <br />
          <span className={s.accentText}>One bracket.</span>
        </h2>
        <p className={s.introBody}>
          A persistent counter and a live browser dashboard.
          <br />
          Same Refs, three Fabrics, one bracket.
        </p>
      </div>
      <ChevronDown className={s.chevronDown} size={40} aria-hidden />
    </section>
  );
}

function BeatSlide({ beat }: { beat: WatchBeat }) {
  const { ref, visible } = useReveal<HTMLDivElement>();
  return (
    <section className={`${s.slide} ${s.beatSlide}`}>
      <span className={s.beatBigNum} aria-hidden>{beat.num}</span>
      <div
        ref={ref}
        className={`${s.beatInner} ${visible ? s.reveal : ''}`}
      >
        <p className={s.beatKind}>{beat.kind}</p>
        <h2 className={s.beatTitle}>{beat.title}</h2>
        <div className={s.codeCard}>
          <div className={s.codeChrome}>
            <span className={s.codeDots}><i /><i /><i /></span>
            <span className={s.codeFile}>nudle_rocksdb.py</span>
            <span className={s.codeRange}>{beat.lines}</span>
          </div>
          <div className={s.codeBody}>
            <Code src={beat.code} />
          </div>
        </div>
        <p className={s.beatBody}>{beat.body}</p>
      </div>
      <ChevronDown className={s.chevronDown} size={36} aria-hidden />
    </section>
  );
}

function ResultSlide() {
  const { ref, visible } = useReveal<HTMLDivElement>();
  return (
    <section className={`${s.slide} ${s.resultSlide}`}>
      <span className={s.beatBigNum} aria-hidden>05</span>
      <div
        ref={ref}
        className={`${s.resultInner} ${visible ? s.reveal : ''}`}
      >
        <p className={s.beatKind}>the result</p>
        <h2 className={s.beatTitle}>A live browser tab, updating every second.</h2>
        <div className={s.mockCard}>
          <DashboardMock />
        </div>
      </div>
      <ChevronDown className={s.chevronDown} size={36} aria-hidden />
    </section>
  );
}

function ModelSlide() {
  const { ref, visible } = useReveal<HTMLDivElement>();
  return (
    <section className={`${s.slide} ${s.modelSlide}`}>
      <div
        ref={ref}
        className={`${s.modelInner} ${visible ? s.reveal : ''}`}
      >
        <p className={s.introEyebrow}>the model</p>
        <h2 className={s.modelTitle}>
          Values, and a way to
          <br />
          <span className={s.accentText}>change them.</span>
        </h2>
        <div className={s.schematicWrap}>
          <ModelSchematic />
        </div>
        <p className={s.modelCaption}>
          A field on a browser tab, a value on disk, a number in memory.
          <br />
          <b>Nu updates all three with one move.</b>
        </p>
      </div>
      <ChevronDown className={s.chevronDown} size={36} aria-hidden />
    </section>
  );
}

/* ============================================================================
 * Pillars — horizontal snap scroll
 * ==========================================================================*/
const PILLARS: Array<{ num: string; name: string; title: string; body: string }> = [
  {
    num: '01',
    name: 'acid',
    title: 'ACID by default.',
    body: 'Any subtree can wrap in nv.Transaction. Retries and snapshots come free with the fabric.',
  },
  {
    num: '02',
    name: 'distributed',
    title: 'One bracket, many machines.',
    body: 'nu.ray binds Ray. The same program runs across a cluster with the same call.',
  },
  {
    num: '03',
    name: 'infinite',
    title: 'Infinite streams, sampled.',
    body: 'kh57 lets you append forever and read a fair sample. Charts stay bounded, data does not.',
  },
  {
    num: '04',
    name: 'no limits',
    title: 'No framework. No DSL.',
    body: 'Pure python semantics. Your editor, your types, your debugger. Nothing hidden.',
  },
];

function PillarsBand() {
  const { ref, visible } = useReveal<HTMLDivElement>();
  return (
    <section className={`${s.slide} ${s.pillarsSlide}`}>
      <div
        ref={ref}
        className={`${s.pillarsHead} ${visible ? s.reveal : ''}`}
      >
        <p className={s.introEyebrow}>and by the way</p>
        <h2 className={s.pillarsHeadTitle}>
          The same thirty-line program is also,
        </h2>
      </div>
      <div className={s.pillarsRail}>
        {PILLARS.map((p) => (
          <article key={p.name} className={s.pillarCard}>
            <span className={s.pillarNum} aria-hidden>{p.num}</span>
            <div className={s.pillarInner}>
              <span className={s.pillarName}>{p.name}</span>
              <h3 className={s.pillarTitle}>{p.title}</h3>
              <p className={s.pillarBody}>{p.body}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

/* ============================================================================
 * Page
 * ==========================================================================*/
export default function DeckPage() {
  return (
    <div className={s.root}>
      <HeroSlide />
      <WatchIntroSlide />
      {WATCH_BEATS.map((b) => (
        <BeatSlide key={b.num} beat={b} />
      ))}
      <ResultSlide />
      <ModelSlide />
      <PillarsBand />
    </div>
  );
}
