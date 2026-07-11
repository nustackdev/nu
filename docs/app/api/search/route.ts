import { source } from '@/lib/source';
import { createFromSource } from 'fumadocs-core/search/server';

// Static export: prebuild the search index at build time so GH Pages can
// serve it as a JSON asset. Client-side fumadocs picks it up as usual.
export const dynamic = 'force-static';
export const revalidate = false;

export const { GET } = createFromSource(source, {
  // https://docs.orama.com/docs/orama-js/supported-languages
  language: 'english',
});
