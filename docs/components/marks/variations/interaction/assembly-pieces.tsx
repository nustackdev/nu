const MONO = 'var(--font-mono)';

/**
 * Concept: three snap-together pieces on the left — ref, interaction,
 * fabric — combine on the right into a working assembly with a concrete
 * value flowing through it. Snap notches hint the "assemble, not write"
 * theme; the assembled block shows the value going 0 → 1.
 */
export function AssemblyPiecesSvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const bg = 'var(--color-fd-background)';

  // pieces column
  const pcX = 40;
  const pcW = 130;
  return (
    <svg
      viewBox="0 0 480 300"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Ref, interaction, and fabric snap together into one working system that moves a value from 0 to 1."
      className={className}
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 464 8 L 472 8 L 472 16" />
        <path d="M 8 284 L 8 292 L 16 292" />
        <path d="M 464 292 L 472 292 L 472 284" />
      </g>

      {/* headings */}
      <text
        x={pcX}
        y={40}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
      >
        pieces
      </text>
      <text
        x={470}
        y={40}
        textAnchor="end"
        style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
      >
        assembled
      </text>

      {/* Piece 1 — ref */}
      <g>
        <rect
          x={pcX}
          y={60}
          width={pcW}
          height={54}
          rx={3}
          fill={bg}
          stroke={ink3}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        {/* snap notches */}
        <line x1={pcX + pcW} y1={78} x2={pcX + pcW + 6} y2={78} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={pcX + pcW} y1={96} x2={pcX + pcW + 6} y2={96} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <circle cx={pcX + 22} cy={87} r={5} fill="none" stroke={ink2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={pcX + 38}
          y={82}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          ref
        </text>
        <text
          x={pcX + 38}
          y={96}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          counter/value
        </text>
      </g>

      {/* Piece 2 — interaction (accent) */}
      <g>
        <rect
          x={pcX}
          y={125}
          width={pcW}
          height={54}
          rx={3}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        <line x1={pcX + pcW} y1={143} x2={pcX + pcW + 6} y2={143} stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={pcX + pcW} y1={161} x2={pcX + pcW + 6} y2={161} stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <rect x={pcX + 14} y={139} width={18} height={18} fill={accentWash} stroke={accent} strokeWidth={1.25} vectorEffect="non-scaling-stroke" />
        <text
          x={pcX + 38}
          y={147}
          style={{ fill: accent, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          interaction
        </text>
        <text
          x={pcX + 38}
          y={161}
          style={{ fill: accent, fontFamily: MONO, fontSize: 10, fontWeight: 700, letterSpacing: '0.02em' }}
        >
          store(1)
        </text>
      </g>

      {/* Piece 3 — fabric */}
      <g>
        <rect
          x={pcX}
          y={190}
          width={pcW}
          height={54}
          rx={3}
          fill={bg}
          stroke={ink3}
          strokeWidth={1}
          strokeDasharray="3 3"
          vectorEffect="non-scaling-stroke"
        />
        <line x1={pcX + pcW} y1={208} x2={pcX + pcW + 6} y2={208} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={pcX + pcW} y1={226} x2={pcX + pcW + 6} y2={226} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <rect x={pcX + 14} y={204} width={18} height={18} fill="none" stroke={ink3} strokeWidth={1} strokeDasharray="2 2" vectorEffect="non-scaling-stroke" />
        <text
          x={pcX + 38}
          y={212}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          fabric
        </text>
        <text
          x={pcX + 38}
          y={226}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          browser tab
        </text>
      </g>

      {/* arrow between pieces and assembled */}
      <g>
        <line
          x1={pcX + pcW + 20}
          y1={152}
          x2={276}
          y2={152}
          stroke={accent}
          strokeWidth={1.25}
          strokeDasharray="4 3"
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${276},${147} ${284},${152} ${276},${157}`}
          fill={accent}
        />
        <text
          x={(pcX + pcW + 20 + 276) / 2}
          y={144}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          nu.run
        </text>
      </g>

      {/* assembled — a working system */}
      <g>
        <rect
          x={290}
          y={60}
          width={170}
          height={184}
          rx={4}
          fill={bg}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        {/* corner ticks inside */}
        <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke">
          <path d="M 290 68 L 290 60 L 298 60" />
          <path d="M 452 60 L 460 60 L 460 68" />
          <path d="M 290 236 L 290 244 L 298 244" />
          <path d="M 452 244 L 460 244 L 460 236" />
        </g>
        {/* browser chrome */}
        <line x1={290} y1={82} x2={460} y2={82} stroke={accentLine} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <circle cx={299} cy={72} r={1.8} fill={accent} opacity={0.6} />
        <circle cx={306} cy={72} r={1.8} fill={accent} opacity={0.6} />
        <circle cx={313} cy={72} r={1.8} fill={accent} opacity={0.6} />
        {/* content */}
        <text
          x={375}
          y={122}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
        >
          counter
        </text>
        {/* before */}
        <text
          x={330}
          y={172}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 26, fontWeight: 700, opacity: 0.55 }}
        >
          0
        </text>
        {/* arrow */}
        <line x1={344} y1={162} x2={396} y2={162} stroke={accent} strokeWidth={1} strokeDasharray="3 2" vectorEffect="non-scaling-stroke" />
        <polygon points="396,158 402,162 396,166" fill={accent} />
        {/* after */}
        <text
          x={420}
          y={172}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 26, fontWeight: 700 }}
        >
          1
        </text>
        <text
          x={375}
          y={222}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          working system
        </text>
      </g>

      {/* caption */}
      <text
        x={472}
        y={284}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        assemble, not write
      </text>
    </svg>
  );
}
