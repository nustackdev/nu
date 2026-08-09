import type { ReactNode } from 'react';
import Link from 'next/link';
import { ArrowRight, ArrowUpRight } from 'lucide-react';
import s from './LinkCard.module.css';

interface Props {
  /** Where the card links to. Same rules as SiteButton — starts with http →
   *  external `<a target="_blank">` + ArrowUpRight; otherwise next/Link + ArrowRight. */
  href: string;
  /** Small icon rendered to the left of the title. Any ReactNode. */
  icon?: ReactNode;
  /** Card title — the primary label. */
  title: ReactNode;
  /** Optional body copy under the title. Keep to one sentence. */
  children?: ReactNode;
  /** Force external-link behavior (target=_blank + ArrowUpRight). */
  external?: boolean;
  ariaLabel?: string;
  className?: string;
}

/**
 * LinkCard — a big-button-shaped link. Bordered surface card with icon +
 * title on top and an optional one-line body underneath. Reach-for pattern
 * whenever you want a click target with more air than a `SiteButton` and
 * a bit of context — Learn / Explore rows, quickstart follow-ups, cross-
 * links to related pages. Pair inside a plain CSS grid for a row of cards.
 */
export function LinkCard({
  href,
  icon,
  title,
  children,
  external,
  ariaLabel,
  className,
}: Props) {
  const isExternal = external ?? /^https?:\/\//.test(href);
  const cls = [s.card, className].filter(Boolean).join(' ');

  const content = (
    <>
      <span className={s.head}>
        {icon ? <span className={s.icon} aria-hidden>{icon}</span> : null}
        <span className={s.title}>{title}</span>
        {isExternal ? (
          <ArrowUpRight size={13} aria-hidden className={s.arrow} />
        ) : (
          <ArrowRight size={13} aria-hidden className={s.arrow} />
        )}
      </span>
      {children ? <span className={s.body}>{children}</span> : null}
    </>
  );

  if (isExternal) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className={cls}
        aria-label={ariaLabel}
      >
        {content}
      </a>
    );
  }

  return (
    <Link href={href} className={cls} aria-label={ariaLabel}>
      {content}
    </Link>
  );
}
