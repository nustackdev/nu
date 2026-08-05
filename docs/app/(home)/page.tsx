import Link from 'next/link';
import { BookOpen } from 'lucide-react';
import { NustackMark } from '@/components/site/marks/NustackMark';
import { NuLogo } from '@/components/site/marks/NuLogo';
import { HeroLogo } from './_blocks/HeroLogo';
import { DotPattern } from '@/components/site/bg/DotPattern';
import { GradientBlobs, HERO_BLOBS } from '@/components/site/bg/GradientBlobs';
import { Cell } from '@/components/site/grid/Cell';
import { CellContent } from '@/components/site/grid/CellContent';
import { Container } from '@/components/site/grid/Container';
import { Row } from '@/components/site/grid/Row';
import { SiteButton, SiteButtonRepoLabel } from '@/components/site/SiteButton';
import { SilverWovenName } from '@/components/site/SilverWovenName';
import { VizFrame } from '@/components/site/VizFrame';
import { MonoKicker } from '@/components/site/MonoKicker';
import { Meta } from '@/components/site/Meta';
import { NumberedList } from '@/components/site/NumberedList';
import { Heading, Tagline, Lede, Description, Label } from '@/components/site/text';
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
import { HeroDemoMark } from '@/components/site/marks/HeroDemoMark';
import { InteractionModelDiagram } from '@/components/site/marks/InteractionModelDiagram';
import { GithubMark } from '@/components/site/marks/GithubMark';
import { DiscordMark } from '@/components/site/marks/DiscordMark';
import { XMark } from '@/components/site/marks/XMark';
import { CodeSample } from '@/components/site/CodeSample';
import { NU_SAMPLE_LINES } from './nu.sample.data';
import s from './page.module.css';

const USE_CASES = [
  'AI agentic systems',
  'Personal apps',
  'Data-intensive apps',
  'Enterprise in-house tools',
];

