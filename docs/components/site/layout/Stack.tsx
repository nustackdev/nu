import type { CSSProperties, ReactNode } from 'react';
import s from './Stack.module.css';

type Direction = 'column' | 'row';
type Gap = 'tight' | 'normal' | 'loose' | 'xloose';

interface Props {
  direction?: Direction;
  gap?: Gap;
  className?: string;
  style?: CSSProperties;
  children: ReactNode;
}

/** Stack — flex container that owns rhythm.
 *  gap resolves to var(--nu-gap-{gap}). Defaults: column, normal. */
export function Stack({
  direction = 'column',
  gap = 'normal',
  className,
  style,
  children,
}: Props) {
  const cls = [
    s.stack,
    direction === 'row' ? s.row : s.column,
    s[gap],
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
