import { Fragment, type ReactNode } from 'react';
import s from './Meta.module.css';

interface Props {
  items: ReactNode[];
  /** Class applied to each `·` separator. Defaults to a light-ink inline
   *  separator with 0 8px padding (matches hero `metaLine` cadence). Override
   *  when the parent is a flex row with its own gap (e.g. footer). */
  sepClassName?: string;
}

/** Meta — intersperse items with `·` separators. Returns a fragment so the
 *  caller keeps full control of the container. Wrap in `MonoKicker` for the
 *  hero-style variant; drop straight into a flex parent for the footer. */
export function Meta({ items, sepClassName }: Props) {
  const sep = sepClassName ?? s.sep;
  return (
    <>
      {items.map((item, i) => (
        <Fragment key={i}>
          {i > 0 && <span className={sep} aria-hidden>·</span>}
          {item}
        </Fragment>
      ))}
    </>
  );
}
