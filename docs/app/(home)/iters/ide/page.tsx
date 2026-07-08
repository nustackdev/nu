import Link from 'next/link';
import {
  ArrowRight,
  ArrowUpRight,
  Book,
  Boxes,
  ChevronDown,
  ChevronRight,
  Circle,
  CircleDot,
  Cpu,
  FileCode2,
  FileText,
  Folder,
  FolderOpen,
  GitBranch,
  Layers,
  Play,
  Puzzle,
  Search,
  Settings,
  SquareTerminal,
  Target,
  Wrench,
  Zap,
} from 'lucide-react';
import s from './page.module.css';

/* ============================================================================
 * Inline GitHub mark
 * ==========================================================================*/
function GithubMark({ size = 15 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 0.5C5.65 0.5 0.5 5.65 0.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-1.94c-3.2.7-3.87-1.54-3.87-1.54-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.56-.29-5.25-1.28-5.25-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.47.11-3.06 0 0 .97-.31 3.18 1.18a11.05 11.05 0 0 1 5.8 0c2.21-1.49 3.18-1.18 3.18-1.18.63 1.59.23 2.77.11 3.06.74.81 1.19 1.84 1.19 3.1 0 4.43-2.7 5.4-5.27 5.69.41.36.78 1.06.78 2.13v3.16c0 .31.21.67.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35 0.5 12 0.5z" />
    </svg>
  );
}

/* ============================================================================
 * Syntax highlighting
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
      parts.push(<span key={i++} className={s.tokKw}>{tok}</span>);
    } else if (/^["'].*["']$/.test(tok)) {
      parts.push(<span key={i++} className={s.tokSt}>{tok}</span>);
    } else if (tok === '>>' || tok === '<<' || tok === '|') {
      parts.push(<span key={i++} className={s.tokOp}>{tok}</span>);
    } else {
      parts.push(<span key={i++}>{tok}</span>);
    }
  }
  if (comment !== null) {
    parts.push(<span key={i++} className={s.tokCm}>{comment}</span>);
  }
  return <span key={key}>{parts}</span>;
}

/** Editor: numbered lines, optional highlighted range. */
function Editor({
  src,
  highlight,
  wrap,
}: {
  src: string;
  highlight?: [number, number];
  wrap?: boolean;
}) {
  const lines = src.replace(/\n$/, '').split('\n');
  const width = String(lines.length).length;
  return (
    <pre className={`${s.editor} ${wrap ? s.editorWrap : ''}`}>
      {lines.map((l, i) => {
        const n = i + 1;
        const hl = highlight && n >= highlight[0] && n <= highlight[1];
        return (
          <div key={i} className={`${s.eLine} ${hl ? s.eLineHl : ''}`}>
            <span className={s.eNum} style={{ minWidth: `${width + 1}ch` }}>{n}</span>
            <span className={s.eCode}>{renderLine(l, i)}</span>
          </div>
        );
      })}
    </pre>
  );
}

/** Compact inline code (no line numbers) — used inside cards. */
function CodeInline({ src }: { src: string }) {
  const lines = src.replace(/\n$/, '').split('\n');
  return (
    <pre className={s.codeInline}>
      {lines.map((l, i) => (
        <div key={i} className={s.codeInlineLine}>{renderLine(l, i)}</div>
      ))}
    </pre>
  );
}

/* ============================================================================
 * IDE chrome — action bar, sidebar, status bar
 * ==========================================================================*/

function ActionBar() {
  return (
    <header className={s.actionBar}>
      <div className={s.abBrand}>
        <span className={s.abLogo}>nu</span>
        <span className={s.abProject}>nustackdev / nu</span>
        <ChevronDown size={11} className={s.abChevron} />
      </div>
      <nav className={s.abMenu}>
        <button type="button">File</button>
        <button type="button">Edit</button>
        <button type="button">View</button>
        <button type="button">Navigate</button>
        <button type="button">Run</button>
        <button type="button">Help</button>
      </nav>
      <div className={s.abRight}>
        <div className={s.abRun}>
          <span className={s.abRunLabel}>counter · rocksdb</span>
          <ChevronDown size={11} />
          <button type="button" className={s.abRunGo} aria-label="Run">
            <Play size={11} fill="currentColor" />
          </button>
        </div>
        <button type="button" className={s.abIcon} aria-label="Search">
          <Search size={14} />
        </button>
        <button type="button" className={s.abIcon} aria-label="Settings">
          <Settings size={14} />
        </button>
      </div>
    </header>
  );
}

