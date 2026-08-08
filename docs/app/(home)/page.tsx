import { BookOpen } from 'lucide-react';
import { NuLogo } from '@/components/site/marks/NuLogo';
import { Cell } from '@/components/site/grid/Cell';
import { CellContent } from '@/components/site/grid/CellContent';
import { Row } from '@/components/site/grid/Row';
import { SiteButton, SiteButtonRepoLabel } from '@/components/site/SiteButton';
import { SilverWovenName } from '@/components/site/SilverWovenName';
import { VizFrame } from '@/components/site/VizFrame';
import { MonoKicker } from '@/components/site/MonoKicker';
import { Meta } from '@/components/site/Meta';
import { NumberedList } from '@/components/site/NumberedList';
import { Heading, Tagline, Description, Label } from '@/components/site/text';
import { Stack } from '@/components/site/layout/Stack';
import { CtaRow } from '@/components/site/layout/CtaRow';
import {
  MemGlyph,
  VirtualsGlyph,
  UiGlyph,
  InvisiblesGlyph,
  RayGlyph,
} from '@/components/site/marks/FabricGlyphs';
import { NulogMockSvg } from '@/components/site/marks/NulogMock';
import { NuspaceMockSvg } from '@/components/site/marks/NuspaceMock';
import { GithubMark } from '@/components/site/marks/GithubMark';
import { DiscordMark } from '@/components/site/marks/DiscordMark';
import { XMark } from '@/components/site/marks/XMark';
import {
  PageShell,
  Page,
  PageHero,
  PageBody,
  Chapter,
  PageFooter,
  Section,
  SectionCell,
  SectionHead,
} from '@/components/site/page';
import { IntroStory } from './_blocks/IntroStory';
import { Quickstart } from './_blocks/Quickstart';
import s from './page.module.css';

const USE_CASES = [
  'AI agentic systems',
  'Personal apps',
  'Data-intensive apps',
  'Enterprise in-house tools',
];

