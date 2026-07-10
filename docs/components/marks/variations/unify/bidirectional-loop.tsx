import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: two-way binding via one shared Ref vocabulary. Browser and disk
 * exchange values in a loop — one Nu Interaction writes browser→disk on
 * change, another writes disk→browser on change. Same Ref on both sides;
 * two Interactions form the loop.
 */
export function BidirectionalLoopSvg({ className }: { className?: string }) {
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

  const panelW = 180;
  const panelH = 160;
  const panelY = 80;
  const leftX = 24;
  const rightX = 372;

  return (
    <svg
      viewBox="0 0 576 340"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Two-way binding: browser and disk both hold Ref counter/value. One Nu Interaction reacts to browser changes and writes to disk, another reacts to disk and writes to browser."
      className={className}
    >
      {/* ============ LEFT PANEL — disk ============ */}
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
        <text
          x={leftX + 14}
          y={panelY + 22}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          fabric · disk
        </text>
        <g transform={`translate(${leftX + panelW - 62} ${panelY + 12})`}>
          <ellipse cx={16} cy={4} rx={14} ry={4} fill="none" stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <line x1={2} y1={4} x2={2} y2={16} stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <line x1={30} y1={4} x2={30} y2={16} stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
          <ellipse cx={16} cy={16} rx={14} ry={4} fill="none" stroke={ink3} strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
        </g>
        {/* ref pill */}
        <rect x={leftX + 14} y={panelY + 40} width={panelW - 28} height={22} rx={2} fill="none" stroke={accent2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={leftX + 22}
          y={panelY + 54}
          style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
        >
          ref
        </text>
        <text
          x={leftX + 48}
          y={panelY + 54}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          counter/value
        </text>
        {/* value */}
        <text
          x={leftX + panelW / 2}
          y={panelY + 100}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={leftX + panelW / 2}
          y={panelY + 134}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 28, fontWeight: 700 }}
        >
          42
        </text>
      </g>

      {/* ============ RIGHT PANEL — browser ============ */}
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
        <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke">
          <path d={`M ${rightX} ${panelY + 8} L ${rightX} ${panelY} L ${rightX + 8} ${panelY}`} />
          <path d={`M ${rightX + panelW - 8} ${panelY} L ${rightX + panelW} ${panelY} L ${rightX + panelW} ${panelY + 8}`} />
          <path d={`M ${rightX} ${panelY + panelH - 8} L ${rightX} ${panelY + panelH} L ${rightX + 8} ${panelY + panelH}`} />
          <path d={`M ${rightX + panelW - 8} ${panelY + panelH} L ${rightX + panelW} ${panelY + panelH} L ${rightX + panelW} ${panelY + panelH - 8}`} />
        </g>
        <text
          x={rightX + 14}
          y={panelY + 22}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        {/* window dots */}
        <g>
          <circle cx={rightX + panelW - 46} cy={panelY + 18} r={2.2} fill={accent} opacity={0.75} />
          <circle cx={rightX + panelW - 38} cy={panelY + 18} r={2.2} fill={accent} opacity={0.75} />
          <circle cx={rightX + panelW - 30} cy={panelY + 18} r={2.2} fill={accent} opacity={0.75} />
        </g>
        {/* ref pill */}
        <rect x={rightX + 14} y={panelY + 40} width={panelW - 28} height={22} rx={2} fill="none" stroke={accent2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={rightX + 22}
          y={panelY + 54}
          style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
        >
          ref
        </text>
        <text
          x={rightX + 48}
          y={panelY + 54}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
        >
          counter/value
        </text>
        <text
          x={rightX + panelW / 2}
          y={panelY + 100}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={rightX + panelW / 2}
          y={panelY + 134}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 28, fontWeight: 700 }}
        >
          42
        </text>
        <circle cx={rightX + panelW - 12} cy={panelY + panelH - 12} r={3} fill={accent2} className={s.blink} />
      </g>

      {/* ============ TOP INTERACTION — browser → disk ============ */}
      <g>
        {/* curve: top of browser → top of disk */}
        <path
          d={`M ${rightX + 20} ${panelY + 4} C ${rightX} 20 ${leftX + panelW} 20 ${leftX + panelW - 20} ${panelY + 4}`}
          fill="none"
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.6}
          vectorEffect="non-scaling-stroke"
        />
        {/* arrowhead pointing at disk (left) */}
        <polygon
          points={`${leftX + panelW - 12},${panelY + 4} ${leftX + panelW - 20},${panelY} ${leftX + panelW - 20},${panelY + 8}`}
          fill={accent}
        />

        {/* pill */}
        <rect
          x={202}
          y={16}
          width={172}
          height={40}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={288}
          y={32}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          interaction · on browser change
        </text>
        <text
          x={288}
          y={50}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          disk.value.store(browser.value)
        </text>
      </g>

      {/* ============ BOTTOM INTERACTION — disk → browser ============ */}
      <g>
        {/* curve: bottom of disk → bottom of browser */}
        <path
          d={`M ${leftX + panelW - 20} ${panelY + panelH - 4} C ${leftX + panelW} 260 ${rightX} 260 ${rightX + 20} ${panelY + panelH - 4}`}
          fill="none"
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.6}
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${rightX + 12},${panelY + panelH - 4} ${rightX + 20},${panelY + panelH - 8} ${rightX + 20},${panelY + panelH}`}
          fill={accent}
        />

        <rect
          x={202}
          y={252}
          width={172}
          height={40}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={288}
          y={268}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          interaction · on disk change
        </text>
        <text
          x={288}
          y={286}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          browser.value.store(disk.value)
        </text>
      </g>

      {/* caption */}
      <text
        x={24}
        y={322}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        two-way binding · one ref vocabulary
      </text>
      <text
        x={552}
        y={322}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        loop closes over the ref
      </text>
    </svg>
  );
}
