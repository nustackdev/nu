import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: Ref at the center, fabrics as satellites. One address is
 * resolved through many fabrics — disk, browser, memory, network — each on
 * a hairline spoke. The Interaction pill below is what actually reifies
 * the equivalence between two of them.
 */
export function RefSatelliteSvg({ className }: { className?: string }) {
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

  const cx = 240;
  const cy = 140;

  const centerR = 60;

  type Sat = {
    x: number;
    y: number;
    label: string;
    tag: string;
    anchor: 'start' | 'middle' | 'end';
    highlighted?: boolean;
  };

  const sats: Sat[] = [
    { x: 60,  y: 60,  label: 'disk',    tag: 'rocksdb', anchor: 'end', highlighted: true },
    { x: 420, y: 60,  label: 'browser', tag: 'nudle',   anchor: 'start', highlighted: true },
    { x: 60,  y: 220, label: 'memory',  tag: 'ctx',     anchor: 'end' },
    { x: 420, y: 220, label: 'network', tag: 'ws',      anchor: 'start' },
  ];

  return (
    <svg
      viewBox="0 0 480 360"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Substrate-agnostic Ref: one Ref at the center, satellites for disk, browser, memory, and network. One Nu Interaction reifies the equivalence between disk and browser."
      className={className}
    >
      {/* faint grid */}
      <g stroke={rule} strokeWidth={0.5} opacity={0.35} vectorEffect="non-scaling-stroke">
        <line x1={0} y1={cy} x2={480} y2={cy} strokeDasharray="2 4" />
        <line x1={cx} y1={0} x2={cx} y2={280} strokeDasharray="2 4" />
      </g>

      {/* spokes */}
      <g stroke={accent2} strokeWidth={1} opacity={0.5} vectorEffect="non-scaling-stroke" fill="none">
        {sats.map((sat) => (
          <line
            key={sat.label}
            x1={cx}
            y1={cy}
            x2={sat.x}
            y2={sat.y}
            strokeDasharray="3 3"
          />
        ))}
      </g>

      {/* ============ CENTER — the Ref ============ */}
      <g>
        <circle cx={cx} cy={cy} r={centerR} fill={accentWash} stroke={accent2} strokeWidth={1.25} vectorEffect="non-scaling-stroke" />
        <circle cx={cx} cy={cy} r={centerR - 10} fill="none" stroke={accent2} strokeWidth={0.5} opacity={0.5} vectorEffect="non-scaling-stroke" />
        <text
          x={cx}
          y={cy - 20}
          textAnchor="middle"
          style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em', fontWeight: 700 }}
        >
          ref
        </text>
        <text
          x={cx}
          y={cy - 2}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 13, letterSpacing: '0.04em', fontWeight: 700 }}
        >
          counter
        </text>
        <text
          x={cx}
          y={cy + 16}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 13, letterSpacing: '0.04em', fontWeight: 700 }}
        >
          /value
        </text>
        <text
          x={cx}
          y={cy + 36}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          one address
        </text>
      </g>

      {/* ============ SATELLITES ============ */}
      {sats.map((sat) => {
        const isBoxAccent = !!sat.highlighted;
        const stroke = isBoxAccent ? accent : rule;
        const sw = isBoxAccent ? 1.25 : 1;
        const labelFill = isBoxAccent ? accent : ink3;

        // small ref circle at spoke endpoint
        return (
          <g key={sat.label}>
            <circle
              cx={sat.x}
              cy={sat.y}
              r={4}
              fill={bg}
              stroke={isBoxAccent ? accent : accent2}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
            {/* fabric label + tag */}
            <text
              x={sat.anchor === 'end' ? sat.x - 10 : sat.x + 10}
              y={sat.y - 2}
              textAnchor={sat.anchor}
              style={{ fill: labelFill, fontFamily: MONO, fontSize: 10, letterSpacing: '0.24em', fontWeight: 700 }}
            >
              {sat.label}
            </text>
            <text
              x={sat.anchor === 'end' ? sat.x - 10 : sat.x + 10}
              y={sat.y + 12}
              textAnchor={sat.anchor}
              style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.18em' }}
            >
              {sat.tag}
            </text>
            {/* small value marker */}
            <text
              x={sat.anchor === 'end' ? sat.x - 10 : sat.x + 10}
              y={sat.y + 26}
              textAnchor={sat.anchor}
              style={{ fill: isBoxAccent ? accent : ink3, fontFamily: MONO, fontSize: 11, letterSpacing: '0.02em', fontWeight: 700 }}
            >
              42
            </text>
          </g>
        );
      })}

      {/* ============ INTERACTION PILL — bottom ============ */}
      <g>
        {/* connectors from the two highlighted sats down to the pill */}
        <line
          x1={60}
          y1={72}
          x2={60}
          y2={296}
          stroke={accent}
          strokeWidth={0.8}
          strokeDasharray="3 3"
          opacity={0.35}
          vectorEffect="non-scaling-stroke"
        />
        <line
          x1={420}
          y1={72}
          x2={420}
          y2={296}
          stroke={accent}
          strokeWidth={0.8}
          strokeDasharray="3 3"
          opacity={0.35}
          vectorEffect="non-scaling-stroke"
        />

        <rect
          x={60}
          y={296}
          width={360}
          height={38}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={72}
          y={311}
          style={{ fill: accent, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          interaction
        </text>
        <text
          x={240}
          y={323}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          browser.value.store(disk.value)
        </text>
        <text
          x={408}
          y={311}
          textAnchor="end"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          nu.run
        </text>
      </g>

      {/* caption */}
      <text
        x={16}
        y={352}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        ref is the center · fabrics are the resolutions
      </text>
    </svg>
  );
}
