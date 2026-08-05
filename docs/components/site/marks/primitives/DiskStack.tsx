/**
 * DiskStack — the canonical rocksdb/storage substrate glyph.
 *
 *   ══════════  (top platter, opacity 1)
 *   │        │
 *   ┈┈┈┈┈┈┈┈  (middle platters, opacity fades toward centre)
 *   │  42   │  (optional bodyLabel or accent chip lives here)
 *   ┈┈┈┈┈┈┈┈
 *   │        │
 *   ══════════  (bottom platter, opacity 1)
 *
 * Adopts the platter-stack recipe from FabricGlyphs.VirtualsGlyph so every
 * disk on the site reads the same way. Configurable platter count so hero
 * (3 platters) and fabric/one-line (4 platters) can share the primitive.
 *
 * Colors read from CSS custom properties — pass a `stroke` override for
 * fixed inks. The optional `chip` renders a small accent-wash pill on
 * the second-to-top platter face (--site-accent* tokens).
 */
export interface DiskStackProps {
  /** Horizontal center of the stack. */
  cx: number;
  /** Y coordinate of the top platter's center. */
  topY: number;
  /** Number of platters (top + middles + bottom). Default 4. */
  platters?: number;
  /** Vertical distance between adjacent platter centers. Default 22. */
  platterGap?: number;
  /** Ellipse half-width. Default 36. */
  rx?: number;
  /** Ellipse half-height. Default 7. */
  ry?: number;
  /** Stroke color for every element. Default var(--site-ink-3). */
  stroke?: string;
  /** Bare text label centered in the body between platter[1] and platter[2]. */
  bodyLabel?: {
    text: string;
    fill?: string;
    fontSize?: number;
    fontWeight?: number;
    letterSpacing?: string;
    fontFamily?: string;
  };
  /** Accent-wash chip centered in the body — mutually exclusive with bodyLabel. */
  chip?: {
    text: string;
    width?: number;
    height?: number;
    /** Which gap (0-indexed) between platters holds the chip. Default 1. */
    gap?: number;
  };
}

const MONO = 'var(--font-mono)';

export function DiskStack({
  cx,
  topY,
  platters = 4,
  platterGap = 22,
  rx = 36,
  ry = 7,
  stroke = 'var(--site-ink-3)',
  bodyLabel,
  chip,
}: DiskStackProps) {
  const bottomY = topY + (platters - 1) * platterGap;
  const leftX = cx - rx;
  const rightX = cx + rx;

  // Progressive opacity fade toward the middle for the platters between
  // top and bottom (top + bottom stay at 1).
  const platterOpacity = (i: number) => {
    if (i === 0 || i === platters - 1) return 1;
    const middleCount = platters - 2;
    if (middleCount <= 0) return 1;
    // 0.7 for the first middle platter, easing down toward 0.5.
    return 0.7 - 0.15 * (i - 1) * (1 / Math.max(1, middleCount));
  };

  const accent = 'var(--site-accent)';
  const accentWash = 'var(--site-accent-wash)';
  const accentLine = 'var(--site-accent-line)';

  // Body chip / label center — sits in the gap between platter[gap] and
  // platter[gap+1].
  const chipGap = chip?.gap ?? 1;
  const bodyCy = topY + (chipGap + 0.5) * platterGap;

  return (
    <g>
      {/* side walls (span top platter cy → bottom platter cy) */}
      <line
        x1={leftX}
        y1={topY}
        x2={leftX}
        y2={bottomY}
        stroke={stroke}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <line
        x1={rightX}
        y1={topY}
        x2={rightX}
        y2={bottomY}
        stroke={stroke}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />

      {/* platters */}
      {Array.from({ length: platters }).map((_, i) => (
        <ellipse
          key={i}
          cx={cx}
          cy={topY + i * platterGap}
          rx={rx}
          ry={ry}
          fill="none"
          stroke={stroke}
          strokeWidth={1}
          opacity={platterOpacity(i)}
          vectorEffect="non-scaling-stroke"
        />
      ))}

      {/* body chip — accent-wash pill (--site-accent* tokens) */}
      {chip && (
        <>
          <rect
            x={cx - (chip.width ?? 68) / 2}
            y={bodyCy - (chip.height ?? 22) / 2}
            width={chip.width ?? 68}
            height={chip.height ?? 22}
            rx={3}
            fill={accentWash}
            stroke={accentLine}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={cx}
            y={bodyCy + 4}
            textAnchor="middle"
            style={{
              fill: accent,
              fontFamily: MONO,
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: '0.04em',
            }}
          >
            {chip.text}
          </text>
        </>
      )}

      {/* body label — bare text (used by fabric's tkv label + one-line's 42) */}
      {!chip && bodyLabel && (
        <text
          x={cx}
          y={bodyCy + (bodyLabel.fontSize ?? 13) / 3}
          textAnchor="middle"
          style={{
            fill: bodyLabel.fill ?? 'var(--site-ink)',
            fontFamily: bodyLabel.fontFamily ?? MONO,
            fontSize: bodyLabel.fontSize ?? 13,
            fontWeight: bodyLabel.fontWeight ?? 700,
            letterSpacing: bodyLabel.letterSpacing ?? '0.22em',
          }}
        >
          {bodyLabel.text}
        </text>
      )}
    </g>
  );
}
