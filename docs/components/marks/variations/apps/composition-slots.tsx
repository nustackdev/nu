/**
 * Apps as compositions of Nu fabrics.
 *
 * The five fabrics Nu ships (`shapes · mem · nudle · apps · lens`) sit
 * in a row along the bottom. Above them, two brackets show which subsets
 * `nulog` and `nuspace` pick. Communicates "each app is a chord of the
 * same instrument."
 */
export function CompositionSlotsSvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const mono = 'var(--font-mono)';

  const fabrics = ['shapes', 'mem', 'nudle', 'apps', 'lens'];
  const cellW = 96;
  const gap = 8;
  const rowY = 240;
  const rowH = 60;
  const rowLeft = 300 - (fabrics.length * cellW + (fabrics.length - 1) * gap) / 2;

  const fabricX = (i: number) => rowLeft + i * (cellW + gap);
  const fabricCX = (i: number) => fabricX(i) + cellW / 2;

  // nulog picks: shapes(0), mem(1)
  const nulogPicks = [0, 1];
  // nuspace picks: shapes(0), nudle(2), apps(3)
  const nuspacePicks = [0, 2, 3];

  const bracket = (app: string, picks: number[], y: number, tagline: string) => {
    const left = fabricX(picks[0]);
    const right = fabricX(picks[picks.length - 1]) + cellW;
    const mid = (left + right) / 2;
    return (
      <g key={app}>
        {/* app title cell */}
        <rect
          x={mid - 78}
          y={y}
          width={156}
          height={38}
          fill="none"
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <circle cx={mid + 60} cy={y + 12} r={2.4} fill={accent2} />
        <text
          x={mid + 68}
          y={y + 15}
          style={{ fill: accent2, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          live
        </text>
        <text
          x={mid - 66}
          y={y + 20}
          style={{
            fill: accent,
            fontFamily: mono,
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: '0.1em',
          }}
        >
          {app}
        </text>
        <text
          x={mid - 66}
          y={y + 32}
          style={{ fill: ink3, fontFamily: mono, fontSize: 9, letterSpacing: '0.16em' }}
        >
          {tagline}
        </text>

        {/* bracket down to picks */}
        <g fill="none" stroke={accent} strokeWidth={1.25} vectorEffect="non-scaling-stroke">
          {/* trunk */}
          <line x1={mid} y1={y + 38} x2={mid} y2={y + 56} />
          {/* horizontal spine over picks */}
          <line x1={left + cellW / 2} y1={y + 56} x2={right - cellW / 2} y2={y + 56} />
          {/* verticals down to each pick */}
          {picks.map((p) => (
            <line
              key={p}
              x1={fabricCX(p)}
              y1={y + 56}
              x2={fabricCX(p)}
              y2={rowY - 2}
            />
          ))}
        </g>
      </g>
    );
  };

  return (
    <svg
      viewBox="0 0 600 360"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Row of Nu fabrics along the bottom; brackets show nulog picks shapes and mem, nuspace picks shapes, nudle, apps."
    >
      {/* eyebrow */}
      <text
        x={22}
        y={28}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
      >
        each app · a chord of nu fabrics
      </text>

      {/* two app brackets */}
      {bracket('nulog', nulogPicks, 60, 'shapes + mem')}
      {bracket('nuspace', nuspacePicks, 140, 'shapes + nudle + apps')}

      {/* fabrics row */}
      {fabrics.map((f, i) => {
        const picked = new Set([...nulogPicks, ...nuspacePicks]).has(i);
        return (
          <g key={f}>
            <rect
              x={fabricX(i)}
              y={rowY}
              width={cellW}
              height={rowH}
              fill={picked ? accentWash : 'none'}
              stroke={picked ? accentLine : ruleSoft}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={fabricCX(i)}
              y={rowY + 26}
              textAnchor="middle"
              style={{
                fill: picked ? accent : ink3,
                fontFamily: mono,
                fontSize: 12,
                fontWeight: picked ? 700 : 500,
                letterSpacing: '0.14em',
              }}
            >
              {f}
            </text>
            <text
              x={fabricCX(i)}
              y={rowY + 46}
              textAnchor="middle"
              style={{
                fill: picked ? accent : ink4,
                fontFamily: mono,
                fontSize: 8.5,
                letterSpacing: '0.28em',
              }}
            >
              fabric
            </text>
          </g>
        );
      })}

      {/* substrate label under row */}
      <text
        x={rowLeft}
        y={rowY + rowH + 22}
        style={{ fill: accent, fontFamily: mono, fontSize: 11, fontWeight: 700, letterSpacing: '0.14em' }}
      >
        nu
      </text>
      <text
        x={rowLeft + 30}
        y={rowY + rowH + 22}
        style={{ fill: ink3, fontFamily: mono, fontSize: 9.5, letterSpacing: '0.22em' }}
      >
        · the shared substrate
      </text>

      {/* bottom caption */}
      <text
        x={578}
        y={352}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        apps compose from nu
      </text>
    </svg>
  );
}