export default function Home() {
  return (
    <div className={s.pageRoot}>
      {/* Layer 1: gradient (bottom) */}
      <div className={s.gradientLayer}>
        <GradientBlobs blobs={HERO_BLOBS} />
      </div>
      {/* Layer 2: nu logo — pinned to hero grid's bottom-left */}
      <div className={s.logoLayer} aria-hidden>
        <div className={s.logoAlign}>
          <HeroLogo className={s.logo} />
        </div>
      </div>
      {/* Layer 3: dotted pattern */}
      <DotPattern className={s.dotLayer} />
      {/* Layer 4: everything else */}
      <Container full className={s.contentLayer}>
        {/* 1. Hero */}
        <Row template="minmax(0, 55fr) minmax(0, 45fr)" divider={false} stackAt="sm" className={s.heroRow}>
            <Cell yalign="middle" className={s.heroLeftCell}>
              <CellContent pad="lg">
                <h1 className={s.sloganStack} aria-label="Nu the interaction primitive">
                  <span className={s.sloganWord} aria-hidden>Nu &mdash;</span>
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
                    <Meta items={[<>Apache&#8209;2.0</>, 'Python 3.12+']} />
                  </MonoKicker>
                </div>
              </CellContent>
            </Cell>
        </Row>

        {/* 2. Hero demo — lede + code-tree/runtime-scene */}
        <Row cols={1} borderBottom="solid" className={s.section2Row}>
          <Cell>
            <CellContent pad="lg">
              <Lede>
                Every app is a set of interactions between systems - a
                database, a UI, AI agents, services. Nu makes interaction the
                primitive: <strong>Refs</strong> name what you touch.{' '}
                <strong>Interactions</strong> describe what to do with them.
                Persistence, reactivity, atomicity, observability, and
                scalability are inherent - not bolted on.
              </Lede>
            </CellContent>
          </Cell>
        </Row>
        <Row cols={1} borderBottom="solid" borderLeft="solid" borderRight="solid">
          <Cell>
            <CellContent pad="lg">
              <HeroDemoMark />
            </CellContent>
          </Cell>
        </Row>

        {/* 3. Foundations — interaction-model */}
        <Row cols={1} borderBottom="solid" borderLeft="solid" borderRight="solid">
          <Cell className={s.chapterCell}>
            <span className={s.chapterPeek} aria-hidden>model</span>
            <CellContent pad="lg">
              <Heading level={1}>
                We build on the Interaction Model.
              </Heading>
              <p className={s.sectionIntro}>
                A language-agnostic specification the whole stack stands on.
              </p>
            </CellContent>
          </Cell>
        </Row>
        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm" className={s.imRow}>
          <Cell className={s.imLeft}>
            <CellContent pad="lg">
              <Stack gap="normal">
                <Description>
                  The interaction-model defines what an interaction is, how Refs
                  name locations, how Interactions compose into programs.
                  Language-agnostic, implementation-agnostic. A specification
                  anyone can implement.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs"><BookOpen size={14} aria-hidden /><span>Read the model</span></SiteButton>
                  <SiteButton href="https://github.com/nustackdev/interaction-model">
                    <GithubMark size={14} />
                    <SiteButtonRepoLabel>nustackdev/interaction-model</SiteButtonRepoLabel>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell className={s.imRight}>
            <CellContent pad="lg">
              <InteractionModelDiagram />
            </CellContent>
          </Cell>
        </Row>

        {/* 4. Foundations — nu */}
        <Row cols={1} borderBottom="solid" borderLeft="solid" borderRight="solid">
          <Cell className={s.chapterCell}>
            <span className={s.chapterPeek} aria-hidden>nu</span>
            <CellContent pad="lg">
              <Heading level={1}>
                Nu - the interaction model made real in Python.
              </Heading>
              <p className={s.sectionIntro}>
                Nu ships the model in pure Python. Batteries included:{' '}
                <strong>fabrics</strong> for the everyday jobs - in-memory
                state, kv-based state, Ray-distributed compute, UI building.
              </p>
            </CellContent>
          </Cell>
        </Row>
        <Row cols={1} borderBottom="solid" borderLeft="solid" borderRight="solid" className={s.hueCode}>
          <Cell>
            <CellContent pad="lg">
              <Stack gap="normal">
                <CodeSample filename="persistent_counter_ui.py" lines={NU_SAMPLE_LINES} />
                <CtaRow>
                  <SiteButton href="/docs"><BookOpen size={14} aria-hidden /><span>Meet Nu</span></SiteButton>
                  <SiteButton href="https://github.com/nustackdev/nu">
                    <GithubMark size={14} />
                    <SiteButtonRepoLabel>nustackdev/nu</SiteButtonRepoLabel>
                  </SiteButton>
                  <SiteButton href="https://github.com/nustackdev/nu/tree/main/examples">
                    <GithubMark size={14} />
                    <span>See more examples</span>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
        </Row>

        {/* 5. Fabrics */}
        <Row cols={1} borderBottom="solid" borderLeft="solid" borderRight="solid">
          <Cell className={s.chapterCell}>
            <span className={s.chapterPeek} aria-hidden>fabrics</span>
            <CellContent pad="lg">
              <Heading level={1}>Fabrics.</Heading>
              <p className={s.sectionIntro}>
                Fabrics are the tissue between Refs and the real world: memory,
                kv stores, UI, network, cluster. These are the ones Nu ships
                with today.
              </p>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm" className={s.hueSteel}>
          <Cell>
            <CellContent pad="lg">
              <SilverWovenName as="h3" hue="steel">nu.mem</SilverWovenName>
              <Stack gap="normal">
                <Tagline>In-memory state fabric.</Tagline>
                <Description>
                  In-memory state on plain dicts. Perfect for cache, hot state,
                  and in-process coordination.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs/fabrics/mem" variant="hueTinted">
                    <BookOpen size={14} aria-hidden />
                    <span>Read the docs</span>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <VizFrame><MemGlyph /></VizFrame>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm" className={s.hueSage}>
          <Cell>
            <CellContent pad="lg">
              <SilverWovenName as="h3" hue="sage">nu.virtuals</SilverWovenName>
              <Stack gap="normal">
                <Tagline>Persistent state fabric.</Tagline>
                <Description>
                  Refs over a KV backend (RocksDB, LMDB). Transactions,
                  snapshots, and change notifications, built in.
                </Description>
                <Label>Backends: rocksdb, lmdb</Label>
                <CtaRow>
                  <SiteButton href="/docs/fabrics/virtuals" variant="hueTinted">
                    <BookOpen size={14} aria-hidden />
                    <span>Read the docs</span>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <VizFrame><VirtualsGlyph /></VizFrame>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm" className={s.hueTeal}>
          <Cell>
            <CellContent pad="lg">
              <SilverWovenName as="h3" hue="teal">nu.ui</SilverWovenName>
              <Stack gap="normal">
                <Tagline>Web UI fabric.</Tagline>
                <Description>
                  Same fabric shape as the others, but the Refs are widgets:
                  text, buttons, tables. The fabric renders them in the browser
                  and live-updates them as your state changes.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs/fabrics/ui" variant="hueTinted">
                    <BookOpen size={14} aria-hidden />
                    <span>Read the docs</span>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <VizFrame><UiGlyph /></VizFrame>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm" className={s.huePlum}>
          <Cell>
            <CellContent pad="lg">
              <SilverWovenName as="h3" hue="plum">nu.invisibles</SilverWovenName>
              <Stack gap="normal">
                <Tagline>Network fabric.</Tagline>
                <Description>
                  A Nu fabric that puts other fabrics on the network. Bind a
                  fabric in one process, use it from another; same Refs, same
                  interactions, over TCP or Unix socket.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs/fabrics/invisibles" variant="hueTinted">
                    <BookOpen size={14} aria-hidden />
                    <span>Read the docs</span>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <VizFrame><InvisiblesGlyph /></VizFrame>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm" className={s.hueAmber}>
          <Cell>
            <CellContent pad="lg">
              <SilverWovenName as="h3" hue="amber">nu.ray</SilverWovenName>
              <Stack gap="normal">
                <Tagline>Cluster compute fabric.</Tagline>
                <Description>
                  A Nu fabric for cluster compute. Teleport a Nu tree to any
                  worker in your Ray cluster; it runs there and returns the
                  result.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs/fabrics/ray" variant="hueTinted">
                    <BookOpen size={14} aria-hidden />
                    <span>Read the docs</span>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <VizFrame><RayGlyph /></VizFrame>
            </CellContent>
          </Cell>
        </Row>

        {/* 6. Apps */}
        <Row cols={1} borderBottom="solid" borderLeft="solid" borderRight="solid">
          <Cell className={s.chapterCell}>
            <span className={s.chapterPeek} aria-hidden>apps</span>
            <CellContent pad="lg">
              <Heading level={1}>Standalone apps built on Nu.</Heading>
              <p className={s.sectionIntro}>
                Applications built on Nu today.
              </p>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm" className={s.hueAmber}>
          <Cell>
            <CellContent pad="lg">
              <SilverWovenName as="h3" hue="amber">nulog</SilverWovenName>
              <Stack gap="normal">
                <Tagline>
                  Pure-Python, serverless logger and metrics store.
                </Tagline>
                <Description>
                  Log messages and observe metrics from any Python code. Entries
                  persist to an embedded KV store (RocksDB, LMDB) and scale to
                  billions, all in-process. One line boots a live viewer.
                </Description>
                <CtaRow>
                  <SiteButton variant="repo" href="https://github.com/nustackdev/nulog">
                    <GithubMark size={14} />
                    <SiteButtonRepoLabel>nustackdev/nulog</SiteButtonRepoLabel>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <VizFrame><NulogMockSvg /></VizFrame>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm" className={s.huePlum}>
          <Cell>
            <CellContent pad="lg">
              <SilverWovenName as="h3" hue="plum">nuspace</SilverWovenName>
              <Stack gap="normal">
                <Tagline>
                  A programmable knowledge base.
                </Tagline>
                <Description>
                  nuspace is Nu made touchable: blocks and pages are Refs, UI
                  edits are Interactions, automations and saved views are trees.
                  Data, UI, and computation live in the same context, and the
                  human and the code meet at a block&apos;s name.
                </Description>
                <Label>Status: Coming soon.</Label>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <VizFrame><NuspaceMockSvg /></VizFrame>
            </CellContent>
          </Cell>
        </Row>

        {/* 7. Infra */}
        <Row cols={1} borderBottom="solid" borderLeft="solid" borderRight="solid">
          <Cell className={s.chapterCell}>
            <span className={s.chapterPeek} aria-hidden>infra</span>
            <CellContent pad="lg">
              <Heading level={1}>Infra. The tools that power Nu fabrics.</Heading>
              <p className={s.sectionIntro}>
                Standalone Python libraries the fabrics build on. Each is
                useful on its own; together they form the substrate under Nu.
              </p>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm">
          <Cell>
            <CellContent pad="lg">
              <Stack gap="normal">
                <Stack gap="tight">
                  <Heading level={2}>virtuals</Heading>
                  <Tagline>
                    Virtual Python collections over any KV storage.
                  </Tagline>
                </Stack>
                <Description>
                  Virtuals gives you native-feeling Python collections that
                  don&apos;t physically exist in memory. They&apos;re lazy views
                  over tuple-key KV storage: define your structure, plug in a
                  backend (RocksDB, LMDB, in-memory), get transactions and change
                  notifications for free.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs/virtuals"><BookOpen size={14} aria-hidden /><span>Read the docs</span></SiteButton>
                  <SiteButton href="https://github.com/nustackdev/virtuals">
                    <GithubMark size={14} />
                    <SiteButtonRepoLabel>nustackdev/virtuals</SiteButtonRepoLabel>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <Stack gap="normal">
                <Stack gap="tight">
                  <Heading level={2}>invisibles</Heading>
                  <Tagline>Transparent remote objects for Python.</Tagline>
                </Stack>
                <Description>
                  You have an object. You move it to another process or node. The
                  code that uses it doesn&apos;t change. Invisibles handles
                  boxing, dispatch, and proxying so remote calls read exactly
                  like local ones. Sync methods stay sync, async methods stay
                  async.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs/invisibles"><BookOpen size={14} aria-hidden /><span>Read the docs</span></SiteButton>
                  <SiteButton href="https://github.com/nustackdev/invisibles">
                    <GithubMark size={14} />
                    <SiteButtonRepoLabel>nustackdev/invisibles</SiteButtonRepoLabel>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
        </Row>

        <Row cols={2} borderBottom="solid" borderLeft="solid" borderRight="solid" stackAt="sm">
          <Cell>
            <CellContent pad="lg">
              <Stack gap="normal">
                <Stack gap="tight">
                  <Heading level={2}>rdbpy</Heading>
                  <Tagline>
                    RocksDB bindings for Python, with transactions.
                  </Tagline>
                </Stack>
                <Description>
                  rdbpy bundles RocksDB and its compression libs into the wheel
                  for Linux and macOS (Intel + Apple Silicon). No system install
                  required. Import, open a DB, put/get/iterate.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs/rdbpy"><BookOpen size={14} aria-hidden /><span>Read the docs</span></SiteButton>
                  <SiteButton href="https://github.com/nustackdev/rdbpy">
                    <GithubMark size={14} />
                    <SiteButtonRepoLabel>nustackdev/rdbpy</SiteButtonRepoLabel>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
          <Cell>
            <CellContent pad="lg">
              <Stack gap="normal">
                <Stack gap="tight">
                  <Heading level={2}>kh57</Heading>
                  <Tagline>
                    Deterministic, stable, range-friendly reservoir sampling.
                  </Tagline>
                </Stack>
                <Description>
                  You have trillions of sorted-by-key items on disk. You want{' '}
                  <code>n</code> uniform samples from a sub-range without pulling
                  the whole thing. kh57 hashes each key into a level, stores
                  under a compound sort key, and reservoir-samples the boundary
                  level. Any sorted KV store works as a backend.
                </Description>
                <CtaRow>
                  <SiteButton href="/docs/kh57"><BookOpen size={14} aria-hidden /><span>Read the docs</span></SiteButton>
                  <SiteButton href="https://github.com/nustackdev/kh57">
                    <GithubMark size={14} />
                    <SiteButtonRepoLabel>nustackdev/kh57</SiteButtonRepoLabel>
                  </SiteButton>
                </CtaRow>
              </Stack>
            </CellContent>
          </Cell>
        </Row>

        {/* 8. Footer */}
        <Row cols={1} borderLeft="solid" borderRight="solid">
          <Cell>
            <CellContent pad="md">
              <div className={s.footer}>
                <Link href="/docs">Docs</Link>
                <span className={s.footerSep}>·</span>
                <a href="https://github.com/nustackdev">GitHub</a>
                <span className={s.footerSep}>·</span>
                <span className={s.footerBrand}>
                  <NuLogo size={14} className={s.footerLogo} />
                  <NustackMark mono /> © 2026
                </span>
              </div>
            </CellContent>
          </Cell>
        </Row>
      </Container>
    </div>
  );
}
