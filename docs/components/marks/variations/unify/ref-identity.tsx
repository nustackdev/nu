import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: two fabrics, one Ref address. A giant ≡ (identity) sign in
 * purple sits between the panels, over the label "same address · different
 * fabric". Below, the Interaction pill reifies the equivalence with the
 * bracket-tree code.
 */
export function RefIdentitySvg({ className }: { className?: string }) {
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
  const panelH = 160;
  const panelW = 200;
  const leftX = 24;
  const rightX = 352;

  return (
    <svg
      viewBox="0 0 576 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Same Ref address, different fabric: disk and browser both hold counter/value. The ≡ identity sign is reified by one Nu Interaction below."
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
        {/* ref pill (highlighted address) */}
        <g>
          <rect
            x={leftX + 14}
            y={panelY + 40}
            width={panelW - 28}
            height={26}
            rx={2}
            fill={bg}
            stroke={accent2}
            strokeWidth={1.25}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={leftX + 22}
            y={panelY + 57}
            style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
          >
            ref
          </text>
          <text
            x={leftX + 48}
            y={panelY + 57}
            style={{ fill: ink, fontFamily: MONO, fontSize: 11, letterSpacing: '0.02em', fontWeight: 700 }}
          >
            counter/value
          </text>
        </g>
        {/* address string */}
        <text
          x={leftX + 14}
          y={panelY + 86}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.16em' }}
        >
          rocksdb://counter/value
        </text>
        {/* value */}
        <text
          x={leftX + panelW / 2}
          y={panelY + 138}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 26, fontWeight: 700 }}
        >
          42
        </text>
      </g>

      {/* ============ MIDDLE — the identity sign ============ */}
      <g>
        {/* wash halo behind the ≡ */}
        <rect
          x={244}
          y={panelY + 32}
          width={88}
          height={96}
          rx={6}
          fill={accentWash}
          stroke={accentLine}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={288}
          y={panelY + 74}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 48, fontWeight: 700 }}
        >
          ≡
        </text>
        <text
          x={288}
          y={panelY + 100}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.22em' }}
        >
          same address
        </text>
        <text
          x={288}
          y={panelY + 116}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.22em' }}
        >
          different fabric
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
        {/* ref pill */}
        <g>
          <rect
            x={rightX + 14}
            y={panelY + 40}
            width={panelW - 28}
            height={26}
            rx={2}
            fill={bg}
            stroke={accent2}
            strokeWidth={1.25}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={rightX + 22}
            y={panelY + 57}
            style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.16em', fontWeight: 700 }}
          >
            ref
          </text>
          <text
            x={rightX + 48}
            y={panelY + 57}
            style={{ fill: ink, fontFamily: MONO, fontSize: 11, letterSpacing: '0.02em', fontWeight: 700 }}
          >
            counter/value
          </text>
        </g>
        <text
          x={rightX + 14}
          y={panelY + 86}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.16em' }}
        >
          nudle://counter/value
        </text>
        <text
          x={rightX + panelW / 2}
          y={panelY + 138}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 26, fontWeight: 700 }}
        >
          42
        </text>
        <circle cx={rightX + panelW - 12} cy={panelY + 22} r={3} fill={accent2} className={s.blink} />
      </g>

      {/* ============ INTERACTION PILL — bottom row ============ */}
      <g>
        {/* thin drop from ≡ sign */}
        <line
          x1={288}
          y1={panelY + panelH + 8}
          x2={288}
          y2={230}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.55}
          vectorEffect="non-scaling-stroke"
        />
        <rect
          x={104}
          y={230}
          width={368}
          height={44}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={116}
          y={247}
          style={{ fill: accent, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          interaction · reifies ≡
        </text>
        <text
          x={288}
          y={264}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 12, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          browser.value.store(disk.value)
        </text>
        <text
          x={460}
          y={247}
          textAnchor="end"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          nu.run
        </text>
      </g>

      {/* caption */}
      <text
        x={24}
        y={302}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        two panels · one address · one interaction
      </text>
      <text
        x={552}
        y={302}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        equivalence, made real
      </text>
    </svg>
  );
}
