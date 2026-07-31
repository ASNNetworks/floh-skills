# Deck schema

One JSON file describes the whole carousel. The renderer never asks a question: whatever
is in here is what gets drawn.

```json
{
  "theme": {
    "accent":     "#84CC16",
    "background": "#0B1020",
    "text":       "#F8FAFC",
    "muted":      "#94A3B8",
    "font":       "Inter"
  },
  "meta": {
    "author": "Alisina Nawabi",
    "handle": "@alisina",
    "logo":   "assets/logo.png"
  },
  "slides": []
}
```

`theme.font` resolves against the system font list; the renderer falls back to DejaVu Sans
and says so, rather than silently drawing boxes.

## Slide kinds

### `hook` (slide 1, exactly one per deck)

```json
{ "kind": "hook", "headline": "...", "sub": "...", "kicker": "SKILLS" }
```

Headline at 72pt, three lines maximum. `sub` is optional and sits under it at 32pt.
`kicker` is a small uppercase label above the headline. No page number is drawn here.

### `point` (the body of the deck)

```json
{ "kind": "point", "headline": "...", "body": "...", "number": true }
```

Headline 48pt, body 28pt and capped at 25 words. The renderer **refuses** a longer body
rather than shrinking the type, because a slide nobody can read in the feed is worse than
a deck with one more slide. Split it.

### `list`

```json
{ "kind": "list", "headline": "...", "items": ["...", "...", "..."] }
```

Three to five items, six words each. More than five and it stops being a slide.

### `quote`

```json
{ "kind": "quote", "text": "...", "attribution": "..." }
```

Centred, 40pt, accent-coloured opening mark. Use at most one per deck.

### `code`

```json
{ "kind": "code", "headline": "...", "code": "...", "language": "python" }
```

Mono, 22pt, at most 12 lines. Nobody reads code on a phone: this is for showing that code
*exists*, not for teaching it.

### `recap`

```json
{ "kind": "recap", "headline": "...", "items": ["...", "...", "..."] }
```

Exactly three items. It is a recap, not a second deck.

### `cta` (last slide, exactly one per deck)

```json
{ "kind": "cta", "headline": "...", "body": "...", "handle": "@alisina" }
```

One action. "Volg me, deel dit, en stuur een bericht" is three, and gets none of them.

## Layout constants

| Constant | Value | Why |
|----------|-------|-----|
| Page | 1080 x 1350 px | 4:5, the tallest LinkedIn accepts |
| Safe margin | 88 px | Below this, text touches the card edge in the feed |
| Headline | 48pt (72pt on hook) | Readable at 20% zoom |
| Body | 28pt | |
| Line length | 32 characters max | Longer and the eye loses the line at this type size |
| Page number | bottom right, 20pt, muted | Absent on the hook slide |

## Validation the renderer performs

- Exactly one `hook`, and it is first.
- Exactly one `cta`, and it is last.
- Total slides between 8 and 12. It warns outside that range, and still renders.
- No `point.body` over 25 words. This one is a hard error.
- Every colour parses as hex.
- The font resolves, or the fallback is named out loud.
