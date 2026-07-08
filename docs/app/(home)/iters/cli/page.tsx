import Link from 'next/link';
import s from './page.module.css';

/* ----------------------------------------------------------------------------
 * Inline GitHub mark
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
 * Code highlighting (borrowed helper, same tokens)
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
  return (
    <pre className={s.code}>
      {lines.map((l, i) => (
        <span key={i} className={s.codeLine}>
          <span className={s.codeGutter}>{String(i + 1).padStart(2, ' ')}</span>
          <span className={s.codeSep}>{'│'}</span>
          <span className={s.codeText}>{renderLine(l, i)}</span>
        </span>
      ))}
    </pre>
  );
}

/* ============================================================================
 * TermPane — a terminal window with tmux-style status bar
 * ==========================================================================*/

function TermPane({
  file,
  range,
  children,
  path = '~/nustackdev/nu',
}: {
  file: string;
  range?: string;
  children: React.ReactNode;
  path?: string;
}) {
  return (
    <div className={s.term}>
      <div className={s.termHead}>
        <span className={s.termHeadPath}>{path}</span>
        <span className={s.termHeadSpacer} />
        <span className={s.termHeadTab}>{file}</span>
        {range ? <span className={s.termHeadRange}>{range}</span> : null}
      </div>
      <div className={s.termBody}>{children}</div>
      <div className={s.termFoot}>
        <span className={s.termFootSection}>[nu]</span>
        <span className={s.termFootSection}>0:vim*</span>
        <span className={s.termFootSection}>1:py</span>
        <span className={s.termFootSection}>2:nudle</span>
        <span className={s.termFootSpacer} />
        <span className={s.termFootSection}>py 3.12</span>
        <span className={s.termFootSection}>utf-8</span>
        <span className={s.termFootSection}>{file}</span>
      </div>
    </div>
  );
}

/* ============================================================================
 * Watch this example — 4 beats + result
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
    lines: 'L 1 - 15',
    title: 'Declare the world.',
    body: (
      <>
        <b>Counter</b> is one IntRef, headed for RocksDB. <b>Dashboard</b> is a
        Page. heading, count, history. headed for a browser tab.
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
    kind: 'the bind',
    lines: 'L 33 - 40',
    title: 'One bracket. Then run.',
    body: (
      <>
        <b>nu.With</b> pins refs to fabrics. RocksDB for <b>Counter</b>, a
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

function ManPageBlock({
  num,
  kind,
  title,
  body,
}: {
  num: string;
  kind: string;
  title: string;
  body: React.ReactNode;
}) {
  return (
    <article className={s.manpage}>
      <div className={s.manpageHead}>
        <span className={s.manpageBeat}>BEAT {num}</span>
        <span className={s.manpageSep}>{'──'}</span>
        <span className={s.manpageKind}>{kind.toUpperCase()}</span>
      </div>
      <div className={s.manpageEntry}>
        <div className={s.manpageLabel}>NAME</div>
        <div className={s.manpageValue}>
          <b>{kind}</b> - {title.toLowerCase()}
        </div>
      </div>
      <div className={s.manpageEntry}>
        <div className={s.manpageLabel}>DESCRIPTION</div>
        <div className={s.manpageValue}>{body}</div>
      </div>
    </article>
  );
}

/* ============================================================================
 * Dashboard mock rendered in ASCII/box-drawing chars
 * ==========================================================================*/

