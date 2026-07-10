import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: three fragmented raw APIs (crossed out) collapse into one
 * central Nu Interaction that fans out to browser / disk / memory
 * substrates. Before value = 0, after = 1.
 */
export function ThreeFabricFanoutSvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const rule = 'var(--nu-rule)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';

  const rowY = [58, 158, 258];
  const midY = 158;
  const mLeft = 200;
  const mRight = 320;

  return (
    <svg
      viewBox="0 0 520 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Three fragmented raw APIs collapse into one Nu interaction that reaches browser, disk, and memory."
      className={className}
    >
      {/* corner ticks */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 504 8 L 512 8 L 512 16" />
        <path d="M 8 304 L 8 312 L 16 312" />
        <path d="M 504 312 L 512 312 L 512 304" />
      </g>

      {/* left column — fragmented APIs, crossed out */}
      {[
        { y: rowY[0], api: 'input.value = 1', label: 'browser' },
        { y: rowY[1], api: 'db.put("count", 1)', label: 'disk' },
        { y: rowY[2], api: 'd["count"] = 1', label: 'memory' },
      ].map((r) => (
        <g key={r.label}>
          <text
            x={20}
            y={r.y - 8}
            style={{
              fill: ink4,
              fontFamily: MONO,
              fontSize: 8.5,
              letterSpacing: '0.22em',
            }}
          >
            {r.label}
          </text>
          <text
            x={20}
            y={r.y + 8}
            style={{
              fill: ink3,
              fontFamily: MONO,
              fontSize: 10.5,
              letterSpacing: '0.02em',
              textDecoration: 'line-through',
            }}
          >
            {r.api}
          </text>
        </g>
      ))}

      {/* collapse — 3 lines into central node */}
      <g fill="none" stroke={accent} strokeWidth={1} opacity={0.55} vectorEffect="non-scaling-stroke">
        <path d={`M 170 ${rowY[0] + 3} C 185 ${rowY[0] + 3} 190 ${midY} ${mLeft} ${midY}`} />
        <path d={`M 170 ${rowY[1] + 3} L ${mLeft} ${midY}`} />
        <path d={`M 170 ${rowY[2] + 3} C 185 ${rowY[2] + 3} 190 ${midY} ${mLeft} ${midY}`} />
      </g>

      {/* central Interaction node */}
      <g>
        <rect
          x={mLeft}
          y={midY - 34}
          width={mRight - mLeft}
          height={68}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={(mLeft + mRight) / 2}
          y={midY - 42}
          textAnchor="middle"
          style={{
            fill: accent,
            fontFamily: MONO,
            fontSize: 9,
            letterSpacing: '0.24em',
          }}
        >
          one interaction
        </text>
        <text
          x={(mLeft + mRight) / 2}
          y={midY - 4}
          textAnchor="middle"
          style={{
            fill: accent,
            fontFamily: MONO,
            fontSize: 12,
            letterSpacing: '0.02em',
          }}
        >
          store(counter,
        </text>
        <text
          x={(mLeft + mRight) / 2}
          y={midY + 14}
          textAnchor="middle"
          style={{
            fill: accent,
            fontFamily: MONO,
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: '0.02em',
          }}
        >
          1)
        </text>
      </g>

      {/* fan-out — dashed hairlines to substrates */}
      <g fill="none" stroke={accent} strokeWidth={1} opacity={0.55} strokeDasharray="4 3" vectorEffect="non-scaling-stroke">
        <path d={`M ${mRight} ${midY} C 340 ${midY} 340 ${rowY[0]} 360 ${rowY[0]}`} />
        <path d={`M ${mRight} ${midY} L 360 ${rowY[1]}`} />
        <path d={`M ${mRight} ${midY} C 340 ${midY} 340 ${rowY[2]} 360 ${rowY[2]}`} />
      </g>

      {/* right substrates — tiny, iconic, with new value */}
      {/* browser */}
      <g transform={`translate(360 ${rowY[0] - 20})`}>
        <rect x={0} y={0} width={140} height={40} rx={3} fill="none" stroke={accent2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={0} y1={11} x2={140} y2={11} stroke={accent2} strokeWidth={0.6} opacity={0.55} />
        <circle cx={6} cy={5.5} r={1.4} fill={accent2} opacity={0.55} />
        <circle cx={11} cy={5.5} r={1.4} fill={accent2} opacity={0.55} />
        <circle cx={16} cy={5.5} r={1.4} fill={accent2} opacity={0.55} />
        <text x={70} y={30} textAnchor="middle" style={{ fill: accent2, fontFamily: MONO, fontSize: 12, letterSpacing: '0.04em', fontWeight: 700 }}>
          count: 1
        </text>
      </g>
      {/* disk */}
      <g transform={`translate(360 ${rowY[1] - 20})`}>
        <rect x={0} y={0} width={140} height={40} rx={3} fill="none" stroke={accent2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <ellipse cx={16} cy={20} rx={9} ry={3} fill="none" stroke={accent2} strokeWidth={0.8} opacity={0.6} />
        <line x1={7} y1={14} x2={7} y2={20} stroke={accent2} strokeWidth={0.8} opacity={0.6} />
        <line x1={25} y1={14} x2={25} y2={20} stroke={accent2} strokeWidth={0.8} opacity={0.6} />
        <ellipse cx={16} cy={14} rx={9} ry={3} fill="none" stroke={accent2} strokeWidth={0.8} opacity={0.6} />
        <text x={82} y={25} textAnchor="middle" style={{ fill: accent2, fontFamily: MONO, fontSize: 12, letterSpacing: '0.04em', fontWeight: 700 }}>
          count: 1
        </text>
      </g>
      {/* memory */}
      <g transform={`translate(360 ${rowY[2] - 20})`}>
        <rect x={0} y={0} width={140} height={40} rx={3} fill="none" stroke={accent2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text x={6} y={13} style={{ fill: accent2, fontFamily: MONO, fontSize: 7, letterSpacing: '0.14em', opacity: 0.7 }}>
          0x00
        </text>
        <text x={70} y={28} textAnchor="middle" style={{ fill: accent2, fontFamily: MONO, fontSize: 11, letterSpacing: '0.02em', fontWeight: 700 }}>
          {'{ count: 1 }'}
        </text>
      </g>

      {/* caption */}
      <text
        x={512}
        y={310}
        textAnchor="end"
        style={{
          fill: ink4,
          fontFamily: MONO,
          fontSize: 9,
          letterSpacing: '0.24em',
        }}
      >
        interaction model
      </text>
      <text
        x={8}
        y={310}
        style={{
          fill: ink4,
          fontFamily: MONO,
          fontSize: 9,
          letterSpacing: '0.24em',
        }}
      >
        3 apis → 1 nu
      </text>
      {/* subtle line under central node hint */}
      <line x1={mLeft + 12} y1={midY + 24} x2={mRight - 12} y2={midY + 24} stroke={accentLine} strokeWidth={1} vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
