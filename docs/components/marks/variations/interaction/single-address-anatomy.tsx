const MONO = 'var(--font-mono)';

/**
 * Concept: anatomy of a single Ref. One central address (counter/value)
 * with four callouts pointing at what it is, what it holds now, what
 * interaction acts on it, and which fabric it resolves inside.
 */
export function SingleAddressAnatomySvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';

  const cx = 230;
  const cy = 160;

  return (
    <svg
      viewBox="0 0 460 300"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Anatomy of a Ref: address, current value, interaction, and fabric it lives in."
      className={className}
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 444 8 L 452 8 L 452 16" />
        <path d="M 8 284 L 8 292 L 16 292" />
        <path d="M 444 292 L 452 292 L 452 284" />
      </g>

      {/* central Ref pill */}
      <g>
        <rect
          x={cx - 96}
          y={cy - 20}
          width={192}
          height={40}
          rx={20}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={cx}
          y={cy + 6}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 14, fontWeight: 700, letterSpacing: '0.02em' }}
        >
          counter/value
        </text>
      </g>

      {/* top: address callout */}
      <g>
        <line
          x1={cx}
          y1={cy - 20}
          x2={cx}
          y2={68}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <line
          x1={cx}
          y1={68}
          x2={cx - 90}
          y2={68}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <circle cx={cx} cy={cy - 20} r={2} fill={accent} />
        <text
          x={cx - 96}
          y={64}
          textAnchor="end"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          ref
        </text>
        <text
          x={cx - 96}
          y={78}
          textAnchor="end"
          style={{ fill: ink2, fontFamily: MONO, fontSize: 11, letterSpacing: '0.02em' }}
        >
          address, not value
        </text>
      </g>

      {/* right: current value */}
      <g>
        <line
          x1={cx + 96}
          y1={cy}
          x2={cx + 148}
          y2={cy}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={cx + 154}
          y={cy - 4}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          current
        </text>
        <text
          x={cx + 154}
          y={cy + 12}
          style={{ fill: ink, fontFamily: MONO, fontSize: 16, fontWeight: 700 }}
        >
          0
        </text>
      </g>

      {/* left: interaction */}
      <g>
        <line
          x1={cx - 96}
          y1={cy}
          x2={cx - 148}
          y2={cy}
          stroke={accent}
          strokeWidth={1.25}
          strokeDasharray="4 3"
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${cx - 96},${cy - 4} ${cx - 88},${cy} ${cx - 96},${cy + 4}`}
          fill={accent}
        />
        <text
          x={cx - 154}
          y={cy - 4}
          textAnchor="end"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          interaction
        </text>
        <text
          x={cx - 154}
          y={cy + 12}
          textAnchor="end"
          style={{ fill: accent, fontFamily: MONO, fontSize: 12, fontWeight: 700 }}
        >
          store(1)
        </text>
      </g>

      {/* bottom: fabric */}
      <g>
        <line
          x1={cx}
          y1={cy + 20}
          x2={cx}
          y2={236}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <rect
          x={cx - 100}
          y={236}
          width={200}
          height={34}
          rx={2}
          fill="none"
          stroke={rule}
          strokeWidth={1}
          strokeDasharray="3 3"
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={cx}
          y={252}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric
        </text>
        <text
          x={cx}
          y={266}
          textAnchor="middle"
          style={{ fill: ink2, fontFamily: MONO, fontSize: 11, letterSpacing: '0.06em' }}
        >
          browser · disk · memory
        </text>
      </g>

      {/* caption */}
      <text
        x={452}
        y={284}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        anatomy of a ref
      </text>
    </svg>
  );
}
