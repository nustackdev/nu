/**
 * The stack — apps stand on Nu stands on the interaction model.
 *
 * Three horizontal bands, bottom → top: the interaction model, then Nu
 * (with the fabrics list), then the apps row (`nulog`, `nuspace`, `more`).
 * Layer-cake cheatsheet — the substrate is right there under the apps.
 */
export function StackLayersSvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink = 'var(--nu-ink)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const mono = 'var(--font-mono)';

  return (
    <svg
      viewBox="0 0 480 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Three horizontal layers: the interaction model on the bottom, Nu with its fabrics in the middle, and the apps row on top."
    >
      {/* eyebrow */}
      <text
        x={22}
        y={26}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
      >
        the stack
      </text>

      {/* ============ apps band (top) ============ */}
      <g>
        <text
          x={22}
          y={62}
          style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.28em' }}
        >
          apps
        </text>
        {/* three app cells */}
        {[
          { x: 88, name: 'nulog', status: 'live', dim: false },
          { x: 224, name: 'nuspace', status: 'live', dim: false },
          { x: 360, name: 'more', status: 'tbd', dim: true },
        ].map((a) => (
          <g key={a.name}>
            <rect
              x={a.x}
              y={46}
              width={108}
              height={44}
              fill="none"
              stroke={a.dim ? ruleSoft : rule}
              strokeWidth={1}
              strokeDasharray={a.dim ? '3 3' : undefined}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={a.x + 14}
              y={68}
              style={{
                fill: a.dim ? ink3 : accent,
                fontFamily: mono,
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: '0.1em',
              }}
            >
              {a.name}
            </text>
            {a.dim ? (
              <text
                x={a.x + 92}
                y={68}
                textAnchor="end"
                style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}
              >
                {a.status}
              </text>
            ) : (
              <g>
                <circle cx={a.x + 78} cy={64} r={2.4} fill={accent2} />
                <text
                  x={a.x + 86}
                  y={68}
                  style={{ fill: accent2, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}
                >
                  {a.status}
                </text>
              </g>
            )}
            {/* mini glyph */}
            <line
              x1={a.x + 14}
              y1={80}
              x2={a.x + 94}
              y2={80}
              stroke={ruleSoft}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          </g>
        ))}
        {/* trunks from apps down to Nu band */}
        <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
          <line x1={142} y1={90} x2={142} y2={122} />
          <line x1={278} y1={90} x2={278} y2={122} />
          <line x1={414} y1={90} x2={414} y2={122} strokeDasharray="2 3" />
        </g>
      </g>

      {/* ============ Nu band (middle, accent wash) ============ */}
      <g>
        <text
          x={22}
          y={140}
          style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.28em' }}
        >
          nu
        </text>
        <rect
          x={64}
          y={122}
          width={392}
          height={72}
          fill={accentWash}
          stroke={accentLine}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={80}
          y={144}
          style={{
            fill: accent,
            fontFamily: mono,
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: '0.12em',
          }}
        >
          nu
        </text>
        <text
          x={106}
          y={144}
          style={{ fill: accent, fontFamily: mono, fontSize: 9.5, letterSpacing: '0.2em' }}
        >
          · the platform
        </text>
        {/* fabrics list as labeled cells */}
        {['shapes', 'mem', 'nudle', 'apps', 'lens'].map((f, i) => (
          <g key={f}>
            <rect
              x={80 + i * 76}
              y={158}
              width={68}
              height={24}
              fill="none"
              stroke={accentLine}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={80 + i * 76 + 34}
              y={174}
              textAnchor="middle"
              style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.16em' }}
            >
              {f}
            </text>
          </g>
        ))}
      </g>

      {/* connector from Nu down to interaction model band */}
      <line
        x1={260}
        y1={194}
        x2={260}
        y2={224}
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />

      {/* ============ interaction model band (bottom) ============ */}
      <g>
        <text
          x={22}
          y={244}
          style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.28em' }}
        >
          model
        </text>
        <rect
          x={64}
          y={224}
          width={392}
          height={64}
          fill="none"
          stroke={rule}
          strokeWidth={1}
          strokeDasharray="3 3"
          vectorEffect="non-scaling-stroke"
        />
        {/* small triad glyphs */}
        <g fill="none" stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke">
          {/* ref */}
          <circle cx={92} cy={256} r={5} />
          <rect x={148} y={251} width={10} height={10} />
          <rect x={192} y={245} width={22} height={22} strokeDasharray="3 3" />
        </g>
        <text x={92} y={280} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 9, letterSpacing: '0.2em' }}>
          ref
        </text>
        <text x={153} y={280} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 9, letterSpacing: '0.2em' }}>
          interaction
        </text>
        <text x={203} y={280} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 9, letterSpacing: '0.2em' }}>
          fabric
        </text>
        <text
          x={264}
          y={252}
          style={{ fill: ink, fontFamily: mono, fontSize: 11, letterSpacing: '0.14em' }}
        >
          the interaction model
        </text>
        <text
          x={264}
          y={268}
          style={{ fill: ink3, fontFamily: mono, fontSize: 9, letterSpacing: '0.16em' }}
        >
          the tiny theory nu implements
        </text>
      </g>

      {/* bottom caption */}
      <text
        x={472}
        y={306}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        apps on nu on the model
      </text>
    </svg>
  );
}
