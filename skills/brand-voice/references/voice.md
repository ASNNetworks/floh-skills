# Voice guide (template)

Copy this to `VOICE.md` at your repo root and edit it. Every rule below is a default, not
a law: the point is that the rules are *written down* and *checkable*, not that they match
someone else's taste.

## 1. Who is speaking

```yaml
person: first-person-singular   # first-person-singular | first-person-plural | none
reader: informal                # informal (je/jij, you) | formal (u)
```

A solo operator writes "ik" and "mijn". Never "we" or "wij", which invents a team that
does not exist and reads as evasion when something goes wrong. A company with staff
writes "we". Pick one and never mix them inside a page.

Address the reader directly and informally: "je krijgt", not "de klant ontvangt".

## 2. Punctuation

```yaml
forbidden_chars: ["—", "–"]     # em dash, en dash
```

Em dashes are the tell of generated text and they hide sloppy sentence structure. Use a
comma, a colon, or two sentences. If a sentence genuinely needs a parenthetical, use
brackets or rewrite it.

Exception: a typographic separator in a fixed template (`Title — Section`) is a layout
element, not prose. Whitelist those explicitly.

## 3. Banned phrases

```yaml
banned:
  - "in het huidige digitale landschap"
  - "in today's fast-paced"
  - "naadloos"
  - "seamless"
  - "revolutionair"
  - "game changer"
  - "ontketen"
  - "unlock the power"
  - "duik in"
  - "dive into"
  - "het is belangrijk op te merken"
  - "it is important to note"
```

These are not banned for being ugly. They are banned for carrying no information: every
one of them can be deleted without changing the meaning of its sentence.

## 4. Register

- **Concrete over abstract.** "Draait in 40 seconden" beats "razendsnel".
- **Say the number or say nothing.** No invented percentages, no "tot wel 3x sneller"
  without a measurement behind it.
- **One claim per sentence.**
- **Short paragraphs.** Three sentences is usually enough.
- **No exclamation marks** outside genuine interjections.
- **Lists earn their place.** Three bullets of four words each should have been a
  sentence.

## 5. Worked example

Before:

> In het huidige digitale landschap is het belangrijk op te merken dat wij een
> revolutionaire, naadloze en schaalbare oplossing bieden die je bedrijfsprocessen
> ontketent — zodat jij kunt focussen op wat écht telt.

Everything wrong at once: corporate opener, invented "wij", three empty adjectives, two
banned phrases, an em dash, and no claim a reader could check.

After:

> Ik koppel je boekhouding aan je webshop, zodat een bestelling meteen als factuur
> binnenkomt. Je typt niets meer over.

Two sentences. One concrete claim. A reader knows within five seconds whether this is for
them.
