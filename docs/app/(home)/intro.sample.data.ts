import type { CodeTok } from '@/components/site/CodeSample';

/** Quickstart — install, run the bundled counter demo, open the browser. */
export const QUICKSTART_TERMINAL_LINES: CodeTok[][] = [
  [{ c: 'cmt', t: '# 1. install' }],
  [{ t: 'pip install ' }, { c: 'str', t: '"nustack-py[all]"' }],
  [],
  [{ c: 'cmt', t: '# 2. run the bundled demo' }],
  [{ t: 'nu demo counter' }],
  [],
  [{ c: 'cmt', t: '# 3. open the browser tab that pops up' }],
];

/** Beat 1 — the joyful three-liner. Plain Python, no Nu. */
export const INTRO_PLAIN_LINES: CodeTok[][] = [
  [{ t: 'a = ' }, { c: 'str', t: '2' }],
  [{ t: 'b = ' }, { c: 'str', t: '5' }],
  [{ c: 'kw', t: 'print' }, { t: '(a + b)' }],
];

/** Beat 2 — same program, a and b persisted in a KV store. Runnable. */
export const INTRO_KV_LINES: CodeTok[][] = [
  [{ c: 'kw', t: 'import' }, { t: ' nu' }],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' DB(' }, { c: 'nu', t: 'nu.Shape' }, { t: '):' }],
  [{ t: '    a = ' }, { c: 'nu', t: 'nu.kv.IntRef' }, { t: '.slot()' }],
  [{ t: '    b = ' }, { c: 'nu', t: 'nu.kv.IntRef' }, { t: '.slot()' }],
  [],
  [{ c: 'cmt', t: '# compute a + b and print it' }],
  [{ t: 'compute = DB.a.set(' }, { c: 'str', t: '2' }, { t: ') >> DB.b.set(' }, { c: 'str', t: '5' }, { t: ') >> ' }, { c: 'nu', t: 'nu.print' }, { t: '(DB.a + DB.b)' }],
  [],
  [{ c: 'cmt', t: '# assemble: rocksdb-backed' }],
  [{ t: 'app = ' }, { c: 'nu', t: 'nu.With' }, { t: '(' }],
  [{ t: '    ' }, { c: 'nu', t: 'nu.kv.rocksdb_navigator' }, { t: '(' }, { c: 'str', t: '".dbsum"' }, { t: '),' }],
  [{ t: '    body=' }, { c: 'nu', t: 'nu.kv.auto_flow_atomic' }, { t: '(compute),' }],
  [{ t: ')' }],
  [],
  [{ c: 'nu', t: 'nu.run' }, { t: '(app)' }],
];

/** Beat 3 — same program, result rendered in a live browser dashboard. Runnable. */
export const INTRO_UI_LINES: CodeTok[][] = [
  [{ c: 'kw', t: 'import' }, { t: ' asyncio' }],
  [{ c: 'kw', t: 'import' }, { t: ' nu' }],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' DB(' }, { c: 'nu', t: 'nu.Shape' }, { t: '):' }],
  [{ t: '    a = ' }, { c: 'nu', t: 'nu.kv.IntRef' }, { t: '.slot()' }],
  [{ t: '    b = ' }, { c: 'nu', t: 'nu.kv.IntRef' }, { t: '.slot()' }],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' Dashboard(' }, { c: 'nu', t: 'nu.ui.Page' }, { t: '):' }],
  [{ t: '    out = ' }, { c: 'nu', t: 'nu.ui.TextRef' }, { t: '.slot()' }],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' App(' }, { c: 'nu', t: 'nu.ui.Index' }, { t: '):' }],
  [{ t: '    pages = ' }, { c: 'nu', t: 'nu.ui.Pages' }, { t: '({' }, { c: 'str', t: '"/"' }, { t: ': Dashboard})' }],
  [],
  [{ c: 'cmt', t: '# compute a + b and render into the dashboard text block' }],
  [{ t: 'compute = DB.a.set(' }, { c: 'str', t: '2' }, { t: ') >> DB.b.set(' }, { c: 'str', t: '5' }, { t: ') >> Dashboard.out.set(DB.a + DB.b)' }],
  [],
  [{ c: 'cmt', t: '# assemble: rocksdb-backed, served over the browser' }],
  [{ t: 'app = ' }, { c: 'nu', t: 'nu.With' }, { t: '(' }],
  [{ t: '    ' }, { c: 'nu', t: 'nu.kv.rocksdb_navigator' }, { t: '(' }, { c: 'str', t: '".dbsum"' }, { t: '),' }],
  [{ t: '    ' }, { c: 'nu', t: 'nu.ui.server' }, { t: '(' }, { c: 'nu', t: 'nu.kv.auto_flow_atomic' }, { t: '(compute)),' }],
  [{ t: ')' }],
  [],
  [{ t: 'asyncio.run(' }, { c: 'nu', t: 'nu.arun' }, { t: '(app))' }],
];
