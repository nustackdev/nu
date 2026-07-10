import s from '../../marks.module.css';

const MONO = 'var(--font-mono)';

/**
 * Concept: one address spans many fabrics. A big top banner pins the shared
 * Ref; three fabric icons hang below it via hairline drops. Communicates
 * "one Ref, many fabrics" — the identity is the address, not the storage.
 */
export function SharedRefBannerSvg({ className }: { className?: string }) {
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

  const bannerX = 40;
  const bannerY = 40;
  const bannerW = 480;
  const bannerH = 60;

  const dropY = bannerY + bannerH;
  const dropEndY = 190;

  const fabricY = 200;
  const fabricH = 110;
  const fabricW = 130;

  type Fabric = { x: number; label: string; tag: string; accent?: boolean };
  const disk: Fabric = { x: 60, label: 'disk', tag: 'rocksdb' };
  const browser: Fabric = { x: 215, label: 'browser', tag: 'nudle', accent: true };
  const memory: Fabric = { x: 370, label: 'memory', tag: 'ctx' };

  return (
    <svg
      viewBox="0 0 560 360"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Shared Ref banner: one Ref (counter/value) spans disk, browser, and memory fabrics — the identity is the address, not the storage."
      className={className}
    >
      {/* corner ticks (outer canvas) */}
      <g fill="none" stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke">
        <path d="M 8 16 L 8 8 L 16 8" />
        <path d="M 544 8 L 552 8 L 552 16" />
        <path d="M 8 344 L 8 352 L 16 352" />
        <path d="M 544 352 L 552 352 L 552 344" />
      </g>

      {/* ============ BANNER — the shared Ref ============ */}
      <g>
        <rect
          x={bannerX}
          y={bannerY}
          width={bannerW}
          height={bannerH}
          rx={4}
          fill={accentWash}
          stroke={accent2}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        {/* ref circle glyph left */}
        <circle
          cx={bannerX + 24}
          cy={bannerY + bannerH / 2}
          r={5}
          fill="none"
          stroke={accent2}
          strokeWidth={1.25}
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={bannerX + 40}
          y={bannerY + 22}
          style={{ fill: accent2, fontFamily: MONO, fontSize: 9, letterSpacing: '0.28em', fontWeight: 700 }}
        >
          ref · one address
        </text>
        <text
          x={bannerX + 40}
          y={bannerY + 48}
          style={{ fill: ink, fontFamily: MONO, fontSize: 20, letterSpacing: '0.04em', fontWeight: 700 }}
        >
          counter/value
        </text>
        {/* live dot */}
        <circle cx={bannerX + bannerW - 16} cy={bannerY + 14} r={3} fill={accent2} className={s.blink} />
      </g>

      {/* hairline drops */}
      <g stroke={accent2} strokeWidth={1} opacity={0.55} vectorEffect="non-scaling-stroke">
        <line x1={disk.x + fabricW / 2} y1={dropY} x2={disk.x + fabricW / 2} y2={dropEndY} strokeDasharray="3 3" />
        <line x1={browser.x + fabricW / 2} y1={dropY} x2={browser.x + fabricW / 2} y2={dropEndY} strokeDasharray="3 3" />
        <line x1={memory.x + fabricW / 2} y1={dropY} x2={memory.x + fabricW / 2} y2={dropEndY} strokeDasharray="3 3" />
      </g>
      {/* small ref circles at the drop endpoints */}
      <g>
        {[disk, browser, memory].map((f) => (
          <g key={f.label}>
            <circle
              cx={f.x + fabricW / 2}
              cy={dropEndY}
              r={3}
              fill={bg}
              stroke={accent2}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          </g>
        ))}
      </g>

      {/* ============ FABRIC ICONS ============ */}
      {[disk, browser, memory].map((f) => {
        const isAccent = !!f.accent;
        const stroke = isAccent ? accent : rule;
        const sw = isAccent ? 1.25 : 1;
        const labelFill = isAccent ? accent : ink3;
        return (
          <g key={f.label}>
            <rect
              x={f.x}
              y={fabricY}
              width={fabricW}
              height={fabricH}
              rx={4}
              fill={bg}
              stroke={stroke}
              strokeWidth={sw}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={f.x + 12}
              y={fabricY + 18}
              style={{ fill: labelFill, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
            >
              fabric · {f.label}
            </text>
            <text
              x={f.x + 12}
              y={fabricY + 36}
              style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.18em' }}
            >
              {f.tag}
            </text>
            <text
              x={f.x + fabricW / 2}
              y={fabricY + 78}
              textAnchor="middle"
              style={{ fill: isAccent ? accent : ink2, fontFamily: MONO, fontSize: 22, fontWeight: 700 }}
            >
              42
            </text>
            <text
              x={f.x + fabricW / 2}
              y={fabricY + 98}
              textAnchor="middle"
              style={{ fill: ink4, fontFamily: MONO, fontSize: 8.5, letterSpacing: '0.24em' }}
            >
              value
            </text>
          </g>
        );
      })}

      {/* ============ CAPTION ============ */}
      <text
        x={40}
        y={340}
        style={{ fill: ink4, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        one ref · resolves in every fabric
      </text>
      <text
        x={520}
        y={340}
        textAnchor="end"
        style={{ fill: accent, fontFamily: MONO, fontSize: 9, letterSpacing: '0.24em' }}
      >
        interaction bridges them
      </text>
    </svg>
  );
}