export default function Home() {
  return (
    <PageShell className={s.landingRoot}>
      <Page>
      {/* 1. Hero */}
      <PageHero>
        <Row template="minmax(0, 55fr) minmax(0, 45fr)" divider={false} stackAt="sm" className={s.heroRow}>
          <Cell yalign="middle" className={s.heroLeftCell}>
            <CellContent pad="lg">
              <h1 className={s.sloganStack} aria-label="Nu the interaction primitive">
                <span className={s.sloganWord} aria-hidden>
                  <NuLogo size="0.9em" className={s.sloganMark} />
                  Nu &mdash;
                </span>
                <span className={s.sloganWord} aria-hidden>the</span>
                <span className={s.sloganWord} aria-hidden>interaction</span>
                <span className={s.sloganWord} aria-hidden>primitive.</span>
              </h1>
            </CellContent>
          </Cell>
          <Cell yalign="middle">
            <CellContent pad="lg">
              <div className={s.heroRight}>
                <h1 className={s.sloganInline}>
                  <NuLogo size="1em" className={s.sloganLogo} />
                  Nu &mdash; the interaction primitive.
                </h1>
                <p className={s.heroTagline}>
                  Build apps in one primitive that spans your
                  <br />
                  whole stack &mdash; databases, UIs, AI agents,
                  <br />
                  and services. No glue.{' '}
                  <em className={s.taglineAccent}>50&times; less code.</em>
                </p>

                <MonoKicker as="p" size="xs" tracking="wider" className={s.useCasesKickerBox}>
                  Built for
                </MonoKicker>
                <NumberedList items={USE_CASES} className={s.useCasesListBox} />

                <div className={s.heroCtaRow}>
                  <SiteButton variant="primaryPurple" href="/docs">
                    <BookOpen size={14} aria-hidden />
                    <span>Quickstart</span>
                  </SiteButton>
                  <SiteButton variant="primaryBlue" href="https://github.com/nustackdev/nu">
                    <GithubMark size={14} />
                    <SiteButtonRepoLabel>nustackdev/nu</SiteButtonRepoLabel>
                  </SiteButton>
                </div>
                <div className={s.heroCtaRow}>
                  <SiteButton href="https://discord.gg/tCa8YE7XVr">
                    <DiscordMark size={14} />
                    <span>Discord</span>
                  </SiteButton>
                  <SiteButton href="https://twitter.com/nustackdev">
                    <XMark size={13} />
                    <span>Follow</span>
                  </SiteButton>
                </div>

                <MonoKicker as="p" size="xs" tracking="wide" className={s.metaLineBox}>
                  <Meta items={[<>Apache&#8209;2.0</>, 'Python 3.10+']} />
                </MonoKicker>
              </div>
            </CellContent>
          </Cell>
        </Row>
      </PageHero>

      <PageBody>
        {/* 2. Intro story — what / how / why, plus theory + impl closer */}
        <IntroStory />

        {/* 3. Quickstart — mirrors README quickstart */}
        <Quickstart />

        {/* 5. Fabrics */}
        <Chapter>
        <SectionHead
          title="Fabrics."
          lede={
            <>
              Fabrics are the tissue between Refs and the real world: memory,
              kv stores, UI, network, cluster. These are the ones Nu ships
              with today.
            </>
          }
        />

        <Section hue="steel">
          <div className={s.itemRow}>
            <div className={s.itemBody}>
              <SilverWovenName as="h3" hue="steel">nu.mem</SilverWovenName>
              <Tagline>In-memory state fabric.</Tagline>
              <Description>
                In-memory state on plain dicts. Perfect for cache, hot state,
                and in-process coordination.
              </Description>
              <CtaRow>
                <SiteButton href="/docs/reference/fabrics/mem" variant="hueTinted">
                  <BookOpen size={14} aria-hidden />
                  <span>Read the docs</span>
                </SiteButton>
              </CtaRow>
            </div>
            <div className={s.itemViz}>
              <VizFrame><MemGlyph /></VizFrame>
            </div>
          </div>
        </Section>

        <Section hue="sage">
          <div className={s.itemRow}>
            <div className={s.itemBody}>
              <SilverWovenName as="h3" hue="sage">nu.virtuals</SilverWovenName>
              <Tagline>Persistent state fabric.</Tagline>
              <Description>
                Refs over a KV backend (RocksDB, LMDB). Transactions,
                snapshots, and change notifications, built in.
              </Description>
              <Label>Backends: rocksdb, lmdb</Label>
              <CtaRow>
                <SiteButton href="/docs/reference/fabrics/virtuals" variant="hueTinted">
                  <BookOpen size={14} aria-hidden />
                  <span>Read the docs</span>
                </SiteButton>
              </CtaRow>
            </div>
            <div className={s.itemViz}>
              <VizFrame><VirtualsGlyph /></VizFrame>
            </div>
          </div>
        </Section>

        <Section hue="teal">
          <div className={s.itemRow}>
            <div className={s.itemBody}>
              <SilverWovenName as="h3" hue="teal">nu.ui</SilverWovenName>
              <Tagline>Web UI fabric.</Tagline>
              <Description>
                Same fabric shape as the others, but the Refs are widgets:
                text, buttons, tables. The fabric renders them in the browser
                and live-updates them as your state changes.
              </Description>
              <CtaRow>
                <SiteButton href="/docs/reference/fabrics/ui" variant="hueTinted">
                  <BookOpen size={14} aria-hidden />
                  <span>Read the docs</span>
                </SiteButton>
              </CtaRow>
            </div>
            <div className={s.itemViz}>
              <VizFrame><UiGlyph /></VizFrame>
            </div>
          </div>
        </Section>

        <Section hue="plum">
          <div className={s.itemRow}>
            <div className={s.itemBody}>
              <SilverWovenName as="h3" hue="plum">nu.invisibles</SilverWovenName>
              <Tagline>Network fabric.</Tagline>
              <Description>
                A Nu fabric that puts other fabrics on the network. Bind a
                fabric in one process, use it from another; same Refs, same
                interactions, over TCP or Unix socket.
              </Description>
              <CtaRow>
                <SiteButton href="/docs/reference/fabrics/invisibles" variant="hueTinted">
                  <BookOpen size={14} aria-hidden />
                  <span>Read the docs</span>
                </SiteButton>
              </CtaRow>
            </div>
            <div className={s.itemViz}>
              <VizFrame><InvisiblesGlyph /></VizFrame>
            </div>
          </div>
        </Section>

        <Section hue="amber">
          <div className={s.itemRow}>
            <div className={s.itemBody}>
              <SilverWovenName as="h3" hue="amber">nu.ray</SilverWovenName>
              <Tagline>Cluster compute fabric.</Tagline>
              <Description>
                A Nu fabric for cluster compute. Teleport a Nu tree to any
                worker in your Ray cluster; it runs there and returns the
                result.
              </Description>
              <CtaRow>
                <SiteButton href="/docs/reference/fabrics/ray" variant="hueTinted">
                  <BookOpen size={14} aria-hidden />
                  <span>Read the docs</span>
                </SiteButton>
              </CtaRow>
            </div>
            <div className={s.itemViz}>
              <VizFrame><RayGlyph /></VizFrame>
            </div>
          </div>
        </Section>
        </Chapter>

        {/* 6. Apps */}
        <Chapter>
        <SectionHead
          title="Standalone apps built on Nu."
          lede="Applications built on Nu today."
        />

        <Section hue="amber">
          <div className={s.itemRow}>
            <div className={s.itemBody}>
              <SilverWovenName as="h3" hue="amber">nulog</SilverWovenName>
              <Tagline>
                Pure-Python, serverless logger and metrics store. Billions of
                entries, live UI.
              </Tagline>
              <Description>
                Log messages and observe metrics from any Python code. Entries
                persist to an embedded KV store and scale to billions,
                in-process. One line boots a live viewer.
              </Description>
              <CtaRow>
                <SiteButton variant="repo" href="https://github.com/nustackdev/nulog">
                  <GithubMark size={14} />
                  <SiteButtonRepoLabel>nustackdev/nulog</SiteButtonRepoLabel>
                </SiteButton>
              </CtaRow>
            </div>
            <div className={s.itemViz}>
              <VizFrame><NulogMockSvg /></VizFrame>
            </div>
          </div>
        </Section>

        <Section hue="plum">
          <div className={s.itemRow}>
            <div className={s.itemBody}>
              <SilverWovenName as="h3" hue="plum">nuspace</SilverWovenName>
              <Tagline>
                A programmable knowledge base.
              </Tagline>
              <Description>
                A knowledge base whose pages hold both writing, data and code
                as first-class citizens. Blocks store markdown, live metrics,
                saved searches, or automation rules, all in the same tree,
                all inspectable and composable.
              </Description>
              <Label>Status: Coming soon.</Label>
            </div>
            <div className={s.itemViz}>
              <VizFrame><NuspaceMockSvg /></VizFrame>
            </div>
          </div>
        </Section>
        </Chapter>

        {/* 7. Infra */}
        <Chapter>
        <SectionHead
          title="Infra. The tools that power Nu fabrics."
          lede={
            <>
              Standalone Python libraries the fabrics build on. Each is
              useful on its own; together they form the substrate under Nu.
            </>
          }
        />

        <Section split="1/1">
          <SectionCell>
            <Stack gap="normal">
              <Stack gap="tight">
                <Heading level={2}>virtuals</Heading>
                <Tagline>
                  Virtual Python collections over any KV storage.
                </Tagline>
              </Stack>
              <Description>
                Native-shaped Python collections that are thin views over an
                ordered KV store. Same API as a built-in dict or list, but
                the bytes stay on disk and stream in on access.
              </Description>
              <CtaRow>
                <SiteButton href="https://github.com/nustackdev/virtuals">
                  <GithubMark size={14} />
                  <SiteButtonRepoLabel>nustackdev/virtuals</SiteButtonRepoLabel>
                </SiteButton>
              </CtaRow>
            </Stack>
          </SectionCell>
          <SectionCell>
            <Stack gap="normal">
              <Stack gap="tight">
                <Heading level={2}>invisibles</Heading>
                <Tagline>Transparent remote objects for Python.</Tagline>
              </Stack>
              <Description>
                Move an object to another process or node; the calling code
                doesn&apos;t change. Sync stays sync, async stays async.
              </Description>
              <CtaRow>
                <SiteButton href="https://github.com/nustackdev/invisibles">
                  <GithubMark size={14} />
                  <SiteButtonRepoLabel>nustackdev/invisibles</SiteButtonRepoLabel>
                </SiteButton>
              </CtaRow>
            </Stack>
          </SectionCell>
        </Section>

        <Section split="1/1">
          <SectionCell>
            <Stack gap="normal">
              <Stack gap="tight">
                <Heading level={2}>rdbpy</Heading>
                <Tagline>RocksDB for Python, with transactions.</Tagline>
              </Stack>
              <Description>
                RocksDB and its compression libs bundled into the wheel for
                Linux and macOS. No system install. Open a DB and
                put/get/iterate.
              </Description>
              <CtaRow>
                <SiteButton href="https://github.com/nustackdev/rdbpy">
                  <GithubMark size={14} />
                  <SiteButtonRepoLabel>nustackdev/rdbpy</SiteButtonRepoLabel>
                </SiteButton>
              </CtaRow>
            </Stack>
          </SectionCell>
          <SectionCell>
            <Stack gap="normal">
              <Stack gap="tight">
                <Heading level={2}>kh57</Heading>
                <Tagline>Deterministic range reservoir sampling.</Tagline>
              </Stack>
              <Description>
                Draw <code>n</code> uniform samples from a sub-range of a
                massive (billions) sorted KV dataset without scanning it. Any
                sorted KV store works as a backend.
              </Description>
              <CtaRow>
                <SiteButton href="https://github.com/nustackdev/kh57">
                  <GithubMark size={14} />
                  <SiteButtonRepoLabel>nustackdev/kh57</SiteButtonRepoLabel>
                </SiteButton>
              </CtaRow>
            </Stack>
          </SectionCell>
        </Section>
        </Chapter>
      </PageBody>

      {/* 8. Footer */}
      <PageFooter />
      </Page>
    </PageShell>
  );
}
