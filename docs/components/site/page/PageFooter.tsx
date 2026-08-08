import Link from 'next/link';
import { Cell } from '@/components/site/grid/Cell';
import { CellContent } from '@/components/site/grid/CellContent';
import { Row } from '@/components/site/grid/Row';
import { NuLogo } from '@/components/site/marks/NuLogo';
import { NustackMark } from '@/components/site/marks/NustackMark';
import s from './PageFooter.module.css';

/**
 * PageFooter — the site's canonical footer strip: Docs · GitHub · brand.
 * Rendered as a bordered Row so it sits flush against the last Section's
 * bottom border.
 */
export function PageFooter() {
  return (
    <Row cols={1}>
      <Cell>
        <CellContent pad="md">
          <div className={s.footer}>
            <Link href="/docs">Docs</Link>
            <span className={s.sep}>·</span>
            <a href="https://github.com/nustackdev">GitHub</a>
            <span className={s.sep}>·</span>
            <span className={s.brand}>
              <NuLogo size={14} className={s.logo} />
              <NustackMark mono /> © 2026
            </span>
          </div>
        </CellContent>
      </Cell>
    </Row>
  );
}
