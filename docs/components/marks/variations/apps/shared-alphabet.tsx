/**
 * Shared alphabet — one primitive palette, many apps.
 *
 * Left panel: the primitives Nu ships (ref, interaction, shape, fabric)
 * with their exact glyphs. Right panel: two apps (nulog, nuspace)
 * composed from the *same* glyphs in different arrangements. Reads as
 * "learn one alphabet, know every app."
 */
export function SharedAlphabetSvg() {
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const mono = 'var(--font-mono)';

  // primitive glyph atoms
  const Ref = ({ x, y }: { x: number; y: number }) => (
    <circle cx={x} cy={y} r={5} fill="none" stroke={ink2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
  );
  const Op = ({ x, y }: { x: number; y: number }) => (
    <rect x={x - 6} y={y - 6} width={12} height={12} fill="none" stroke={ink2} strokeWidth={1} vectorEffect="non-scaling-stroke" />
  );
  const Fab = ({ x, y, w, h }: { x: number; y: number; w: number; h: number }) => (
    <rect x={x} y={y} width={w} height={h} fill="none" stroke={ink3} strokeWidth={1} strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
  );

  return (
    <svg
      viewBox="0 0 600 360"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Left panel names the four primitives; right panel shows nulog and nuspace composed from the same primitive glyphs."
    >
      {/* left panel — primitives */}
      <rect
        x={20}
        y={40}
        width={200}
        height={300}
        fill="none"
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={34}
        y={62}
        style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.28em' }}
      >
        primitives
      </text>
      <line x1={20} y1={72} x2={220} y2={72} stroke={ruleSoft} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* rows */}
      {[
        { y: 108, label: 'ref', glyph: <Ref x={64} y={108} /> },
        { y: 168, label: 'interaction', glyph: <Op x={64} y={168} /> },
        {
          y: 228,
          label: 'shape',
          glyph: (
            <text x={64} y={234} textAnchor="middle" style={{ fill: ink2, fontFamily: mono, fontSize: 18 }}>
              {'{ }'}
            </text>
          ),
        },
        {
          y: 292,
          label: 'fabric',
          glyph: <Fab x={50} y={280} w={28} h={22} />,
        },
      ].map((r) => (
        <g key={r.label}>
          {r.glyph}
          <text
            x={102}
            y={r.y + 4}
            style={{ fill: ink2, fontFamily: mono, fontSize: 11, letterSpacing: '0.18em' }}
          >
            {r.label}
          </text>
        </g>
      ))}

      {/* connector — palette becomes apps */}
      <g fill="none" stroke={accent} strokeWidth={1} vectorEffect="non-scaling-stroke" opacity={0.7}>
        <line x1={220} y1={190} x2={260} y2={190} strokeDasharray="4 3" />
      </g>
      <polygon points="258,186 268,190 258,194" fill={accent} opacity={0.75} />

      {/* right panel — apps */}
      <rect
        x={276}
        y={40}
        width={304}
        height={300}
        fill="none"
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={290}
        y={62}
        style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.28em' }}
      >
        apps · same glyphs, different sentences
      </text>
      <line x1={276} y1={72} x2={580} y2={72} stroke={accentLine} strokeWidth={1} vectorEffect="non-scaling-stroke" />

      {/* nulog composition — top half */}
      <g>
        <text x={296} y={98} style={{ fill: accent, fontFamily: mono, fontSize: 12, fontWeight: 700, letterSpacing: '0.14em' }}>
          nulog
        </text>
        <text x={352} y={98} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.22em' }}>
          shape: Log · fabric: rocksdb
        </text>
        <Fab x={296} y={112} w={266} h={64} />
        {/* Log shape braces */}
        <text x={318} y={148} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 14 }}>
          {'{ }'}
        </text>
        {/* three refs */}
        <Ref x={368} y={144} />
        <Ref x={396} y={144} />
        <Ref x={424} y={144} />
        {/* interaction — append */}
        <line x1={432} y1={144} x2={456} y2={144} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <Op x={468} y={144} />
        <text x={468} y={148} textAnchor="middle" style={{ fill: ink2, fontFamily: mono, fontSize: 8 }}>
          {'>>'}
        </text>
        <text x={490} y={148} style={{ fill: ink3, fontFamily: mono, fontSize: 9, letterSpacing: '0.16em' }}>
          append
        </text>
      </g>

      {/* nuspace composition — bottom half */}
      <g>
        <text x={296} y={218} style={{ fill: accent, fontFamily: mono, fontSize: 12, fontWeight: 700, letterSpacing: '0.14em' }}>
          nuspace
        </text>
        <text x={372} y={218} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.22em' }}>
          shape: Space · fabric: nudle
        </text>
        <Fab x={296} y={232} w={266} h={84} />
        {/* Space shape */}
        <text x={318} y={272} textAnchor="middle" style={{ fill: ink3, fontFamily: mono, fontSize: 14 }}>
          {'{ }'}
        </text>
        {/* three refs stacked and one op fanning to them (fork) */}
        <Op x={382} y={272} />
        <text x={382} y={276} textAnchor="middle" style={{ fill: ink2, fontFamily: mono, fontSize: 8 }}>
          {'>>'}
        </text>
        <g fill="none" stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke">
          <line x1={390} y1={272} x2={420} y2={272} />
          <line x1={420} y1={254} x2={420} y2={290} />
          <line x1={420} y1={254} x2={440} y2={254} />
          <line x1={420} y1={272} x2={440} y2={272} />
          <line x1={420} y1={290} x2={440} y2={290} />
        </g>
        <Ref x={448} y={254} />
        <Ref x={448} y={272} />
        <Ref x={448} y={290} />
        <text x={468} y={258} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.14em' }}>
          tab
        </text>
        <text x={468} y={276} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.14em' }}>
          tab
        </text>
        <text x={468} y={294} style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.14em' }}>
          tab
        </text>
      </g>

      {/* accent wash micro-bar between the two comps to underline "same alphabet" */}
      <rect
        x={296}
        y={188}
        width={266}
        height={12}
        fill={accentWash}
        stroke="none"
      />
      <text
        x={429}
        y={197}
        textAnchor="middle"
        style={{ fill: accent, fontFamily: mono, fontSize: 9, letterSpacing: '0.28em' }}
      >
        same alphabet
      </text>

      {/* bottom caption */}
      <text
        x={580}
        y={352}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        learn one, know them all
      </text>
    </svg>
  );
}
