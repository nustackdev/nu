import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: a value lives on disk (rocksdb), the same shape has a Ref in the
 * browser. One Nu Interaction reads disk and stores to browser — same Ref
 * vocabulary on both sides, one bracket-tree unifies them.
 */
export function DiskToBrowserSvg({ className }: { className?: string }) {
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

  const panelY = 40;
  const panelH = 200;
  const leftX = 16;
  const rightX = 400;
  const panelW = 160;

  return (
    <svg
      viewBox="0 0 576 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="A value on disk and a Ref in the browser: one Nu Interaction reads disk and stores to browser, unifying both fabrics under the same Ref vocabulary."
      className={className}
    >
      {/* ============ LEFT PANEL — disk fabric ============ */}
      <g>
        <rect
          x={leftX}
          y={panelY}
          width={panelW}
          height={panelH}
          rx={4}
          fill={bg}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        {/* fabric label */}
        <text
          x={leftX + 14}
          y={panelY + 22}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          fabric · disk
        </text>
        {/* rocksdb glyph */}
        <g transform={`translate(${leftX + 14} ${panelY + 44})`}>
          <ellipse cx={16} cy={4} rx={14} ry={4} fill="none" stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <line x1={2} y1={4} x2={2} y2={16} stroke={ink3} strokeWidth={0.8} />
          <line x1={30} y1={4} x2={30} y2={16} stroke={ink3} strokeWidth={0.8} />
          <ellipse cx={16} cy={16} rx={14} ry={4} fill="none" stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <text x={42} y={14} style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.18em' }}>
            rocksdb
          </text>
        </g>
        {/* ref pill */}
        <g>
          <rect
            x={leftX + 14}
            y={panelY + 90}
            width={panelW - 28}
            height={22}
            rx={2}
            fill="none"
            stroke={accent2}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={leftX + 22}
            y={panelY + 104}
            style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
          >
            ref
          </text>
          <text
            x={leftX + 48}
            y={panelY + 104}
            style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
          >
            counter/value
          </text>
        </g>
        {/* value */}
        <text
          x={leftX + panelW / 2}
          y={panelY + 158}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={leftX + panelW / 2}
          y={panelY + 190}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 28, fontWeight: 700 }}
        >
          42
        </text>
      </g>

      {/* ============ MIDDLE — interaction ============ */}
      <g>
        {/* dashed load arrow (disk → interaction) */}
        <line
          x1={leftX + panelW}
          y1={panelY + 140}
          x2={220}
          y2={panelY + 140}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.6}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={(leftX + panelW + 220) / 2}
          y={panelY + 132}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          load
        </text>

        {/* interaction pill */}
        <rect
          x={220}
          y={panelY + 84}
          width={160}
          height={112}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={300}
          y={panelY + 104}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          interaction
        </text>
        <line
          x1={240}
          y1={panelY + 114}
          x2={360}
          y2={panelY + 114}
          stroke={accentLine}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        {/* the code */}
        <text
          x={300}
          y={panelY + 138}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em' }}
        >
          browser.value
        </text>
        <text
          x={300}
          y={panelY + 156}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          .store(disk.value)
        </text>
        {/* nu.run tag */}
        <text
          x={300}
          y={panelY + 184}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.28em' }}
        >
          nu.run
        </text>

        {/* dashed store arrow (interaction → browser) */}
        <line
          x1={380}
          y1={panelY + 140}
          x2={rightX}
          y2={panelY + 140}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.6}
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${rightX - 8},${panelY + 135} ${rightX},${panelY + 140} ${rightX - 8},${panelY + 145}`}
          fill={accent}
        />
        <text
          x={(380 + rightX) / 2}
          y={panelY + 132}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          store
        </text>
      </g>

      {/* ============ RIGHT PANEL — browser fabric ============ */}
      <g>
        <rect
          x={rightX}
          y={panelY}
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
          <path d={`M ${rightX} ${panelY + 8} L ${rightX} ${panelY} L ${rightX + 8} ${panelY}`} />
          <path d={`M ${rightX + panelW - 8} ${panelY} L ${rightX + panelW} ${panelY} L ${rightX + panelW} ${panelY + 8}`} />
          <path d={`M ${rightX} ${panelY + panelH - 8} L ${rightX} ${panelY + panelH} L ${rightX + 8} ${panelY + panelH}`} />
          <path d={`M ${rightX + panelW - 8} ${panelY + panelH} L ${rightX + panelW} ${panelY + panelH} L ${rightX + panelW} ${panelY + panelH - 8}`} />
        </g>
        {/* fabric label */}
        <text
          x={rightX + 14}
          y={panelY + 22}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        {/* browser chrome glyph */}
        <g transform={`translate(${rightX + 14} ${panelY + 44})`}>
          <circle cx={4} cy={4} r={2.2} fill={accent} opacity={0.75} />
          <circle cx={11} cy={4} r={2.2} fill={accent} opacity={0.75} />
          <circle cx={18} cy={4} r={2.2} fill={accent} opacity={0.75} />
          <line x1={26} y1={4} x2={panelW - 42} y2={4} stroke={accentLine} strokeWidth={1} vectorEffect="non-scaling-stroke" />
          <text x={0} y={20} style={{ fill: accent, fontFamily: MONO, fontSize: 10, letterSpacing: '0.18em' }}>
            nudle tab
          </text>
        </g>
        {/* ref pill */}
        <g>
          <rect
            x={rightX + 14}
            y={panelY + 90}
            width={panelW - 28}
            height={22}
            rx={2}
            fill="none"
            stroke={accent2}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={rightX + 22}
            y={panelY + 104}
            style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
          >
            ref
          </text>
          <text
            x={rightX + 48}
            y={panelY + 104}
            style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
          >
            counter/value
          </text>
        </g>
        {/* value */}
        <text
          x={rightX + panelW / 2}
          y={panelY + 158}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={rightX + panelW / 2}
          y={panelY + 190}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 28, fontWeight: 700 }}
        >
          42
        </text>
        {/* live dot */}
        <circle
          cx={rightX + panelW - 12}
          cy={panelY + 22}
          r={3}
          fill={accent2}
          className={s.blink}
        />
      </g>

      {/* ============ CAPTION ROW ============ */}
      <text
        x={16}
        y={302}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        one interaction · two fabrics · unified
      </text>
      <text
        x={560}
        y={302}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        same ref, different fabric
      </text>
    </svg>
  );
}
