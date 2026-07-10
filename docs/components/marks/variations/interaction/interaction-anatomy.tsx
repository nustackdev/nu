const MONO = 'var(--font-mono)';

/**
 * Concept: anatomy of an Interaction expression. `Add(counter, 1)` is
 * dissected with three callouts — operator, target ref, and argument.
 * A small legend on the right pins the model vocabulary.
 */
export function InteractionAnatomySvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';

  // Central expression: `Add(counter, 1)`
  // Split into positions we can callout.
  // x-anchors: Add ≈ 132, counter ≈ 208, 1 ≈ 288
  const exprY = 150;

  return (
    <svg
      viewBox="0 0 460 300"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Anatomy of an interaction: Add is the operator, counter is the ref, 1 is the value."
      className={className}
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 444 8 L 452 8 L 452 16" />
        <path d="M 8 284 L 8 292 L 16 292" />
        <path d="M 444 292 L 452 292 L 452 284" />
      </g>

      {/* faint accent band behind the expression */}
      <rect
        x={40}
        y={exprY - 32}
        width={280}
        height={60}
        rx={4}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />

      {/* the expression */}
      <text
        x={180}
        y={exprY + 8}
        textAnchor="middle"
        style={{ fill: ink, fontFamily: MONO, fontSize: 26, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        <tspan fill={accent}>Add</tspan>
        <tspan fill={ink3}>(</tspan>
        <tspan fill={ink}>counter</tspan>
        <tspan fill={ink3}>, </tspan>
        <tspan fill={ink}>1</tspan>
        <tspan fill={ink3}>)</tspan>
      </text>

      {/* callouts */}
      {/* Add — operator (top-left) */}
      <g>
        <line x1={120} y1={exprY - 12} x2={120} y2={72} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={120} y1={72} x2={80} y2={72} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={74}
          y={68}
          textAnchor="end"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          operator
        </text>
        <text
          x={74}
          y={82}
          textAnchor="end"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          the interaction
        </text>
      </g>

      {/* counter — target ref (top-right) */}
      <g>
        <line x1={200} y1={exprY - 12} x2={200} y2={64} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={200} y1={64} x2={280} y2={64} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <circle cx={200} cy={exprY - 12} r={2} fill={ink2} />
        <text
          x={286}
          y={60}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          ref
        </text>
        <text
          x={286}
          y={74}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          address it acts on
        </text>
      </g>

      {/* 1 — value (bottom-right) */}
      <g>
        <line x1={266} y1={exprY + 16} x2={266} y2={240} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={266} y1={240} x2={340} y2={240} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={346}
          y={236}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          arg
        </text>
        <text
          x={346}
          y={250}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          value or ref
        </text>
      </g>

      {/* right-side legend */}
      <g>
        <line
          x1={370}
          y1={130}
          x2={370}
          y2={200}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={378}
          y={124}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          legend
        </text>
        {/* ref */}
        <circle cx={382} cy={148} r={3.5} fill="none" stroke={ink2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={392}
          y={151}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.16em' }}
        >
          ref
        </text>
        {/* interaction */}
        <rect x={378} y={164} width={9} height={9} fill={accentWash} stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={392}
          y={172}
          style={{ fill: accent, fontFamily: MONO, fontSize: 10, letterSpacing: '0.16em' }}
        >
          interaction
        </text>
        {/* fabric */}
        <rect x={378} y={184} width={9} height={9} fill="none" stroke={ink3} strokeWidth={1} strokeDasharray="2 2" vectorEffect="non-scaling-stroke" />
        <text
          x={392}
          y={193}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.16em' }}
        >
          fabric
        </text>
      </g>

      {/* caption */}
      <text
        x={452}
        y={284}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        anatomy of an interaction
      </text>
    </svg>
  );
}
