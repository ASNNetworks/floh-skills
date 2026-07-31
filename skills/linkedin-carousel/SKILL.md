---
name: linkedin-carousel
description: Turn an article, a case or a set of notes into a LinkedIn carousel PDF — slide structure, per-slide copy, and a renderer that produces the exact aspect ratio LinkedIn accepts. Use when asked to make a carousel, a slide deck for social, or to repurpose a long piece into slides.
---

# LinkedIn carousel

A carousel is a document upload, not an image post. That single fact decides the format,
and getting it wrong is why most carousels look cropped.

## When to use this

Repurposing an article, case study, lesson or set of notes into a LinkedIn carousel.
Also for the hook-and-structure work before any slides exist.

## The format, which is not negotiable

- **PDF**, uploaded as a document. Not a set of images.
- **1080 x 1350** (4:5 portrait). LinkedIn also accepts 1:1, but 4:5 takes the most
  vertical space in the feed, so it is the default.
- **8 to 12 slides.** Under 8 does not justify the swipe; over 12 and the drop-off is
  steeper than the reach gain.
- **Fonts embedded.** A PDF with linked fonts renders as fallback boxes on LinkedIn's
  server-side thumbnailer, and you will not see it in your own preview.
- **Under 100 MB**, which is never the binding constraint if you are not embedding photos.

## The structure that works

| Slide | Job |
|-------|-----|
| 1 | **Hook.** One claim, large. It has to work as a static thumbnail, because that is all most people see |
| 2 | **Stakes.** Why this costs the reader something today |
| 3-9 | **One idea per slide.** A heading and at most 25 words. If it needs 40, it is two slides |
| 10 | **Recap.** The three things worth remembering |
| 11 | **CTA.** One action, spelled out |

Rules that hold across all of them:

- **One idea per slide.** The most common failure is slide 4 carrying three points because
  the source paragraph had three sentences.
- **Slide 1 has no context.** It cannot say "as I mentioned". It is a cold open.
- **Readable at thumbnail size.** Headline at least 48pt at 1080 wide. Hold the slide at
  20% zoom; if you cannot read the headline, nobody in the feed can.
- **No paragraph anywhere.** If a slide has a paragraph, it wanted to be an article.

## How to run it

1. **Write the outline first, as text.** Slide number, headline, body. Get the structure
   approved before rendering anything. Regenerating a deck because slide 3 was wrong is
   ten seconds; rewriting after design is not.

2. **Put it in a JSON deck file:**

   ```json
   {
     "theme": { "accent": "#84CC16", "background": "#0B1020", "text": "#F8FAFC" },
     "slides": [
       { "kind": "hook",  "headline": "Je AI-agent leest je documenten verkeerd",
                          "sub": "En hij zegt het er niet bij" },
       { "kind": "point", "headline": "03/04/2026",
                          "body": "3 april of 4 maart. Zonder context is dat een gok, en een gok in je boekhouding." },
       { "kind": "cta",   "headline": "Wil je dit goed hebben?",
                          "body": "Stuur me een bericht.", "handle": "@alisina" }
     ]
   }
   ```

3. **Render:**

   ```bash
   python3 scripts/render.py deck.json -o carousel.pdf
   ```

   The renderer produces 1080x1350 pages with embedded fonts and reports the page count
   and file size so you can check both before uploading.

4. **Check at thumbnail size before you post.** Every time.

## Writing the hook

The hook slide decides everything downstream. Four openings that work, in rough order of
reliability:

1. **A cost.** "Deze fout kost je een kwartaal aan verkeerde cijfers."
2. **A contradiction.** "Snellere agents maken je trager."
3. **A concrete number.** "Zes van de tien facturen die ik zag hadden een verkeerde datum."
4. **A named mistake.** "De fout die iedereen maakt met SKILL.md."

Openings that do not work: a question the reader can answer with "no", a definition, and
anything beginning "In het huidige digitale landschap".

## The accompanying post

The carousel does not stand alone. The post text above it carries the hook again in
plain words and ends with one question. Three to five lines. The first two lines are what
shows before "see more", so the hook has to land there.

## Files

- `scripts/render.py` — deck JSON to a 1080x1350 PDF with embedded fonts. No design tool
  needed.
- `references/deck-schema.md` — every slide kind and its fields, with layout notes.
