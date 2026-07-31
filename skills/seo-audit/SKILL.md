---
name: seo-audit
description: Audit a web page or a whole site for technical and on-page SEO problems, ranked by what actually moves rankings. Use when asked to review SEO, diagnose why a page does not rank, check metadata and structured data, or prepare a page for indexing.
---

# SEO audit

Audit a page the way a search engine reads it: fetch the rendered HTML, check what is
actually in it, and rank findings by impact rather than by how easy they are to spot.

## When to use this

Reach for this skill when someone asks why a page is not ranking, wants metadata or
structured data checked, is about to publish something and wants it indexable, or asks
for "an SEO check" in any wording.

Do not use it for keyword research or content strategy. This skill inspects what exists.

## How to run it

1. **Get the rendered HTML.** Server-rendered markup is what matters. Fetch the URL, or
   for a local project read the built output rather than the source component.

2. **Run the checker.**

   ```bash
   python3 scripts/audit.py <url-or-file> --json
   ```

   It returns findings grouped as `critical`, `important` and `polish`.

3. **Read the findings in that order and stop adding your own.** The temptation is to
   list every deviation from a best-practice checklist. Do not. A page with a missing
   `<title>` does not need a note about image lazy-loading in the same breath.

## What gets checked

**Critical** — the page cannot rank or cannot be indexed:

- `noindex` in a meta robots tag or an `X-Robots-Tag` header
- missing or empty `<title>`
- missing `<h1>`, or more than one
- canonical pointing somewhere unexpected (another host, a redirect, itself via a
  different protocol)
- the main content is absent from server-rendered HTML and only appears after hydration
- 4xx/5xx on the URL itself or on the canonical target

**Important** — the page ranks worse than it should:

- `<title>` outside 30-60 characters, or duplicated across pages
- meta description missing, or outside 120-160 characters
- heading hierarchy that skips levels
- images without `alt`, links whose only text is "hier" or "lees meer"
- no structured data where the content type clearly has a schema (`Article`, `FAQPage`,
  `BreadcrumbList`, `Product`)
- structured data present but failing validation
- Open Graph or Twitter card incomplete, so shares render bare

**Polish** — real but small:

- no `lang` attribute
- absolute internal links where relative would do
- trailing-slash inconsistency against the rest of the site

## Reporting

Write findings as: what is wrong, what it costs, and the exact fix. One line each.

```
CRITICAL  <title> is empty
          Google renders the URL as the result title. Nothing else on this page
          matters until this is fixed.
          → app/kennis/[slug]/page.tsx:31 — generateMetadata returns no title when
            post.seoTitle is undefined; fall back to post.title.
```

Never report a count without the list. "12 images missing alt text" is not actionable;
the twelve paths are.

## Things that look like problems and are not

- **A canonical that points to itself.** That is correct and expected.
- **Multiple `<h2>`s.** Fine. Only `<h1>` is constrained.
- **A low word count.** Not a ranking factor on its own. A short page that answers the
  query completely beats a padded one.
- **Missing keywords meta tag.** No search engine has used it for over a decade.

## Files

- `scripts/audit.py` — the checker. Runs offline against a file, or fetches a URL.
- `references/schema-types.md` — which structured-data type fits which page, with the
  required fields for each.
