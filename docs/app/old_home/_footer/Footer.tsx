import Link from 'next/link';
import { NustackMark } from '@/components/site/marks/NustackMark';
import { Meta } from '@/components/site/Meta';
import s from './Footer.module.css';

/**
 * Footer — one simple row closing the page.
 */
export function Footer() {
  return (
    <footer className={s.footer} data-hue="s4">
      <Meta
        sepClassName={s.footerSep}
        items={[
          <Link key="docs" href="/docs">Docs</Link>,
          <a key="gh" href="https://github.com/nustackdev">GitHub</a>,
          <span key="brand" className={s.footerBrand}>
            <NustackMark className={s.footerBrandMark} /> © 2026
          </span>,
        ]}
      />
    </footer>
  );
}
