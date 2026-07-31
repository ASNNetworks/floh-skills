---
name: nextjs-conventions
description: Apply App Router and Tailwind v4 conventions correctly in a Next.js project — server vs client components, data fetching, metadata, and the Tailwind v4 changes that silently break v3 habits. Use when writing or reviewing Next.js pages, components, layouts, route handlers or Tailwind classes.
---

# Next.js App Router and Tailwind v4

The App Router and Tailwind v4 both punish habits carried over from their previous
versions, and both do it quietly: the page renders, the class is ignored, nothing errors.
This skill is the set of rules that catch that.

## When to use this

Writing or reviewing anything in a Next.js 14+ App Router project: pages, layouts,
components, route handlers, metadata, Tailwind classes.

## Server components are the default. Keep them that way.

`'use client'` is not a fix for a build error. Every time you add it, you move the
component *and its whole import subtree* into the browser bundle.

Add it only for: `useState`/`useEffect`/`useRef`, event handlers, browser APIs, or a
library that needs them. Anything else stays on the server.

**The pattern that keeps the boundary small** — a server page fetching data, handing a
serialised prop to a thin client leaf:

```tsx
// app/thing/[slug]/page.tsx  — server, no directive
import { getThing } from '@/lib/things';
import ThingChart from '@/components/ThingChart'; // 'use client' lives THERE

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;              // params is a Promise in Next 15+
  const thing = await getThing(slug);
  if (!thing) notFound();
  return <ThingChart points={thing.points} />;
}
```

Push `'use client'` down to the leaf that needs it, never up to the page.

**Props crossing the boundary must be serialisable.** Functions, class instances,
`Date`, `Map`, `Set` and React components do not cross. Pass a slug and resolve the
component from a client-side registry on the other side.

## Data fetching

- `fetch` in a server component is cached and deduped. Two components fetching the same
  URL in one render make one request.
- `export const dynamic = 'force-static'` on a route handler that reads only local content.
- `export const revalidate = 3600` beats a hand-rolled cache.
- **Never fetch your own API route from a server component.** It is an HTTP round trip to
  yourself. Call the function the route handler calls.
- **Never fetch same-server data from a client component with a loading spinner.** Render
  it on the server; the data is already there. A skeleton for data the server could have
  inlined is a self-inflicted layout shift.

## Metadata

```tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const { slug } = await params;
  const thing = await getThing(slug);
  if (!thing) return {};
  return {
    title: thing.seoTitle,
    description: thing.seoDescription,
    alternates: { canonical: `https://example.com/thing/${slug}` },
    openGraph: { title: thing.seoTitle, images: [`/og/thing/${slug}.png`] },
  };
}

export function generateStaticParams() {
  return allSlugs.map((slug) => ({ slug }));
}
```

`generateMetadata` and the page body both run; shared work is deduped by the fetch cache,
so do not thread data between them manually.

## Tailwind v4, and what changed

**Configuration moved into CSS.** `@theme` in your stylesheet, not `theme.extend` in a
config file. A v3 config still works through the compat layer, but new tokens belong in
CSS.

**Opacity modifiers now compile to `color-mix`.** This is the good news: `bg-[var(--x)]/10`
works on an arbitrary CSS variable, which it could not in v3. Design tokens as CSS
variables plus opacity modifiers is now the idiomatic pattern.

**`transform` utilities are standalone.** In v3, `scale-105` implied `transform`. In v4
`scale`, `translate` and `rotate` are independent properties. So:

```html
<!-- broken in v4: transitions nothing -->
<div class="transition-transform hover:scale-105">

<!-- correct -->
<div class="transition-[scale] hover:scale-105">
<div class="transition-[scale,translate] hover:scale-105 hover:-translate-y-1">
```

This is the single most common silent v4 breakage: the hover still applies, it just snaps
instead of animating.

**Class names must be statically visible.** Tailwind scans source text. `` `bg-${c}-500` ``
generates nothing. Write full class strings and pick between them:

```tsx
const TONE = {
  ok:   'bg-green-500/10 text-green-600',
  warn: 'bg-amber-500/10 text-amber-600',
} as const;
```

**Default border colour changed** from `gray-200` to `currentColor`. A bare `border`
inherits text colour now. Always name the colour.

## Review checklist

- [ ] Is `'use client'` on the smallest component that needs it?
- [ ] Do all boundary props serialise?
- [ ] Is `params` awaited?
- [ ] Does every dynamic route have `generateStaticParams` where the set is known?
- [ ] Any interpolated Tailwind class names?
- [ ] Any `transition-transform` paired with a v4 standalone transform utility?
- [ ] Any client-side fetch of data the server already had?
- [ ] Any `border` without an explicit colour?
