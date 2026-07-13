import s from './marks.module.css';
import { BrowserChrome } from './primitives/BrowserChrome';

/**
 * nulog — running app mock.
 *
 * BrowserChrome (shared) hosts the app title strip with a pulsing `live`
 * dot, five log rows with timestamp / level / message / ref payload, and
 * a footer strip that names the substrate.
 */
export function NulogMockSvg() {
  const rule = 'var(--nu-rule)';
  const ink = 'var(--nu-ink)';
  const ink2 = 'var(--nu-ink-2)';
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const accent = 'var(--nu-accent)';
  const accentWash = 'var(--nu-accent-wash)';
  const accentLine = 'var(--nu-accent-line)';
  const accent2 = 'var(--nu-accent-2)';
  const mono = 'var(--font-mono)';

  const rows: Array<{ t: string; level: 'info' | 'warn'; msg: string; payload: string }> = [
    { t: '15:24:03', level: 'info', msg: 'order.placed', payload: '{ id: "o_9x2" }' },
    { t: '15:24:04', level: 'warn', msg: 'payment.retry', payload: '{ attempt: 2 }' },
    { t: '15:24:05', level: 'info', msg: 'webhook.received', payload: '{ src: "stripe" }' },
    { t: '15:24:06', level: 'info', msg: 'order.shipped', payload: '{ id: "o_9x2" }' },
    { t: '15:24:07', level: 'info', msg: 'email.sent', payload: '{ to: "…" }' },
  ];

  return (
    <svg
      viewBox="0 0 480 320"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="nulog running: browser chrome, live pill, five log rows with structured payloads, footer identifying rocksdb + shape."
    >
      {/* browser window (shared primitive) with URL bar */}
      <BrowserChrome
        x={16}
        y={16}
        width={448}
        height={288}
        chromeHeight={28}
        url="nu://nulog"
        dotRadius={2.6}
        dotSpacing={10}
      />

      {/* title band */}
      <text
        x={30}
        y={68}
        style={{ fill: ink3, fontFamily: mono, fontSize: 9.5, letterSpacing: '0.24em' }}
      >
        app
      </text>
      <text
        x={30}
        y={92}
        style={{
          fill: accent,
          fontFamily: mono,
          fontSize: 20,
          fontWeight: 700,
          letterSpacing: '0.08em',
        }}
      >
        nulog
      </text>
      {/* live pill */}
      <g>
        <circle cx={402} cy={82} r={3} fill={accent2} className={s.blink} />
        <text
          x={410}
          y={86}
          style={{ fill: accent2, fontFamily: mono, fontSize: 10, letterSpacing: '0.24em' }}
        >
          live
        </text>
      </g>

      {/* header rule */}
      <line
        x1={30}
        y1={108}
        x2={450}
        y2={108}
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />

      {/* column labels */}
      <g>
        <text x={30} y={124} style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}>
          time
        </text>
        <text x={102} y={124} style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}>
          level
        </text>
        <text x={162} y={124} style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}>
          msg
        </text>
        <text x={310} y={124} style={{ fill: ink4, fontFamily: mono, fontSize: 8.5, letterSpacing: '0.24em' }}>
          ref
        </text>
      </g>

      {/* log rows */}
      {rows.map((r, i) => {
        const y = 148 + i * 22;
        const levelColor = r.level === 'warn' ? accent2 : ink2;
        return (
          <g key={i}>
            <text x={30} y={y} style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.04em' }}>
              {r.t}
            </text>
            <text x={102} y={y} style={{ fill: levelColor, fontFamily: mono, fontSize: 10, letterSpacing: '0.14em' }}>
              {r.level}
            </text>
            <text x={162} y={y} style={{ fill: ink, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em' }}>
              {r.msg}
            </text>
            <text x={310} y={y} style={{ fill: ink3, fontFamily: mono, fontSize: 10, letterSpacing: '0.02em' }}>
              {r.payload}
            </text>
          </g>
        );
      })}

      {/* footer strip — wash band */}
      <rect
        x={16}
        y={272}
        width={448}
        height={32}
        rx={3}
        fill={accentWash}
        stroke={accentLine}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={30}
        y={292}
        style={{ fill: accent, fontFamily: mono, fontSize: 10, letterSpacing: '0.22em' }}
      >
        built on nu · shape=Log · fabric=rocksdb
      </text>
      <text
        x={450}
        y={292}
        textAnchor="end"
        style={{ fill: ink4, fontFamily: mono, fontSize: 9, letterSpacing: '0.24em' }}
      >
        one of the apps
      </text>
    </svg>
  );
}
