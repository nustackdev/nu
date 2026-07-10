const MONO = 'var(--font-mono)';

/**
 * v1 snapshot — the "One line, two places" viz that reads
 * `counter.store(rocksdb)` in a mini sync.py file, with dotted drops to a
 * browser tab and a rocksdb disk. Zero hints, minimal chrome.
 * Kept alongside the enhanced v2 (`./one-line.tsx`) as a fallback pick.
 */
export function OneLineV1Svg({ className }: { className?: string }) {
  const accent = 'var(--nu-accent)';
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const codeBg = 'var(--nu-code-bg-2)';
  const bg = 'var(--color-fd-background)';

  const W = 480;
  const fileX = 64;
  const fileY = 22;
  const fileW = 352;
  const fileH = 92;
  const fileHeadH = 22;
  const codeBaselineY = fileY + fileHeadH + 42;

  const seg = {
    counter: { x: 150 },
    mid:     { x: 234 },
    rocksdb: { x: 318 },
    tail:    { x: 366 },
  };

  const browserCx = seg.counter.x;
  const diskCx = seg.rocksdb.x;
  const iconTopY = fileY + fileH + 40;

  return (
    <svg
      viewBox={`0 0 ${W} 288`}
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="v1 — counter.store(rocksdb) with dotted drops to browser tab and rocksdb."
      className={className}
    >
      <rect x={fileX} y={fileY} width={fileW} height={fileH} rx={4} fill={bg} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
      <rect x={fileX} y={fileY} width={fileW} height={fileHeadH} rx={4} fill={codeBg} />
      <rect x={fileX} y={fileY + fileHeadH - 4} width={fileW} height={4} fill={codeBg} />
      <line x1={fileX} y1={fileY + fileHeadH} x2={fileX + fileW} y2={fileY + fileHeadH} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
      <circle cx={fileX + 10} cy={fileY + 11} r={2.4} fill={ink4} />
      <circle cx={fileX + 18} cy={fileY + 11} r={2.4} fill={ink4} />
      <circle cx={fileX + 26} cy={fileY + 11} r={2.4} fill={ink4} />
      <text x={fileX + fileW / 2} y={fileY + 15} textAnchor="middle" style={{ fill: ink3, fontFamily: MONO, fontSize: 10.5, letterSpacing: '0.14em' }}>sync.py</text>

      <text x={fileX + 14} y={codeBaselineY} style={{ fill: ink4, fontFamily: MONO, fontSize: 12, letterSpacing: '0.02em' }}>1</text>
      <text x={seg.counter.x} y={codeBaselineY} textAnchor="middle" style={{ fill: accent, fontFamily: MONO, fontSize: 20, fontWeight: 700, letterSpacing: '0.02em' }}>counter</text>
      <text x={seg.mid.x} y={codeBaselineY} textAnchor="middle" style={{ fill: ink2, fontFamily: MONO, fontSize: 20, letterSpacing: '0.02em' }}>.store(</text>
      <text x={seg.rocksdb.x} y={codeBaselineY} textAnchor="middle" style={{ fill: accent, fontFamily: MONO, fontSize: 20, fontWeight: 700, letterSpacing: '0.02em' }}>rocksdb</text>
      <text x={seg.tail.x} y={codeBaselineY} textAnchor="middle" style={{ fill: ink2, fontFamily: MONO, fontSize: 20, letterSpacing: '0.02em' }}>)</text>

      <g fill="none" stroke={accent} strokeWidth={1} strokeDasharray="2 4" vectorEffect="non-scaling-stroke" opacity={0.85}>
        <line x1={browserCx} y1={fileY + fileH} x2={browserCx} y2={iconTopY} />
        <line x1={diskCx}    y1={fileY + fileH} x2={diskCx}    y2={iconTopY} />
      </g>
      <circle cx={browserCx} cy={fileY + fileH} r={2} fill={accent} />
      <circle cx={diskCx}    cy={fileY + fileH} r={2} fill={accent} />

      <g transform={`translate(${browserCx - 62} ${iconTopY})`}>
        <rect x={0} y={0} width={124} height={84} rx={4} fill={bg} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={0} y1={16} x2={124} y2={16} stroke={rule} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <circle cx={7} cy={8} r={1.8} fill={ink3} opacity={0.6} />
        <circle cx={13} cy={8} r={1.8} fill={ink3} opacity={0.6} />
        <circle cx={19} cy={8} r={1.8} fill={ink3} opacity={0.6} />
        <text x={62} y={60} textAnchor="middle" style={{ fill: ink, fontFamily: MONO, fontSize: 34, fontWeight: 700 }}>42</text>
      </g>
      <text x={browserCx} y={iconTopY + 104} textAnchor="middle" style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em' }}>browser tab</text>

      <g transform={`translate(${diskCx - 40} ${iconTopY + 4})`}>
        <ellipse cx={40} cy={6} rx={36} ry={7} fill="none" stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={4} y1={6} x2={4} y2={72} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <line x1={76} y1={6} x2={76} y2={72} stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <ellipse cx={40} cy={30} rx={36} ry={7} fill="none" stroke={ink3} strokeWidth={1} opacity={0.7} vectorEffect="non-scaling-stroke" />
        <ellipse cx={40} cy={54} rx={36} ry={7} fill="none" stroke={ink3} strokeWidth={1} opacity={0.55} vectorEffect="non-scaling-stroke" />
        <ellipse cx={40} cy={72} rx={36} ry={7} fill="none" stroke={ink3} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <text x={40} y={44} textAnchor="middle" style={{ fill: ink, fontFamily: MONO, fontSize: 22, fontWeight: 700 }}>42</text>
      </g>
      <text x={diskCx} y={iconTopY + 104} textAnchor="middle" style={{ fill: ink3, fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em' }}>rocksdb</text>
    </svg>
  );
}
