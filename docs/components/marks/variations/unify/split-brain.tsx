import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: two fabrics diverged (disk 42, browser 0). One Nu Interaction
 * runs; both now hold 42. The divergence is made visible before-after —
 * split-brain, then reconciled.
 */
export function SplitBrainSvg({ className }: { className?: string }) {
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

  const panelW = 220;
  const panelH = 100;
  const leftX = 24;
  const rightX = 356;

  const beforeY = 40;
  const afterY = 220;

  // ref pill
  const RefPill = ({ x, y, w, color }: { x: number; y: number; w: number; color: string }) => (
    <g>
      <rect
        x={x}
        y={y}
        width={w}
        height={20}
        rx={2}
        fill="none"
        stroke={color}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={x + 8}
        y={y + 13}
        style={{ fill: color, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.16em', fontWeight: 700 }}
      >
        ref
      </text>
      <text
        x={x + 32}
        y={y + 13}
        style={{ fill: ink2, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.02em' }}
      >
        counter/value
      </text>
    </g>
  );

  return (
    <svg
      viewBox="0 0 600 380"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Split-brain reconciliation: disk holds 42 while browser holds 0. One Nu Interaction reconciles them so both hold 42."
      className={className}
    >
      {/* ==================== BEFORE ROW ==================== */}
      {/* row label */}
      <text
        x={24}
        y={26}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
      >
        before · diverged
      </text>
      <line x1={24} y1={32} x2={112} y2={32} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* left panel — disk (has 42) */}
      <g>
        <rect
          x={leftX}
          y={beforeY}
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
          y={beforeY + 18}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric · disk
        </text>
        <RefPill x={leftX + 12} y={beforeY + 30} w={panelW - 24} color={accent2} />
        <text
          x={leftX + 20}
          y={beforeY + 84}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={leftX + panelW - 20}
          y={beforeY + 90}
          textAnchor="end"
          style={{ fill: ink, fontFamily: MONO, fontSize: 22, fontWeight: 700 }}
        >
          42
        </text>
      </g>

      {/* divergence sigil */}
      <g>
        <text
          x={300}
          y={beforeY + 60}
          textAnchor="middle"
          style={{ fill: ink3, fontFamily: MONO, fontSize: 32, fontWeight: 700 }}
        >
          ≠
        </text>
        <text
          x={300}
          y={beforeY + 88}
          textAnchor="middle"
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          diverged
        </text>
      </g>

      {/* right panel — browser (has 0) */}
      <g>
        <rect
          x={rightX}
          y={beforeY}
          width={panelW}
          height={panelH}
          rx={4}
          fill={bg}
          stroke={rule}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={rightX + 12}
          y={beforeY + 18}
          style={{ fill: ink3, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        <RefPill x={rightX + 12} y={beforeY + 30} w={panelW - 24} color={accent2} />
        <text
          x={rightX + 20}
          y={beforeY + 84}
          style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={rightX + panelW - 20}
          y={beforeY + 90}
          textAnchor="end"
          style={{ fill: ink2, fontFamily: MONO, fontSize: 22, fontWeight: 700, opacity: 0.55 }}
        >
          0
        </text>
      </g>

      {/* ==================== INTERACTION BRIDGE ==================== */}
      <g>
        {/* down connector from before */}
        <line
          x1={300}
          y1={beforeY + panelH + 4}
          x2={300}
          y2={168}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.55}
          vectorEffect="non-scaling-stroke"
        />

        {/* pill */}
        <rect
          x={186}
          y={168}
          width={228}
          height={40}
          rx={4}
          fill={accentWash}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
          className={s.pulse}
        />
        <text
          x={300}
          y={184}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
        >
          interaction · nu.run
        </text>
        <text
          x={300}
          y={202}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.01em', fontWeight: 700 }}
        >
          browser.value.store(disk.value)
        </text>

        {/* down connector to after */}
        <line
          x1={300}
          y1={208}
          x2={300}
          y2={afterY - 4}
          stroke={accent}
          strokeWidth={1}
          strokeDasharray="4 3"
          opacity={0.55}
          vectorEffect="non-scaling-stroke"
        />
      </g>

      {/* ==================== AFTER ROW ==================== */}
      <text
        x={24}
        y={afterY - 16}
        style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em' }}
      >
        after · unified
      </text>
      <line x1={24} y1={afterY - 10} x2={116} y2={afterY - 10} stroke={accentLine} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* left panel — disk (still 42) */}
      <g>
        <rect
          x={leftX}
          y={afterY}
          width={panelW}
          height={panelH}
          rx={4}
          fill={bg}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={leftX + 12}
          y={afterY + 18}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric · disk
        </text>
        <RefPill x={leftX + 12} y={afterY + 30} w={panelW - 24} color={accent2} />
        <text
          x={leftX + 20}
          y={afterY + 84}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={leftX + panelW - 20}
          y={afterY + 90}
          textAnchor="end"
          style={{ fill: accent, fontFamily: MONO, fontSize: 22, fontWeight: 700 }}
        >
          42
        </text>
      </g>

      {/* identity sigil */}
      <g>
        <text
          x={300}
          y={afterY + 60}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 32, fontWeight: 700 }}
        >
          ≡
        </text>
        <text
          x={300}
          y={afterY + 88}
          textAnchor="middle"
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          unified
        </text>
      </g>

      {/* right panel — browser (now 42) */}
      <g>
        <rect
          x={rightX}
          y={afterY}
          width={panelW}
          height={panelH}
          rx={4}
          fill={bg}
          stroke={accent}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={rightX + 12}
          y={afterY + 18}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          fabric · browser
        </text>
        <RefPill x={rightX + 12} y={afterY + 30} w={panelW - 24} color={accent2} />
        <text
          x={rightX + 20}
          y={afterY + 84}
          style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
        >
          value
        </text>
        <text
          x={rightX + panelW - 20}
          y={afterY + 90}
          textAnchor="end"
          style={{ fill: accent, fontFamily: MONO, fontSize: 22, fontWeight: 700 }}
        >
          42
        </text>
        <circle cx={rightX + panelW - 12} cy={afterY + 12} r={3} fill={accent2} className={s.blink} />
      </g>

      {/* caption */}
      <text
        x={24}
        y={362}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        split-brain → one interaction → unified
      </text>
      <text
        x={576}
        y={362}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        same ref, same value
      </text>
    </svg>
  );
}
