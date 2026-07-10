import s from '../../marks.module.css';

/**
 * Apps roster — honest status.
 *
 * A horizontal timeline anchored on `nu`: two `live` milestones
 * (`nulog`, `nuspace`) sit to the right of a marker, and a dimmed
 * `tbd` milestone hints at what's next. Communicates the roster as-is
 * without inventing a release.
 */
export function TimelineSvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const mono = 'var(--font-mono)';

  const axisY = 168;
  const nuMarker = { x: 60 };
  const marks: Array<{
    x: number;
    name: string;
    status: 'live' | 'tbd';
    tagline: string;
    dim?: boolean;
  }> = [
    { x: 160, name: 'nulog', status: 'live', tagline: 'logs as refs' },
    { x: 290, name: 'nuspace', status: 'live', tagline: 'workspace on nudle' },
    { x: 420, name: 'more', status: 'tbd', tagline: 'when it ships', dim: true },
  ];

  return (
    <svg
      viewBox="0 0 480 280"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Roster timeline: nu at the origin; nulog and nuspace are live milestones on the axis; more is a dimmed placeholder."
    >
      {/* eyebrow */}
      <text
        x={22}
        y={28}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
      >
        apps · the roster
      </text>

      {/* nu origin wash bar under the whole axis */}
      <rect
        x={30}
        y={axisY - 12}
        width={434}
        height={24}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={38}
        y={axisY + 4}
        style={{ fill: accent, fontFamily: mono, fontSize: 11, fontWeight: 700, letterSpacing: '0.16em' }}
      >
        nu
      </text>
      <text
        x={60}
        y={axisY + 4}
        style={{ fill: accent, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em', opacity: 0.7 }}
      >
        · substrate
      </text>

      {/* axis line */}
      <line
        x1={30}
        y1={axisY}
        x2={464}
        y2={axisY}
        stroke={rule}
        strokeWidth={1.25}
        vectorEffect="non-scaling-stroke"
      />

      {/* origin tick — nu */}
      <line
        x1={nuMarker.x}
        y1={axisY - 6}
        x2={nuMarker.x}
        y2={axisY + 6}
        stroke={accent}
        strokeWidth={1.25}
        vectorEffect="non-scaling-stroke"
      />

      {/* milestone marks */}
      {marks.map((m) => (
        <g key={m.name}>
          {/* tick */}
          <line
            x1={m.x}
            y1={axisY - 6}
            x2={m.x}
            y2={axisY + 6}
            stroke={m.dim ? ruleSoft : rule}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          {/* label stem going up */}
          <line
            x1={m.x}
            y1={axisY - 6}
            x2={m.x}
            y2={axisY - 44}
            stroke={m.dim ? ruleSoft : rule}
            strokeWidth={1}
            strokeDasharray={m.dim ? '2 3' : undefined}
            vectorEffect="non-scaling-stroke"
          />
          {/* status pill */}
          <g>
            <circle
              cx={m.x - 20}
              cy={axisY - 56}
              r={2.6}
              fill={m.dim ? ink4 : accent2}
              className={m.dim ? undefined : s.blink}
            />
            <text
              x={m.x - 12}
              y={axisY - 53}
              style={{
                fill: m.dim ? ink4 : accent2,
                fontFamily: mono,
                fontSize: 9,
                letterSpacing: '0.24em',
              }}
            >
              {m.status}
            </text>
          </g>
          {/* app name */}
          <text
            x={m.x}
            y={axisY - 74}
            textAnchor="middle"
            style={{
              fill: m.dim ? ink3 : accent,
              fontFamily: mono,
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: '0.1em',
            }}
          >
            {m.name}
          </text>
          {/* tagline */}
          <text
            x={m.x}
            y={axisY + 30}
            textAnchor="middle"
            style={{
              fill: m.dim ? ink4 : ink3,
              fontFamily: mono,
              fontSize: 9.5,
              letterSpacing: '0.18em',
            }}
          >
            {m.tagline}
          </text>
        </g>
      ))}

      {/* origin label under */}
      <text
        x={nuMarker.x}
        y={axisY + 30}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        origin
      </text>

      {/* bottom caption */}
      <text
        x={472}
        y={266}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        no vaporware
      </text>
    </svg>
  );
}
