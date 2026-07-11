import { useId } from 'react';

/**
 * NustackLogo — a square with a diagonal line crossing through it,
 * and a dot sitting exactly on the line. The concept: darts thrown
 * into a 2D space (the square). Landing on the line is possible,
 * but the probability is zero. Measure-zero, in one glyph.
 *
 * Paints in the same silver metallic gradient used by the "stack"
 * portion of the hero wordmark so the mark reads coherent with the
 * type it sits beside.
 */
export function NustackLogo({
  size = 22,
  className,
}: {
  size?: number | string;
  className?: string;
}) {
  const gid = useId();
  const gradId = `nustack-logo-silver-${gid}`;
  const paint = `url(#${gradId})`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="-2 -2 28 28"
      fill="none"
      className={className}
      aria-hidden
    >
      <defs>
        {/* Silver metallic — matches --wm-stack-grad (dark theme) so the
            mark reads coherent with the "stack" letters next to it. Uses
            userSpaceOnUse so the gradient spans the whole SVG, giving
            each shape the same tonal band based on its vertical position. */}
        <linearGradient
          id={gradId}
          gradientUnits="userSpaceOnUse"
          x1="12"
          y1="-2"
          x2="12"
          y2="26"
        >
          <stop offset="0%" stopColor="#eae8f4" />
          <stop offset="22%" stopColor="#eae8f4" />
          <stop offset="50%" stopColor="#d5d3e4" />
          <stop offset="72%" stopColor="#b3b0c8" />
          <stop offset="100%" stopColor="#eae8f4" />
        </linearGradient>
      </defs>

      {/* square — the sample space. Subtle silver wash inside so the
          mark reads as a filled tile rather than a hollow frame. */}
      <rect
        x="3"
        y="3"
        width="18"
        height="18"
        rx="2"
        stroke={paint}
        strokeWidth="2.25"
        fill={paint}
        fillOpacity="0.08"
      />
      {/* asymmetric diagonal — slope = -1/3, enters left edge of the
          square at y=15 (2/3 down), exits right edge at y=9 (1/3 down).
          20% longer than the square-inscribed version, so it visibly
          "crosses" the square rather than nicking its edges.
          Light bottom shadow so the line reads as sitting ON the square. */}
      <line
        x1="-0.6"
        y1="16.2"
        x2="24.6"
        y2="7.8"
        stroke={paint}
        strokeWidth="2.25"
        strokeLinecap="round"
        style={{ filter: 'drop-shadow(0 1px 0.6px rgba(0, 0, 0, 0.22))' }}
      />
      {/* dot on the line — dart that landed exactly on it.
          At the segment midpoint: ((-0.6+24.6)/2, (16.2+7.8)/2) = (12, 12).
          Same light bottom shadow so the dot reads as sitting ON the line. */}
      <circle
        cx="12"
        cy="12"
        r="2.85"
        fill={paint}
        style={{ filter: 'drop-shadow(0 1.5px 1px rgba(0, 0, 0, 0.35))' }}
      />
    </svg>
  );
}
