import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: two fabric panels at the bottom-left and bottom-right; one Nu
 * Interaction at the apex. Arrows converge into the pill, then one arrow
 * drops down through the middle carrying the unified value. Many fabrics
 * converge under one Interaction.
 */
export function ConvergingVSvg({ className }: { className?: string }) {
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

  const pillX = 152;
  const pillY = 24;
  const pillW = 176;
  const pillH = 84;

  const apex = { x: pillX + pillW / 2, y: pillY + pillH };

  const panelW = 140;
  const panelH = 110;
  const panelY = 210;
  const leftX = 24;
  const rightX = 316;

  const leftTop = { x: leftX + panelW / 2, y: panelY };
  const rightTop = { x: rightX + panelW / 2, y: panelY };

  // unified value cell at bottom center
  const cellY = 330;
  const cellX = pillX + pillW / 2 - 40;

  return (
    <svg
      viewBox="0 0 480 380"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Converging V: disk and browser fabrics converge into one Nu Interaction at the apex, which yields a unified value below."
      className={className}
    >
      {/* ============ APEX — interaction pill ============ */}
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
          x={apex.x}
          y={pillY + 20}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          interaction · nu.run
        </text>
        <line x1={pillX + 16} y1={pillY + 30} x2={pillX + pillW - 16} y2={pillY + 30} stroke={accentLine} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={apex.x}
          y={pillY + 52}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em' }}
        >
          browser.value
        </text>
        <text
          x={apex.x}
          y={pillY + 72}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          .store(disk.value)
        </text>
      </g>

      {/* ============ CONVERGING ARROWS (V shape) ============ */}
      <g>
        <line
          x1={leftTop.x}
          y1={leftTop.y}
          x2={apex.x - 10}
          y2={apex.y + 4}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.55}
          vectorEffect="non-scaling-stroke"
        />
        <line
          x1={rightTop.x}
          y1={rightTop.y}
          x2={apex.x + 10}
          y2={apex.y + 4}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.55}
          vectorEffect="non-scaling-stroke"
        />
        {/* labels along the two rails */}
        <text
          x={(leftTop.x + apex.x) / 2 - 14}
          y={(leftTop.y + apex.y) / 2}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          disk.value
        </text>
        <text
          x={(rightTop.x + apex.x) / 2 + 14}
          y={(rightTop.y + apex.y) / 2}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          browser.value
        </text>
      </g>

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
          x={leftX + 12}
          y={panelY + 18}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric · disk
        </text>
        {/* ref pill */}
        <rect x={leftX + 12} y={panelY + 30} width={panelW - 24} height={20} rx={2} fill="none" stroke={accent2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={leftX + 18}
          y={panelY + 44}
          style={{ fill: accent2, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.14em', fontWeight: 700 }}
        >
          ref
        </text>
        <text
          x={leftX + 40}
          y={panelY + 44}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.02em' }}
        >
          counter/value
        </text>
        <text
          x={leftX + panelW / 2}
          y={panelY + 90}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 22, fontWeight: 700 }}
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
          x={rightX + 12}
          y={panelY + 18}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        <rect x={rightX + 12} y={panelY + 30} width={panelW - 24} height={20} rx={2} fill="none" stroke={accent2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={rightX + 18}
          y={panelY + 44}
          style={{ fill: accent2, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.14em', fontWeight: 700 }}
        >
          ref
        </text>
        <text
          x={rightX + 40}
          y={panelY + 44}
          style={{ fill: ink2, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.02em' }}
        >
          counter/value
        </text>
        <text
          x={rightX + panelW / 2}
          y={panelY + 90}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 22, fontWeight: 700 }}
        >
          42
        </text>
        <circle cx={rightX + panelW - 12} cy={panelY + 12} r={3} fill={accent2} className={s.blink} />
      </g>

      {/* ============ UNIFIED VALUE — apex drops down ============ */}
      <g>
        <line
          x1={apex.x}
          y1={panelY + panelH / 2}
          x2={apex.x}
          y2={cellY - 4}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.55}
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${apex.x - 4},${cellY - 8} ${apex.x},${cellY} ${apex.x + 4},${cellY - 8}`}
          fill={accent}
        />

        <rect
          x={cellX}
          y={cellY}
          width={80}
          height={38}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={apex.x}
          y={cellY + 14}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          unified
        </text>
        <text
          x={apex.x}
          y={cellY + 32}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 16, fontWeight: 700 }}
        >
          42
        </text>
      </g>

      {/* connecting brackets/notches at panel tops signaling attachment */}
      <g stroke={accent} strokeWidth={0.75} vectorEffect="non-scaling-stroke" opacity={0.7}>
        <line x1={leftTop.x - 6} y1={leftTop.y - 4} x2={leftTop.x + 6} y2={leftTop.y - 4} />
        <line x1={rightTop.x - 6} y1={rightTop.y - 4} x2={rightTop.x + 6} y2={rightTop.y - 4} />
      </g>

      {/* caption */}
      <text
        x={24}
        y={372}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        two fabrics converge · one interaction
      </text>
      <text
        x={456}
        y={372}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        unified state
      </text>
    </svg>
  );
}
