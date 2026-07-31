---
name: brand-voice
description: Enforce a project's writing voice on any text the agent produces or edits — pronouns, forbidden punctuation, banned phrases, sentence rhythm. Use when writing or reviewing copy, marketing text, UI strings, documentation or commit messages for a project that has a defined voice.
---

# Brand voice

A voice guide that lives in a document gets read once. A voice guide that lives in a skill
gets applied to every sentence the agent writes.

## When to use this

Any time you write or edit prose that a reader outside the team will see: page copy, UI
strings, emails, changelogs, documentation, social posts. Also when reviewing a pull
request that touches user-facing text.

Do not apply it to code comments or internal notes unless the project says so.

## How to run it

1. **Read the voice file.** `references/voice.md` in this skill is the template. A project
   overrides it by putting its own `VOICE.md` at the repo root; that file wins on every
   rule it defines.

2. **Write the text.**

3. **Check it before you hand it over.**

   ```bash
   python3 scripts/check_voice.py <file-or-glob>
   ```

   The checker is mechanical: it catches the rules that can be caught mechanically
   (forbidden characters, banned phrases, pronoun drift). Everything it cannot catch is
   on you.

4. **Fix, do not annotate.** A note saying "this uses 'we' but the guide says 'I'" is not
   the deliverable. The corrected sentence is.

## The rules that get broken most

**Pronouns drift under pressure.** A solo operator writing "we offer" is the single most
common failure, and it happens on the third paragraph, not the first: the writing slips
into corporate register when the topic gets abstract. Reread specifically for this.

**Punctuation the guide forbids comes back through rewriting.** If a project bans em
dashes, an agent that removes them in draft one reintroduces them in draft three while
"improving flow". Run the checker on the final text, not the draft.

**Hedging.** "Kan helpen bij", "zou kunnen bijdragen aan", "is bedoeld om". If the thing
works, say it works. If it does not, do not write about it yet.

**The three-adjective sentence.** "Een snelle, moderne en schaalbare oplossing" says
nothing. One concrete claim beats three abstract ones.

## What the checker cannot see

- Whether the text is *true*. A perfectly on-voice sentence about a feature that does not
  exist is worse than an off-voice one about a feature that does.
- Whether it is worth reading. Voice compliance is a floor.
- Rhythm. Six sentences of identical length read as a machine wrote them, and no regex
  catches that. Read it aloud.

## Files

- `references/voice.md` — the template guide: pronouns, punctuation, banned phrases,
  register, and a worked before/after.
- `scripts/check_voice.py` — mechanical checker. Exits non-zero on any violation, so it
  drops into CI.
