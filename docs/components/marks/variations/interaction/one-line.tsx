const MONO = 'var(--font-mono)';

/**
 * v2 — one-line-two-places, made informative (anatomy-panel edition).
 *   The code sits inside a wide accent-wash panel — like the interaction-anatomy
 *   variant — rather than a file card. Bigger expression, quieter chrome.
 *   Colour code:
 *     purple = Refs (identifiers + their hint chips)
 *     blue   = Interaction (.store call + its hint chip)
 *   v1 snapshot lives at `./one-line-v1.tsx`.
 */
export function OneLineSvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const accent2Wash = 'var(--nu-accent-2-wash)';
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink3 = 'var(--nu-ink-3)';

  // canvas
  const W = 480;
  const H = 380;

  // ============ expression panel (anatomy-style) ============
  const panelX = 40;
  const panelW = 400;
  const panelY = 30;
  const panelH = 84;
  const panelBottomY = panelY + panelH; // 114

  // code segments — 22px mono, ~13.2px/char.
  // `counter_ref.store(db_ref)` = 25 chars → ~330px.
  const codeStartX = 76;                   // (W - 330) / 2 ≈ 75
  const seg = {
    counterRef: { x: codeStartX + 72  }, // "counter_ref"  → 148
    mid:        { x: codeStartX + 192 }, // ".store("      → 268
    dbRef:      { x: codeStartX + 273 }, // "db_ref"       → 349
    tail:       { x: codeStartX + 322 }, // ")"            → 398
  };
  const codeBaselineY = panelY + panelH / 2 + 8; // 80

  // icons align with the identifiers' centers → clean vertical drops
  const browserCx = seg.counterRef.x; // 148
  const diskCx    = seg.dbRef.x;      // 349
  const iconTopY  = panelBottomY + 84; // 198

  // ref hint chips sit at the midpoint of each drop
  const refChipY = panelBottomY + 32; // 146
  const chipH = 18;

  const iconLabelY = iconTopY + 104; // 302

  // interaction hint chip — long leader from `.store(` down between the icons
  const iChipCx = seg.mid.x; // 268
  const iChipW = 108;
  const iChipH = 22;
  const iChipY = H - 30;     // 350

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Anatomy of one Nu interaction — counter_ref.store(db_ref). Purple ui-ref/disk-ref chips label the Refs and drop to a browser tab and rocksdb disk; a blue leader drops from .store between them to an `interaction` chip below."
      className={className}
    >
      {/* ============ EXPRESSION PANEL — anatomy-style accent wash ============ */}
      <rect
        x={panelX}
        y={panelY}
        width={panelW}
        height={panelH}
        rx={4}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {/* inner corner ticks — the anatomy signature */}
      <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke" opacity={0.55}>
        <path d={`M ${panelX} ${panelY + 10} L ${panelX} ${panelY} L ${panelX + 10} ${panelY}`} />
        <path d={`M ${panelX + panelW - 10} ${panelY} L ${panelX + panelW} ${panelY} L ${panelX + panelW} ${panelY + 10}`} />
        <path d={`M ${panelX} ${panelBottomY - 10} L ${panelX} ${panelBottomY} L ${panelX + 10} ${panelBottomY}`} />
        <path d={`M ${panelX + panelW - 10} ${panelBottomY} L ${panelX + panelW} ${panelBottomY} L ${panelX + panelW} ${panelBottomY - 10}`} />
      </g>

      {/* ============ THE EXPRESSION ============ */}
      {/* counter_ref — purple (Ref) */}
      <text
        x={seg.counterRef.x}
        y={codeBaselineY}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: MONO, fontSize: 22, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        counter_ref
      </text>
      {/* .store( — blue (Interaction) */}
      <text
        x={seg.mid.x}
        y={codeBaselineY}
        textAnchor="middle"
        style={{ fill: accent2, fontFamily: MONO, fontSize: 22, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        .store(
      </text>
      {/* db_ref — purple (Ref) */}
      <text
        x={seg.dbRef.x}
        y={codeBaselineY}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: MONO, fontSize: 22, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        db_ref
      </text>
      {/* ) — blue (Interaction) */}
      <text
        x={seg.tail.x}
        y={codeBaselineY}
        textAnchor="middle"
        style={{ fill: accent2, fontFamily: MONO, fontSize: 22, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        )
      </text>

      {/* ============ REF DROPS + CHIPS (purple) ============ */}
      {/* left drop — above chip */}
      <line
        x1={browserCx}
        y1={panelBottomY}
        x2={browserCx}
        y2={refChipY}
        stroke={accent}
        strokeWidth={1}
        strokeDasharray="2 4"
        vectorEffect="non-scaling-stroke"
        opacity={0.85}
      />
      {/* left drop — below chip */}
      <line
        x1={browserCx}
        y1={refChipY + chipH}
        x2={browserCx}
        y2={iconTopY}
        stroke={accent}
        strokeWidth={1}
        strokeDasharray="2 4"
        vectorEffect="non-scaling-stroke"
        opacity={0.85}
      />
      {/* left chip: `ui ref` */}
      <rect
        x={browserCx - 30}
        y={refChipY}
        width={60}
        height={chipH}
        rx={9}
        fill={accentWash}
        stroke={accent}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={browserCx}
        y={refChipY + 12}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.22em', fontWeight: 700 }}
      >
        ui ref
      </text>

      {/* right drop — above chip */}
      <line
        x1={diskCx}
        y1={panelBottomY}
        x2={diskCx}
        y2={refChipY}
        stroke={accent}
        strokeWidth={1}
        strokeDasharray="2 4"
        vectorEffect="non-scaling-stroke"
        opacity={0.85}
      />
      {/* right drop — below chip */}
      <line
        x1={diskCx}
        y1={refChipY + chipH}
        x2={diskCx}
        y2={iconTopY}
        stroke={accent}
        strokeWidth={1}
        strokeDasharray="2 4"
        vectorEffect="non-scaling-stroke"
        opacity={0.85}
      />
      {/* right chip: `disk ref` */}
      <rect
        x={diskCx - 36}
        y={refChipY}
        width={72}
        height={chipH}
        rx={9}
        fill={accentWash}
        stroke={accent}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={diskCx}
        y={refChipY + 12}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: MONO, fontSize: 9.5, letterSpacing: '0.22em', fontWeight: 700 }}
      >
        disk ref
      </text>

      {/* anchor dots where the ref drops exit the panel (purple) */}
      <circle cx={browserCx} cy={panelBottomY} r={2} fill={accent} />
      <circle cx={diskCx}    cy={panelBottomY} r={2} fill={accent} />

      {/* ============ LEFT — BROWSER TAB with counter ============ */}
      <g transform={`translate(${browserCx - 62} ${iconTopY})`}>
        <rect
          x={0}
          y={0}
          width={124}
          height={84}
          rx={4}
          fill="var(--color-fd-background)"
          stroke={ink3}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <line x1={0} y1={16} x2={124} y2={16} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <circle cx={7} cy={8} r={1.8} fill={ink3} opacity={0.6} />
        <circle cx={13} cy={8} r={1.8} fill={ink3} opacity={0.6} />
        <circle cx={19} cy={8} r={1.8} fill={ink3} opacity={0.6} />
        <text
          x={62}
          y={60}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 34, fontWeight: 700 }}
        >
          42
        </text>
      </g>
      <text
        x={browserCx}
        y={iconLabelY}
        textAnchor="middle"
        style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em' }}
      >
        browser tab
      </text>

      {/* ============ RIGHT — ROCKSDB DISK ============ */}
      <g transform={`translate(${diskCx - 40} ${iconTopY + 4})`}>
        <ellipse cx={40} cy={6} rx={36} ry={7} fill="none" stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={4} y1={6} x2={4} y2={72} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={76} y1={6} x2={76} y2={72} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <ellipse cx={40} cy={30} rx={36} ry={7} fill="none" stroke={ink3} strokeWidth={1} opacity={0.7} vectorEffect="non-scaling-stroke" />
        <ellipse cx={40} cy={54} rx={36} ry={7} fill="none" stroke={ink3} strokeWidth={1} opacity={0.55} vectorEffect="non-scaling-stroke" />
        <ellipse cx={40} cy={72} rx={36} ry={7} fill="none" stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text
          x={40}
          y={44}
          textAnchor="middle"
          style={{ fill: ink, fontFamily: MONO, fontSize: 22, fontWeight: 700 }}
        >
          42
        </text>
      </g>
      <text
        x={diskCx}
        y={iconLabelY}
        textAnchor="middle"
        style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em' }}
      >
        rocksdb
      </text>

      {/* ============ INTERACTION HINT — bottom, long blue leader ============ */}
      <circle cx={iChipCx} cy={panelBottomY} r={2} fill={accent2} />
      <line
        x1={iChipCx}
        y1={panelBottomY}
        x2={iChipCx}
        y2={iChipY}
        stroke={accent2}
        strokeWidth={1}
        strokeDasharray="2 4"
        vectorEffect="non-scaling-stroke"
        opacity={0.85}
      />
      <rect
        x={iChipCx - iChipW / 2}
        y={iChipY}
        width={iChipW}
        height={iChipH}
        rx={11}
        fill={accent2Wash}
        stroke={accent2}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={iChipCx}
        y={iChipY + 14}
        textAnchor="middle"
        style={{ fill: accent2, fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em', fontWeight: 700 }}
      >
        interaction
      </text>
    </svg>
  );
}
