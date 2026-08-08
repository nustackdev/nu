import type { ReactNode } from 'react';
import { Container } from '@/components/site/grid/Container';
import { DotPattern } from '@/components/site/bg/DotPattern';
import { GradientBlobs, HERO_BLOBS } from '@/components/site/bg/GradientBlobs';
import type { Blob as GradientBlob } from '@/components/site/bg/GradientBlobs';
import s from './PageShell.module.css';

export interface PageShellProps {
  children?: ReactNode;
  /**
   * Absolute-positioned decorations sitting between the gradient (z=0) and
   * the dot pattern (z=2). Used by pages that want extra background layers
   * (e.g. the landing's giant nu logo pinned to the hero grid). Rendered
   * in a pointer-events: none container.
   */
  decorations?: ReactNode;
  /** Override the gradient blobs. Defaults to HERO_BLOBS. */
  gradientBlobs?: GradientBlob[];
  /** Extra className applied to the pageRoot. */
  className?: string;
}

/**
 * PageShell — outer wrapper for a site page. Sets up the four background/
 * content layers (gradient → decorations → dots → content) inside a
 * full-height Container. Children are rendered in the content layer.
 */
export function PageShell({
  children,
  decorations,
  gradientBlobs = HERO_BLOBS,
  className,
}: PageShellProps) {
  const cls = [s.pageRoot, className].filter(Boolean).join(' ');
  return (
    <div className={cls}>
      <div className={s.gradientLayer}>
        <GradientBlobs blobs={gradientBlobs} />
      </div>
      {decorations ? (
        <div className={s.decorationsLayer} aria-hidden>
          {decorations}
        </div>
      ) : null}
      <DotPattern className={s.dotLayer} />
      <Container full className={s.contentLayer}>
        {children}
      </Container>
    </div>
  );
}
