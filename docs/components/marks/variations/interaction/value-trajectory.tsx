import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: a single Ref's value across time. Each state is a small
 * numbered box; each transition is a labelled Interaction. Reads left
 * to right as a story: 0 → store(1) → 1 → store(value + 42) → 43.
 */
export function ValueTrajectorySvg({ className }: { className?: string }) {
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

  const y = 108;
  const boxW = 72;
  const boxH = 56;
  const states = [
    { x: 20, v: '0', label: 'v0' },
    { x: 200, v: '1', label: 'v1' },
    { x: 400, v: '43', label: 'v2' },
  ];

  return (
    <svg
      viewBox="0 0 520 240"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="A single ref's value through time: 0 becomes 1 after store, then 43 after another interaction."
      className={className}
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 504 8 L 512 8 L 512 16" />
        <path d="M 8 224 L 8 232 L 16 232" />
        <path d="M 504 232 L 512 232 L 512 224" />
      </g>

      {/* top label — the ref this trajectory belongs to */}
      <text
        x={20}
        y={40}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
      >
        ref
      </text>
      <text
        x={20}
        y={56}
        style={{ fill: ink, fontFamily: MONO, fontSize: 14, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        counter/value
      </text>
      <text
        x={500}
        y={40}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
      >
        trajectory
      </text>
      <line x1={20} y1={72} x2={500} y2={72} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* state boxes */}
      {states.map((st, i) => {
        const accentBox = i === states.length - 1;
        const stroke = accentBox ? accent : ink3;
        const sw = accentBox ? 1.25 : 1;
        const valueFill = accentBox ? accent : ink2;
        return (
          <g key={st.label}>
            <rect
              x={st.x}
              y={y}
              width={boxW}
              height={boxH}
              rx={3}
              fill={accentBox ? accentWash : bg}
              stroke={stroke}
              strokeWidth={sw}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={st.x + boxW / 2}
              y={y + 18}
              textAnchor="middle"
              style={{ fill: accentBox ? accent : ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
            >
              {st.label}
            </text>
            <text
              x={st.x + boxW / 2}
              y={y + 44}
              textAnchor="middle"
              style={{ fill: valueFill, fontFamily: MONO, fontSize: 20, fontWeight: 700 }}
            >
              {st.v}
            </text>
          </g>
        );
      })}

      {/* transitions */}
      {[
        { from: states[0], to: states[1], label: 'store(1)' },
        { from: states[1], to: states[2], label: 'store(value + 42)' },
      ].map((tr, i) => {
        const startX = tr.from.x + boxW;
        const endX = tr.to.x;
        const midX = (startX + endX) / 2;
        return (
          <g key={i}>
            <line
              x1={startX + 4}
              y1={y + boxH / 2}
              x2={endX - 8}
              y2={y + boxH / 2}
              stroke={accent}
              strokeWidth={1.25}
              strokeDasharray="4 3"
              vectorEffect="non-scaling-stroke"
              className={i === 1 ? s.pulse : undefined}
            />
            <polygon
              points={`${endX - 8},${y + boxH / 2 - 4} ${endX},${y + boxH / 2} ${endX - 8},${y + boxH / 2 + 4}`}
              fill={accent}
            />
            <text
              x={midX}
              y={y + boxH / 2 - 12}
              textAnchor="middle"
              style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
            >
              interaction
            </text>
            <text
              x={midX}
              y={y + boxH / 2 + 22}
              textAnchor="middle"
              style={{ fill: accent, fontFamily: MONO, fontSize: 12, fontWeight: 700 }}
            >
              {tr.label}
            </text>
          </g>
        );
      })}

      {/* caption */}
      <text
        x={500}
        y={222}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        one ref, over time
      </text>
      {/* live dot */}
      <circle cx={20} cy={222} r={3} fill={accent2} className={s.blink} />
      <text
        x={30}
        y={225}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        live
      </text>
    </svg>
  );
}
