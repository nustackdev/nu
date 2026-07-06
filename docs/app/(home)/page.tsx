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
 * Context showcase: three fabrics, before → after
 * Each SVG is a "diff" between Context v0 and Context v1.
 * The mutated cell is the only element in the accent color.
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
      {children}
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
  title: string;
  code: string;
  twist: React.ReactNode;
  twistBody: React.ReactNode;
}> = [
  {
    n: 'step 01',
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
          <div className={s.eyebrow}>the interaction model</div>
          <h1 className={s.wordmark}>
            <span>N</span>
            <span className={s.wordmarkAccent}>U</span>
          </h1>
          <p className={s.lede}>
            Write the program.<br />
            <span className={s.ledeAccent}>Swap the world.</span>
          </p>
          <p className={s.subLede}>
            Nu is a programming model built on two citizens — <b>Refs</b> and{' '}
            <b>Interactions</b> — evaluated against a <b>Context</b>. One
            program. Any world.
          </p>
        </header>

        {/* ---------- interaction model ---------- */}
        <section className={s.modelSec} id="model">
          <div className={s.modelHead}>
            <span className={s.modelLabel}>the model</span>
            <h2 className={s.modelTitle}>
              A program is <span className={s.accent}>Refs</span> and{' '}
              <span className={s.accent}>Interactions</span>. It runs against a{' '}
              <span className={s.accent}>Context</span>.
            </h2>
            <p className={s.modelIntro}>
              Two citizens describe every program: a <b>Ref</b> is an address
              into the world, an <b>Interaction</b> is what you do with it.
              Together they build a tree. A <b>Context</b> is the world that
              tree runs against — the same tree can be evaluated against any
              Context.
            </p>
          </div>

          {/* three citizen cards */}
          <div className={s.citizens}>
            <div className={s.citizen}>
              <div className={s.citizenLabel}>Ref</div>
              <p className={s.citizenVerb}>names.</p>
              <p className={s.citizenBody}>
                A pointer to a resource — a db row, a config key, a file path,
                an api endpoint, a slot in a dict. Carries the address, not the
                value at the address.
              </p>
            </div>
            <div className={s.citizen}>
              <div className={s.citizenLabel}>Interaction</div>
              <p className={s.citizenVerb}>describes.</p>
              <p className={s.citizenBody}>
                What the program does with Refs: read, write, compute, branch,
                iterate, compose. Every non-Ref node in the tree is one.
              </p>
            </div>
            <div className={s.citizen}>
              <div className={s.citizenLabel}>Context</div>
              <p className={s.citizenVerb}>holds the world.</p>
              <p className={s.citizenBody}>
                The addressable space Refs resolve inside. Bind different
                Contexts — memory, disk, browser — and the same tree touches
                different worlds.
              </p>
            </div>
          </div>

          {/* mutation kernel */}
          <div className={s.kernel}>
            <span className={s.kernelTag}>the kernel</span>
            <div className={s.kernelFormula}>
              <span>Context v0</span>
              <span className={s.arrow}>→</span>
              <span><span className={s.accent}>Interaction(Ref)</span></span>
              <span className={s.arrow}>→</span>
              <span>Context v1</span>
            </div>
            <p className={s.kernelNote}>
              A program mutates the Context. That&apos;s <b>all</b> the model
              says. Everything else is derived from these three lines.
            </p>
          </div>

          {/* showcase: three contexts, before → after */}
          <div className={s.showcase}>
            <div className={s.showcaseHead}>
              <span className={s.showcaseLabel}>see the context change</span>
              <h3 className={s.showcaseTitle}>
                Three worlds. One pattern.
              </h3>
              <p className={s.showcaseIntro}>
                The same tree runs against three different Contexts. Only the
                <code> bind(...)</code> line differs — the interaction stays the
                same. Watch what changes on the right.
              </p>
            </div>
            <div className={s.showcaseRows}>
              {CTX_ROWS.map((r) => (
                <article key={r.name} className={s.ctxRow}>
                  <div className={s.ctxRowHead}>
                    <span className={s.ctxName}>{r.name}</span>
                    <p className={s.ctxHint}>{r.hint}</p>
                  </div>
                  <div className={s.ctxCode}>
                    <Code src={r.code} />
                  </div>
                  <div className={s.ctxViz}>{r.viz}</div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ---------- getting started ---------- */}
        <section className={s.stepsSec} id="start">
          <div className={s.stepsHead}>
            <div>
              <div className={s.stepsLabel}>getting started</div>
              <h2 className={s.stepsTitle}>Six steps. All the way to a shipped app.</h2>
            </div>
          </div>
          <div className={s.stepsList}>
            {STEPS.map((st) => (
              <article key={st.n} className={s.step}>
                <div className={s.stepHead}>
                  <span className={s.stepN}>{st.n}</span>
                  <h3 className={s.stepTitle}>{st.title}</h3>
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
                name="nu.mem"
                title="In-memory dict."
                body="Dict-backed. Sketches, tests, ephemeral state."
                status="stable"
              />
              <Tile
                name="nu.virtuals"
                title="Persistent, transactional."
                body="RocksDB. Snapshots, transactions, observers, ordered scans."
                status="alpha · active"
              />
              <Tile
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
              {FEATURES.map((f) => (
                <div key={f.name} className={s.feature}>
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
          <span>
            nu · built by <a href="https://github.com/nustackdev">nustackdev</a>
          </span>
          <span>
            <Link href="/docs">read the docs →</Link>
          </span>
        </footer>

      </div>
    </div>
  );
}

/* ============================================================================
 * Tile
 * ==========================================================================*/

function Tile({
  name,
  title,
  body,
  status,
  wip,
}: {
  name: string;
  title: string;
  body: string;
  status: string;
  wip?: boolean;
}) {
  return (
    <div className={s.tile}>
      <div className={s.tileName}>{name}</div>
      <h3 className={s.tileTitle}>{title}</h3>
      <p className={s.tileBody}>{body}</p>
      <div className={`${s.tileStatus} ${wip ? s.tileStatusWip : ''}`}>
        {status}
      </div>
    </div>
  );
}
