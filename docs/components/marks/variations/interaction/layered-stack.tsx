const MONO = 'var(--font-mono)';

/**
 * Concept: the three-tier cheatsheet. Refs on top (addresses), Interactions
 * in the middle (what changes them), Fabrics on the bottom (worlds they
 * resolve inside). Each band shows its own glyphs and a small caption.
 */
export function LayeredStackSvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const rule = 'var(--nu-rule)';
  const rule2 = 'var(--nu-rule-2)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';

  const bandX = 20;
  const bandW = 420;
  const labelX = 32;

  return (
    <svg
      viewBox="0 0 460 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Three-layer cheatsheet: refs name, interactions change, fabrics execute."
      className={className}
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 444 8 L 452 8 L 452 16" />
        <path d="M 8 304 L 8 312 L 16 312" />
        <path d="M 444 312 L 452 312 L 452 304" />
      </g>

      {/* --- band 1: refs --- */}
      <g>
        <rect
          x={bandX}
          y={30}
          width={bandW}
          height={80}
          fill="none"
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={labelX}
          y={50}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.28em' }}
        >
          refs
        </text>
        <text
          x={labelX}
          y={66}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em' }}
        >
          name locations
        </text>
        {/* three ref circles + labels */}
        {[
          { x: 200, label: 'counter/value' },
          { x: 300, label: 'user/name' },
          { x: 390, label: 'orders/total' },
        ].map((r) => (
          <g key={r.label}>
            <circle
              cx={r.x}
              cy={70}
              r={4.5}
              fill="none"
              stroke={ink2}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={r.x}
              y={92}
              textAnchor="middle"
              style={{ fill: ink2, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.02em' }}
            >
              {r.label}
            </text>
          </g>
        ))}
      </g>

      {/* --- band 2: interactions (accent) --- */}
      <g>
        <rect
          x={bandX}
          y={120}
          width={bandW}
          height={80}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={labelX}
          y={140}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.28em' }}
        >
          interactions
        </text>
        <text
          x={labelX}
          y={156}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em' }}
        >
          change them
        </text>
        {/* three interaction squares with glyphs */}
        {[
          { x: 200, g: 'store(1)' },
          { x: 300, g: '+ 42' },
          { x: 390, g: '>>' },
        ].map((it) => (
          <g key={it.g}>
            <rect
              x={it.x - 30}
              y={156}
              width={60}
              height={28}
              rx={2}
              fill="none"
              stroke={accent}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={it.x}
              y={174}
              textAnchor="middle"
              style={{ fill: accent, fontFamily: MONO, fontSize: 11, fontWeight: 700 }}
            >
              {it.g}
            </text>
          </g>
        ))}
      </g>

      {/* --- band 3: fabrics --- */}
      <g>
        <rect
          x={bandX}
          y={210}
          width={bandW}
          height={80}
          fill="none"
          stroke={rule}
          strokeWidth={1}
          strokeDasharray="3 3"
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={labelX}
          y={230}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.28em' }}
        >
          fabrics
        </text>
        <text
          x={labelX}
          y={246}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em' }}
        >
          worlds they resolve in
        </text>
        {/* three fabric rectangles */}
        {[
          { x: 180, label: 'browser' },
          { x: 280, label: 'disk' },
          { x: 380, label: 'memory' },
        ].map((f) => (
          <g key={f.label}>
            <rect
              x={f.x - 30}
              y={246}
              width={60}
              height={30}
              rx={2}
              fill="none"
              stroke={rule}
              strokeWidth={1}
              strokeDasharray="2 2"
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={f.x}
              y={266}
              textAnchor="middle"
              style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.16em' }}
            >
              {f.label}
            </text>
          </g>
        ))}
      </g>

      {/* caption */}
      <text
        x={452}
        y={304}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        refs · interactions · fabrics
      </text>
    </svg>
  );
}
