import { useId } from 'react';

/**
 * HeroLogo — home-page-exclusive fork of NuLogo.
 *
 * Current deviations from NuLogo:
 *   - u letter carries a partial white outline hugging ONLY its outer
 *     left and bottom edges: full strength at the bottom-left corner,
 *     fading out up the left edge and right along the bottom.
 *
 * Approach: two OPEN paths extracted straight from the u path's outline —
 * one tracing the outer left edge (top-left angle → bottom-left corner),
 * one tracing the outer bottom edge (bottom-left corner → end of the
 * bottom-right curve). Each is stroked with its own fading linear
 * gradient. No masks, no strips.
 *
 * Gradient coords: the paths live inside translate(0,552) scale(0.1,-0.1),
 * and userSpaceOnUse gradients resolve in the referencing element's local
 * (path) space — so the viewBox-space landmark constants below are
 * converted to path space (px = vx * 10, py = (552 - vy) * 10) at use.
 */
export function HeroLogo({
  size,
  className,
  from = '#7a4ce0',
  to = '#3e72e7',
}: {
  size?: number | string;
  className?: string;
  from?: string;
  to?: string;
}) {
  const gid = useId();
  const gradId = `hero-logo-grad-${gid}`;
  const leftGradId = `hero-logo-u-left-${gid}`;
  const bottomGradId = `hero-logo-u-bottom-${gid}`;
  const nTopGradId = `hero-logo-n-top-${gid}`;
  const nRightGradId = `hero-logo-n-right-${gid}`;

  // u letter outer edges in viewBox coords (viewBox "140 144 271 263"). Tune by eye.
  const U_LEFT_X = 218; // outer left edge of u (path x 2180)
  const U_BOTTOM_Y = 407; // outer bottom edge of u (path y 1450)
  const U_TOP_Y = 241; // where left outline ends (just below top curvature) — fade fully transparent here
  const U_RIGHT_X = 337; // where bottom outline ends (just before right curvature) — fade fully transparent here

  // n letter outer edges — mirror of u, hugging top-right corner.
  const N_RIGHT_X = 333; // outer right edge of n (path x 3330)
  const N_TOP_Y = 144; // outer top edge of n (path y 4080)
  const N_TOP_LEFT_END_X = 276; // where top outline starts (just past the left shoulder curve) — fade fully transparent here
  const N_RIGHT_BOTTOM_END_Y = 195; // where right outline ends — fade fully transparent here

  // viewBox → path space (inverse of translate(0,552) scale(0.1,-0.1)).
  const px = (vx: number) => vx * 10;
  const py = (vy: number) => (552 - vy) * 10;

  const uPath =
    'M3730 3203 c0 -973 2 -940 -66 -1076 -47 -93 -144 -190 -235 -234 -117 -58 -158 -63 -531 -63 l-338 0 0 681 0 680 -142 -3 c-160 -3 -178 -10 -217 -79 -21 -36 -21 -46 -21 -848 l0 -811 563 0 c350 0 586 4 623 11 379 67 675 365 734 739 6 41 10 402 10 973 l0 907 -190 0 -190 0 0 -877z';

  // Outer LEFT edge of u, trimmed to skip the top shoulder curvature:
  // starts just below the top curve (2201,3109) → straight down to bottom-left corner (2180,1450).
  const uLeftEdge = 'M2201 3109 c-21 -36 -21 -46 -21 -848 l0 -811';

  // Outer BOTTOM edge of u, trimmed to stop before the sharp right curvature:
  // bottom-left corner (2180,1450) → along the bottom, ending at (3366,1461).
  const uBottomEdge = 'M2180 1450 l563 0 c350 0 586 4 623 11';

  // Outer TOP edge of n, trimmed to skip the top-left shoulder curvature:
  // just past the shoulder (2758,4079) → straight across to top-right corner (3330,4080).
  const nTopEdge = 'M2758 4079 l572 1';

  // Outer RIGHT edge of n, trimmed to stop before the bottom-right curvature:
  // top-right corner (3330,4080) → straight down to (3330,3268).
  const nRightEdge = 'M3330 4080 l0 -812';

  return (
    <svg
      viewBox="140 144 271 263"
      width={size}
      height={size}
      className={className}
      aria-hidden
      overflow="visible"
    >
      <defs>
        <linearGradient
          id={gradId}
          gradientUnits="userSpaceOnUse"
          x1="1400"
          y1="4080"
          x2="4110"
          y2="1450"
        >
          <stop offset="0.5" stopColor={from} />
          <stop offset="0.5" stopColor={to} />
        </linearGradient>

        {/* Left edge fade: transparent at top (U_TOP_Y) → opaque at bottom (U_BOTTOM_Y). */}
        <linearGradient
          id={leftGradId}
          gradientUnits="userSpaceOnUse"
          x1="0"
          y1={py(U_TOP_Y)}
          x2="0"
          y2={py(U_BOTTOM_Y)}
        >
          <stop offset="0" stopColor="#fff" stopOpacity="0" />
          <stop offset="1" stopColor="#fff" stopOpacity="0.5" />
        </linearGradient>

        {/* Bottom edge fade: opaque at left (U_LEFT_X) → transparent at right (U_RIGHT_X). */}
        <linearGradient
          id={bottomGradId}
          gradientUnits="userSpaceOnUse"
          x1={px(U_LEFT_X)}
          y1="0"
          x2={px(U_RIGHT_X)}
          y2="0"
        >
          <stop offset="0" stopColor="#fff" stopOpacity="1" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>

        {/* Top edge fade: transparent at left (N_TOP_LEFT_END_X) → opaque at right (N_RIGHT_X, corner). */}
        <linearGradient
          id={nTopGradId}
          gradientUnits="userSpaceOnUse"
          x1={px(N_TOP_LEFT_END_X)}
          y1="0"
          x2={px(N_RIGHT_X)}
          y2="0"
        >
          <stop offset="0" stopColor="#fff" stopOpacity="0" />
          <stop offset="1" stopColor="#fff" stopOpacity="0.5" />
        </linearGradient>

        {/* Right edge fade: opaque at top (N_TOP_Y, corner) → transparent at bottom (N_RIGHT_BOTTOM_END_Y). */}
        <linearGradient
          id={nRightGradId}
          gradientUnits="userSpaceOnUse"
          x1="0"
          y1={py(N_TOP_Y)}
          x2="0"
          y2={py(N_RIGHT_BOTTOM_END_Y)}
        >
          <stop offset="0" stopColor="#fff" stopOpacity="0.5" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>

      </defs>

      {/* Fills — the visible nu letters */}
      <g
        transform="translate(0,552) scale(0.1,-0.1)"
        fill={`url(#${gradId})`}
        stroke="none"
      >
        {/* n */}
        <path d="M2121 4065 c-376 -82 -653 -368 -711 -735 -6 -41 -10 -402 -10 -972 l0 -908 190 0 190 0 0 878 c0 968 -1 941 64 1070 19 37 51 86 71 110 54 62 155 130 238 161 l72 26 363 3 362 3 0 -681 0 -681 143 3 c132 3 145 5 172 26 68 53 64 1 65 900 l0 812 -572 -1 c-449 0 -587 -4 -637 -14z" />
        {/* u fill */}
        <path d={uPath} />
      </g>

      {/* Outer outline overlays — fading gradient on n's top-right. */}
      <g data-hero-outline transform="translate(0,552) scale(0.1,-0.1)">
        {/* HIDDEN — u's bottom-left fading outline.
        <path d={uLeftEdge}   fill="none" stroke={`url(#${leftGradId})`}   strokeWidth="3" vectorEffect="non-scaling-stroke" strokeLinecap="round" />
        <path d={uBottomEdge} fill="none" stroke={`url(#${bottomGradId})`} strokeWidth="3" vectorEffect="non-scaling-stroke" strokeLinecap="round" />
        */}
        <path d={nTopEdge}    fill="none" stroke={`url(#${nTopGradId})`}   strokeWidth="3" vectorEffect="non-scaling-stroke" strokeLinecap="round" />
        <path d={nRightEdge}  fill="none" stroke={`url(#${nRightGradId})`} strokeWidth="3" vectorEffect="non-scaling-stroke" strokeLinecap="round" />
      </g>
    </svg>
  );
}
