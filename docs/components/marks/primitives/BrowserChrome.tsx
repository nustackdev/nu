import s from '../marks.module.css';

/**
 * BrowserChrome — the canonical browser tab used in every landing SVG.
 *
 *   ┌──────────────────────────────────────────┐  rx=3, hairline stroke
 *   │ ● ● ●   [address bar (optional)]   ○ live│  22px chrome by default
 *   ├──────────────────────────────────────────┤
 *   │                                          │  body area — caller draws
 *   │             (caller content)             │  its own content here
 *   │                                          │
 *   └──────────────────────────────────────────┘
 *
 * The primitive renders only the frame + chrome bar decorations (traffic
 * lights, optional address bar, optional live pill). Body content is the
 * caller's responsibility — place elements inside the same parent <svg> at
 * (x + pad, y + chromeHeight + pad).
 *
 * All colors read from CSS custom properties, so the chrome auto-recolors
 * when a parent section overrides --nu-accent[-2] (fabric/apps rows do this
 * per-row; hero/interaction-model do it at the section wrap).
 */
export interface BrowserChromeProps {
  x: number;
  y: number;
  width: number;
  height: number;

  /** Show an address bar with this URL. Omit for a bare chrome. */
  url?: string;
  /** Show a pulsing "live" dot + label on the right side of the chrome. */
  live?: boolean;
  /** Corner radius. Default 3 (gentle round). */
  rx?: number;
  /** Chrome bar height. Default 22. */
  chromeHeight?: number;
  /** Traffic-light dot radius. Default 2.2. */
  dotRadius?: number;
  /** Space between traffic-light dot centers. Default 8. */
  dotSpacing?: number;
}

export function BrowserChrome({
  x,
  y,
  width,
  height,
  url,
  live,
  rx = 3,
  chromeHeight = 22,
  dotRadius = 2.2,
  dotSpacing = 8,
}: BrowserChromeProps) {
  const ink3 = 'var(--nu-ink-3)';
  const ink4 = 'var(--nu-ink-4)';
  const rule = 'var(--nu-rule)';
  const ruleSoft = 'var(--nu-rule-2)';
  const accent = 'var(--nu-accent)';
  const bg = 'var(--color-fd-background)';
  const mono = 'var(--font-mono)';

  const dividerY = y + chromeHeight;
  const dotCy = y + chromeHeight / 2;
  const dotStart = x + 12;
  const dotsEnd = dotStart + 2 * dotSpacing + dotRadius;

  const livePillW = 34;
  const liveCx = x + width - livePillW;
  const liveTextX = liveCx + 6;

  const addressBarLeft = dotsEnd + 8;
  const addressBarRight = live ? liveCx - 10 : x + width - 12;
  const addressBarW = addressBarRight - addressBarLeft;
  const addressBarH = Math.max(chromeHeight - 8, 12);
  const addressBarY = y + (chromeHeight - addressBarH) / 2;
  const addressBarTextY = addressBarY + addressBarH / 2 + 3;

  return (
    <g>
      {/* body */}
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        rx={rx}
        fill={bg}
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {/* chrome divider */}
      <line
        x1={x}
        y1={dividerY}
        x2={x + width}
        y2={dividerY}
        stroke={rule}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {/* traffic-light dots */}
      {[0, 1, 2].map((i) => (
        <circle
          key={i}
          cx={dotStart + i * dotSpacing}
          cy={dotCy}
          r={dotRadius}
          fill={ink4}
        />
      ))}
      {/* address bar */}
      {url && addressBarW > 24 && (
        <>
          <rect
            x={addressBarLeft}
            y={addressBarY}
            width={addressBarW}
            height={addressBarH}
            rx={2}
            fill="var(--nu-code-bg-2)"
            stroke={ruleSoft}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={addressBarLeft + 8}
            y={addressBarTextY}
            style={{
              fill: ink3,
              fontFamily: mono,
              fontSize: 9,
              letterSpacing: '0.04em',
            }}
          >
            {url}
          </text>
        </>
      )}
      {/* live pill (right side of chrome bar) */}
      {live && (
        <>
          <circle
            cx={liveCx}
            cy={dotCy}
            r={dotRadius}
            fill={accent}
            className={s.blink}
          />
          <text
            x={liveTextX}
            y={dotCy + 3}
            style={{
              fill: accent,
              fontFamily: mono,
              fontSize: 8.5,
              letterSpacing: '0.24em',
            }}
          >
            live
          </text>
        </>
      )}
    </g>
  );
}
