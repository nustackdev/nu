/**
 * The stack — landscape specimen frame, four layers, top → bottom:
 *
 *   interaction model   ← the theory  (dashed, subdued, sublabels)
 *   nu                  ← the platform  (purple wash, Interactions + Refs)
 *   fabrics             ← the substrates  (blue wash, worlds + their Refs)
 *   apps                ← on nu  (abstract app-tile clusters)
 *
 * Legends live on the left, chrome ticks at the corners, a mono version
 * stamp bottom-right. Pills lay out dynamically so labels never overlap;
 * each pill has a soft wash fill so text reads even against band washes.
 */
export function StackLayersSvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentSoft = 'var(--nu-accent-soft)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const accent2Wash = 'var(--nu-accent-2-wash)';
  const accent2Soft = 'var(--nu-accent-2-soft)';
  const accent2Line = 'var(--nu-accent-2-line)';
  const mono = 'var(--font-mono)';

  // ---------------------------------------------------------------- canvas
  const W = 960;
  const H = 480;

  // legend column & box column
  const legendRight = 178;
  const boxX = 194;
  const boxRight = 944;
  const boxW = boxRight - boxX;
  const boxH = 78;
  const appsBoxH = 108; // apps band taller so square tiles have breathing room
  const bandGap = 16;
  const bandStart = 44;
  const bandY = [
    bandStart,
    bandStart + 1 * (boxH + bandGap),
    bandStart + 2 * (boxH + bandGap),
    bandStart + 3 * (boxH + bandGap),
  ];
  // spine — vertical dashed rule at the boundary between legend + boxes
  const spineX = boxX - 12;

  // -------- pill layout: dynamic widths, no overlaps --------
  function layoutPills(labels: string[], startX: number, gap = 8) {
    const positions: Array<{ x: number; w: number }> = [];
    let cursor = startX;
    for (const label of labels) {
      const w = Math.max(48, labelWidth(label));
      positions.push({ x: cursor, w });
      cursor += w + gap;
    }
    return { positions, endX: cursor };
  }
  function labelWidth(label: string) {
    // ~7.4px per char at font-size 11 + 14 padding
    return Math.round(label.length * 7.4 + 16);
  }

  // pill rows
  const nuInteractions = ['Store', '+', '>>', 'React', 'Snapshot'];
  const nuRefs = ['DictRef', 'IntRef', 'StrRef', 'BytesRef', 'NodeRef'];
  const fabWorlds = ['mem', 'ui', 'rocksdb', 'ray'];
  const fabRefs = ['KH57Ref', 'CounterRef', 'TabRef', 'ActorRef'];

  const rowStartX = boxX + 118; // leaves room for row label on left of each row
  const nuIntLayout = layoutPills(nuInteractions, rowStartX);
  const nuRefLayout = layoutPills(nuRefs, rowStartX);
  const fabWorldLayout = layoutPills(fabWorlds, rowStartX);
  const fabRefLayout = layoutPills(fabRefs, rowStartX);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Nustack — a four-layer specimen: interaction model (theory), Nu (the platform), fabrics (substrates), apps on Nu."
    >
      {/* header rail — small eyebrow across the top */}
      <text
        x={boxX}
        y={28}
        style={{ fill: ink4, fontFamily: mono, fontSize: 10, letterSpacing: '0.28em' }}
      >
        the stack
      </text>
      <line
        x1={boxX + 74}
        y1={24}
        x2={boxRight}
        y2={24}
        stroke={ruleSoft}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />

      {/* ============ dashed spine — traces the boundary column ============ */}
      <line
        x1={spineX}
        y1={bandY[0]}
        x2={spineX}
        y2={bandY[3] + appsBoxH}
        stroke={ruleSoft}
        strokeWidth={1}
        strokeDasharray="2 4"
        vectorEffect="non-scaling-stroke"
      />
      {/* joint dots on the spine between bands */}
      {[0, 1, 2].map((i) => (
        <g key={i}>
          <circle cx={spineX} cy={bandY[i] + boxH + bandGap / 2} r={2.4} fill={ink3} />
        </g>
      ))}

      {/* ============ LAYER 1 · interaction model (dashed, subdued) ============ */}
      <BandLegend
        title="interaction model"
        subtitle="theory"
        y={bandY[0] + boxH / 2}
        rightX={legendRight}
        titleFill={ink2}
        subtitleFill={ink4}
        mono={mono}
      />
      <rect
        x={boxX}
        y={bandY[0]}
        width={boxW}
        height={boxH}
        rx={3}
        fill="none"
        stroke={ink3}
        strokeWidth={1}
        strokeDasharray="4 4"
        vectorEffect="non-scaling-stroke"
      />
      {/* three concepts, each with glyph + name + sublabel */}
      {[
        { label: 'ref', sub: 'address', glyph: 'circle', x: boxX + 60 },
        { label: 'interaction', sub: 'transition', glyph: 'square', x: boxX + 260 },
        { label: 'fabric', sub: 'world', glyph: 'dashed', x: boxX + 500 },
      ].map((c) => (
        <ConceptGroup
          key={c.label}
          x={c.x}
          cy={bandY[0] + boxH / 2}
          label={c.label}
          sub={c.sub}
          glyph={c.glyph as 'circle' | 'square' | 'dashed'}
          ink={ink}
          ink3={ink3}
          ink4={ink4}
          mono={mono}
        />
      ))}
      {/* trailing hint */}
      <text
        x={boxRight - 20}
        y={bandY[0] + boxH / 2 + 5}
        textAnchor="end"
        style={{ fill: ink3, fontFamily: mono, fontSize: 14, letterSpacing: '0.14em' }}
      >
        …
      </text>

      {/* ============ LAYER 2 · nu (purple wash) ============ */}
      <BandLegend
        title="nu"
        subtitle="the platform"
        y={bandY[1] + boxH / 2}
        rightX={legendRight}
        titleFill={accent}
        subtitleFill={ink4}
        mono={mono}
      />
      <rect
        x={boxX}
        y={bandY[1]}
        width={boxW}
        height={boxH}
        rx={3}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <RowLabel x={boxX + 16} y={bandY[1] + 26} text="interactions" fill={accent} mono={mono} />
      {nuIntLayout.positions.map((p, i) => (
        <FilledPill
          key={i}
          x={p.x}
          y={bandY[1] + 12}
          w={p.w}
          label={nuInteractions[i]}
          textFill={accent}
          fill={accentSoft}
          stroke={accentLine}
          mono={mono}
        />
      ))}
      <text
        x={nuIntLayout.endX + 2}
        y={bandY[1] + 27}
        style={{ fill: accent, fontFamily: mono, fontSize: 13, letterSpacing: '0.12em', opacity: 0.8 }}
      >
        …
      </text>
      <RowLabel x={boxX + 16} y={bandY[1] + 60} text="refs" fill={accent} mono={mono} />
      {nuRefLayout.positions.map((p, i) => (
        <FilledPill
          key={i}
          x={p.x}
          y={bandY[1] + 46}
          w={p.w}
          label={nuRefs[i]}
          textFill={accent}
          fill={accentSoft}
          stroke={accentLine}
          mono={mono}
        />
      ))}
      <text
        x={nuRefLayout.endX + 2}
        y={bandY[1] + 61}
        style={{ fill: accent, fontFamily: mono, fontSize: 13, letterSpacing: '0.12em', opacity: 0.8 }}
      >
        …
      </text>

      {/* ============ LAYER 3 · fabrics (blue wash) ============ */}
      <BandLegend
        title="fabrics"
        subtitle="substrates"
        y={bandY[2] + boxH / 2}
        rightX={legendRight}
        titleFill={accent2}
        subtitleFill={ink4}
        mono={mono}
      />
      <rect
        x={boxX}
        y={bandY[2]}
        width={boxW}
        height={boxH}
        rx={3}
        fill={accent2Wash}
        stroke={accent2Line}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <RowLabel x={boxX + 16} y={bandY[2] + 26} text="worlds" fill={accent2} mono={mono} />
      {fabWorldLayout.positions.map((p, i) => (
        <FilledPill
          key={i}
          x={p.x}
          y={bandY[2] + 12}
          w={p.w}
          label={fabWorlds[i]}
          textFill={accent2}
          fill={accent2Soft}
          stroke={accent2Line}
          mono={mono}
        />
      ))}
      <text
        x={fabWorldLayout.endX + 2}
        y={bandY[2] + 27}
        style={{ fill: accent2, fontFamily: mono, fontSize: 13, letterSpacing: '0.12em', opacity: 0.8 }}
      >
        …
      </text>
      <RowLabel x={boxX + 16} y={bandY[2] + 60} text="refs" fill={accent2} mono={mono} />
      {fabRefLayout.positions.map((p, i) => (
        <FilledPill
          key={i}
          x={p.x}
          y={bandY[2] + 46}
          w={p.w}
          label={fabRefs[i]}
          textFill={accent2}
          fill={accent2Soft}
          stroke={accent2Line}
          mono={mono}
        />
      ))}
      <text
        x={fabRefLayout.endX + 2}
        y={bandY[2] + 61}
        style={{ fill: accent2, fontFamily: mono, fontSize: 13, letterSpacing: '0.12em', opacity: 0.8 }}
      >
        …
      </text>

      {/* ============ LAYER 4 · apps (square app-tiles) ============ */}
      <BandLegend
        title="apps"
        subtitle="on nu"
        y={bandY[3] + appsBoxH / 2}
        rightX={legendRight}
        titleFill={ink2}
        subtitleFill={ink4}
        mono={mono}
      />
      <rect
        x={boxX}
        y={bandY[3]}
        width={boxW}
        height={appsBoxH}
        rx={3}
        fill="var(--nu-code-bg-2)"
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {/* six square app-tiles — each a mini iconic composition */}
      {(() => {
        const tileSize = 72;
        const count = 6;
        const gap = 20;
        const rowWidth = count * tileSize + (count - 1) * gap;
        const startX = boxX + (boxW - rowWidth - 60) / 2; // leave room for trailing "…"
        const cy = bandY[3] + appsBoxH / 2;
        return (
          <>
            {Array.from({ length: count }).map((_, i) => (
              <SquareAppTile
                key={i}
                x={startX + i * (tileSize + gap)}
                cy={cy}
                size={tileSize}
                variant={i}
                ink={ink}
                ink2={ink2}
                ink3={ink3}
                ink4={ink4}
                rule={rule}
                ruleSoft={ruleSoft}
                mono={mono}
              />
            ))}
            <text
              x={startX + rowWidth + 34}
              y={cy + 4}
              textAnchor="middle"
              style={{ fill: ink3, fontFamily: mono, fontSize: 16, letterSpacing: '0.18em' }}
            >
              …
            </text>
          </>
        );
      })()}
    </svg>
  );
}

