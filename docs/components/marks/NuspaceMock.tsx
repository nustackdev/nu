import s from './marks.module.css';

/**
 * nuspace — running app mock.
 *
 * A workspace tab (nudle-style) with a browser chrome, tab strip, sidebar,
 * and a notion-like page body. Inline "ref" tags glow in accent — showing
 * that values in the page are live Nu Refs, not plain text.
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

  const tabs = ['notes', 'metrics', 'runs'];
  const sidebarItems = ['welcome', 'q3 plan', 'metrics', 'refs'];

  return (
    <svg
      viewBox="0 0 480 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="nuspace running: browser chrome, tab strip, sidebar, and a workspace page with inline Nu Ref tags — values in the doc are live Refs, not plain text."
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

      {/* tab strip */}
      <line x1={16} y1={68} x2={464} y2={68} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
      {tabs.map((t, i) => {
        const x = 30 + i * 78;
        const active = i === 1;
        return (
          <g key={t}>
            {active && (
              <rect
                x={x - 8}
                y={50}
                width={64}
                height={18}
                fill={bg}
                stroke={rule}
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
            )}
            <text
              x={x}
              y={63}
              style={{
                fill: active ? ink : ink3,
                fontFamily: mono,
                fontSize: 10,
                letterSpacing: '0.14em',
                fontWeight: active ? 700 : 400,
              }}
            >
              {t}
            </text>
          </g>
        );
      })}

      {/* title band */}
      <text
        x={30}
        y={92}
        style={{ fill: ink3, fontFamily: mono, fontSize: 9.5, letterSpacing: '0.24em' }}
      >
        app
      </text>
      <text
        x={30}
        y={116}
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
      {/* live pill */}
      <g>
        <circle cx={396} cy={106} r={3} fill={accent2} className={s.blink} />
        <text
          x={404}
          y={110}
          style={{ fill: accent2, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
        >
          live
        </text>
      </g>

      {/* header rule */}
      <line x1={30} y1={132} x2={450} y2={132} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* ============ LEFT — sidebar ============ */}
      <text
        x={30}
        y={148}
        style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}
      >
        pages
      </text>
      {sidebarItems.map((item, i) => {
        const y = 168 + i * 20;
        const active = i === 1;
        return (
          <g key={item}>
            {active && (
              <rect
                x={26}
                y={y - 12}
                width={94}
                height={18}
                fill={accentWash}
                stroke={accentLine}
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
            )}
            <text
              x={32}
              y={y}
              style={{
                fill: active ? accent : ink3,
                fontFamily: mono,
                fontSize: 10,
                letterSpacing: '0.02em',
              }}
            >
              {item}
            </text>
          </g>
        );
      })}
      {/* sidebar divider */}
      <line x1={130} y1={144} x2={130} y2={264} stroke={ruleSoft} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* ============ RIGHT — page body ============ */}
      {/* page title */}
      <text
        x={148}
        y={158}
        style={{ fill: ink, fontFamily: mono, fontSize: 13, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        Q3 plan
      </text>
      {/* meta line */}
      <text
        x={148}
        y={174}
        style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.14em' }}
      >
        owner:
      </text>
      {/* inline ref pill — owner */}
      <rect
        x={185}
        y={165}
        width={54}
        height={12}
        rx={2}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={0.8}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={190}
        y={174}
        style={{ fill: accent, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.06em', fontWeight: 700 }}
      >
        gor@nu
      </text>

      {/* body paragraph — one line with inline refs */}
      <text
        x={148}
        y={196}
        style={{ fill: ink2, fontFamily: mono, fontSize: 10.5, letterSpacing: '0.02em' }}
      >
        target:
      </text>
      {/* inline ref pill — target metric */}
      <rect
        x={196}
        y={187}
        width={44}
        height={14}
        rx={2}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={0.8}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={202}
        y={198}
        style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em', fontWeight: 700 }}
      >
        $12.4k
      </text>
      <text
        x={246}
        y={196}
        style={{ fill: ink2, fontFamily: mono, fontSize: 10.5, letterSpacing: '0.02em' }}
      >
        · deadline:
      </text>
      <rect
        x={317}
        y={187}
        width={62}
        height={14}
        rx={2}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={0.8}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={323}
        y={198}
        style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em', fontWeight: 700 }}
      >
        oct 15
      </text>

      {/* two-column KPI block */}
      <g>
        {/* left kpi */}
        <rect
          x={148}
          y={214}
          width={140}
          height={38}
          fill="none"
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={158}
          y={228}
          style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          revenue
        </text>
        <text
          x={158}
          y={246}
          style={{ fill: accent, fontFamily: mono, fontSize: 15, fontWeight: 700, letterSpacing: '0.02em' }}
        >
          $8,240
        </text>
        {/* right kpi */}
        <rect
          x={296}
          y={214}
          width={140}
          height={38}
          fill="none"
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={306}
          y={228}
          style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          users
        </text>
        <text
          x={306}
          y={246}
          style={{ fill: accent, fontFamily: mono, fontSize: 15, fontWeight: 700, letterSpacing: '0.02em' }}
        >
          1,204
        </text>
      </g>

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
      <text
        x={450}
        y={292}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        one of the apps
      </text>
    </svg>
  );
}