function DashboardAscii() {
  // Fixed width, programmatic. Every rendered line is exactly WIDTH chars.
  // Accent spans wrap character sequences, so column alignment is preserved.
  const WIDTH = 60;
  const inner = WIDTH - 2; // content between the outer │ chars

  const dash = (n: number) => '─'.repeat(n);
  const sp = (n: number) => ' '.repeat(n);
  const row = (children: React.ReactNode) => (
    <>
      {'│'}
      {children}
      {'│'}
      {'\n'}
    </>
  );
  // Fill row: pad plain text out to `inner` chars.
  const fill = (text: string) => text + sp(inner - text.length);

  const topLabel = ' nu://counter ';
  const top = '┌─' + topLabel + dash(inner - 2 - topLabel.length) + '┐';
  const bot = '└' + dash(inner) + '┘';

  // Inner columns for the boxes row.
  // Layout inside a row:  "  " + LEFT + "  " + RIGHT + "  "
  const leftW = 15;   // ┌─ COUNT ─────┐   = 15
  const rightW = 37;  // ┌─ HISTORY ─────────────────────────┐ = 37
  // 2 + 15 + 2 + 37 + 2 = 58 = inner
  const leftHeader = '┌─ COUNT ' + dash(leftW - 10) + '┐';   // 1 + 8 + (leftW-10) + 1 = leftW
  const leftInside = '│' + sp(leftW - 2) + '│';
  const leftBot = '└' + dash(leftW - 2) + '┘';
  const rightHeader = '┌─ HISTORY ' + dash(rightW - 12) + '┐'; // 1 + 10 + (rightW-12) + 1 = rightW
  const rightInside = '│' + sp(rightW - 2) + '│';
  const rightBot = '└' + dash(rightW - 2) + '┘';

  // For the value row we place "42" centered in left, sparkline in right.
  const spark = '▂▂▃▃▄▄▅▅▆▆▇▇▇██'; // 15 wide
  // Left value row inside: "│" + centered "42" in (leftW - 2) + "│"
  // leftW - 2 = 13, "42" is 2, pad each side ~5/6.
  const leftValInsideL = 6, leftValInsideR = 13 - 2 - 6;
  // Right value row inside: "│" + "  " + spark + pad + "│"
  const rightPad = rightW - 2 - 2 - spark.length;

  return (
    <pre className={s.asciiDashboard} aria-label="Live dashboard: counter and history chart">
      {top}
      {'\n'}
      {row(fill(''))}
      {row(<>{'  '}<span className={s.asciiAccent}>counter live</span>{sp(inner - 2 - 'counter live'.length)}</>)}
      {row(fill('  ────────────'))}
      {row(fill(''))}
      {row(fill('  ' + leftHeader + '  ' + rightHeader + '  '))}
      {row(fill('  ' + leftInside + '  ' + rightInside + '  '))}
      {row(<>
        {'  '}
        {'│'}{sp(leftValInsideL)}<span className={s.asciiAccentBold}>42</span>{sp(leftValInsideR)}{'│'}
        {'  '}
        {'│'}{'  '}<span className={s.asciiAccent}>{spark}</span>{sp(rightPad)}{'│'}
        {'  '}
      </>)}
      {row(fill('  ' + leftInside + '  ' + rightInside + '  '))}
      {row(fill('  ' + leftBot + '  ' + rightBot + '  '))}
      {row(fill(''))}
      {(() => {
        const lead = '  ';
        const dot = '●';
        const mid = ' live · rocksdb · 1s tick';
        const tail = 'NUDLE';
        const rightPad2 = 2;
        const midPad = inner - lead.length - dot.length - mid.length - tail.length - rightPad2;
        return row(<>
          {lead}
          <span className={s.asciiAccent}>{dot}</span>
          {mid}
          {sp(midPad)}
          <span className={s.asciiDim}>{tail}</span>
          {sp(rightPad2)}
        </>);
      })()}
      {bot}
    </pre>
  );
}

/* ============================================================================
 * Model viz — SVG with hard corners, straight lines
 * ==========================================================================*/

