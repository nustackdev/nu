import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex flex-col justify-center items-center text-center flex-1 gap-8 px-6">
      <div className="flex flex-col gap-4 max-w-2xl">
        <h1 className="text-5xl font-bold tracking-tight">Nu</h1>
        <p className="text-xl text-fd-muted-foreground">
          A programming model where everything is a Nu.
        </p>
        <p className="text-fd-muted-foreground">
          Two top-level kinds: <b>Ref</b> (an address) and{' '}
          <b>Interaction</b> (Query, Command, Flow, Span).
        </p>
      </div>
      <div className="flex gap-3">
        <Link
          href="/docs"
          className="rounded-md bg-fd-primary text-fd-primary-foreground px-5 py-2.5 text-sm font-medium hover:opacity-90 transition"
        >
          Read the docs
        </Link>
        <Link
          href="https://github.com/nustackdev/nu"
          className="rounded-md border border-fd-border px-5 py-2.5 text-sm font-medium hover:bg-fd-accent transition"
        >
          GitHub
        </Link>
      </div>
    </div>
  );
}
