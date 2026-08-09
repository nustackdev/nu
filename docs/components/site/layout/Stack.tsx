import type { CSSProperties, ReactNode } from 'react';
import s from './Stack.module.css';

type Direction = 'column' | 'row';
type Gap = 'tight' | 'normal' | 'loose' | 'xloose';

interface Props {
  direction?: Direction;
  gap?: Gap;
  /** Fill parent height and push the last child to the bottom. Use inside
   *  multi-cell rows (Infra chapter, IntroStory closer, demo grids) so CTA
   *  rows / commands line up across cells regardless of description length.
   *  Requires an ancestor that grants stretched height — SectionCell does. */
  pushLast?: boolean;
  className?: string;
  style?: CSSProperties;
  children: ReactNode;
}

/** Stack — flex container that owns rhythm.
 *  gap resolves to var(--site-gap-{gap}). Defaults: column, normal. */
export function Stack({
  direction = 'column',
  gap = 'normal',
  pushLast = false,
  className,
  style,
  children,
}: Props) {
  const cls = [
    s.stack,
    direction === 'row' ? s.row : s.column,
    s[gap],
    pushLast && s.pushLast,
    className,
  ]
    .filter(Boolean)
    .join(' ');
  return (
    <div className={cls} style={style}>
      {children}
    </div>
  );
}
