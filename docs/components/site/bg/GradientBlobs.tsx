import type { CSSProperties } from 'react';
import s from './GradientBlobs.module.css';

export interface Blob {
  /** Color at the blob center (any valid CSS color). */
  color: string;
  /** Horizontal anchor inside the 4000px band (e.g. "1800px"). */
  x: string;
  /** Vertical anchor from top (e.g. "0", "500px"). */
  y: string;
  /** Blob diameter as `<w> <h>` or a single length. Default "1300px 1400px". */
  size?: string;
  /** Opacity applied via color-mix; not currently used — pass alpha in `color`. */
  opacity?: number;
}

export interface GradientBlobsProps {
  blobs: Blob[];
  /** Band height. Default "1700px" (matches live hero). */
  height?: string;
  className?: string;
  style?: CSSProperties;
}

/**
 * HERO_BLOBS — the exact two-blob config that matches the current live hero
 * (purple bloom top-left + blue bloom right). Colors + anchors sourced from
 * app/(home)/_shell/Backdrop.module.css .heroBg.
 */
export const HERO_BLOBS: Blob[] = [
  {
    color: 'rgb(122 76 224 / 0.78)',
    x: '1800px',
    y: '0px',
    size: '1300px 1400px',
  },
  {
    color: 'rgb(62 114 231 / 0.66)',
    x: '2500px',
    y: '500px',
    size: '1400px 1400px',
  },
];

function blobLayer(b: Blob): string {
  const size = b.size ?? '1300px 1400px';
  // Purple bloom-style stops keep the two live-hero blobs identical; a
  // single-stop fallback also works for arbitrary user blobs.
  return `radial-gradient(${size} at ${b.x} ${b.y}, ${b.color} 0%, ${b.color} 10%, transparent 65%)`;
}

/** GradientBlobs — soft radial glow layer behind a section. */
export function GradientBlobs({
  blobs,
  height = '1700px',
  className,
  style,
}: GradientBlobsProps) {
  const background = blobs.map(blobLayer).join(', ');
  return (
    <div
      aria-hidden
      className={[s.root, className].filter(Boolean).join(' ')}
      style={{
        ['--site-kal-blobs-height' as string]: height,
        background,
        ...style,
      }}
    />
  );
}
