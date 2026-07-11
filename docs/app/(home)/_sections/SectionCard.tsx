import type { HTMLAttributes, ReactNode } from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import s from './SectionCard.module.css';

type Hue = 's1' | 's2' | 's3' | 's4';

/**
 * SectionCard — the wrapper every deck-block section shares.
 * Sets the per-section hue (s1..s4) which drives accent tokens + bloom
 * anchor via `[data-hue]` selectors in SectionCard.module.css.
 */
export function SectionCard({
  hue, id, children,
}: {
  hue: Hue;
  id?: string;
  children: ReactNode;
}) {
  return (
    <section className={s.section} id={id} data-hue={hue}>
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
 * Cta — primary action. Uses next/link for internal hrefs, plain `<a>` for
 * external URLs. The arrow is appended automatically after children.
 */
export function Cta({
  href, children, external,
}: { href: string; children: ReactNode; external?: boolean }) {
  const arrow = <ArrowRight size={13} aria-hidden className={s.ctaArrow} />;
  const isExternal = external ?? /^https?:\/\//.test(href);
  if (isExternal) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={s.cta}>
        {children}
        {arrow}
      </a>
    );
  }
  return (
    <Link href={href} className={s.cta}>
      {children}
      {arrow}
    </Link>
  );
}

/**
 * CtaGhost — secondary silver ghost. No auto-appended arrow — pass leading
 * icons/labels as children.
 */
export function CtaGhost({
  href, children, external,
}: { href: string; children: ReactNode; external?: boolean }) {
  const isExternal = external ?? /^https?:\/\//.test(href);
  if (isExternal) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={s.ctaGhost}>
        {children}
      </a>
    );
  }
  return (
    <Link href={href} className={s.ctaGhost}>
      {children}
    </Link>
  );
}

export const sectionShelfClass = s.sectionShelf;