function SidebarTool({
  icon,
  label,
  active,
  badge,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  badge?: string;
}) {
  return (
    <button
      type="button"
      className={`${s.sbTool} ${active ? s.sbToolActive : ''}`}
    >
      <span className={s.sbToolIcon}>{icon}</span>
      <span className={s.sbToolLabel}>{label}</span>
      {badge ? <span className={s.sbToolBadge}>{badge}</span> : null}
    </button>
  );
}

function Sidebar() {
  return (
    <aside className={s.sidebar}>
      <SidebarTool icon={<Folder size={14} />} label="Project" active />
      <SidebarTool icon={<Layers size={14} />} label="Structure" />
      <SidebarTool icon={<Book size={14} />} label="Learn" />
      <SidebarTool icon={<Puzzle size={14} />} label="Plugins" />
      <SidebarTool icon={<Circle size={14} />} label="Problems" badge="0" />
      <div className={s.sbSpacer} />
      <SidebarTool icon={<SquareTerminal size={14} />} label="Terminal" />
      <SidebarTool icon={<Settings size={14} />} label="Preferences" />
    </aside>
  );
}

function StatusBar() {
  return (
    <footer className={s.statusBar}>
      <span className={s.stItem}><GitBranch size={11} /> main</span>
      <span className={s.stItem}>Python 3.12</span>
      <span className={s.stItem}>UTF-8</span>
      <span className={s.stItem}>LF</span>
      <span className={s.stItem}>4 spaces</span>
      <span className={s.stSpacer} />
      <span className={s.stItem}>nu <b>v0.1.0-alpha</b></span>
      <span className={`${s.stItem} ${s.stReady}`}>
        <CircleDot size={11} /> ready
      </span>
    </footer>
  );
}

/* ============================================================================
 * Tool-window primitives
 * ==========================================================================*/

/** Panel with an eyebrow header — the standard container in this iter. */
function Panel({
  eyebrow,
  title,
  actions,
  children,
  id,
}: {
  eyebrow?: React.ReactNode;
  title?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  id?: string;
}) {
  return (
    <section className={s.panel} id={id}>
      {(eyebrow || title || actions) && (
        <div className={s.panelHead}>
          <div className={s.panelHeadLeft}>
            {eyebrow ? <span className={s.panelEyebrow}>{eyebrow}</span> : null}
            {title ? <h2 className={s.panelTitle}>{title}</h2> : null}
          </div>
          {actions ? <div className={s.panelActions}>{actions}</div> : null}
        </div>
      )}
      <div className={s.panelBody}>{children}</div>
    </section>
  );
}

/** Tabs strip. Static — active tab is fixed. */
function TabStrip({
  tabs,
  activeIndex = 0,
  trailing,
}: {
  tabs: Array<{ icon?: React.ReactNode; label: string; sub?: string }>;
  activeIndex?: number;
  trailing?: React.ReactNode;
}) {
  return (
    <div className={s.tabs}>
      {tabs.map((t, i) => (
        <div
          key={t.label}
          className={`${s.tab} ${i === activeIndex ? s.tabActive : ''}`}
        >
          {t.icon ? <span className={s.tabIcon}>{t.icon}</span> : null}
          <span className={s.tabLabel}>{t.label}</span>
          {t.sub ? <span className={s.tabSub}>{t.sub}</span> : null}
          {i === activeIndex ? <span className={s.tabClose}>×</span> : null}
        </div>
      ))}
      {trailing ? <div className={s.tabsTrailing}>{trailing}</div> : null}
    </div>
  );
}

/** Breadcrumb bar under the tab strip. */
function Breadcrumb({ parts }: { parts: string[] }) {
  return (
    <div className={s.crumb}>
      {parts.map((p, i) => (
        <span key={i} className={s.crumbPart}>
          {i > 0 ? <ChevronRight size={11} className={s.crumbSep} /> : null}
          {p}
        </span>
      ))}
    </div>
  );
}

/* ============================================================================
 * DATA — same content as main page, restructured for IDE views
 * ==========================================================================*/

const WATCH_CODE = `import nu

class Counter(nu.Shape):
    value: nu.v.IntRef

class Dashboard(nu.nd.Page):
    heading: nu.nd.HeadingRef
    count: nu.nd.TextRef
    history: nu.nd.LineChart

class App(nu.nd.Index):
    title: nu.nd.TitleRef
    nav: nu.nd.NavRef
    pages = nu.nd.Pages({"/": Dashboard})

counter = (
    nu.IfDo(Counter.value.missing(), Counter.value.store(0))
    >> nu.ForeverDo(Counter.value.inc() >> nu.Delay(1.0))
)

ui = (
    App.title.store("nudle bracket counter")
    >> Dashboard.heading.store("counter live")
    >> nu.ReactForever(
        Counter.value.on_change(),
        Dashboard.count.store(Counter.value)
        | Dashboard.history.append(Counter.value, Counter.value),
    )
)

app = nu.With(
    nu.v.presets.rocksdb_navigator_inmemory(".dbtest"),
    nu.nd.presets.server(ui),
    body=counter,
)

nu.run(nu.v.auto_flow_atomic(app))`;