function ModelViz() {
  // Three rows of substrates on the left, one central node, three on the right.
  const oldApis = [
    { y: 90, label: 'BROWSER TAB', code: 'input.value = 1', boxKind: 'browser' as const },
    { y: 240, label: 'ON DISK', code: 'db.put("count", 1)', boxKind: 'disk' as const },
    { y: 390, label: 'IN MEMORY', code: 'd["count"] = 1', boxKind: 'memory' as const },
  ];
  const midY = 240;
  const nodeX = 460;
  const nodeW = 200;
  const leftX = 40;
  const leftW = 220;
  const rightX = 760;
  const rightW = 220;

  return (
    <svg
      viewBox="0 0 1000 500"
      xmlns="http://www.w3.org/2000/svg"
      className={s.modelSvg}
      role="img"
      aria-label="Three fragmented APIs collapse into one Nu interaction."
    >
      {/* row labels */}
      {oldApis.map((r) => (
        <text
          key={r.label}
          x={leftX}
          y={r.y - 34}
          fontFamily="var(--font-mono)"
          fontSize={11}
          letterSpacing="0.28em"
          fill="var(--nu-ink-3)"
        >
          [{r.label}]
        </text>
      ))}

      {/* left substrates - hard-cornered rectangles */}
      {oldApis.map((r) => (
        <g key={`L-${r.label}`}>
          <rect
            x={leftX}
            y={r.y - 24}
            width={leftW}
            height={54}
            fill="var(--nu-code-bg-2)"
            stroke="var(--nu-rule)"
            strokeWidth={1}
          />
          <text
            x={leftX + 10}
            y={r.y - 8}
            fontFamily="var(--font-mono)"
            fontSize={10}
            fill="var(--nu-ink-3)"
          >
            $
          </text>
          <text
            x={leftX + 22}
            y={r.y - 8}
            fontFamily="var(--font-mono)"
            fontSize={11}
            fill="var(--nu-ink-2)"
          >
            {r.boxKind}
          </text>
          <text
            x={leftX + 10}
            y={r.y + 16}
            fontFamily="var(--font-mono)"
            fontSize={13}
            fill="var(--nu-ink-2)"
            style={{ textDecoration: 'line-through' }}
          >
            {r.code}
          </text>
        </g>
      ))}

      {/* collapse lines: three left boxes into central node - straight lines only */}
      {oldApis.map((r) => (
        <g key={`c-${r.label}`} stroke="var(--nu-accent)" strokeWidth={1.2} fill="none" opacity={0.55}>
          <line x1={leftX + leftW} y1={r.y} x2={leftX + leftW + 40} y2={r.y} />
          <line x1={leftX + leftW + 40} y1={r.y} x2={leftX + leftW + 40} y2={midY} />
          <line x1={leftX + leftW + 40} y1={midY} x2={nodeX} y2={midY} />
        </g>
      ))}

      {/* central node - hard corners */}
      <g>
        <rect
          x={nodeX}
          y={midY - 40}
          width={nodeW}
          height={80}
          fill="var(--nu-accent-soft)"
          stroke="var(--nu-accent)"
          strokeWidth={1.8}
        />
        {/* corner ticks */}
        <g stroke="var(--nu-accent)" strokeWidth={1.4} fill="none">
          <path d={`M ${nodeX - 6} ${midY - 40} L ${nodeX} ${midY - 40} L ${nodeX} ${midY - 34}`} />
          <path d={`M ${nodeX + nodeW} ${midY - 34} L ${nodeX + nodeW} ${midY - 40} L ${nodeX + nodeW + 6} ${midY - 40}`} />
          <path d={`M ${nodeX - 6} ${midY + 40} L ${nodeX} ${midY + 40} L ${nodeX} ${midY + 34}`} />
          <path d={`M ${nodeX + nodeW} ${midY + 34} L ${nodeX + nodeW} ${midY + 40} L ${nodeX + nodeW + 6} ${midY + 40}`} />
        </g>
        <text
          x={nodeX + nodeW / 2}
          y={midY - 20}
          textAnchor="middle"
          fontFamily="var(--font-mono)"
          fontSize={10}
          letterSpacing="0.28em"
          fill="var(--nu-accent)"
        >
          NU.RUN
        </text>
        <text
          x={nodeX + nodeW / 2}
          y={midY + 8}
          textAnchor="middle"
          fontFamily="var(--font-mono)"
          fontSize={17}
          fontWeight={800}
          fill="var(--nu-accent)"
        >
          Add(CounterRef, 1)
        </text>
        <text
          x={nodeX + nodeW / 2}
          y={midY + 28}
          textAnchor="middle"
          fontFamily="var(--font-mono)"
          fontSize={9}
          letterSpacing="0.28em"
          fill="var(--nu-accent)"
        >
          ONE INTERACTION
        </text>
      </g>

      {/* fan-out lines: central node to three right substrates */}
      {oldApis.map((r) => (
        <g key={`f-${r.label}`} stroke="var(--nu-accent)" strokeWidth={1.2} fill="none" opacity={0.65} strokeDasharray="4 4">
          <line x1={nodeX + nodeW} y1={midY} x2={nodeX + nodeW + 40} y2={midY} />
          <line x1={nodeX + nodeW + 40} y1={midY} x2={nodeX + nodeW + 40} y2={r.y} />
          <line x1={nodeX + nodeW + 40} y1={r.y} x2={rightX - 6} y2={r.y} />
          {/* arrow tip */}
          <polygon
            points={`${rightX - 6},${r.y - 4} ${rightX},${r.y} ${rightX - 6},${r.y + 4}`}
            fill="var(--nu-accent)"
            opacity={1}
            stroke="none"
          />
        </g>
      ))}

      {/* right substrates - accent, with value 1 */}
      {oldApis.map((r) => (
        <g key={`R-${r.label}`}>
          <rect
            x={rightX}
            y={r.y - 24}
            width={rightW}
            height={54}
            fill="var(--nu-accent-soft)"
            stroke="var(--nu-accent)"
            strokeWidth={1.6}
          />
          <text
            x={rightX + 10}
            y={r.y - 8}
            fontFamily="var(--font-mono)"
            fontSize={10}
            fill="var(--nu-accent)"
          >
            $
          </text>
          <text
            x={rightX + 22}
            y={r.y - 8}
            fontFamily="var(--font-mono)"
            fontSize={11}
            fill="var(--nu-accent)"
          >
            {r.boxKind}
          </text>
          <text
            x={rightX + 10}
            y={r.y + 16}
            fontFamily="var(--font-mono)"
            fontSize={13}
            fill="var(--nu-ink)"
          >
            count: <tspan fill="var(--nu-accent)" fontWeight={800}>1</tspan>
          </text>
        </g>
      ))}
    </svg>
  );
}

