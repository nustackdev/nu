import Link from 'next/link';
import s from './page.module.css';

/* ============================================================================
 * Code highlighting — a small local copy (kept independent from the reference)
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
 * WATCH beats — same copy as the reference page
 * ==========================================================================*/

type WatchBeat = {
  num: string;        // 01, 02, ...
  sup: string;        // superscript numeral: ¹ ² ³ ⁴
  roman: string;      // I., II., ...
  kind: string;
  lines: string;
  title: string;
  body: React.ReactNode;
  code: string;
};

const WATCH_BEATS: WatchBeat[] = [
  {
    num: '01',
    sup: '¹',
    roman: 'I.',
    kind: 'shapes',
    lines: 'L 1 - 15',
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
    sup: '²',
    roman: 'II.',
    kind: 'the loop',
    lines: 'L 17 - 20',
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
    sup: '³',
    roman: 'III.',
    kind: 'reactivity',
    lines: 'L 22 - 31',
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
    sup: '⁴',
    roman: 'IV.',
    kind: 'the bind',
    lines: 'L 33 - 40',
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

const PILLARS: Array<{ name: string; title: string; body: string; roman: string; ornament: string }> = [
  {
    roman: 'I.',
    ornament: '§',
    name: 'acid',
    title: 'ACID by default.',
    body: 'Any subtree can wrap in nv.Transaction. Retries and snapshots come free with the fabric.',
  },
  {
    roman: 'II.',
    ornament: '†',
    name: 'distributed',
    title: 'One bracket, many machines.',
    body: 'nu.ray binds Ray. The same program runs across a cluster with the same call.',
  },
  {
    roman: 'III.',
    ornament: '‡',
    name: 'infinite',
    title: 'Infinite streams, sampled.',
    body: 'kh57 lets you append forever and read a fair sample. Charts stay bounded, data does not.',
  },
  {
    roman: 'IV.',
    ornament: '¶',
    name: 'no limits',
    title: 'No framework. No DSL.',
    body: 'Pure python semantics. Your editor, your types, your debugger. Nothing hidden.',
  },
];

/* ============================================================================
 * Dashboard mock — kept restrained, no shadows, thin strokes
 * ==========================================================================*/

function DashboardFigure() {
  const chartPoints: Array<[number, number]> = [
    [182, 178], [200, 176], [218, 172], [236, 168], [254, 162],
    [272, 158], [290, 152], [308, 146], [326, 141], [344, 138],
    [362, 134], [380, 132], [398, 130], [416, 128], [428, 128],
  ];
  const pathD = chartPoints
    .map((p, i) => (i === 0 ? `M ${p[0]} ${p[1]}` : `L ${p[0]} ${p[1]}`))
    .join(' ');
  return (
    <svg viewBox="0 0 460 260" xmlns="http://www.w3.org/2000/svg"
      role="img" aria-label="Live dashboard: counter and history chart"
      style={{ width: '100%', height: 'auto', display: 'block' }}>
      {/* browser chrome */}
      <rect x={0.5} y={0.5} width={459} height={259}
        fill="var(--paper)" stroke="var(--rule)" strokeWidth={1} />
      <line x1={0} y1={36} x2={460} y2={36} stroke="var(--rule)" strokeWidth={1} />
      <circle cx={18} cy={18} r={3.2} fill="var(--ink-4)" />
      <circle cx={30} cy={18} r={3.2} fill="var(--ink-4)" />
      <circle cx={42} cy={18} r={3.2} fill="var(--ink-4)" />
      <text x={70} y={22} fontFamily="Georgia, serif" fontSize={11}
        fontStyle="italic" fill="var(--ink-3)">
        nu://counter
      </text>

      <text x={20} y={62} fontFamily="Georgia, serif" fontSize={11}
        letterSpacing="0.24em" fill="var(--ink-3)">
        NUDLE BRACKET COUNTER
      </text>

      <text x={20} y={92}
        fontFamily="Georgia, serif" fontSize={20} fontStyle="italic"
        fill="var(--accent)">
        counter live
      </text>

      {/* big count value */}
      <rect x={20} y={108} width={130} height={80}
        fill="none" stroke="var(--ink)" strokeWidth={1} />
      <text x={35} y={126} fontFamily="Georgia, serif" fontSize={10}
        letterSpacing="0.24em" fill="var(--ink-3)">
        COUNT
      </text>
      <text x={85} y={172} textAnchor="middle"
        fontFamily="Georgia, serif" fontSize={40} fontWeight={400}
        fill="var(--ink)">
        42
      </text>

      {/* chart panel */}
      <rect x={170} y={108} width={270} height={80}
        fill="none" stroke="var(--rule)" strokeWidth={1} />
      <text x={185} y={126} fontFamily="Georgia, serif" fontSize={10}
        letterSpacing="0.24em" fill="var(--ink-3)">
        HISTORY
      </text>
      <path d={pathD} fill="none" stroke="var(--accent)" strokeWidth={1.4} />
      {chartPoints.filter((_, i) => i % 3 === 0).map((p, i) => (
        <circle key={i} cx={p[0]} cy={p[1]} r={1.6} fill="var(--accent)" />
      ))}

      <line x1={20} y1={218} x2={440} y2={218} stroke="var(--rule-2)" strokeWidth={1} />
      <text x={20} y={240} fontFamily="Georgia, serif" fontSize={11}
        fontStyle="italic" fill="var(--ink-3)">
        live . rocksdb . 1s tick
      </text>
      <text x={440} y={240} textAnchor="end"
        fontFamily="Georgia, serif" fontSize={11}
        letterSpacing="0.24em" fill="var(--ink-4)">
        NUDLE
      </text>
    </svg>
  );
}

/* ============================================================================
 * The model — schematic figure (Fig. 2)
 * ==========================================================================*/

function ModelSchematic() {
  return (
    <svg viewBox="0 0 900 340" xmlns="http://www.w3.org/2000/svg"
      className={s.modelSchematic}
      role="img"
      aria-label="Three fragmented APIs collapse into one nu.run interaction that reaches all substrates.">
      {/* three old APIs (left) */}
      <g fontFamily="Georgia, serif" fontStyle="italic" fontSize={14} fill="var(--ink-3)">
        <text x={20} y={70}>i. input.value = 1</text>
        <line x1={20} y1={64} x2={200} y2={64} stroke="var(--ink-3)" strokeWidth={0.5} opacity={0.6} />
        <text x={20} y={168}>ii. db.put(&quot;count&quot;, 1)</text>
        <line x1={20} y1={162} x2={200} y2={162} stroke="var(--ink-3)" strokeWidth={0.5} opacity={0.6} />
        <text x={20} y={266}>iii. d[&quot;count&quot;] = 1</text>
        <line x1={20} y1={260} x2={200} y2={260} stroke="var(--ink-3)" strokeWidth={0.5} opacity={0.6} />
      </g>

      {/* strike through the three old APIs to signal deprecation */}
      <g stroke="var(--ink-3)" strokeWidth={0.8} opacity={0.85}>
        <line x1={22} y1={66} x2={196} y2={66} />
        <line x1={22} y1={164} x2={196} y2={164} />
        <line x1={22} y1={262} x2={196} y2={262} />
      </g>

      {/* converging lines to central node */}
      <g fill="none" stroke="var(--accent)" strokeWidth={1} opacity={0.55}>
        <path d="M 220 66  C 300 66  340 170 400 170" />
        <path d="M 220 164 L 400 170" />
        <path d="M 220 262 C 300 262 340 170 400 170" />
      </g>

      {/* central node — the interaction, framed as a plate */}
      <g>
        <rect x={400} y={130} width={200} height={80}
          fill="var(--paper)" stroke="var(--ink)" strokeWidth={1} />
        <text x={500} y={122} textAnchor="middle"
          fontFamily="Georgia, serif" fontVariant="small-caps"
          fontSize={11} letterSpacing="0.22em" fill="var(--ink-2)">
          NU.RUN . ONE INTERACTION
        </text>
        <text x={500} y={175} textAnchor="middle"
          fontFamily="ui-monospace, monospace" fontSize={18} fontWeight={700}
          fill="var(--accent)">
          Add(CounterRef, 1)
        </text>
        <line x1={430} y1={190} x2={570} y2={190}
          stroke="var(--accent-line)" strokeWidth={1} />
      </g>

      {/* diverging lines to the three substrates */}
      <g fill="none" stroke="var(--accent)" strokeWidth={1} opacity={0.55}
         strokeDasharray="4 4">
        <path d="M 600 170 C 660 170 660 66 720 66" />
        <path d="M 600 170 L 720 170" />
        <path d="M 600 170 C 660 170 660 262 720 262" />
      </g>
      {/* arrowheads */}
      <g fill="var(--accent)">
        <polygon points="720,62 728,66 720,70" />
        <polygon points="720,166 728,170 720,174" />
        <polygon points="720,258 728,262 720,266" />
      </g>

      {/* three substrates on the right, drawn as thin diagrams */}
      {/* browser tab */}
      <g>
        <rect x={740} y={30} width={140} height={70} fill="none" stroke="var(--ink)" strokeWidth={1} />
        <line x1={740} y1={48} x2={880} y2={48} stroke="var(--rule)" strokeWidth={0.7} />
        <circle cx={750} cy={39} r={2} fill="var(--ink-3)" opacity={0.7} />
        <circle cx={758} cy={39} r={2} fill="var(--ink-3)" opacity={0.7} />
        <circle cx={766} cy={39} r={2} fill="var(--ink-3)" opacity={0.7} />
        <text x={810} y={83} textAnchor="middle" fontFamily="Georgia, serif" fontSize={13}>
          count: <tspan fill="var(--accent)" fontWeight={700}>1</tspan>
        </text>
        <text x={738} y={22} fontFamily="Georgia, serif" fontVariant="small-caps"
          fontSize={10} letterSpacing="0.22em" fill="var(--ink-3)">
          BROWSER TAB
        </text>
      </g>
      {/* on disk */}
      <g>
        <ellipse cx={810} cy={140} rx={70} ry={7} fill="none" stroke="var(--ink)" strokeWidth={1} />
        <line x1={740} y1={140} x2={740} y2={190} stroke="var(--ink)" strokeWidth={1} />
        <line x1={880} y1={140} x2={880} y2={190} stroke="var(--ink)" strokeWidth={1} />
        <path d="M 740 190 A 70 7 0 0 0 880 190" fill="none" stroke="var(--ink)" strokeWidth={1} />
        <circle cx={810} cy={158} r={1.6} fill="var(--ink-3)" />
        <text x={810} y={188} textAnchor="middle" fontFamily="Georgia, serif" fontSize={13}>
          count: <tspan fill="var(--accent)" fontWeight={700}>1</tspan>
        </text>
        <text x={738} y={124} fontFamily="Georgia, serif" fontVariant="small-caps"
          fontSize={10} letterSpacing="0.22em" fill="var(--ink-3)">
          ON DISK
        </text>
      </g>
      {/* in memory */}
      <g>
        <rect x={740} y={228} width={140} height={70} fill="none" stroke="var(--ink)" strokeWidth={1} />
        <text x={750} y={248} fontFamily="ui-monospace, monospace" fontSize={10}
          letterSpacing="0.16em" fill="var(--ink-3)">
          0x00
        </text>
        <text x={810} y={278} textAnchor="middle" fontFamily="ui-monospace, monospace" fontSize={17} fill="var(--ink)">
          {'{ count: '}
          <tspan fill="var(--accent)" fontWeight={700}>1</tspan>
          {' }'}
        </text>
        <text x={738} y={220} fontFamily="Georgia, serif" fontVariant="small-caps"
          fontSize={10} letterSpacing="0.22em" fill="var(--ink-3)">
          IN MEMORY
        </text>
      </g>
    </svg>
  );
}

/* ============================================================================
 * Beat block (renders a single WATCH beat as a footnoted essay unit)
 * ==========================================================================*/

function Beat({ b }: { b: WatchBeat }) {
  return (
    <div className={s.beat}>
      <div className={s.beatHead}>
        <div>
          <span className={s.beatKind}>{b.roman} {b.kind}</span>
        </div>
        <span className={s.beatLines}>{b.lines}</span>
      </div>
      <h3 className={s.beatTitle}>{b.title}</h3>

      <div className={s.beatBody}>
        <div className={s.beatCodeWrap}>
          <div className={s.codeBlock}>
            <div className={s.codeCaption}>
              <span>nudle_rocksdb.py</span>
              <span>
                {b.lines}
                <span className={s.codeCaptionSup}>{b.sup}</span>
              </span>
            </div>
            <Code src={b.code} />
          </div>
        </div>
        <aside className={s.beatMarginNote}>
          <span className={s.beatMarginNoteMark}>Marginalia</span>
          Read the block from top to bottom. The runtime does nothing yet, this
          is a tree, unwound only at nu.run.
        </aside>
      </div>

      <p className={s.footnote}>
        <span className={s.footnoteMark}>{b.sup}</span>
        <span className={s.footnoteTitle}>{b.title}</span>
        {b.body}
      </p>
    </div>
  );
}

/* ============================================================================
 * Page
 * ==========================================================================*/

export default function EditorialLandingPage() {
  return (
    <div className={s.root}>
      <div className={s.page}>

        {/* ================= MASTHEAD ================= */}
        <header className={s.masthead}>
          <div className={s.mastheadDateline}>
            <span>vol. i, no. 1</span>
            <span className={s.mastheadDatelineMid}>the editorial iteration</span>
            <span>v0.1.0, alpha, py 3.12+</span>
          </div>

          <h1 className={s.wordmark}>
            N<em>u</em>
          </h1>

          <p className={s.tagline}>
            Compose <em>any tool</em> in pure python.
          </p>

          <p className={s.subTagline}>
            Nu turns any tool into a program of <b>Refs</b> and{' '}
            <b>Interactions</b> you compose like data. Built on{' '}
            <Link className={s.subTagLink} href="/docs/model">
              the interaction model
            </Link>
            .
          </p>

          <div className={s.byline}>a working essay, by nustackdev</div>

          <a className={s.heroCta} href="https://github.com/nustackdev/nu">
            open on github
          </a>

          <div className={s.mastheadIntro}>
            <p>
              This is a small essay in the shape of a landing page. It sets down
              what Nu is, shows a working program of thirty lines, and closes on
              the four properties that fall out of the model without being asked
              for.
            </p>
            <p>
              Read it top to bottom, the way you would read a piece in print,
              and you will finish with a working mental model of the tree, the
              context, and the run. No prior context is assumed. A python
              editor helps, though it is not required.
            </p>
          </div>
        </header>

        {/* ================= I. WATCH THIS EXAMPLE ================= */}
        <section className={s.section}>
          <div className={s.sectionHead}>
            <span className={s.romanNumeral}>I.</span>
            <span className={s.sectionLabel}>watch this example</span>
          </div>
          <h2 className={s.sectionTitle}>
            Thirty lines. One <em>bracket</em>. Three fabrics at once.
          </h2>

          <p className={s.lede}>
            The program below persists a counter to RocksDB, mirrors it into a
            live browser tab, and appends a point to a chart each second. It is
            not a demo, it is production Nu. Read the four beats in order, then
            look at the figure at the end.
          </p>

          {WATCH_BEATS.map((b) => (
            <Beat key={b.num} b={b} />
          ))}

          <div className={s.rule}>
            <span className={s.ruleMark}>&#8290;&#8290;&#8290;</span>
          </div>

          <div className={s.figure}>
            <div className={s.figureFrame}>
              <DashboardFigure />
            </div>
            <p className={s.figureCaption}>
              <span className={s.figureCaptionNum}>Fig. 1</span>
              A browser tab lit up by the same bracket, counting once a second,
              its history sampled into a bounded line.
            </p>
          </div>

          <p className={s.pullQuote}>
            Same Refs, three Fabrics, one bracket.
          </p>
        </section>

        {/* ================= II. THE MODEL ================= */}
        <section className={s.section}>
          <div className={s.sectionHead}>
            <span className={s.romanNumeral}>II.</span>
            <span className={s.sectionLabel}>the model</span>
          </div>
          <h2 className={s.sectionTitle}>
            Values, and a way to <em>change</em> them.
          </h2>

          <div className={s.modelIntro}>
            <p>
              Look, in the schematic below, at what happens on the left side.
              Three languages, three habits, three fragile APIs. A field on a
              browser tab set with an assignment. A value on disk written with a
              put. A number in memory changed with a subscript.
            </p>
            <p>
              Nu collapses all three into a single move. The addresses are
              Refs. The verb is an Interaction. The world it resolves inside is
              a Fabric. Give <b>nu.run</b> the interaction and it fans the
              change out to every substrate the ref is bound to.
            </p>
          </div>

          <div className={s.figure} style={{ maxWidth: 1000 }}>
            <div className={s.figureFrame}>
              <ModelSchematic />
            </div>
            <p className={s.figureCaption}>
              <span className={s.figureCaptionNum}>Fig. 2</span>
              A field on a browser tab, a value on disk, a number in memory,
              Nu updates all three with one move.
            </p>
          </div>

          <div className={s.rule}>
            <span className={s.ruleMark}>&#8290;&#8290;&#8290;</span>
          </div>

          <p className={s.pullQuote}>
            The tree carries the recipe; the context is the kitchen.
          </p>
        </section>

        {/* ================= III. THE PILLARS ================= */}
        <section className={s.section}>
          <div className={s.sectionHead}>
            <span className={s.romanNumeral}>III.</span>
            <span className={s.sectionLabel}>and by the way</span>
          </div>
          <h2 className={s.sectionTitle}>
            The same thirty-line program is <em>also</em>.
          </h2>

          <p className={s.lede}>
            None of what follows was added to the program. These properties fall
            out of the model itself, of composing brackets over refs, of the
            fabric doing its own work when a run touches it. Four short essays,
            four columns.
          </p>

          <div className={s.pillars}>
            {PILLARS.map((p) => (
              <article key={p.name} className={s.pillar}>
                <span className={s.pillarOrnament}>{p.ornament}</span>
                <div>
                  <span className={s.pillarRoman}>{p.roman}</span>
                  <span className={s.pillarName}>{p.name}</span>
                </div>
                <h3 className={s.pillarTitle}>{p.title}</h3>
                <p className={s.pillarBody}>{p.body}</p>
              </article>
            ))}
          </div>

          <div className={s.rule}>
            <span className={s.ruleMark}>&#8290;&#8290;&#8290;</span>
          </div>
        </section>

        <footer className={s.colophon}>
          <div><b>colophon</b></div>
          Set in Georgia. Composed in python, printed in html. Read the
          documentation at <Link href="/docs">the docs</Link>, or peek at the
          source on <a href="https://github.com/nustackdev/nu">github</a>.
        </footer>

      </div>
    </div>
  );
}
