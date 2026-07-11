import s from './marks.module.css';

/**
 * Apps sit on the Nu substrate.
 *
 * A wide purple-wash substrate bar labeled `nu` runs across the bottom.
 * Three app cells (`nulog`, `nuspace`, `more`) rest on it, each rooted
 * with a hairline trunk into the substrate. Cells carry a tagline and a
 * `live` pill so the viewer instantly reads "these are the apps."
 */
export function AppShelfSvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const mono = 'var(--font-mono)';

  const cells: Array<{
    x: number;
    name: string;
    tagline: string;
    status: 'live' | 'tbd';
    dim?: boolean;
  }> = [
    { x: 32, name: 'nulog', tagline: 'logs as refs', status: 'live' },
    { x: 176, name: 'nuspace', tagline: 'workspace on nudle', status: 'live' },
    { x: 320, name: 'more', tagline: 'coming', status: 'tbd', dim: true },
  ];

  return (
    <svg
      viewBox="0 0 480 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Three app cells — nulog, nuspace, more — resting on the Nu substrate, each rooted with a hairline trunk."
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 464 8 L 472 8 L 472 16" />
        <path d="M 8 304 L 8 312 L 16 312" />
        <path d="M 464 312 L 472 312 L 472 304" />
      </g>

      {/* top eyebrow */}
      <text
        x={22}
        y={30}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
      >
        apps on nu
      </text>

      {/* three cells */}
      {cells.map((c) => {
        const cx = c.x + 64;
        return (
          <g key={c.name}>
            {/* cell frame */}
            <rect
              x={c.x}
              y={54}
              width={128}
              height={148}
              fill="none"
              stroke={c.dim ? ruleSoft : rule}
              strokeWidth={1}
              strokeDasharray={c.dim ? '3 3' : undefined}
              vectorEffect="non-scaling-stroke"
            />
            {/* status pill top-right */}
            <g>
              <circle
                cx={c.x + 108}
                cy={68}
                r={2.4}
                fill={c.dim ? ink4 : accent2}
                className={c.dim ? undefined : s.blink}
              />
              <text
                x={c.x + 114}
                y={71}
                style={{
                  fill: c.dim ? ink4 : accent2,
                  fontFamily: mono,
                  fontSize: 8.5,
                  letterSpacing: '0.24em',
                }}
              >
                {c.status}
              </text>
            </g>

            {/* app name — brand accent (dimmed for placeholder) */}
            <text
              x={cx}
              y={104}
              textAnchor="middle"
              style={{
                fill: c.dim ? ink3 : accent,
                fontFamily: mono,
                fontSize: 15,
                fontWeight: 700,
                letterSpacing: '0.12em',
              }}
            >
              {c.name}
            </text>

            {/* tagline */}
            <text
              x={cx}
              y={126}
              textAnchor="middle"
              style={{
                fill: c.dim ? ink4 : ink3,
                fontFamily: mono,
                fontSize: 9.5,
                letterSpacing: '0.18em',
              }}
            >
              {c.tagline}
            </text>

            {/* mini glyph row — content preview */}
            {!c.dim && c.name === 'nulog' && (
              <g>
                {/* three log rows */}
                {[0, 1, 2].map((i) => (
                  <g key={i}>
                    <rect
                      x={c.x + 20}
                      y={148 + i * 14}
                      width={6}
                      height={6}
                      fill="none"
                      stroke={ink3}
                      strokeWidth={1}
                      vectorEffect="non-scaling-stroke"
                    />
                    <line
                      x1={c.x + 32}
                      y1={151 + i * 14}
                      x2={c.x + 108}
                      y2={151 + i * 14}
                      stroke={ruleSoft}
                      strokeWidth={1}
                      vectorEffect="non-scaling-stroke"
                    />
                  </g>
                ))}
              </g>
            )}
            {!c.dim && c.name === 'nuspace' && (
              <g>
                {/* mini browser with 3 tabs */}
                <rect
                  x={c.x + 18}
                  y={148}
                  width={92}
                  height={38}
                  fill="none"
                  stroke={rule}
                  strokeWidth={1}
                  vectorEffect="non-scaling-stroke"
                />
                <line
                  x1={c.x + 18}
                  y1={158}
                  x2={c.x + 110}
                  y2={158}
                  stroke={ruleSoft}
                  strokeWidth={1}
                  vectorEffect="non-scaling-stroke"
                />
                {[0, 1, 2].map((i) => (
                  <circle
                    key={i}
                    cx={c.x + 24 + i * 5}
                    cy={153}
                    r={1.4}
                    fill={ink3}
                    opacity={0.6}
                  />
                ))}
                <text
                  x={c.x + 64}
                  y={175}
                  textAnchor="middle"
                  style={{
                    fill: ink3,
                    fontFamily: mono,
                    fontSize: 8.5,
                    letterSpacing: '0.18em',
                  }}
                >
                  tabs · apps
                </text>
              </g>
            )}
            {c.dim && (
              <text
                x={cx}
                y={172}
                textAnchor="middle"
                style={{
                  fill: ink4,
                  fontFamily: mono,
                  fontSize: 22,
                  letterSpacing: '0.02em',
                }}
              >
                ·
              </text>
            )}

            {/* trunk down into substrate */}
            <line
              x1={cx}
              y1={202}
              x2={cx}
              y2={232}
              stroke={c.dim ? ruleSoft : rule}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
              strokeDasharray={c.dim ? '2 3' : undefined}
            />
            {/* snap notch where trunk meets substrate */}
            <line
              x1={cx - 4}
              y1={232}
              x2={cx + 4}
              y2={232}
              stroke={c.dim ? ink4 : ink3}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          </g>
        );
      })}

      {/* ===== substrate ===== */}
      <rect
        x={20}
        y={232}
        width={440}
        height={56}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        strokeDasharray="3 3"
        vectorEffect="non-scaling-stroke"
      />
      {/* substrate inner corner ticks */}
      <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke" opacity={0.65}>
        <path d="M 20 242 L 20 232 L 30 232" />
        <path d="M 450 232 L 460 232 L 460 242" />
        <path d="M 20 278 L 20 288 L 30 288" />
        <path d="M 450 288 L 460 288 L 460 278" />
      </g>
      {/* nu wordmark */}
      <text
        x={40}
        y={266}
        style={{
          fill: accent,
          fontFamily: mono,
          fontSize: 15,
          fontWeight: 700,
          letterSpacing: '0.14em',
        }}
      >
        nu
      </text>
      {/* fabrics list right-aligned */}
      <text
        x={452}
        y={266}
        textAnchor="end"
        style={{
          fill: ink3,
          fontFamily: mono,
          fontSize: 9.5,
          letterSpacing: '0.22em',
        }}
      >
        shapes · mem · nudle · apps · lens
      </text>
      {/* substrate meta */}
      <text
        x={80}
        y={266}
        style={{
          fill: ink4,
          fontFamily: mono,
          fontSize: 9,
          letterSpacing: '0.24em',
        }}
      >
        substrate
      </text>

      {/* bottom caption */}
      <text
        x={472}
        y={306}
        textAnchor="end"
        style={{
          fill: ink4,
          fontFamily: mono,
          fontSize: 9,
          letterSpacing: '0.24em',
        }}
      >
        apps · rooted in nu
      </text>
    </svg>
  );
}
