import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: physical forms differ, the Ref does not. Left panel shows raw
 * bytes on disk (0x0000002a). Right panel shows a DOM element in the
 * browser (<span>42</span>). One Nu Interaction labels both as the same
 * Ref counter/value. The Ref abstracts over the physical form.
 */
export function PhysicalFormsSvg({ className }: { className?: string }) {
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

  const panelY = 32;
  const panelH = 210;
  const panelW = 180;
  const leftX = 16;
  const rightX = 380;

  return (
    <svg
      viewBox="0 0 576 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Same Ref, different physical form: 0x0000002a on disk, <span>42</span> in the browser DOM. One Nu Interaction bridges them."
      className={className}
    >
      {/* ============ LEFT PANEL — bytes on disk ============ */}
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
        <text
          x={leftX + 14}
          y={panelY + 42}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          physical · bytes
        </text>

        {/* ref pill */}
        <g>
          <rect
            x={leftX + 14}
            y={panelY + 62}
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
            y={panelY + 76}
            style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
          >
            ref
          </text>
          <text
            x={leftX + 48}
            y={panelY + 76}
            style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
          >
            counter/value
          </text>
        </g>

        {/* raw byte block */}
        <g transform={`translate(${leftX + 14} ${panelY + 100})`}>
          <rect x={0} y={0} width={panelW - 28} height={80} rx={2} fill={bg} stroke={rule} strokeWidth={0.6} strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
          {/* address gutter */}
          <text
            x={10}
            y={20}
            style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.14em' }}
          >
            0x00
          </text>
          <line x1={10} y1={24} x2={40} y2={24} stroke={rule} strokeWidth={0.5} opacity={0.6} />
          {/* hex bytes */}
          <text
            x={panelW / 2 - 14}
            y={46}
            textAnchor="middle"
            style={{ fill: ink2, fontFamily: MONO, fontSize: 13, letterSpacing: '0.06em' }}
          >
            00 00 00 2a
          </text>
          <text
            x={panelW / 2 - 14}
            y={64}
            textAnchor="middle"
            style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
          >
            i64 · little-endian
          </text>
        </g>
      </g>

      {/* ============ MIDDLE — interaction pill ============ */}
      <g>
        {/* dashed inbound */}
        <line
          x1={leftX + panelW}
          y1={panelY + 130}
          x2={210}
          y2={panelY + 130}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.6}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={(leftX + panelW + 210) / 2}
          y={panelY + 122}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          load
        </text>

        <rect
          x={210}
          y={panelY + 70}
          width={150}
          height={120}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={285}
          y={panelY + 90}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          interaction
        </text>
        <line x1={228} y1={panelY + 100} x2={342} y2={panelY + 100} stroke={accentLine} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={285}
          y={panelY + 124}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em' }}
        >
          browser.value
        </text>
        <text
          x={285}
          y={panelY + 142}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          .store(disk.value)
        </text>
        <text
          x={285}
          y={panelY + 172}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.28em' }}
        >
          same ref · either form
        </text>

        {/* dashed outbound */}
        <line
          x1={360}
          y1={panelY + 130}
          x2={rightX}
          y2={panelY + 130}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.6}
          vectorEffect="non-scaling-stroke"
        />
        <polygon
          points={`${rightX - 8},${panelY + 125} ${rightX},${panelY + 130} ${rightX - 8},${panelY + 135}`}
          fill={accent}
        />
        <text
          x={(360 + rightX) / 2}
          y={panelY + 122}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          store
        </text>
      </g>

      {/* ============ RIGHT PANEL — DOM in browser ============ */}
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

        <text
          x={rightX + 14}
          y={panelY + 22}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        <text
          x={rightX + 14}
          y={panelY + 42}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          physical · dom node
        </text>

        {/* ref pill */}
        <g>
          <rect
            x={rightX + 14}
            y={panelY + 62}
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
            y={panelY + 76}
            style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
          >
            ref
          </text>
          <text
            x={rightX + 48}
            y={panelY + 76}
            style={{ fill: ink2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.02em' }}
          >
            counter/value
          </text>
        </g>

        {/* dom element block */}
        <g transform={`translate(${rightX + 14} ${panelY + 100})`}>
          <rect x={0} y={0} width={panelW - 28} height={80} rx={2} fill={bg} stroke={accent} strokeWidth={0.8} strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
          <text
            x={10}
            y={20}
            style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.14em' }}
          >
            #counter
          </text>
          <line x1={10} y1={24} x2={46} y2={24} stroke={accentLine} strokeWidth={0.5} opacity={0.7} />
          <text
            x={panelW / 2 - 14}
            y={46}
            textAnchor="middle"
            style={{ fill: accent, fontFamily: MONO, fontSize: 13, letterSpacing: '0.02em', fontWeight: 700 }}
          >
            {'<span>42</span>'}
          </text>
          <text
            x={panelW / 2 - 14}
            y={64}
            textAnchor="middle"
            style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
          >
            live text node
          </text>
        </g>
        {/* live dot */}
        <circle cx={rightX + panelW - 12} cy={panelY + 22} r={3} fill={accent2} className={s.blink} />
      </g>

      {/* caption */}
      <text
        x={16}
        y={302}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        bytes on disk · dom in browser
      </text>
      <text
        x={560}
        y={302}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        one ref hides the form
      </text>
    </svg>
  );
}
