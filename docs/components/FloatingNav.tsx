'use client';

import Link from 'next/link';
import { Search, BookOpen } from 'lucide-react';
import { useSearchContext } from 'fumadocs-ui/contexts/search';
import { NustackMark } from '@/components/marks/NustackMark';
import { NustackLogo } from '@/components/marks/NustackLogo';
import { GithubMark } from '@/components/marks/GithubMark';
import s from './FloatingNav.module.css';

export function FloatingNav() {
  const { setOpenSearch } = useSearchContext();

  return (
    <header className={s.floatingNav}>
      <div className={s.navPill}>
        <Link href="/" className={s.navBrand} aria-label="nustack home">
          <NustackLogo size={18} />
          <NustackMark />
        </Link>

        <div className={s.navRight}>
          <button
            type="button"
            className={s.navIcon}
            onClick={() => setOpenSearch(true)}
            aria-label="search"
          >
            <Search size={16} aria-hidden />
          </button>

          <Link href="/docs" className={s.navIcon} aria-label="docs">
            <BookOpen size={16} aria-hidden />
          </Link>

          <a
            className={s.navIcon}
            href="https://github.com/nustackdev"
            target="_blank"
            rel="noreferrer"
            aria-label="github"
          >
            <GithubMark size={16} />
          </a>
        </div>
      </div>
    </header>
  );
}