/* ============================================================================
 * Pillars
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

// ASCII wordmark
const NU_ASCII = String.raw` ███╗   ██╗██╗   ██╗
 ████╗  ██║██║   ██║
 ██╔██╗ ██║██║   ██║
 ██║╚██╗██║██║   ██║
 ██║ ╚████║╚██████╔╝
 ╚═╝  ╚═══╝ ╚═════╝ `;

export default function IterCliPage() {
  return (
    <div className={s.root}>
      <div className={s.shell}>

        {/* ---------- HERO — man-page style ---------- */}
        <header className={s.hero}>
          {/* status strip at very top */}
          <div className={s.topBar}>
            <span className={s.topBarCell}>[nu-manual]</span>
            <span className={s.topBarCell}>page: 1 of 1</span>
            <span className={s.topBarSpacer} />
            <span className={s.topBarCell}>v0.1.0-alpha</span>
            <span className={s.topBarCell}>py 3.12+</span>
            <span className={`${s.topBarCell} ${s.topBarBlink}`}>REC</span>
          </div>

          {/* man page header line */}
          <div className={s.manHeader}>
            <span>NU(1)</span>
            <span>Nu Manual</span>
            <span>NU(1)</span>
          </div>

          {/* wordmark */}
          <pre className={s.wordmark} aria-label="NU">{NU_ASCII}</pre>

          {/* tagline as NAME field */}
          <div className={s.heroManBlock}>
            <div className={s.heroManLabel}>NAME</div>
            <div className={s.heroManValue}>
              <span className={s.heroTagline}>
                <span className={s.heroPrompt}>&gt; </span>
                Compose <span className={s.accent}>any tool</span> in pure python.
                <span className={s.caret} aria-hidden />
              </span>
            </div>
          </div>

          <div className={s.heroManBlock}>
            <div className={s.heroManLabel}>DESCRIPTION</div>
            <div className={s.heroManValue}>
              Nu turns any tool into a program of <b>Refs</b> and{' '}
              <b>Interactions</b> you compose like data. Built on{' '}
              <Link className={s.heroManLink} href="/docs/model">
                the interaction model
              </Link>
              .
            </div>
          </div>

          <div className={s.heroManBlock}>
            <div className={s.heroManLabel}>SYNOPSIS</div>
            <div className={s.heroManValue}>
              <a className={s.heroCta} href="https://github.com/nustackdev/nu">
                <span className={s.heroCtaBracket}>[</span>
                <GithubMark size={14} />
                <span> open on github </span>
                <span className={s.heroCtaArrow}>{'→'}</span>
                <span className={s.heroCtaBracket}>]</span>
              </a>
            </div>
          </div>

          <pre className={s.divider} aria-hidden>
            {'═'.repeat(120)}
          </pre>
        </header>

        {/* ---------- WATCH THIS EXAMPLE ---------- */}
        <section className={s.section} id="watch">
          <div className={s.sectionHead}>
            <div className={s.sectionEyebrow}>
              <span>{'§'} section 01</span>
              <span className={s.sectionEyebrowDot}>{'·'}</span>
              <span>watch</span>
            </div>
            <h2 className={s.sectionTitle}>
              <span className={s.sectionHash}>#</span> Watch this example.
            </h2>
            <p className={s.sectionIntro}>
              30 lines. Persistent counter, live browser dashboard.
              <b> same Refs, three Fabrics, one bracket.</b>
            </p>
          </div>

          <div className={s.beats}>
            {WATCH_BEATS.map((b) => (
              <div key={b.num} className={s.beat}>
                <TermPane file="nudle_rocksdb.py" range={b.lines}>
                  <Code src={b.code} />
                </TermPane>
                <ManPageBlock num={b.num} kind={b.kind} title={b.title} body={b.body} />
              </div>
            ))}
          </div>

          <div className={s.result}>
            <div className={s.resultLead}>
              <pre className={s.dividerSm} aria-hidden>{'─'.repeat(60)}</pre>
              <div className={s.resultHead}>
                <span className={s.resultTag}>[RESULT 05]</span>
                <span className={s.resultKind}>the payoff</span>
              </div>
              <h3 className={s.resultTitle}>
                A live browser tab, updating every second.
              </h3>
            </div>
            <DashboardAscii />
          </div>
        </section>

        {/* ---------- THE MODEL ---------- */}
        <section className={s.section} id="model">
          <div className={s.sectionHead}>
            <div className={s.sectionEyebrow}>
              <span>{'§'} section 02</span>
              <span className={s.sectionEyebrowDot}>{'·'}</span>
              <span>the model</span>
            </div>
            <h2 className={s.sectionTitle}>
              <span className={s.sectionHash}>#</span> Values, and a way to change them.
            </h2>
          </div>

          <pre className={s.dividerAscii} aria-hidden>
{`┌───────────────────────────────────────────────────────────────────────────────┐
│  BEFORE                        NU.RUN                          AFTER  │
└───────────────────────────────────────────────────────────────────────────────┘`}
          </pre>

          <div className={s.modelWrap}>
            <ModelViz />
          </div>

          <p className={s.modelCaption}>
            <span className={s.heroPrompt}>&gt; </span>
            A field on a browser tab, a value on disk, a number in memory.
            <b> Nu updates all three with one move.</b>
          </p>
        </section>

        {/* ---------- PILLARS ---------- */}
        <section className={s.section} id="pillars">
          <div className={s.sectionHead}>
            <div className={s.sectionEyebrow}>
              <span>{'§'} section 03</span>
              <span className={s.sectionEyebrowDot}>{'·'}</span>
              <span>pillars</span>
            </div>
            <div className={s.pillarsEyebrow}>and by the way,</div>
            <h2 className={s.sectionTitle}>
              <span className={s.sectionHash}>#</span> The same 30-line program is also...
            </h2>
          </div>

          <pre className={s.pillarsHeader} aria-hidden>
            {`  IDX  NAME          TITLE${' '.repeat(46)}`}
          </pre>
          <pre className={s.pillarsRule} aria-hidden>
            {'─'.repeat(120)}
          </pre>

          <ol className={s.pillarsList}>
            {PILLARS.map((p, i) => {
              const idx = String(i + 1).padStart(2, '0');
              return (
                <li key={p.name} className={s.pillar}>
                  <div className={s.pillarRow}>
                    <span className={s.pillarIdx}>[{idx}]</span>
                    <span className={s.pillarName}>{p.name.padEnd(14, ' ')}</span>
                    <span className={s.pillarTitle}>{p.title}</span>
                  </div>
                  <div className={s.pillarBody}>
                    <span className={s.pillarBodyLead}>{'└'}{'─'.repeat(2)} </span>
                    {p.body}
                  </div>
                </li>
              );
            })}
          </ol>

          <pre className={s.pillarsRule} aria-hidden>
            {'─'.repeat(120)}
          </pre>
          <div className={s.pillarsFoot}>
            <span className={s.heroPrompt}>$</span>{' '}
            <span>echo &quot;{PILLARS.length} pillars listed. end of program.&quot;</span>
            <span className={s.caret} aria-hidden />
          </div>
        </section>

        <pre className={s.divider} aria-hidden>
          {'═'.repeat(120)}
        </pre>

        {/* ---------- FOOTER strip ---------- */}
        <footer className={s.footer}>
          <span className={s.footerCell}>
            <span className={s.footerLabel}>project</span>
            <span>nu v0.1.0</span>
          </span>
          <span className={s.footerCell}>
            <span className={s.footerLabel}>read</span>
            <Link href="/docs">the docs {'→'}</Link>
          </span>
          <span className={s.footerCell}>
            <span className={s.footerLabel}>src</span>
            <a href="https://github.com/nustackdev/nu">github.com/nustackdev/nu</a>
          </span>
          <span className={s.footerCell}>
            <span className={s.footerLabel}>built by</span>
            <a href="https://github.com/nustackdev">nustackdev</a>
          </span>
        </footer>

      </div>
    </div>
  );
}
