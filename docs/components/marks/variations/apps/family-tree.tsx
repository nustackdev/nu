import s from '../../marks.module.css';

/**
 * Family tree from Nu.
 *
 * `nu` sits at the top in an accent-wash node. Two live children —
 * `nulog` and `nuspace` — branch down from it, plus a dimmed `more`
 * placeholder. Each edge is annotated with what the app inherits from
 * Nu (`shapes+mem`, `shapes+nudle`, …). Reads as a roster with lineage.
 */
export function FamilyTreeSvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const mono = 'var(--font-mono)';

  const children: Array<{
    x: number;
    name: string;
    tagline: string;
    inherits: string;
    status: 'live' | 'tbd';
    dim?: boolean;
  }> = [
    { x: 68, name: 'nulog', tagline: 'logs as refs', inherits: 'shapes · mem', status: 'live' },
    { x: 218, name: 'nuspace', tagline: 'workspace on nudle', inherits: 'shapes · nudle · apps', status: 'live' },
    { x: 368, name: 'more', tagline: 'coming', inherits: 'tbd', status: 'tbd', dim: true },
  ];

  return (
    <svg
      viewBox="0 0 480 300"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Family tree: nu root at top branches into nulog and nuspace live, plus a dimmed more placeholder; edges are annotated with inherited fabrics."
    >
      {/* eyebrow */}
      <text
        x={22}
        y={26}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
      >
        apps · what grows from nu
      </text>

      {/* root — nu */}
      <g>
        <rect
          x={200}
          y={54}
          width={80}
          height={40}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={240}
          y={80}
          textAnchor="middle"
          style={{
            fill: accent,
            fontFamily: mono,
            fontSize: 17,
            fontWeight: 700,
            letterSpacing: '0.14em',
          }}
        >
          nu
        </text>
        <text
          x={240}
          y={110}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: mono, fontSize: 9, letterSpacing: '0.22em' }}
        >
          the substrate
        </text>
      </g>

      {/* spine down to horizontal splitter */}
      <g fill="none" stroke={accent} strokeWidth={1.25} vectorEffect="non-scaling-stroke">
        <line x1={240} y1={94} x2={240} y2={130} />
        {/* horizontal splitter reaches each child column */}
        <line x1={children[0].x + 56} y1={130} x2={children[children.length - 1].x + 56} y2={130} />
      </g>
      {/* verticals down to each child */}
      {children.map((c) => (
        <line
          key={c.name}
          x1={c.x + 56}
          y1={130}
          x2={c.x + 56}
          y2={168}
          stroke={c.dim ? ruleSoft : accent}
          strokeWidth={c.dim ? 1 : 1.25}
          strokeDasharray={c.dim ? '3 3' : undefined}
          vectorEffect="non-scaling-stroke"
        />
      ))}

      {/* inheritance labels along the verticals */}
      {children.map((c) => (
        <text
          key={c.name}
          x={c.x + 60}
          y={152}
          style={{
            fill: c.dim ? ink4 : accent,
            fontFamily: mono,
            fontSize: 8.5,
            letterSpacing: '0.24em',
            opacity: c.dim ? 1 : 0.85,
          }}
        >
          {c.inherits}
        </text>
      ))}

      {/* child cells */}
      {children.map((c) => (
        <g key={c.name}>
          <rect
            x={c.x}
            y={168}
            width={112}
            height={90}
            fill="none"
            stroke={c.dim ? ruleSoft : rule}
            strokeWidth={1}
            strokeDasharray={c.dim ? '3 3' : undefined}
            vectorEffect="non-scaling-stroke"
          />
          {/* status */}
          <g>
            <circle
              cx={c.x + 14}
              cy={186}
              r={2.4}
              fill={c.dim ? ink4 : accent2}
              className={c.dim ? undefined : s.blink}
            />
            <text
              x={c.x + 22}
              y={189}
              style={{
                fill: c.dim ? ink4 : accent2,
                fontFamily: mono,
                fontSize: 8.5,
                letterSpacing: '0.24em',
              }}
            >
              {c.status}
            </text>
          </g>
          {/* name */}
          <text
            x={c.x + 56}
            y={218}
            textAnchor="middle"
            style={{
              fill: c.dim ? ink3 : accent,
              fontFamily: mono,
              fontSize: 15,
              fontWeight: 700,
              letterSpacing: '0.1em',
            }}
          >
            {c.name}
          </text>
          {/* tagline */}
          <text
            x={c.x + 56}
            y={238}
            textAnchor="middle"
            style={{
              fill: c.dim ? ink4 : ink3,
              fontFamily: mono,
              fontSize: 9.5,
              letterSpacing: '0.18em',
            }}
          >
            {c.tagline}
          </text>
        </g>
      ))}

      {/* bottom caption */}
      <text
        x={472}
        y={286}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        one root, many apps
      </text>
    </svg>
  );
}
