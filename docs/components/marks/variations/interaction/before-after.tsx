import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: an Interaction is a Context transition. Two panels — V0 and V1 —
 * with the interaction `store(1)` labelled on the arrow between them.
 * Concrete values (counter: 0 → 1), MemViz-style paneled framing.
 */
export function BeforeAfterSvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accent2 = 'var(--nu-accent-2)';
  const accentLine = 'var(--nu-accent-line)';
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const bg = 'var(--color-fd-background)';

  const panelY = 40;
  const panelH = 170;

  return (
    <svg
      viewBox="0 0 500 260"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="An interaction transitions the Context: counter 0 becomes counter 1 via store(1)."
      className={className}
    >
      {/* left panel — context v0 */}
      <g>
        <rect
          x={16}
          y={panelY}
          width={180}
          height={panelH}
          rx={4}
          fill={bg}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={30}
          y={panelY + 24}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          context v0
        </text>
        <text
          x={106}
          y={panelY + 70}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          counter
        </text>
        <text
          x={106}
          y={panelY + 118}
          textAnchor="middle"
          style={{ fill: ink2, fontFamily: MONO, fontSize: 42, fontWeight: 700, opacity: 0.55 }}
        >
          0
        </text>
        <text
          x={106}
          y={panelY + 148}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          {'{ counter: 0 }'}
        </text>
      </g>

      {/* the arrow — interaction */}
      <g>
        <text
          x={250}
          y={panelY + 44}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 10, letterSpacing: '0.24em' }}
        >
          interaction
        </text>
        <line
          x1={200}
          y1={panelY + 84}
          x2={296}
          y2={panelY + 84}
          stroke={accent}
          strokeWidth={1.25}
          strokeDasharray="4 3"
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${296},${panelY + 79} ${304},${panelY + 84} ${296},${panelY + 89}`}
          fill={accent}
        />
        <text
          x={250}
          y={panelY + 74}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 13, fontWeight: 700 }}
        >
          store(1)
        </text>
        <text
          x={250}
          y={panelY + 108}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
        >
          nu.run
        </text>
      </g>

      {/* right panel — context v1 (accent) */}
      <g>
        <rect
          x={304}
          y={panelY}
          width={180}
          height={panelH}
          rx={4}
          fill={bg}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        {/* accent corner ticks (inner) */}
        <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke">
          <path d={`M 304 ${panelY + 8} L 304 ${panelY} L 312 ${panelY}`} />
          <path d={`M 476 ${panelY} L 484 ${panelY} L 484 ${panelY + 8}`} />
          <path d={`M 304 ${panelY + panelH - 8} L 304 ${panelY + panelH} L 312 ${panelY + panelH}`} />
          <path d={`M 476 ${panelY + panelH} L 484 ${panelY + panelH} L 484 ${panelY + panelH - 8}`} />
        </g>
        <text
          x={318}
          y={panelY + 24}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          context v1
        </text>
        <text
          x={394}
          y={panelY + 70}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          counter
        </text>
        <text
          x={394}
          y={panelY + 118}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 42, fontWeight: 700 }}
        >
          1
        </text>
        <text
          x={394}
          y={panelY + 148}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          {'{ counter: '}
          <tspan fill={accent} fontWeight={700}>1</tspan>
          {' }'}
        </text>
      </g>

      {/* caption row */}
      <text
        x={16}
        y={244}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        v0 → interaction → v1
      </text>
      <text
        x={484}
        y={244}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        interaction model
      </text>
      {/* live dot on v1 */}
      <circle cx={472} cy={panelY + 22} r={3} fill={accent2} className={s.blink} />
    </svg>
  );
}