/* -------------------------------------------------------------------------- */
/* helpers                                                                    */
/* -------------------------------------------------------------------------- */

function BandLegend({
  title,
  subtitle,
  y,
  rightX,
  titleFill,
  subtitleFill,
  mono,
}: {
  title: string;
  subtitle: string;
  y: number;
  rightX: number;
  titleFill: string;
  subtitleFill: string;
  mono: string;
}) {
  return (
    <g>
      <text
        x={rightX}
        y={y - 6}
        textAnchor="end"
        style={{ fill: titleFill, fontFamily: mono, fontSize: 13, letterSpacing: '0.18em', fontWeight: 700 }}
      >
        {title}
      </text>
      <text
        x={rightX}
        y={y + 14}
        textAnchor="end"
        style={{ fill: subtitleFill, fontFamily: mono, fontSize: 9.5, letterSpacing: '0.28em' }}
      >
        {subtitle}
      </text>
    </g>
  );
}

function RowLabel({
  x,
  y,
  text,
  fill,
  mono,
}: {
  x: number;
  y: number;
  text: string;
  fill: string;
  mono: string;
}) {
  return (
    <text
      x={x}
      y={y}
      style={{ fill, fontFamily: mono, fontSize: 9, letterSpacing: '0.28em', opacity: 0.72, fontWeight: 700 }}
    >
      {text}
    </text>
  );
}

