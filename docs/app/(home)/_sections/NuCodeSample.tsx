import s from './NuCodeSample.module.css';

/**
 * A small Nu program shown in §2 — hand-highlighted with CSS classes for
 * kw / nu / str / cmt. Deliberately tiny so it reads as an example, not a
 * feature list.
 */
export function NuCodeSample() {
  return (
    <div className={s.codeShell}>
      <pre className={s.codeBlock}>
<span className={s.cmt}>{'"""Basic Nu bracket-tree app: mem preset + tiny compute."""'}</span>
{'\n\n'}
<span className={s.kw}>from</span>{' __future__ '}<span className={s.kw}>import</span>{' annotations\n\n'}
<span className={s.kw}>import</span>{' '}<span className={s.nu}>nu</span>{'\n\n\n'}
<span className={s.kw}>class</span>{' Counter('}<span className={s.nu}>nu.Shape</span>{'):\n    value: '}<span className={s.nu}>nu.v.IntRef</span>{'\n\n\n'}
{'tree = '}<span className={s.nu}>nu.With</span>{'(\n    '}<span className={s.nu}>nu.v.presets.memory_navigator</span>{'(),\n    body='}<span className={s.nu}>nu.v.Transaction</span>{'(Counter.value.store(0) >> Counter.value.store(Counter.value + 42))\n    >> '}<span className={s.nu}>nu.v.Snapshot</span>{'('}<span className={s.nu}>nu.print</span>{'(Counter.value)),\n)\n\n\n'}
<span className={s.kw}>if</span>{' __name__ == '}<span className={s.str}>{"'__main__'"}</span>{':\n    '}<span className={s.nu}>nu.run</span>{'(tree)\n'}
      </pre>
      <div className={s.codeCaption}>examples/basic.py · 20 loc</div>
    </div>
  );
}
