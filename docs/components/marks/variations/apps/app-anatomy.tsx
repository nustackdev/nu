/**
 * Anatomy of an app on Nu.
 *
 * Cross-section of `nulog`: a Shape at the top, its Refs, the Interaction
 * that writes to it, and the Fabric it resolves in. Each part labeled
 * with its Nu vocabulary so the viewer reads "an app is just Nu
 * vocabulary composed."
 */
export function AppAnatomySvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const mono = 'var(--font-mono)';

  return (
    <svg
      viewBox="0 0 480 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Anatomy of nulog: the Log shape, its three Refs, the append Interaction, and the rocksdb Fabric — each labeled in Nu vocabulary."
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 464 8 L 472 8 L 472 16" />
        <path d="M 8 304 L 8 312 L 16 312" />
        <path d="M 464 312 L 472 312 L 472 304" />
      </g>

      {/* header */}
      <text
        x={22}
        y={30}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
      >
        anatomy of an app
      </text>
      <text
        x={22}
        y={54}
        style={{
          fill: accent,
          fontFamily: mono,
          fontSize: 17,
          fontWeight: 700,
          letterSpacing: '0.1em',
        }}
      >
        nulog
      </text>
      <text
        x={72}
        y={54}
        style={{ fill: ink3, fontFamily: mono, fontSize: 11, letterSpacing: '0.14em' }}
      >
        = shape + refs + interaction + fabric
      </text>

      {/* SHAPE row */}
      <text x={22} y={94} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}>
        shape
      </text>
      <rect
        x={72}
        y={78}
        width={168}
        height={22}
        fill="none"
        stroke={ink2}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={80}
        y={94}
        style={{ fill: ink, fontFamily: mono, fontSize: 11, letterSpacing: '0.06em' }}
      >
        {'Log { level, msg, at }'}
      </text>
      <text
        x={252}
        y={94}
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.2em' }}
      >
        one record type
      </text>

      {/* REFS row */}
      <text x={22} y={144} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}>
        refs
      </text>
      {/* three ref circles with labels */}
      {[
        { x: 92, label: 'level' },
        { x: 172, label: 'msg' },
        { x: 252, label: 'at' },
      ].map((r) => (
        <g key={r.label}>
          <circle cx={r.x} cy={140} r={5} fill="none" stroke={ink2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
          <text
            x={r.x + 12}
            y={144}
            style={{ fill: ink2, fontFamily: mono, fontSize: 10, letterSpacing: '0.14em' }}
          >
            {r.label}
          </text>
        </g>
      ))}
      <text
        x={332}
        y={144}
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.2em' }}
      >
        addressable slots
      </text>

      {/* connector — refs into interaction */}
      <g fill="none" stroke={ruleSoft} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <line x1={92} y1={148} x2={92} y2={168} />
        <line x1={172} y1={148} x2={172} y2={168} />
        <line x1={252} y1={148} x2={252} y2={168} />
        <line x1={92} y1={168} x2={252} y2={168} />
        <line x1={172} y1={168} x2={172} y2={186} />
      </g>

      {/* INTERACTION row */}
      <text x={22} y={198} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}>
        interaction
      </text>
      <rect
        x={116}
        y={184}
        width={112}
        height={24}
        fill={accentWash}
        stroke={accent}
        strokeWidth={1.25}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={172}
        y={200}
        textAnchor="middle"
        style={{
          fill: accent,
          fontFamily: mono,
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.06em',
        }}
      >
        Log.append(row)
      </text>
      <text
        x={244}
        y={200}
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.2em' }}
      >
        the change that runs
      </text>

      {/* connector down to fabric */}
      <line
        x1={172}
        y1={208}
        x2={172}
        y2={230}
        stroke={accent}
        strokeWidth={1.25}
        vectorEffect="non-scaling-stroke"
      />

      {/* FABRIC row — dashed accent-line rect (Nu substrate) */}
      <text x={22} y={252} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}>
        fabric
      </text>
      <rect
        x={72}
        y={230}
        width={352}
        height={48}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        strokeDasharray="3 3"
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={92}
        y={260}
        style={{ fill: accent, fontFamily: mono, fontSize: 13, fontWeight: 700, letterSpacing: '0.12em' }}
      >
        nu.v · rocksdb
      </text>
      <text
        x={224}
        y={260}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.14em' }}
      >
        where the refs actually live
      </text>

      {/* bottom caption */}
      <text
        x={472}
        y={306}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        an app is nu vocabulary composed
      </text>
    </svg>
  );
}
