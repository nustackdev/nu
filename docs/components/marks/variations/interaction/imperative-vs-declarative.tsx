const MONO = 'var(--font-mono)';

/**
 * Concept: side-by-side mirror. Left column — three ink-3 imperative snippets,
 * each targeting a different substrate, disconnected. Right column — one
 * declarative Nu Interaction that covers all three. The visual asks
 * "which side do you want to write?"
 */
export function ImperativeVsDeclarativeSvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const bg = 'var(--color-fd-background)';

  const leftX = 22;
  const rightX = 260;
  const colW = 200;
  const topY = 62;

  return (
    <svg
      viewBox="0 0 480 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Three imperative snippets vs one Nu interaction that covers all substrates."
      className={className}
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 464 8 L 472 8 L 472 16" />
        <path d="M 8 304 L 8 312 L 16 312" />
        <path d="M 464 312 L 472 312 L 472 304" />
      </g>

      {/* column headings */}
      <text
        x={leftX}
        y={38}
        style={{ fill: ink3, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.28em' }}
      >
        today
      </text>
      <text
        x={leftX}
        y={52}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em' }}
      >
        one api per fabric
      </text>

      <text
        x={rightX}
        y={38}
        style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.28em' }}
      >
        with nu
      </text>
      <text
        x={rightX}
        y={52}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em' }}
      >
        one interaction, all fabrics
      </text>

      {/* left column — 3 imperative snippets, each with a fabric tag */}
      {[
        { y: topY, tag: 'browser', code: 'input.value = 1' },
        { y: topY + 70, tag: 'disk', code: 'db.put("count", 1)' },
        { y: topY + 140, tag: 'memory', code: 'd["count"] = 1' },
      ].map((r) => (
        <g key={r.tag}>
          <rect
            x={leftX}
            y={r.y}
            width={colW}
            height={54}
            rx={2}
            fill="none"
            stroke={rule}
            strokeWidth={1}
            strokeDasharray="3 3"
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={leftX + 10}
            y={r.y + 16}
            style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
          >
            {r.tag}
          </text>
          <text
            x={leftX + 10}
            y={r.y + 38}
            style={{ fill: ink3, fontFamily: MONO, fontSize: 11, letterSpacing: '0.02em', textDecoration: 'line-through' }}
          >
            {r.code}
          </text>
        </g>
      ))}

      {/* vertical seam between columns */}
      <line
        x1={232}
        y1={44}
        x2={232}
        y2={276}
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={241}
        y={162}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        vs
      </text>

      {/* right column — one Nu interaction, tall accent panel */}
      <g>
        <rect
          x={rightX}
          y={topY}
          width={colW}
          height={194}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        {/* accent corner ticks */}
        <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke">
          <path d={`M ${rightX} ${topY + 8} L ${rightX} ${topY} L ${rightX + 8} ${topY}`} />
          <path d={`M ${rightX + colW - 8} ${topY} L ${rightX + colW} ${topY} L ${rightX + colW} ${topY + 8}`} />
          <path d={`M ${rightX} ${topY + 194 - 8} L ${rightX} ${topY + 194} L ${rightX + 8} ${topY + 194}`} />
          <path d={`M ${rightX + colW - 8} ${topY + 194} L ${rightX + colW} ${topY + 194} L ${rightX + colW} ${topY + 194 - 8}`} />
        </g>
        <text
          x={rightX + colW / 2}
          y={topY + 32}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
        >
          interaction
        </text>
        <text
          x={rightX + colW / 2}
          y={topY + 90}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 15, fontWeight: 700, letterSpacing: '0.02em' }}
        >
          store(counter, 1)
        </text>
        <line
          x1={rightX + 20}
          y1={topY + 108}
          x2={rightX + colW - 20}
          y2={topY + 108}
          stroke={accentLine}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={rightX + colW / 2}
          y={topY + 132}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabrics
        </text>
        <text
          x={rightX + colW / 2}
          y={topY + 156}
          textAnchor="middle"
          style={{ fill: ink2, fontFamily: MONO, fontSize: 11, letterSpacing: '0.16em' }}
        >
          browser · disk · memory
        </text>
        <text
          x={rightX + colW / 2}
          y={topY + 180}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          same tree, any fabric
        </text>
      </g>

      {/* caption */}
      <text
        x={472}
        y={304}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        imperative vs declarative
      </text>
    </svg>
  );
}
