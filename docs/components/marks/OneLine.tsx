import { BrowserChrome } from './primitives/BrowserChrome';
import { DiskStack } from './primitives/DiskStack';

const MONO = 'var(--font-mono)';

/**
 * OneLine — anatomy of one Nu interaction: `counter_ref.set(db_ref)`.
 *
 *   Two Ref chips (--nu-accent) drop from the two identifiers to a browser
 *   tab and a rocksdb disk (shared primitives). One Interaction chip
 *   (--nu-accent-2) drops from `.set(` between them.
 *
 * Palette is scoped at the section level (InteractionModelSection wraps in
 * a hue-carrier that remaps --nu-accent → sage, --nu-accent-2 → steel), so
 * this file stays semantic — it just says "Ref" and "Interaction".
 */
export function OneLineSvg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const accent2Wash = 'var(--nu-accent-2-wash)';
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
  // `counter_ref.set( db_ref )` = 25 chars (with 1-char pads around db_ref) → ~330px.
  const codeStartX = 76;                   // (W - 330) / 2 ≈ 75
  const seg = {
    counterRef: { x: codeStartX + 72  }, // "counter_ref"  → 148
    mid:        { x: codeStartX + 178 }, // ".set("        → 254
    dbRef:      { x: codeStartX + 264 }, // "db_ref"       → 340
    tail:       { x: codeStartX + 323 }, // ")"            → 399
  };
  const codeBaselineY = panelY + panelH / 2 + 8; // 80

  // icons align with the identifiers' centers → clean vertical drops
  const browserCx = seg.counterRef.x; // 148
  const diskCx    = seg.dbRef.x;      // 340
  const iconTopY  = panelBottomY + 84; // 198

  // ref hint chips sit at the midpoint of each drop
  const refChipY = panelBottomY + 32; // 146
  const chipH = 18;

  const iconLabelY = iconTopY + 104; // 302

  // interaction hint chip — long leader from `.set(` down between the icons
  const iChipCx = seg.mid.x; // 254
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
      aria-label="Anatomy of one Nu interaction — counter_ref.set(db_ref). Ref chips label the identifiers and drop to a browser tab and rocksdb disk; an Interaction chip drops from .set between them."
      className={className}
    >
      {/* ============ EXPRESSION PANEL — anatomy-style accent wash ============ */}
      <rect
        x={panelX}
        y={panelY}
        width={panelW}
        height={panelH}
        rx={3}
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
      {/* counter_ref — Ref */}
      <text
        x={seg.counterRef.x}
        y={codeBaselineY}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: MONO, fontSize: 22, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        counter_ref
      </text>
      {/* .set( — Interaction */}
      <text
        x={seg.mid.x}
        y={codeBaselineY}
        textAnchor="middle"
        style={{ fill: accent2, fontFamily: MONO, fontSize: 22, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        .set(
      </text>
      {/* db_ref — Ref */}
      <text
        x={seg.dbRef.x}
        y={codeBaselineY}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: MONO, fontSize: 22, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        db_ref
      </text>
      {/* ) — Interaction */}
      <text
        x={seg.tail.x}
        y={codeBaselineY}
        textAnchor="middle"
        style={{ fill: accent2, fontFamily: MONO, fontSize: 22, fontWeight: 700, letterSpacing: '0.02em' }}
      >
        )
      </text>

      {/* ============ REF DROPS + CHIPS ============ */}
      {/* left drop — above chip */}
      <line
        x1={browserCx}
        y1={panelBottomY}
        x2={browserCx}
        y2={refChipY}
        stroke={accent}
        strokeWidth={1}
        strokeDasharray="3 3"
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
        strokeDasharray="3 3"
        vectorEffect="non-scaling-stroke"
        opacity={0.85}
      />
      {/* left chip: `ui ref` */}
      <rect
        x={browserCx - 30}
        y={refChipY}
        width={60}
        height={chipH}
        rx={3}
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
        strokeDasharray="3 3"
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
        strokeDasharray="3 3"
        vectorEffect="non-scaling-stroke"
        opacity={0.85}
      />
      {/* right chip: `disk ref` */}
      <rect
        x={diskCx - 36}
        y={refChipY}
        width={72}
        height={chipH}
        rx={3}
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

      {/* anchor dots where the ref drops exit the panel */}
      <circle cx={browserCx} cy={panelBottomY} r={2} fill={accent} />
      <circle cx={diskCx}    cy={panelBottomY} r={2} fill={accent} />

      {/* ============ LEFT — BROWSER TAB (shared primitive) ============ */}
      <BrowserChrome x={browserCx - 62} y={iconTopY} width={124} height={84} />
      <text
        x={browserCx}
        y={iconTopY + 60}
        textAnchor="middle"
        style={{ fill: ink, fontFamily: MONO, fontSize: 34, fontWeight: 700 }}
      >
        42
      </text>
      <text
        x={browserCx}
        y={iconLabelY}
        textAnchor="middle"
        style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em' }}
      >
        browser tab
      </text>

      {/* ============ RIGHT — ROCKSDB DISK (shared primitive) ============ */}
      <DiskStack
        cx={diskCx}
        topY={iconTopY + 10}
        platters={4}
        platterGap={22}
        rx={36}
        ry={7}
        bodyLabel={{
          text: '42',
          fill: ink,
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: '0.02em',
        }}
      />
      <text
        x={diskCx}
        y={iconLabelY}
        textAnchor="middle"
        style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em' }}
      >
        kv storage
      </text>

      {/* ============ INTERACTION HINT — bottom, long leader ============ */}
      <circle cx={iChipCx} cy={panelBottomY} r={2} fill={accent2} />
      <line
        x1={iChipCx}
        y1={panelBottomY}
        x2={iChipCx}
        y2={iChipY}
        stroke={accent2}
        strokeWidth={1}
        strokeDasharray="3 3"
        vectorEffect="non-scaling-stroke"
        opacity={0.85}
      />
      <rect
        x={iChipCx - iChipW / 2}
        y={iChipY}
        width={iChipW}
        height={iChipH}
        rx={3}
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
