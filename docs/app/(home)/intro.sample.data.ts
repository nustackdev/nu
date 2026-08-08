import type { CodeTok } from '@/components/site/CodeSample';

/** Beat 1 — the joyful three-liner. Plain Python, no Nu. */
export const INTRO_PLAIN_LINES: CodeTok[][] = [
  [{ t: 'a = ' }, { c: 'str', t: '2' }],
  [{ t: 'b = ' }, { c: 'str', t: '5' }],
  [{ c: 'kw', t: 'print' }, { t: '(a + b)' }],
];

/** Beat 2 — same program, a and b persisted in a KV store. */
export const INTRO_KV_LINES: CodeTok[][] = [
  [{ c: 'kw', t: 'class' }, { t: ' DB(' }, { c: 'nu', t: 'nu.Shape' }, { t: '):' }],
  [{ t: '    a: ' }, { c: 'nu', t: 'nu.kv.IntRef' }],
  [{ t: '    b: ' }, { c: 'nu', t: 'nu.kv.IntRef' }],
  [],
  [{ t: 'DB.a.set(' }, { c: 'str', t: '2' }, { t: ') >> DB.b.set(' }, { c: 'str', t: '5' }, { t: ') >> ' }, { c: 'nu', t: 'nu.print' }, { t: '(DB.a + DB.b)' }],
];

/** Beat 3 — same program, result rendered in a live browser dashboard. */
export const INTRO_UI_LINES: CodeTok[][] = [
  [{ c: 'kw', t: 'class' }, { t: ' DB(' }, { c: 'nu', t: 'nu.Shape' }, { t: '):' }],
  [{ t: '    a: ' }, { c: 'nu', t: 'nu.kv.IntRef' }],
  [{ t: '    b: ' }, { c: 'nu', t: 'nu.kv.IntRef' }],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' Dashboard(' }, { c: 'nu', t: 'nu.Shape' }, { t: '):' }],
  [{ t: '    out: ' }, { c: 'nu', t: 'nu.ui.TextRef' }],
  [],
  [{ t: 'DB.a.set(' }, { c: 'str', t: '2' }, { t: ') >> DB.b.set(' }, { c: 'str', t: '5' }, { t: ') >> Dashboard.out.set(DB.a + DB.b)' }],
];
