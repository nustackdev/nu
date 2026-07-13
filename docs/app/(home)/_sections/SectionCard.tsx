import type { HTMLAttributes, ReactNode } from 'react';
import Link from 'next/link';
import { ArrowRight, ArrowUpRight } from 'lucide-react';
import s from './SectionCard.module.css';

type Hue = 's1' | 's2' | 's3' | 's4';

/** Silver-woven fabric hue keys — remap --nu-accent[-2] for every SVG
    inside this section so shared primitives auto-tint. */
type VizHue = 'steel' | 'sage' | 'teal' | 'plum' | 'amber';

/**
 * SectionCard — the wrapper every deck-block section shares.
 *   `hue`     drives section-chrome accent tokens (--sec-*) via [data-hue].
 *   `vizHue`  scopes --nu-accent[-2] to a silver-woven fabric hue so any
 *             visualization inside this card renders on that hue. Fabric &
 *             app rows override --nu-accent[-2] again at row scope; sections
 *             without per-row scope (hero, interaction-model, nu) rely on
 *             this prop to pick their canonical viz hue.
 */
export function SectionCard({
  hue, vizHue, id, children,
}: {
  hue: Hue;
  vizHue?: VizHue;
  id?: string;
  children: ReactNode;
}) {
  return (
    <section
      className={s.section}
      id={id}
      data-hue={hue}
      data-viz-hue={vizHue}
    >
      <div className={s.sectionCard}>{children}</div>
    </section>
  );
}

/** 2-column grid. `flip` swaps the column ratio for the mirror layout. */
export function SectionSplit({
  flip, children,
}: { flip?: boolean; children: ReactNode }) {
  const cn = flip
    ? `${s.sectionSplit} ${s.sectionSplitFlip}`
    : s.sectionSplit;
  return <div className={cn}>{children}</div>;
}

export function SectionCol({ children }: { children: ReactNode }) {
  return <div className={s.sectionCol}>{children}</div>;
}

export function SectionVisual(
  { children, ...rest }: HTMLAttributes<HTMLElement>,
) {
  return <aside className={s.sectionVisual} {...rest}>{children}</aside>;
}

export function VizFrame({ children }: { children: ReactNode }) {
  return <div className={s.vizFrame}>{children}</div>;
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className={s.sectionTitle}>{children}</h2>;
}

export function SectionIntro({ children }: { children: ReactNode }) {
  return <p className={s.sectionIntro}>{children}</p>;
}

export function ActionRow({ children }: { children: ReactNode }) {
  return <div className={s.actions}>{children}</div>;
}

/**
 * Cta — unified action link, styled identically to the hero CTAs
 * (neutral transparent-white bg, hairline border). Auto-detects internal vs
 * external hrefs: internal uses next/link + ArrowRight; external uses <a>
 * + ArrowUpRight (out-of-site glyph). Pass a leading icon/label as children.
 *
 * variant="hueTinted" reads --nu-accent-* tokens for border, bg, arrow color
 * — use it inside a row that scopes those tokens (fabrics/apps rows do).
 */
export function Cta({
  href, children, external, variant = 'neutral',
}: {
  href: string;
  children: ReactNode;
  external?: boolean;
  variant?: 'neutral' | 'hueTinted';
}) {
  const isExternal = external ?? /^https?:\/\//.test(href);
  const arrowCls = variant === 'hueTinted' ? s.ctaArrowHue : s.ctaArrow;
  const arrow = isExternal
    ? <ArrowUpRight size={13} aria-hidden className={arrowCls} />
    : <ArrowRight size={13} aria-hidden className={arrowCls} />;
  const cls = variant === 'hueTinted' ? `${s.cta} ${s.ctaHueTinted}` : s.cta;
  if (isExternal) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={cls}>
        {children}
        {arrow}
      </a>
    );
  }
  return (
    <Link href={href} className={cls}>
      {children}
      {arrow}
    </Link>
  );
}

/** Mono org/repo label — use inside a Cta for GitHub repo links. */
export function RepoName({ children }: { children: ReactNode }) {
  return <span className={s.ctaRepo}>{children}</span>;
}
