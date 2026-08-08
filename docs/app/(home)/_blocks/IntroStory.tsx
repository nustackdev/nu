import { BookOpen } from 'lucide-react';
import { Stack } from '@/components/site/layout/Stack';
import { CtaRow } from '@/components/site/layout/CtaRow';
import { Heading, Tagline, Description } from '@/components/site/text';
import { MonoKicker } from '@/components/site/MonoKicker';
import { CodeSample } from '@/components/site/CodeSample';
import { SiteButton, SiteButtonRepoLabel } from '@/components/site/SiteButton';
import { GithubMark } from '@/components/site/marks/GithubMark';
import { Chapter, Section, SectionCell, SectionHead } from '@/components/site/page';
import {
  INTRO_PLAIN_LINES,
  INTRO_KV_LINES,
  INTRO_UI_LINES,
} from '../intro.sample.data';
import s from './IntroStory.module.css';

/**
 * IntroStory — chapter header + body. Body is one Section where every beat
 * is a two-column split (explanation left, demonstration right); pull-quotes
 * span full width and act as landmarks between beats. Closer cards below.
 */
export function IntroStory() {
  return (
    <Chapter>
      {/* Chapter header */}
      <SectionHead
        peek="intro"
        title="Meet Nu."
        lede={<>What Nu is, how it works, why it matters &mdash; in one read.</>}
      />

      {/* Body */}
      <Section>
        <div className={s.story}>

          {/* Beat 1 — WHAT: the tiny program */}
          <section className={s.beat}>
            <div className={s.beatLeft}>
              <Description>
                A tiny program is a joy to write. Three lines, one
                substrate, no ceremony.
              </Description>
            </div>
            <div className={s.beatRight}>
              <CodeSample filename="tiny.py" lines={INTRO_PLAIN_LINES} />
            </div>
          </section>

          {/* Beat 2 — the crack, then Ref + Interaction */}
          <section className={s.beat}>
            <div className={s.beatLeft}>
              <Description>
                Real apps don&apos;t stay here. <code>a</code> moves into
                a database. <code>b</code> comes from a form a user
                submits. The result renders in a browser. A background job
                reruns it when either input changes. Now the three lines
                are three hundred: an ORM, a request handler, a template,
                a websocket, a queue. Almost none of it is about{' '}
                <code>a + b</code> anymore. It is about ferrying values
                across substrates.
              </Description>
              <Description>
                <strong>Nu makes the ferrying the primitive.</strong>
              </Description>
            </div>
            <div className={s.beatRight}>
              <dl className={s.vocab}>
                <div className={s.vocabItem}>
                  <dt>Ref</dt>
                  <dd>
                    A name for a value, wherever it lives: a KV slot, a
                    UI text block, an LLM endpoint, a remote object.
                  </dd>
                </div>
                <div className={s.vocabItem}>
                  <dt>Interaction</dt>
                  <dd>
                    What you do with a Ref: read, write, branch, iterate,
                    compose.
                  </dd>
                </div>
                <div className={s.vocabItem}>
                  <dt>Fabric</dt>
                  <dd>Binds Refs to a real backend.</dd>
                </div>
              </dl>
            </div>
          </section>

          {/* Beat 3 — same program, KV persisted */}
          <section className={s.beat}>
            <div className={s.beatLeft}>
              <MonoKicker as="p" size="xs" tracking="wide">
                same program, a and b persisted in a kv store
              </MonoKicker>
              <Description>
                <code>&gt;&gt;</code> chains interactions in order. Kill
                the process, run it again, the values are still there.
              </Description>
            </div>
            <div className={s.beatRight}>
              <CodeSample filename="kv.py" lines={INTRO_KV_LINES} />
            </div>
          </section>

          {/* Beat 4 — same program, live browser dashboard */}
          <section className={s.beat}>
            <div className={s.beatLeft}>
              <MonoKicker as="p" size="xs" tracking="wide">
                same program, result rendered in a live browser dashboard
              </MonoKicker>
              <Description>
                <code>Dashboard.out</code> is a Ref too. Setting a browser
                text block is the same interaction as setting a KV slot.
              </Description>
            </div>
            <div className={s.beatRight}>
              <CodeSample filename="ui.py" lines={INTRO_UI_LINES} />
            </div>
          </section>

          {/* Pull-quote landmark */}
          <p className={s.pullQuote}>
            <em>Same primitive, different substrate.</em> The shape of the
            program didn&apos;t change when the substrates did. That is
            the point of Nu.
          </p>

          {/* Beat 5 — HOW: Fabrics */}
          <section className={s.beat}>
            <div className={s.beatLeft}>
              <Heading level={2}>Nu is small on purpose.</Heading>
              <Description>
                Nu is a model and a set of interfaces, hosted in Python.
                There is no runtime magic to learn beyond Refs and
                Interactions. Capabilities come from{' '}
                <strong>Fabrics</strong>. You compose them; the Refs and
                Interactions stay the same across every one.
              </Description>
            </div>
            <div className={s.beatRight}>
              <dl className={s.fabricList}>
                <div className={s.fabricRow}>
                  <dt><code>nu.mem</code></dt>
                  <dd>plain dicts, hot state</dd>
                </div>
                <div className={s.fabricRow}>
                  <dt><code>nu.kv</code></dt>
                  <dd>persistent state on a KV store</dd>
                </div>
                <div className={s.fabricRow}>
                  <dt><code>nu.ui</code></dt>
                  <dd>browser widgets, live-rendered</dd>
                </div>
                <div className={s.fabricRow}>
                  <dt><code>nu.invisibles</code></dt>
                  <dd>any Fabric on the wire</dd>
                </div>
                <div className={s.fabricRow}>
                  <dt><code>nu.ray</code></dt>
                  <dd>teleport to a Ray cluster worker</dd>
                </div>
              </dl>
            </div>
          </section>

          {/* Pull-quote landmark */}
          <p className={s.pullQuote}>
            Persistence, reactivity, atomicity, observability,
            distribution &mdash; <em>not features Nu has,</em> but what
            falls out of naming interactions instead of executing them.
          </p>

          {/* Beat 6 — WHY: consequences */}
          <section className={s.beat}>
            <div className={s.beatLeft}>
              <Heading level={2}>Why this matters.</Heading>
              <Description>
                Because Refs are just names and Interactions are just
                descriptions, the runtime is free to persist them, replay
                them, ship them across the network, watch them for
                changes, batch them into a transaction, run them on
                another machine.
              </Description>
              <Description>
                Which means the same lines that put <code>a + b</code> on
                a dashboard can, without changing shape:
              </Description>
            </div>
            <div className={s.beatRight}>
              <ul className={s.consequences}>
                <li>
                  <strong>Persist across restarts</strong> &mdash; the KV
                  slot is already durable.
                </li>
                <li>
                  <strong>Re-render live on input changes</strong> &mdash;
                  wrap in a <code>React</code> interaction.
                </li>
                <li>
                  <strong>Run partitioned across a cluster</strong>{' '}
                  &mdash; bind through <code>nu.ray</code>; the Refs
                  don&apos;t notice.
                </li>
              </ul>
            </div>
          </section>

        </div>
      </Section>

      {/* Closer — theory + implementation */}
      <Section split="1/1">
        <SectionCell>
          <Stack gap="normal">
            <div className={s.closerCardTitle}>
              <Heading level={2}>interaction-model</Heading>
              <MonoKicker as="span" size="xs" tracking="wide">
                the theory
              </MonoKicker>
            </div>
            <Tagline>The language-agnostic specification.</Tagline>
            <Description>
              What an interaction is, how Refs name locations, how
              Interactions compose into programs. Nu is one implementation;
              anyone can build another.
            </Description>
            <CtaRow>
              <SiteButton href="https://github.com/nustackdev/interaction-model">
                <GithubMark size={14} />
                <SiteButtonRepoLabel>nustackdev/interaction-model</SiteButtonRepoLabel>
              </SiteButton>
            </CtaRow>
          </Stack>
        </SectionCell>
        <SectionCell>
          <Stack gap="normal">
            <div className={s.closerCardTitle}>
              <Heading level={2}>nu</Heading>
              <MonoKicker as="span" size="xs" tracking="wide">
                the python implementation
              </MonoKicker>
            </div>
            <Tagline>Batteries-included, ready to run.</Tagline>
            <Description>
              The interaction model in pure Python, with Fabrics for the
              everyday jobs: in-memory state, kv-based state, UI, network,
              cluster compute.
            </Description>
            <CtaRow>
              <SiteButton href="/docs">
                <BookOpen size={14} aria-hidden />
                <span>Quickstart</span>
              </SiteButton>
              <SiteButton href="https://github.com/nustackdev/nu">
                <GithubMark size={14} />
                <SiteButtonRepoLabel>nustackdev/nu</SiteButtonRepoLabel>
              </SiteButton>
            </CtaRow>
          </Stack>
        </SectionCell>
      </Section>
    </Chapter>
  );
}