function FilledPill({
  x,
  y,
  w,
  label,
  textFill,
  fill,
  stroke,
  mono,
}: {
  x: number;
  y: number;
  w: number;
  label: string;
  textFill: string;
  fill: string;
  stroke: string;
  mono: string;
}) {
  const h = 22;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={3}
        fill={fill}
        stroke={stroke}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={x + w / 2}
        y={y + 15}
        textAnchor="middle"
        style={{ fill: textFill, fontFamily: mono, fontSize: 11, letterSpacing: '0.06em', fontWeight: 700 }}
      >
        {label}
      </text>
    </g>
  );
}

function ConceptGroup({
  x,
  cy,
  label,
  sub,
  glyph,
  ink,
  ink3,
  ink4,
  mono,
}: {
  x: number;
  cy: number;
  label: string;
  sub: string;
  glyph: 'circle' | 'square' | 'dashed';
  ink: string;
  ink3: string;
  ink4: string;
  mono: string;
}) {
  const gy = cy - 4;
  return (
    <g>
      <g fill="none" stroke={ink} strokeWidth={1.4} vectorEffect="non-scaling-stroke">
        {glyph === 'circle' && <circle cx={x} cy={gy} r={9} />}
        {glyph === 'square' && <rect x={x - 9} y={gy - 9} width={18} height={18} />}
        {glyph === 'dashed' && (
          <rect x={x - 12} y={gy - 11} width={24} height={22} strokeDasharray="3 3" />
        )}
      </g>
      <text
        x={x + 22}
        y={cy - 1}
        style={{ fill: ink, fontFamily: mono, fontSize: 13.5, letterSpacing: '0.1em', fontWeight: 700 }}
      >
        {label}
      </text>
      <text
        x={x + 22}
        y={cy + 15}
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        {sub}
      </text>
    </g>
  );
}

