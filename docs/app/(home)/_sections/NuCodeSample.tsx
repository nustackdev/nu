'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import s from './NuCodeSample.module.css';

type Tok = { c?: 'kw' | 'nu' | 'str' | 'cmt'; t: string };

/**
 * Flat IDE-style block for a single-file code sample.
 * Tab strip on top, line-numbered gutter on the left, tokens color-tagged
 * from the shared palette (--nu-accent = purple, --nu-accent-2 = blue).
 *
 * Lines are declared as arrays of tokens so the gutter aligns perfectly and
 * empty lines render at line-height.
 *
 * Source: nu/examples/persistent_counter_ui.py — a RocksDB + NudleServer bracket app,
 * a browser dashboard on a live counter. Verbatim minus the module docstring
 * and `from __future__ import annotations` (both pure noise on the landing).
 */
const LINES: Tok[][] = [
  [{ c: 'kw', t: 'import' }, { t: ' ' }, { c: 'nu', t: 'nu' }],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' Counter(' }, { c: 'nu', t: 'nu.Shape' }, { t: '):' }],
  [{ t: '    value: ' }, { c: 'nu', t: 'nu.v.IntRef' }],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' Dashboard(' }, { c: 'nu', t: 'nu.ui.Page' }, { t: '):' }],
  [{ t: '    count: ' }, { c: 'nu', t: 'nu.ui.TextRef' }],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' App(' }, { c: 'nu', t: 'nu.ui.Index' }, { t: '):' }],
  [{ t: '    pages = ' }, { c: 'nu', t: 'nu.ui.Pages' }, { t: '({' }, { c: 'str', t: '"/"' }, { t: ': Dashboard})' }],
  [],
  [{ t: 'app = ' }, { c: 'nu', t: 'nu.With' }, { t: '(' }],
  [{ t: '    ' }, { c: 'nu', t: 'nu.v.presets.rocksdb_navigator_inmemory' }, { t: '(' }, { c: 'str', t: '".dbtest"' }, { t: '),' }],
  [{ t: '    ' }, { c: 'nu', t: 'nu.ui.presets.server' }, { t: '(' }],
  [{ t: '        ' }, { c: 'nu', t: 'nu.ReactForever' }, { t: '(' }],
  [{ t: '            Counter.value.on_change(),' }],
  [{ t: '            Dashboard.count.set(Counter.value),' }],
  [{ t: '        ),' }],
  [{ t: '    ),' }],
  [{ t: '    body=' }, { c: 'nu', t: 'nu.ForeverDo' }, { t: '(' }],
  [{ t: '        Counter.value.inc()' }],
  [{ t: '        >> ' }, { c: 'nu', t: 'nu.Delay' }, { t: '(1.0),' }],
  [{ t: '    ),' }],
  [{ t: ')' }],
  [],
  [{ c: 'kw', t: 'if' }, { t: ' __name__ == ' }, { c: 'str', t: "'__main__'" }, { t: ':' }],
  [{ t: '    ' }, { c: 'kw', t: 'import' }, { t: ' asyncio' }],
  [{ t: '    asyncio.run(' }, { c: 'nu', t: 'nu.arun' }, { t: '(' }, { c: 'nu', t: 'nu.v.auto_flow_atomic' }, { t: '(app)))' }],
];

const RAW = LINES.map((tokens) => tokens.map((tok) => tok.t).join('')).join('\n');

export function NuCodeSample() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(RAW);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      /* clipboard blocked — silent no-op */
    }
  };

  return (
    <div className={s.ide} role="figure" aria-label="Nu code sample: persistent_counter_ui.py">
      <div className={s.ideTabs}>
        <div className={`${s.ideTab} ${s.ideTabActive}`}>
          <span className={s.ideTabDot} aria-hidden />
          persistent_counter_ui.py
        </div>
        <div className={s.ideMeta}>python · {LINES.length} loc</div>
      </div>
      <div className={s.ideBody}>
        <button
          type="button"
          className={s.ideCopy}
          onClick={handleCopy}
          aria-label={copied ? 'code copied' : 'copy code'}
        >
          {copied ? <Check size={14} aria-hidden /> : <Copy size={14} aria-hidden />}
        </button>
        <div className={s.ideGutter} aria-hidden>
          {LINES.map((_, i) => (
            <div key={i} className={s.ideLineNo}>{i + 1}</div>
          ))}
        </div>
        <div className={s.ideCode}>
          {LINES.map((tokens, i) => (
            <div key={i} className={s.ideLine}>
              {tokens.length === 0 ? ' ' : tokens.map((tok, j) =>
                tok.c ? (
                  <span key={j} className={s[tok.c]}>{tok.t}</span>
                ) : (
                  <span key={j}>{tok.t}</span>
                ),
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
