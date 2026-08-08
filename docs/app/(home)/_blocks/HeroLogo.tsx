import { useId } from 'react';

/**
 * HeroLogo — home-page-exclusive rendering of the nu mark.
 * Currently identical to NuLogo (kept as a separate component so
 * hero-only tweaks don't leak into the shared mark).
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

  const uPath =
    'M3730 3203 c0 -973 2 -940 -66 -1076 -47 -93 -144 -190 -235 -234 -117 -58 -158 -63 -531 -63 l-338 0 0 681 0 680 -142 -3 c-160 -3 -178 -10 -217 -79 -21 -36 -21 -46 -21 -848 l0 -811 563 0 c350 0 586 4 623 11 379 67 675 365 734 739 6 41 10 402 10 973 l0 907 -190 0 -190 0 0 -877z';

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
      </defs>

      <g
        transform="translate(0,552) scale(0.1,-0.1)"
        fill={`url(#${gradId})`}
        stroke="none"
      >
        {/* n */}
        <path d="M2121 4065 c-376 -82 -653 -368 -711 -735 -6 -41 -10 -402 -10 -972 l0 -908 190 0 190 0 0 878 c0 968 -1 941 64 1070 19 37 51 86 71 110 54 62 155 130 238 161 l72 26 363 3 362 3 0 -681 0 -681 143 3 c132 3 145 5 172 26 68 53 64 1 65 900 l0 812 -572 -1 c-449 0 -587 -4 -637 -14z" />
        {/* u */}
        <path d={uPath} />
      </g>
    </svg>
  );
}
