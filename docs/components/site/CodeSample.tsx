'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import s from './CodeSample.module.css';

export type CodeTok = { c?: 'kw' | 'nu' | 'str' | 'cmt'; t: string };

interface Props {
  /** Filename shown in the tab strip (e.g. "app.py"). */
  filename: string;
  /** Language label for the meta line (e.g. "python"). */
  lang?: string;
  /** Short lang label used at narrow widths (e.g. "py"). */
  langShort?: string;
  /** Lines as arrays of tokens. Empty inner array renders a blank line. */
  lines: CodeTok[][];
  /** Optional aria label; defaults to `Code sample: <filename>`. */
  ariaLabel?: string;
  className?: string;
}

/**
 * CodeSample — flat IDE-style code block. Tab strip, gutter, tokens.
 * Token colors follow --site-accent / --site-accent-2 from the surrounding hue
 * scope (e.g. wrap in a class that remaps to silver-woven teal + steel).
 */
export function CodeSample({
  filename,
  lang = 'python',
  langShort = 'py',
  lines,
  ariaLabel,
  className,
}: Props) {
  const [copied, setCopied] = useState(false);
  const raw = lines.map((tokens) => tokens.map((tok) => tok.t).join('')).join('\n');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(raw);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      /* clipboard blocked — silent no-op */
    }
  };

  const cls = [s.ide, className].filter(Boolean).join(' ');

  return (
    <div className={cls} role="figure" aria-label={ariaLabel ?? `Code sample: ${filename}`}>
      <div className={s.ideTabs}>
        <div className={`${s.ideTab} ${s.ideTabActive}`}>
          <span className={s.ideTabDot} aria-hidden />
          {filename}
        </div>
        <div className={s.ideMeta}>
          <span className={s.ideMetaLong}>{lang} · {lines.length} loc</span>
          <span className={s.ideMetaShort}>{langShort}</span>
        </div>
      </div>
      <div className={s.ideBody}>
        <button
          type="button"
          className={s.ideCopy}
          onClick={handleCopy}
          aria-label={copied ? 'code copied' : 'copy code'}
        >
          {copied ? <Check size={14} aria-hidden /> : <Copy size={14} aria-hidden />}
        </button>
        <div className={s.ideGutter} aria-hidden>
          {lines.map((_, i) => (
            <div key={i} className={s.ideLineNo}>{i + 1}</div>
          ))}
        </div>
        <div className={s.ideCode}>
          {lines.map((tokens, i) => (
            <div key={i} className={s.ideLine}>
              {tokens.length === 0 ? ' ' : tokens.map((tok, j) =>
                tok.c ? (
                  <span key={j} className={s[tok.c]}>{tok.t}</span>
                ) : (
                  <span key={j}>{tok.t}</span>
                ),
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
