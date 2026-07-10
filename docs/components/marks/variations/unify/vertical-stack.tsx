import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: disk fabric on top, one Nu Interaction in the middle, browser
 * fabric on the bottom. Same Ref on both sides, vertical rhythm instead of
 * horizontal.
 */
export function VerticalStackSvg({ className }: { className?: string }) {
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

  const panelW = 320;
  const panelH = 130;
  const panelX = 40;
  const topY = 32;
  const botY = 328;

  const cx = panelX + panelW / 2;

  const pillY = 194;
  const pillH = 96;
  const pillW = 260;
  const pillX = panelX + (panelW - pillW) / 2;

  return (
    <svg
      viewBox="0 0 400 496"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Disk fabric on top, one Nu Interaction in the middle, browser fabric on the bottom — same Ref on both sides, vertical unification."
      className={className}
    >
      {/* ============ TOP PANEL — disk fabric ============ */}
      <g>
        <rect
          x={panelX}
          y={topY}
          width={panelW}
          height={panelH}
          rx={4}
          fill={bg}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={panelX + 14}
          y={topY + 20}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          fabric · disk
        </text>
        {/* rocksdb glyph */}
        <g transform={`translate(${panelX + panelW - 82} ${topY + 12})`}>
          <ellipse cx={16} cy={4} rx={14} ry={4} fill="none" stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <line x1={2} y1={4} x2={2} y2={16} stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <line x1={30} y1={4} x2={30} y2={16} stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <ellipse cx={16} cy={16} rx={14} ry={4} fill="none" stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <text x={42} y={14} style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.18em' }}>
            rocksdb
          </text>
        </g>
        {/* ref pill */}
        <g>
          <rect
            x={panelX + 14}
            y={topY + 42}
            width={panelW - 28}
            height={22}
            rx={2}
            fill="none"
            stroke={accent2}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={panelX + 22}
            y={topY + 56}
            style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
          >
            ref
          </text>
          <text
            x={panelX + 48}
            y={topY + 56}
            style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
          >
            counter/value
          </text>
        </g>
        {/* value row */}
        <text
          x={panelX + 22}
          y={topY + 100}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={panelX + panelW - 22}
          y={topY + 108}
          textAnchor="end"
          style={{ fill: ink, fontFamily: MONO, fontSize: 28, fontWeight: 700 }}
        >
          42
        </text>
      </g>

      {/* connector: disk → interaction (load) */}
      <g>
        <line
          x1={cx}
          y1={topY + panelH}
          x2={cx}
          y2={pillY}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.6}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={cx + 10}
          y={topY + panelH + 20}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          load
        </text>
      </g>

      {/* ============ MIDDLE — interaction pill ============ */}
      <g>
        <rect
          x={pillX}
          y={pillY}
          width={pillW}
          height={pillH}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={cx}
          y={pillY + 20}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          interaction · nu.run
        </text>
        <line
          x1={pillX + 20}
          y1={pillY + 30}
          x2={pillX + pillW - 20}
          y2={pillY + 30}
          stroke={accentLine}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={cx}
          y={pillY + 56}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 12, letterSpacing: '0.01em' }}
        >
          browser.value
        </text>
        <text
          x={cx}
          y={pillY + 78}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 12, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          .store(disk.value)
        </text>
      </g>

      {/* connector: interaction → browser (store) */}
      <g>
        <line
          x1={cx}
          y1={pillY + pillH}
          x2={cx}
          y2={botY}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.6}
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${cx - 4},${botY - 8} ${cx},${botY} ${cx + 4},${botY - 8}`}
          fill={accent}
        />
        <text
          x={cx + 10}
          y={pillY + pillH + 20}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          store
        </text>
      </g>

      {/* ============ BOTTOM PANEL — browser fabric (accent) ============ */}
      <g>
        <rect
          x={panelX}
          y={botY}
          width={panelW}
          height={panelH}
          rx={4}
          fill={bg}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        {/* accent corner ticks */}
        <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke">
          <path d={`M ${panelX} ${botY + 8} L ${panelX} ${botY} L ${panelX + 8} ${botY}`} />
          <path d={`M ${panelX + panelW - 8} ${botY} L ${panelX + panelW} ${botY} L ${panelX + panelW} ${botY + 8}`} />
          <path d={`M ${panelX} ${botY + panelH - 8} L ${panelX} ${botY + panelH} L ${panelX + 8} ${botY + panelH}`} />
          <path d={`M ${panelX + panelW - 8} ${botY + panelH} L ${panelX + panelW} ${botY + panelH} L ${panelX + panelW} ${botY + panelH - 8}`} />
        </g>
        <text
          x={panelX + 14}
          y={botY + 20}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        {/* nudle tab glyph */}
        <g transform={`translate(${panelX + panelW - 82} ${botY + 12})`}>
          <circle cx={4} cy={4} r={2.2} fill={accent} opacity={0.75} />
          <circle cx={11} cy={4} r={2.2} fill={accent} opacity={0.75} />
          <circle cx={18} cy={4} r={2.2} fill={accent} opacity={0.75} />
          <text x={26} y={8} style={{ fill: accent, fontFamily: MONO, fontSize: 10, letterSpacing: '0.18em' }}>
            nudle
          </text>
        </g>
        {/* ref pill */}
        <g>
          <rect
            x={panelX + 14}
            y={botY + 42}
            width={panelW - 28}
            height={22}
            rx={2}
            fill="none"
            stroke={accent2}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={panelX + 22}
            y={botY + 56}
            style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
          >
            ref
          </text>
          <text
            x={panelX + 48}
            y={botY + 56}
            style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
          >
            counter/value
          </text>
        </g>
        <text
          x={panelX + 22}
          y={botY + 100}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={panelX + panelW - 22}
          y={botY + 108}
          textAnchor="end"
          style={{ fill: accent, fontFamily: MONO, fontSize: 28, fontWeight: 700 }}
        >
          42
        </text>
        {/* live dot */}
        <circle
          cx={panelX + panelW - 12}
          cy={botY + 20}
          r={3}
          fill={accent2}
          className={s.blink}
        />
      </g>

      {/* caption */}
      <text
        x={40}
        y={484}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        one interaction · two fabrics · unified
      </text>
      <text
        x={360}
        y={484}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        same ref
      </text>
    </svg>
  );
}
