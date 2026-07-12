import s from './marks.module.css';

/**
 * nuspace — workspace mock, calm cut.
 *
 * Browser chrome, sidebar with two pages, page body with one live Ref pill
 * and a footer strip identifying the substrate. Kept deliberately quiet so
 * it reads as one glance, not a screenshot.
 */
export function NuspaceMockSvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const mono = 'var(--font-mono)';
  const bg = 'var(--color-fd-background)';

  return (
    <svg
      viewBox="0 0 480 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="nuspace running: browser chrome, sidebar, a workspace page with one live Nu Ref pill in the body."
    >
      {/* browser window */}
      <rect
        x={16}
        y={16}
        width={448}
        height={288}
        fill={bg}
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {/* chrome bar */}
      <line x1={16} y1={44} x2={464} y2={44} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
      {[0, 1, 2].map((i) => (
        <circle key={i} cx={30 + i * 10} cy={30} r={2.6} fill={ink4} />
      ))}
      {/* address bar */}
      <rect
        x={80}
        y={22}
        width={368}
        height={16}
        fill="var(--nu-code-bg-2, transparent)"
        stroke={ruleSoft}
        strokeWidth={0.5}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={90}
        y={34}
        style={{ fill: ink3, fontFamily: mono, fontSize: 9.5, letterSpacing: '0.04em' }}
      >
        nu://nuspace/q3-plan
      </text>

      {/* app name + live pill */}
      <text
        x={30}
        y={78}
        style={{
          fill: accent,
          fontFamily: mono,
          fontSize: 20,
          fontWeight: 700,
          letterSpacing: '0.08em',
        }}
      >
        nuspace
      </text>
      <circle cx={396} cy={72} r={3} fill={accent2} className={s.blink} />
      <text
        x={404}
        y={76}
        style={{ fill: accent2, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
      >
        live
      </text>

      {/* header rule */}
      <line x1={30} y1={98} x2={450} y2={98} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* sidebar */}
      <text
        x={30}
        y={122}
        style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}
      >
        pages
      </text>
      <rect
        x={26}
        y={136}
        width={94}
        height={18}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={32}
        y={148}
        style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em' }}
      >
        q3 plan
      </text>
      <text
        x={32}
        y={172}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em' }}
      >
        refs
      </text>
      {/* sidebar divider */}
      <line x1={130} y1={118} x2={130} y2={264} stroke={ruleSoft} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* page body */}
      <text
        x={148}
        y={140}
        style={{ fill: ink, fontFamily: mono, fontSize: 14, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        Q3 plan
      </text>
      <text
        x={148}
        y={176}
        style={{ fill: ink2, fontFamily: mono, fontSize: 11, letterSpacing: '0.02em' }}
      >
        target:
      </text>
      <rect
        x={196}
        y={166}
        width={54}
        height={16}
        rx={2}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={0.8}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={203}
        y={178}
        style={{ fill: accent, fontFamily: mono, fontSize: 10.5, letterSpacing: '0.02em', fontWeight: 700 }}
      >
        $12.4k
      </text>

      {/* footer strip — wash band */}
      <rect
        x={16}
        y={272}
        width={448}
        height={32}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={30}
        y={292}
        style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.22em' }}
      >
        built on nu · shape=Page · fabric=nudle
      </text>
    </svg>
  );
}
