import { useId } from 'react';

/**
 * NustackLogo — rounded square (rx=5), a bold asymmetric chord contained
 * inside it, and a dot sitting on the line midpoint. Measure-zero, in one
 * glyph.
 *
 * The rect + line + dot are welded into one continuous shape via a subtle
 * gaussian goo filter (small blur + high-threshold alpha matrix), so the
 * T-junctions where line meets square edge round out into small fillets
 * while outer edges stay crisp.
 *
 * Two paint variants:
 *   silver — default, silver metallic gradient matching the hero wordmark
 *   accent — diagonal purple→blue (var(--nu-accent) top-left → var(--nu-accent-2)
 *            bottom-right), for palette-tinted contexts like the floating nav
 *
 * `weight` scales the stroke width for the rect + chord (default 3.2). Bump
 * it down slightly (~3.0) when the logo sits inside a compact chrome.
 */
type NustackLogoVariant = 'silver' | 'accent';

export function NustackLogo({
  size = 22,
  className,
  variant = 'silver',
  weight = 3.2,
}: {
  size?: number | string;
  className?: string;
  variant?: NustackLogoVariant;
  weight?: number;
}) {
  const gid = useId();
  const gradId = `nustack-logo-grad-${gid}`;
  const gooId = `nustack-logo-goo-${gid}`;
  const paint = `url(#${gradId})`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="1.4 1.4 21.2 21.2"
      overflow="visible"
      fill="none"
      className={className}
      aria-hidden
    >
      <defs>
        {variant === 'silver' ? (
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
        ) : (
          <linearGradient
            id={gradId}
            gradientUnits="userSpaceOnUse"
            x1="3"
            y1="3"
            x2="21"
            y2="21"
          >
            {/* Bright text-tuned purple → blue. Palette accents are
                background-weight; on the dark nav pill we need higher-
                luminance stops so the mark reads like foreground type. */}
            <stop offset="0%" stopColor="#c8a8ff" />
            <stop offset="100%" stopColor="#7fb0ff" />
          </linearGradient>
        )}

        <filter
          id={gooId}
          filterUnits="userSpaceOnUse"
          x="-4"
          y="-4"
          width="32"
          height="32"
          colorInterpolationFilters="sRGB"
        >
          <feGaussianBlur in="SourceGraphic" stdDeviation="0.8" result="blur" />
          <feColorMatrix
            in="blur"
            mode="matrix"
            values="1 0 0 0 0
                    0 1 0 0 0
                    0 0 1 0 0
                    0 0 0 32 -14"
          />
        </filter>
      </defs>

      <g filter={`url(#${gooId})`}>
        <rect
          x="3"
          y="3"
          width="18"
          height="18"
          rx="5"
          stroke={paint}
          strokeWidth={weight}
          fill={paint}
          fillOpacity="0.08"
        />
        <line
          x1="4"
          y1="16"
          x2="20"
          y2="7.5"
          stroke={paint}
          strokeWidth={weight}
          strokeLinecap="round"
        />
        {/* dot at line midpoint: (4 + 16·½, 16 − 8.5·½) */}
        <circle cx="12" cy="11.75" r="3.6" fill={paint} />
      </g>
    </svg>
  );
}
