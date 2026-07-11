import s from './NuCodeSample.module.css';

type Tok = { c?: 'kw' | 'nu' | 'str' | 'cmt'; t: string };

/**
 * Flat IDE-style block for a single-file code sample.
 * Tab strip on top, line-numbered gutter on the left, tokens color-tagged
 * from the shared palette (--nu-accent = purple, --nu-accent-2 = blue).
 *
 * Lines are declared as arrays of tokens so the gutter aligns perfectly and
 * empty lines render at line-height.
 */
const LINES: Tok[][] = [
  [{ c: 'cmt', t: '"""Basic Nu bracket-tree app: mem preset + tiny compute."""' }],
  [],
  [{ c: 'kw', t: 'from' }, { t: ' __future__ ' }, { c: 'kw', t: 'import' }, { t: ' annotations' }],
  [],
  [{ c: 'kw', t: 'import' }, { t: ' ' }, { c: 'nu', t: 'nu' }],
  [],
  [],
  [{ c: 'kw', t: 'class' }, { t: ' Counter(' }, { c: 'nu', t: 'nu.Shape' }, { t: '):' }],
  [{ t: '    value: ' }, { c: 'nu', t: 'nu.v.IntRef' }],
  [],
  [],
  [{ t: 'tree = ' }, { c: 'nu', t: 'nu.With' }, { t: '(' }],
  [{ t: '    ' }, { c: 'nu', t: 'nu.v.presets.memory_navigator' }, { t: '(),' }],
  [{ t: '    body=' }, { c: 'nu', t: 'nu.v.Transaction' }, { t: '(Counter.value.store(0) >> Counter.value.store(Counter.value + 42))' }],
  [{ t: '    >> ' }, { c: 'nu', t: 'nu.v.Snapshot' }, { t: '(' }, { c: 'nu', t: 'nu.print' }, { t: '(Counter.value)),' }],
  [{ t: ')' }],
  [],
  [],
  [{ c: 'kw', t: 'if' }, { t: ' __name__ == ' }, { c: 'str', t: "'__main__'" }, { t: ':' }],
  [{ t: '    ' }, { c: 'nu', t: 'nu.run' }, { t: '(tree)' }],
];

export function NuCodeSample() {
  return (
    <div className={s.ide} role="figure" aria-label="Nu code sample: basic.py">
      <div className={s.ideTabs}>
        <div className={`${s.ideTab} ${s.ideTabActive}`}>
          <span className={s.ideTabDot} aria-hidden />
          basic.py
        </div>
        <div className={s.ideMeta}>python · {LINES.length} loc</div>
      </div>
      <div className={s.ideBody}>
        <div className={s.ideGutter} aria-hidden>
          {LINES.map((_, i) => (
            <div key={i} className={s.ideLineNo}>{i + 1}</div>
          ))}
        </div>
        <div className={s.ideCode}>
          {LINES.map((tokens, i) => (
            <div key={i} className={s.ideLine}>
              {tokens.length === 0 ? ' ' : tokens.map((tok, j) =>
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