function SquareAppTile({
  x,
  cy,
  size,
  variant,
  ink,
  ink2,
  ink3,
  ink4,
  rule,
  ruleSoft,
  mono,
}: {
  x: number;
  cy: number;
  size: number;
  variant: number;
  ink: string;
  ink2: string;
  ink3: string;
  ink4: string;
  rule: string;
  ruleSoft: string;
  mono: string;
}) {
  const y = cy - size / 2;
  const chromeH = 14;
  const bodyY = y + chromeH;
  const bodyH = size - chromeH;
  const bodyCx = x + size / 2;
  const bodyCy = bodyY + bodyH / 2;

  return (
    <g>
      {/* the tile — solid backdrop so shapes read clearly */}
      <rect
        x={x}
        y={y}
        width={size}
        height={size}
        rx={5}
        fill="var(--color-fd-background)"
        stroke={ink3}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {/* header rule inside the tile — hints at "app chrome" */}
      <line
        x1={x}
        y1={y + chromeH}
        x2={x + size}
        y2={y + chromeH}
        stroke={ruleSoft}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {/* chrome dots top-left */}
      {[0, 1, 2].map((i) => (
        <circle key={i} cx={x + 6 + i * 5} cy={y + 7} r={1.4} fill={ink3} />
      ))}

      {/* body — iconic composition per variant, bold weight */}
      <g fill="none" stroke={ink} strokeWidth={1.6} vectorEffect="non-scaling-stroke">
        {variant === 0 && (
          <>
            {/* stacked bars — logs */}
            <rect x={bodyCx - 18} y={bodyCy - 12} width={36} height={5} rx={1} />
            <rect x={bodyCx - 18} y={bodyCy - 3} width={26} height={5} rx={1} />
            <rect x={bodyCx - 18} y={bodyCy + 6} width={32} height={5} rx={1} />
          </>
        )}
        {variant === 1 && (
          <>
            {/* concentric circles — workspace / atom */}
            <circle cx={bodyCx} cy={bodyCy} r={16} />
            <circle cx={bodyCx} cy={bodyCy} r={8} />
            <circle cx={bodyCx} cy={bodyCy} r={2} fill={ink} />
          </>
        )}
        {variant === 2 && (
          <>
            {/* triangle + line — pipeline */}
            <path d={`M ${bodyCx - 14} ${bodyCy + 10} L ${bodyCx} ${bodyCy - 14} L ${bodyCx + 14} ${bodyCy + 10} Z`} />
            <line x1={bodyCx - 18} y1={bodyCy + 15} x2={bodyCx + 18} y2={bodyCy + 15} strokeDasharray="3 3" />
          </>
        )}
        {variant === 3 && (
          <>
            {/* grid — table / dashboard */}
            <rect x={bodyCx - 16} y={bodyCy - 12} width={14} height={11} />
            <rect x={bodyCx + 2} y={bodyCy - 12} width={14} height={11} />
            <rect x={bodyCx - 16} y={bodyCy + 2} width={14} height={11} />
            <rect x={bodyCx + 2} y={bodyCy + 2} width={14} height={11} />
          </>
        )}
        {variant === 4 && (
          <>
            {/* diamond + node — graph */}
            <path d={`M ${bodyCx} ${bodyCy - 16} L ${bodyCx + 16} ${bodyCy} L ${bodyCx} ${bodyCy + 16} L ${bodyCx - 16} ${bodyCy} Z`} />
            <circle cx={bodyCx} cy={bodyCy} r={3} fill={ink} />
          </>
        )}
        {variant === 5 && (
          <>
            {/* rounded square + tick — inbox / notes */}
            <rect x={bodyCx - 15} y={bodyCy - 14} width={30} height={28} rx={4} />
            <line x1={bodyCx - 8} y1={bodyCy - 3} x2={bodyCx + 8} y2={bodyCy - 3} />
            <line x1={bodyCx - 8} y1={bodyCy + 4} x2={bodyCx + 5} y2={bodyCy + 4} />
          </>
        )}
      </g>
    </g>
  );
}
