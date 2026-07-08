'use client';

import { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import s from './landing.module.css';

export function CopyBtn({ text, label = 'copy' }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className={s.copyBtn}
      aria-label={copied ? 'copied' : label}
      data-copied={copied ? '1' : undefined}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1400);
        } catch {
          /* clipboard denied — silent */
        }
      }}
    >
      {copied ? <Check size={13} strokeWidth={2.4} /> : <Copy size={13} strokeWidth={2} />}
      <span className={s.copyBtnLabel}>{copied ? 'copied' : 'copy'}</span>
    </button>
  );
}
