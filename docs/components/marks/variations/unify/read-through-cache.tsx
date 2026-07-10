import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: read-through cache in three numbered steps. Browser reads the
 * Ref and misses; one Nu Interaction loads from disk and stores back into
 * browser; both hold the value. Numbered sequence — miss, load, store.
 */
export function ReadThroughCacheSvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const bg = 'var(--color-fd-background)';

  // step badge
  const StepBadge = ({ x, y, n }: { x: number; y: number; n: string }) => (
    <g>
      <circle cx={x} cy={y} r={9} fill={bg} stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke" />
      <text
        x={x}
        y={y + 4}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: MONO, fontSize: 10, letterSpacing: '0.06em', fontWeight: 700 }}
      >
        {n}
      </text>
    </g>
  );

  return (
    <svg
      viewBox="0 0 600 360"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Read-through cache in three numbered steps: browser reads and misses, one Nu Interaction loads from disk and stores back into browser."
      className={className}
    >
      {/* row labels */}
      <text x={24} y={20} style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}>
        step 1 · miss
      </text>
      <text x={224} y={20} style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}>
        step 2 · load
      </text>
      <text x={424} y={20} style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}>
        step 3 · store
      </text>

      {/* ============ COLUMN 1 — miss ============ */}
      <g>
        <rect
          x={24}
          y={40}
          width={168}
          height={200}
          rx={4}
          fill={bg}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={40}
          y={60}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        {/* code line: read attempt */}
        <text
          x={40}
          y={98}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 11, letterSpacing: '0.02em' }}
        >
          browser.value
        </text>
        <text
          x={40}
          y={116}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 11, letterSpacing: '0.02em', fontWeight: 700 }}
        >
          .load()
        </text>

        {/* result panel */}
        <rect x={40} y={144} width={136} height={70} rx={2} fill={bg} stroke={rule} strokeWidth={0.8} strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
        <text
          x={108}
          y={168}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          returns
        </text>
        <text
          x={108}
          y={196}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 20, letterSpacing: '0.06em', fontWeight: 700 }}
        >
          EMPTY
        </text>
        <StepBadge x={40} y={40} n="1" />
      </g>

      {/* between-column arrow */}
      <g>
        <line
          x1={192}
          y1={140}
          x2={224}
          y2={140}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.55}
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${224},${135} ${232},${140} ${224},${145}`}
          fill={accent}
        />
      </g>

      {/* ============ COLUMN 2 — interaction (load) ============ */}
      <g>
        <rect
          x={232}
          y={40}
          width={168}
          height={200}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={248}
          y={60}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          interaction
        </text>

        {/* disk source label */}
        <text
          x={316}
          y={94}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          reaches fabric · disk
        </text>

        {/* the code (bracket-tree) */}
        <text
          x={316}
          y={128}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11, letterSpacing: '0.01em' }}
        >
          browser.value
        </text>
        <text
          x={316}
          y={146}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          .store(
        </text>
        <text
          x={316}
          y={164}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          disk.value.load()
        </text>
        <text
          x={316}
          y={182}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          )
        </text>

        <text
          x={316}
          y={216}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.28em' }}
        >
          nu.run
        </text>

        <StepBadge x={248} y={40} n="2" />
      </g>

      {/* arrow to col 3 */}
      <g>
        <line
          x1={400}
          y1={140}
          x2={432}
          y2={140}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.55}
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${432},${135} ${440},${140} ${432},${145}`}
          fill={accent}
        />
      </g>

      {/* ============ COLUMN 3 — stored ============ */}
      <g>
        <rect
          x={440}
          y={40}
          width={136}
          height={200}
          rx={4}
          fill={bg}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        {/* accent corner ticks */}
        <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke">
          <path d={`M 440 48 L 440 40 L 448 40`} />
          <path d={`M 568 40 L 576 40 L 576 48`} />
          <path d={`M 440 232 L 440 240 L 448 240`} />
          <path d={`M 568 240 L 576 240 L 576 232`} />
        </g>
        <text
          x={456}
          y={60}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        {/* ref pill */}
        <rect x={456} y={78} width={104} height={20} rx={2} fill="none" stroke={accent2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={462}
          y={91}
          style={{ fill: accent2, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.14em', fontWeight: 700 }}
        >
          ref
        </text>
        <text
          x={482}
          y={91}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.02em' }}
        >
          counter/value
        </text>
        <text
          x={508}
          y={148}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          now holds
        </text>
        <text
          x={508}
          y={196}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 32, fontWeight: 700 }}
        >
          42
        </text>
        <text
          x={508}
          y={224}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          disk still has 42
        </text>
        <StepBadge x={456} y={40} n="3" />
        <circle cx={568} cy={48} r={3} fill={accent2} className={s.blink} />
      </g>

      {/* bottom summary row */}
      <g>
        <rect x={24} y={274} width={552} height={54} rx={4} fill={bg} stroke={rule} strokeWidth={1} strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
        <text
          x={40}
          y={294}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          bracket-tree
        </text>
        <text
          x={300}
          y={316}
          textAnchor="middle"
          style={{ fill: ink2, fontFamily: MONO, fontSize: 12, letterSpacing: '0.02em', fontWeight: 700 }}
        >
          browser.value.store(disk.value.load())
        </text>
      </g>

      {/* caption */}
      <text
        x={24}
        y={352}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        miss · load · store — one interaction
      </text>
      <text
        x={576}
        y={352}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        same ref both sides
      </text>
    </svg>
  );
}
