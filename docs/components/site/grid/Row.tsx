import type { CSSProperties, ReactNode } from 'react';
import s from './Row.module.css';

export type RowCols = 1 | 2 | 3 | '2:1' | '1:2';
export type RowBorder = false | 'solid' | 'dashed' | 'dotted';
/**
 * Named breakpoints for `stackAt`. Values match the site's existing @media
 * scale (grep `page.module.css` / `Container.module.css`):
 *   sm →  640px   (mobile / global safety-net collapse)
 *   md →  900px   (small tablet — used by slogan sizing, old_home sections)
 *   lg → 1024px   (tablet / narrow laptop)
 *   xl → 1280px   (Container's own step-down)
 *
 * Numeric arbitrary breakpoints are intentionally NOT supported: inline CSS
 * variables cannot drive `@media` queries, and we don't want a runtime
 * <style> injection dependency here. If you need an off-scale breakpoint
 * (e.g. the 701–1075 interaction-model row), write a scoped CSS-module rule
 * on the row's own className and override `grid-template-columns` there.
 */
export type RowStackAt = 'sm' | 'md' | 'lg' | 'xl';

export interface RowProps {
  children?: ReactNode;
  /** Preset column layout. Ignored if `template` is set. */
  cols?: RowCols;
  /** Escape hatch: raw grid-template-columns value. */
  template?: string;
  borderTop?: RowBorder;
  borderBottom?: RowBorder;
  borderLeft?: RowBorder;
  borderRight?: RowBorder;
  /** Vertical rule style between cells. Default 'solid'. */
  divider?: RowBorder;
  /**
   * Collapse this Row to a single column at the given breakpoint and below.
   * At that breakpoint the divider, outer borders and trailing-cell top
   * padding are stripped so the row reads as one continuous vertical stack.
   *
   * Named tokens map to the site's @media scale — see `RowStackAt` above.
   * Note: rows already collapse implicitly at ≤640px via a global safety-net
   * rule; use `stackAt` to collapse *earlier* (md/lg/xl), or to be explicit
   * about intent.
   */
  stackAt?: RowStackAt;
  className?: string;
  style?: CSSProperties;
}

const COL_TEMPLATES: Record<RowCols, string> = {
  1: 'minmax(0, 1fr)',
  2: 'minmax(0, 1fr) minmax(0, 1fr)',
  3: 'minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr)',
  '2:1': 'minmax(0, 2fr) minmax(0, 1fr)',
  '1:2': 'minmax(0, 1fr) minmax(0, 2fr)',
};

const STACK_CLASS: Record<RowStackAt, string> = {
  sm: s.stackSm,
  md: s.stackMd,
  lg: s.stackLg,
  xl: s.stackXl,
};

const SIDE_CLASS: Record<
  'bt' | 'bb' | 'bl' | 'br',
  Record<Exclude<RowBorder, false>, string>
> = {
  bt: { solid: s.btSolid, dashed: s.btDashed, dotted: s.btDotted },
  bb: { solid: s.bbSolid, dashed: s.bbDashed, dotted: s.bbDotted },
  bl: { solid: s.blSolid, dashed: s.blDashed, dotted: s.blDotted },
  br: { solid: s.brSolid, dashed: s.brDashed, dotted: s.brDotted },
};

const DIVIDER_CLASS: Record<Exclude<RowBorder, false>, string> = {
  solid: s.divSolid,
  dashed: s.divDashed,
  dotted: s.divDotted,
};

/**
 * Row — one horizontal band inside a Container. Lays out Cells in a grid
 * and handles outer borders + inter-cell dividers.
 */
export function Row({
  children,
  cols = 1,
  template,
  borderTop = false,
  borderBottom = false,
  borderLeft = false,
  borderRight = false,
  divider = 'solid',
  stackAt,
  className,
  style,
}: RowProps) {
  const gridTemplate = template ?? COL_TEMPLATES[cols];
  const cls = [
    s.root,
    borderTop && SIDE_CLASS.bt[borderTop],
    borderBottom && SIDE_CLASS.bb[borderBottom],
    borderLeft && SIDE_CLASS.bl[borderLeft],
    borderRight && SIDE_CLASS.br[borderRight],
    divider && DIVIDER_CLASS[divider],
    stackAt && STACK_CLASS[stackAt],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className={cls}
      style={{ ['--kal-row-template' as string]: gridTemplate, ...style }}
    >
      {children}
    </div>
  );
}