type WatchBeat = {
  num: string;
  kind: string;
  range: [number, number];
  title: string;
  body: React.ReactNode;
};

const WATCH_BEATS: WatchBeat[] = [
  {
    num: '01',
    kind: 'shapes',
    range: [1, 15],
    title: 'Declare the world.',
    body: (
      <>
        <b>Counter</b> is one IntRef, headed for RocksDB. <b>Dashboard</b> is a
        Page — heading, count, history — headed for a browser tab.
      </>
    ),
  },
  {
    num: '02',
    kind: 'the loop',
    range: [17, 20],
    title: 'A forever bracket.',
    body: (
      <>
        <b>IfDo</b> initializes on cold start. <b>ForeverDo</b> increments the
        counter every second — for as long as the app runs.
      </>
    ),
  },
  {
    num: '03',
    kind: 'reactivity',
    range: [22, 31],
    title: 'A reactive mirror.',
    body: (
      <>
        <b>ReactForever</b> watches <b>Counter.value</b>. Every change stores
        into the dashboard&apos;s count and appends a point to the history chart.
      </>
    ),
  },
  {
    num: '04',
    kind: 'the bind',
    range: [33, 40],
    title: 'One bracket. Then run.',
    body: (
      <>
        <b>nu.With</b> pins refs to fabrics: RocksDB for <b>Counter</b>, a
        browser tab for <b>Dashboard</b>. The counter loop runs in the middle.
        Then <b>nu.run</b>.
      </>
    ),
  },
];

const FABRICS: Array<{
  name: string;
  file: string;
  hint: React.ReactNode;
  code: string;
  viz: 'mem' | 'disk' | 'browser';
}> = [
  {
    name: 'nu.mem',
    file: 'mem.py',
    hint: <>the Context is a <b>Python dict</b>.</>,
    code: `class Counter(nu.Shape):
    value: nu.mem.IntRef

ctx = nu.Context().bind(dict, {}, Counter)

nu.run(Counter.value.store(1), ctx)`,
    viz: 'mem',
  },
  {
    name: 'nu.virtuals',
    file: 'virtuals.py',
    hint: <>the Context is <b>RocksDB on disk</b>.</>,
    code: `class Counter(nu.Shape):
    value: nu.virtuals.IntRef

ctx = nu.Context().bind(Navigator, rocksdb)

nu.run(Counter.value.store(1), ctx)`,
    viz: 'disk',
  },
  {
    name: 'nu.nudle',
    file: 'nudle.py',
    hint: <>the Context is a <b>live browser tab</b>.</>,
    code: `class Dashboard(nu.nudle.Page):
    count: nu.nudle.TextRef

ctx = nu.Context().bind(nd.Server, tab)

nu.run(Dashboard.count.store(1), ctx)`,
    viz: 'browser',
  },
];

type Step = {
  num: string;
  file: string;
  kind: React.ReactNode;
  title: string;
  code: string;
  twist: React.ReactNode;
  twistBody: React.ReactNode;
};

const STEPS: Step[] = [
  {
    num: '01',
    file: '01_reads.py',
    kind: <><b>ref</b> · address</>,
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
    num: '02',
    file: '02_computes.py',
    kind: <><b>tree</b> · defer</>,
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
    num: '03',
    file: '03_writes.py',
    kind: <><b>cmd</b> · write</>,
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
    num: '04',
    file: '04_persists.py',
    kind: <><b>swap</b> · disk</>,
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
    num: '05',
    file: '05_composes.py',
    kind: <><b>&gt;&gt;</b> · <b>|</b></>,
    title: 'It composes.',
    code: `app = (
    Order.price.store(200.0)
    >> Order.qty.store(50)
    >> nu.Print("notional", Order.price * Order.qty)
)

nu.run(app, ctx)           # notional 10000.0`,
    twist: <><b>&gt;&gt; sequences.</b> <b>| runs in parallel.</b></>,
    twistBody: (
      <>
        Two operators for the whole language of composition. Every Nu program —
        reads, writes, control flow, IO — is one tree, built with{' '}
        <code>&gt;&gt;</code> and <code>|</code>.
      </>
    ),
  },
  {
    num: '06',
    file: '06_ships.py',
    kind: <><b>ship</b> · prod</>,
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

const PILLARS: Array<{ name: string; title: string; body: string; icon: React.ReactNode }> = [
  {
    name: 'acid',
    title: 'ACID by default.',
    body: 'Any subtree can wrap in nv.Transaction. Retries and snapshots come free with the fabric.',
    icon: <Wrench size={13} />,
  },
  {
    name: 'distributed',
    title: 'One bracket, many machines.',
    body: 'nu.ray binds Ray. The same program runs across a cluster with the same call.',
    icon: <Cpu size={13} />,
  },
  {
    name: 'infinite',
    title: 'Infinite streams, sampled.',
    body: 'kh57 lets you append forever and read a fair sample. Charts stay bounded, data does not.',
    icon: <Layers size={13} />,
  },
  {
    name: 'no limits',
    title: 'No framework. No DSL.',
    body: 'Pure python semantics. Your editor, your types, your debugger. Nothing hidden.',
    icon: <Target size={13} />,
  },
];

const CONTEXTS: Array<{ name: string; title: string; body: string; status: string; primary?: boolean }> = [
  {
    name: 'nu.mem',
    title: 'In-memory dict.',
    body: 'Dict-backed. Sketches, tests, ephemeral state.',
    status: 'stable',
  },
  {
    name: 'nu.virtuals',
    title: 'Persistent, transactional.',
    body: 'RocksDB. Snapshots, transactions, observers, ordered scans.',
    status: 'alpha · active',
    primary: true,
  },
  {
    name: 'nu.nudle',
    title: 'A browser tab as a Context.',
    body: 'Refs become UI. Mutations land on the tab.',
    status: 'alpha · active',
    primary: true,
  },
];

const OPERATORS: Array<{ name: string; title: string; body: string; code: string }> = [
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
 * SECTION 1 — HERO / WELCOME
 * ==========================================================================*/

function HeroWelcome() {
  return (
    <section className={s.hero}>
      <div className={s.heroMain}>
        <div className={s.heroEyebrow}>
          <span className={s.heroDot} /> welcome
        </div>
        <h1 className={s.heroWord}>
          n<em>u</em>
        </h1>
        <p className={s.heroTagline}>
          Compose <span className={s.heroAccent}>any tool</span> in pure python.
        </p>
        <p className={s.heroSub}>
          Nu turns any tool into a program of <b>Refs</b> and{' '}
          <b>Interactions</b> you compose like data. Built on{' '}
          <Link className={s.heroLink} href="/docs/model">the interaction model</Link>.
        </p>
        <div className={s.heroActions}>
          <a className={`${s.btn} ${s.btnPrimary}`} href="https://github.com/nustackdev/nu">
            <GithubMark size={14} />
            <span>Open on GitHub</span>
            <ArrowUpRight size={14} />
          </a>
          <Link className={`${s.btn} ${s.btnGhost}`} href="/docs">
            <FileText size={14} />
            <span>Read the docs</span>
          </Link>
        </div>
      </div>
      <aside className={s.heroSide}>
        <div className={s.heroCard}>
          <div className={s.heroCardHead}>
            <span className={s.heroCardLabel}>Release</span>
            <span className={s.tagPrimary}>alpha</span>
          </div>
          <div className={s.heroCardBody}>
            <div className={s.heroCardKV}><span>version</span><b>v0.1.0</b></div>
            <div className={s.heroCardKV}><span>status</span><b>active</b></div>
            <div className={s.heroCardKV}><span>python</span><b>3.12+</b></div>
            <div className={s.heroCardKV}><span>license</span><b>MIT</b></div>
          </div>
        </div>
        <div className={s.heroCard}>
          <div className={s.heroCardHead}>
            <span className={s.heroCardLabel}>Jump to</span>
          </div>
          <ul className={s.heroLinks}>
            <li><a href="#watch"><Play size={12} /> Watch an example</a></li>
            <li><a href="#model"><Layers size={12} /> The interaction model</a></li>
            <li><a href="#fabrics"><Boxes size={12} /> Three fabrics</a></li>
            <li><a href="#start"><Book size={12} /> Getting started · 6 steps</a></li>
            <li><a href="#batteries"><Puzzle size={12} /> Batteries</a></li>
          </ul>
        </div>
      </aside>
    </section>
  );
}

/* ============================================================================
 * SECTION 2 — WATCH: editor tab + Structure panel + Run panel
 * ==========================================================================*/

function StructureTree() {
  return (
    <div className={s.structure}>
      <div className={s.structureHead}>
        <Layers size={12} />
        <span>Structure</span>
        <span className={s.structureCount}>{WATCH_BEATS.length}</span>
      </div>
      <ul className={s.structureList}>
        {WATCH_BEATS.map((b) => (
          <li key={b.num} className={s.structureItem}>
            <div className={s.structureRow}>
              <ChevronDown size={12} className={s.structureCaret} />
              <FileCode2 size={12} className={s.structureIcon} />
              <span className={s.structureLabel}>
                <b>{b.num}</b> · {b.kind}
              </span>
              <span className={s.structureRange}>
                L {b.range[0]}–{b.range[1]}
              </span>
            </div>
            <div className={s.structureDesc}>
              <div className={s.structureDescTitle}>{b.title}</div>
              <div className={s.structureDescBody}>{b.body}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RunOutputMock() {
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
    <div className={s.runPanel}>
      <div className={s.runHead}>
        <span className={s.runTab}>
          <Play size={11} fill="currentColor" /> Run: counter · rocksdb
        </span>
        <span className={s.runStat}><CircleDot size={10} /> alive · 1s tick</span>
        <span className={s.runSpacer} />
        <span className={s.runMeta}>PID 8213 · elapsed 00:00:42</span>
      </div>
      <div className={s.runBody}>
        <div className={s.runLog}>
          <div><span className={s.runLogT}>[00:00:00]</span> nu.run: bind rocksdb → .dbtest</div>
          <div><span className={s.runLogT}>[00:00:00]</span> nu.run: bind nudle → tab@localhost:8000</div>
          <div><span className={s.runLogT}>[00:00:00]</span> Counter.value.missing → store(0)</div>
          <div><span className={s.runLogT}>[00:00:01]</span> Counter.value.inc → 1</div>
          <div><span className={s.runLogT}>[00:00:02]</span> Counter.value.inc → 2</div>
          <div className={s.runLogDim}><span className={s.runLogT}>[00:00:..]</span> …</div>
          <div>
            <span className={s.runLogT}>[00:00:42]</span>{' '}
            <span className={s.runLogOk}>Counter.value.inc → 42</span>
          </div>
        </div>
        <div className={s.runPreview}>
          <div className={s.runPreviewHead}>
            <span className={s.runPreviewDot} />
            <span className={s.runPreviewDot} />
            <span className={s.runPreviewDot} />
            <span className={s.runPreviewUrl}>nu://counter</span>
          </div>
          <div className={s.runPreviewBody}>
            <div className={s.runPreviewTitle}>counter live</div>
            <div className={s.runPreviewGrid}>
              <div className={s.runPreviewStat}>
                <div className={s.runPreviewStatLabel}>COUNT</div>
                <div className={s.runPreviewStatVal}>42</div>
              </div>
              <div className={s.runPreviewChart}>
                <div className={s.runPreviewChartLabel}>HISTORY</div>
                <svg viewBox="0 0 260 80" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <linearGradient id="ideChartFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--ide-primary)" stopOpacity="0.28" />
                      <stop offset="100%" stopColor="var(--ide-primary)" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <path d={areaD} transform="translate(-170, 30)" fill="url(#ideChartFill)" />
                  <path d={pathD} transform="translate(-170, 30)" fill="none" stroke="var(--ide-primary)" strokeWidth={1.5} />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function EditorWatch() {
  return (
    <Panel
      id="watch"
      eyebrow="§ 01 · Editor"
      title="Watch this example."
      actions={
        <>
          <span className={s.metaChip}>40 lines</span>
          <span className={s.metaChip}>python 3.12</span>
        </>
      }
    >
      <TabStrip
        tabs={[
          { icon: <FileCode2 size={12} />, label: 'nudle_rocksdb.py', sub: '*' },
        ]}
      />
      <Breadcrumb parts={['nu', 'examples', 'nudle_rocksdb.py']} />
      <div className={s.editorSplit}>
        <div className={s.editorMain}>
          <Editor src={WATCH_CODE} />
        </div>
        <StructureTree />
      </div>
      <RunOutputMock />
    </Panel>
  );
}

/* ============================================================================
 * SECTION 3 — MODEL: diagram tab
 * ==========================================================================*/

function ModelDiagram() {
  return (
    <svg viewBox="0 0 1000 480" xmlns="http://www.w3.org/2000/svg" className={s.modelSvg} role="img"
      aria-label="Three fragmented APIs collapse into one Nu interaction that reaches all substrates.">
      <defs>
        <radialGradient id="idePillGlow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="var(--ide-primary)" stopOpacity="0.18" />
          <stop offset="100%" stopColor="var(--ide-primary)" stopOpacity="0" />
        </radialGradient>
      </defs>
      {(() => {
        const rows = [
          { y: 90, label: 'BROWSER TAB', code: 'input.value = 1' },
          { y: 240, label: 'ON DISK', code: 'db.put("count", 1)' },
          { y: 390, label: 'IN MEMORY', code: 'd["count"] = 1' },
        ];
        const midY = 240, mLeft = 440, mRight = 640;
        return (
          <>
            {rows.map((r) => (
              <g key={r.label}>
                <text x={20} y={r.y - 32}
                  fontFamily="var(--font-mono)" fontSize={11}
                  letterSpacing="0.28em" fill="var(--ide-ink-3)">
                  [{r.label}]
                </text>
                <rect x={20} y={r.y - 24} width={220} height={54}
                  fill="var(--ide-editor)" stroke="var(--ide-hairline)" strokeWidth={1} />
                <text x={30} y={r.y}
                  fontFamily="var(--font-mono)" fontSize={12} fill="var(--ide-ink-3)">$</text>
                <text x={30} y={r.y + 16}
                  fontFamily="var(--font-mono)" fontSize={12} fill="var(--ide-ink-2)"
                  style={{ textDecoration: 'line-through' }}>
                  {r.code}
                </text>
              </g>
            ))}
            {rows.map((r) => (
              <g key={`c-${r.label}`} stroke="var(--ide-primary)" strokeWidth={1.3} fill="none" opacity={0.55}>
                <path d={`M 240 ${r.y} C 320 ${r.y} 360 ${midY} ${mLeft} ${midY}`} />
              </g>
            ))}
            <g>
              <ellipse cx={(mLeft + mRight) / 2} cy={midY + 8} rx={140} ry={70} fill="url(#idePillGlow)" />
              <rect x={mLeft} y={midY - 40} width={mRight - mLeft} height={80}
                fill="var(--ide-primary-soft)" stroke="var(--ide-primary)" strokeWidth={1.5} />
              <text x={(mLeft + mRight) / 2} y={midY - 20} textAnchor="middle"
                fontFamily="var(--font-mono)" fontSize={10} letterSpacing="0.28em"
                fill="var(--ide-primary)">NU.RUN · ONE INTERACTION</text>
              <text x={(mLeft + mRight) / 2} y={midY + 8} textAnchor="middle"
                fontFamily="var(--font-mono)" fontSize={17} fontWeight={700}
                fill="var(--ide-primary)">Add(CounterRef, 1)</text>
              <line x1={mLeft + 40} y1={midY + 22} x2={mRight - 40} y2={midY + 22}
                stroke="var(--ide-primary)" strokeWidth={1} opacity={0.28} />
            </g>
            {rows.map((r) => (
              <g key={`f-${r.label}`} stroke="var(--ide-primary)" strokeWidth={1.3}
                fill="none" opacity={0.6} strokeDasharray="4 4">
                <path d={`M ${mRight} ${midY} C 700 ${midY} 700 ${r.y} 760 ${r.y}`} />
                <polygon points={`${760 - 6},${r.y - 4} ${760},${r.y} ${760 - 6},${r.y + 4}`}
                  fill="var(--ide-primary)" opacity={1} stroke="none" />
              </g>
            ))}
            {rows.map((r) => (
              <g key={`R-${r.label}`}>
                <rect x={760} y={r.y - 24} width={220} height={54}
                  fill="var(--ide-primary-soft)" stroke="var(--ide-primary)" strokeWidth={1.4} />
                <text x={770} y={r.y}
                  fontFamily="var(--font-mono)" fontSize={12} fill="var(--ide-primary)">$</text>
                <text x={770} y={r.y + 16}
                  fontFamily="var(--font-mono)" fontSize={12} fill="var(--ide-ink)">
                  count: <tspan fill="var(--ide-primary)" fontWeight={700}>1</tspan>
                </text>
              </g>
            ))}
          </>
        );
      })()}
    </svg>
  );
}

function DiagramModel() {
  return (
    <Panel
      id="model"
      eyebrow="§ 02 · Diagram"
      title="Values, and a way to change them."
      actions={<span className={s.metaChip}>interaction-model.diagram</span>}
    >
      <TabStrip
        tabs={[{ icon: <Layers size={12} />, label: 'interaction-model.diagram' }]}
      />
      <div className={s.diagramWrap}>
        <ModelDiagram />
      </div>
      <div className={s.diagramCaption}>
        A field on a browser tab, a value on disk, a number in memory.{' '}
        <b>Nu updates all three with one move.</b>
      </div>
    </Panel>
  );
}

/* ============================================================================
 * SECTION 4 — THREE FABRICS: split editor with 3 stacked mini-editors
 * ==========================================================================*/

function FabricViz({ kind }: { kind: 'mem' | 'disk' | 'browser' }) {
  if (kind === 'mem') {
    return (
      <div className={s.fabricViz}>
        <div className={s.fabricVizLabel}>context.state</div>
        <pre className={s.fabricVizBody}>
          {'{ '}<span className={s.fabricVizKey}>&quot;value&quot;</span>
          {': '}<span className={s.fabricVizVal}>1</span>{' }'}
        </pre>
      </div>
    );
  }
  if (kind === 'disk') {
    return (
      <div className={s.fabricViz}>
        <div className={s.fabricVizLabel}>rocksdb · .dbtest</div>
        <div className={s.fabricVizRow}>
          <span className={s.fabricVizK}>Counter/value</span>
          <span className={s.fabricVizEq}>=</span>
          <span className={s.fabricVizVal}>1</span>
        </div>
      </div>
    );
  }
  return (
    <div className={s.fabricViz}>
      <div className={s.fabricVizBrowser}>
        <span className={s.rpDot} /><span className={s.rpDot} /><span className={s.rpDot} />
        <span className={s.fabricVizUrl}>nu://counter</span>
      </div>
      <div className={s.fabricVizBrowserBody}>
        <div className={s.fabricVizBrowserLabel}>COUNT</div>
        <div className={s.fabricVizBrowserVal}>1</div>
      </div>
    </div>
  );
}

function ThreeFabrics() {
  return (
    <Panel
      id="fabrics"
      eyebrow="§ 03 · Editor group"
      title="Three fabrics. Same shape."
      actions={<span className={s.metaChip}>3 files</span>}
    >
      <TabStrip
        tabs={FABRICS.map((f) => ({
          icon: <FileCode2 size={12} />,
          label: f.file,
        }))}
      />
      <p className={s.fabricsIntro}>
        The addresses it acts on are <b>Refs</b>. The world they resolve inside
        is a <b>Fabric</b>. Same Refs, same Interactions, three fabrics — watch
        the diff.
      </p>
      <div className={s.fabricList}>
        {FABRICS.map((f) => (
          <article key={f.name} className={s.fabricRow}>
            <div className={s.fabricRowHead}>
              <span className={s.fabricRowName}>{f.name}</span>
              <span className={s.fabricRowHint}>{f.hint}</span>
              <span className={s.fabricRowIdx}>{f.file}</span>
            </div>
            <div className={s.fabricRowBody}>
              <div className={s.fabricRowCode}>
                <Editor src={f.code} />
              </div>
              <FabricViz kind={f.viz} />
            </div>
          </article>
        ))}
      </div>
    </Panel>
  );
}

/* ============================================================================
 * SECTION 5 — PILLARS: Structure tool window
 * ==========================================================================*/

function StructurePillars() {
  return (
    <Panel
      id="pillars"
      eyebrow="§ 04 · Structure"
      title="The same 30-line program is also…"
    >
      <div className={s.pillarStructure}>
        <div className={s.pillarStructureHead}>
          <span>and by the way,</span>
          <span className={s.pillarStructureCount}>{PILLARS.length} items</span>
        </div>
        <ul className={s.pillarList}>
          {PILLARS.map((p, i) => (
            <li key={p.name} className={s.pillarItem}>
              <span className={s.pillarChevron}><ChevronRight size={12} /></span>
              <span className={s.pillarIcon}>{p.icon}</span>
              <span className={s.pillarIdx}>{String(i + 1).padStart(2, '0')}</span>
              <span className={s.pillarName}>{p.name}</span>
              <span className={s.pillarTitle}>{p.title}</span>
              <span className={s.pillarBody}>{p.body}</span>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

/* ============================================================================
 * SECTION 6 — GETTING STARTED: Learn tool window
 * ==========================================================================*/

function LearnQuickstart() {
  return (
    <Panel
      id="start"
      eyebrow="§ 05 · Learn"
      title="Six steps. All the way to a shipped app."
      actions={
        <>
          <span className={s.metaChip}>0 / 6 complete</span>
          <span className={s.metaChip}>~5 min</span>
        </>
      }
    >
      <div className={s.learn}>
        <nav className={s.learnNav} aria-label="Lessons">
          {STEPS.map((st) => (
            <a key={st.num} href={`#lesson-${st.num}`} className={s.learnNavItem}>
              <span className={s.learnNavNum}>{st.num}</span>
              <span className={s.learnNavTitle}>{st.title}</span>
              <span className={s.learnNavKind}>{st.kind}</span>
            </a>
          ))}
        </nav>
        <div className={s.learnList}>
          {STEPS.map((st, i) => (
            <article key={st.num} id={`lesson-${st.num}`} className={s.lesson}>
              <div className={s.lessonHead}>
                <span className={s.lessonNum}>{st.num}</span>
                <span className={s.lessonBar} />
                <h3 className={s.lessonTitle}>{st.title}</h3>
                <span className={s.lessonKind}>{st.kind}</span>
              </div>
              <div className={s.lessonBody}>
                <div className={s.lessonEditor}>
                  <div className={s.lessonEditorHead}>
                    <FileCode2 size={11} />
                    <span>{st.file}</span>
                    <span className={s.lessonEditorSpacer} />
                    <span className={s.lessonEditorRange}>
                      L 1–{st.code.replace(/\n$/, '').split('\n').length}
                    </span>
                  </div>
                  <Editor src={st.code} />
                </div>
                <aside className={s.lessonHint}>
                  <div className={s.lessonHintHead}>
                    <Zap size={11} />
                    <span>Hint {st.num}</span>
                  </div>
                  <p className={s.lessonHintLead}>{st.twist}</p>
                  <p className={s.lessonHintBody}>{st.twistBody}</p>
                  <div className={s.lessonHintFoot}>
                    <span className={s.lessonProgressDot} data-done={i < 0 ? 'true' : 'false'} />
                    <span>lesson {String(i + 1).padStart(2, '0')} of 06</span>
                  </div>
                </aside>
              </div>
            </article>
          ))}
        </div>
      </div>
    </Panel>
  );
}

/* ============================================================================
 * SECTION 7 — BATTERIES: Plugins marketplace
 * ==========================================================================*/

function PluginsBatteries() {
  return (
    <Panel
      id="batteries"
      eyebrow="§ 06 · Plugins"
      title="Contexts and operators you can pick up now."
      actions={
        <>
          <span className={s.metaChip}>{CONTEXTS.length + OPERATORS.length} items</span>
          <span className={s.metaChip}>Nu ecosystem</span>
        </>
      }
    >
      <div className={s.mktSearch}>
        <Search size={13} />
        <span className={s.mktSearchPh}>Search plugins…</span>
      </div>
      <div className={s.mktGroup}>
        <div className={s.mktGroupHead}>
          <FolderOpen size={13} />
          <span>Ready contexts</span>
          <span className={s.mktGroupCount}>{CONTEXTS.length}</span>
        </div>
        <div className={s.mktGrid}>
          {CONTEXTS.map((c, i) => (
            <article key={c.name} className={`${s.card} ${c.primary ? s.cardAlt : ''}`}>
              <div className={s.cardHead}>
                <span className={s.cardIdx}>[{String(i + 1).padStart(2, '0')}]</span>
                <span className={c.primary ? s.tagPrimary : s.tagAlt}>{c.status}</span>
              </div>
              <div className={s.cardName}>{c.name}</div>
              <h3 className={s.cardTitle}>{c.title}</h3>
              <p className={s.cardBody}>{c.body}</p>
              <button type="button" className={`${s.btn} ${s.btnGhost} ${s.btnSm}`}>
                <ArrowRight size={12} />
                <span>Open</span>
              </button>
            </article>
          ))}
        </div>
      </div>
      <div className={s.mktGroup}>
        <div className={s.mktGroupHead}>
          <FolderOpen size={13} />
          <span>Operators &amp; primitives</span>
          <span className={s.mktGroupCount}>{OPERATORS.length}</span>
        </div>
        <div className={s.mktGrid}>
          {OPERATORS.map((op, i) => (
            <article key={op.name} className={s.card}>
              <div className={s.cardHead}>
                <span className={s.cardIdx}>[{String(i + 1).padStart(2, '0')}]</span>
                <span className={s.tagPrimary}>{op.name}</span>
              </div>
              <h3 className={s.cardTitle}>{op.title}</h3>
              <p className={s.cardBody}>{op.body}</p>
              <div className={s.cardCode}>
                <CodeInline src={op.code} />
              </div>
            </article>
          ))}
        </div>
      </div>
    </Panel>
  );
}

/* ============================================================================
 * PAGE
 * ==========================================================================*/

export default function IterIdePage() {
  return (
    <div className={s.root}>
      <div className={s.shell}>
        <ActionBar />
        <div className={s.layout}>
          <Sidebar />
          <main className={s.main}>
            <HeroWelcome />
            <EditorWatch />
            <DiagramModel />
            <ThreeFabrics />
            <StructurePillars />
            <LearnQuickstart />
            <PluginsBatteries />
            <footer className={s.pageFoot}>
              <div className={s.pageFootCell}>
                <span className={s.pageFootLabel}>Project</span>
                <span>nu · v0.1.0-alpha</span>
              </div>
              <div className={s.pageFootCell}>
                <span className={s.pageFootLabel}>Read</span>
                <Link href="/docs">the docs →</Link>
              </div>
              <div className={s.pageFootCell}>
                <span className={s.pageFootLabel}>Source</span>
                <a href="https://github.com/nustackdev/nu">github.com/nustackdev/nu</a>
              </div>
              <div className={s.pageFootCell}>
                <span className={s.pageFootLabel}>Built by</span>
                <a href="https://github.com/nustackdev">nustackdev</a>
              </div>
            </footer>
          </main>
        </div>
        <StatusBar />
      </div>
    </div>
  );
}
