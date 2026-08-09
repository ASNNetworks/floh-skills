---
name: pharos
description: "Use for AZURE DEVOPS work — when the user says Azure DevOps, ADO or dev.azure.com, or names an ADO work item by number (\"pick up 4821\", \"what's on 210\"). Covers reading or updating an ADO work item, ticket, bug, story or epic; the ADO board, backlog, sprint or iteration; what is assigned to you; reading or writing an ADO wiki page and its comments; linking a plan to an epic; attaching a file to a work item or taking one off; inline images in a field or wiki page; @mentioning somebody so they are notified; importing Markdown, Word or PDF as wiki pages; and whether a failed call is retryable. ALSO the GITHUB ISSUE ↔ work item EDGE: adopting an issue as a work item linked at both ends, bulk-adopting a repo, one reply reaching reporter and board, where they have drifted, closing both ends together, and changing a comment that ALREADY EXISTS: editing, deleting, reacting, hiding, pinning. NOT a GitHub CLI: listing or viewing an issue, or POSTING a comment, is `gh`'s job. NOT for other trackers — Argus, Jira, Linear."
license: Proprietary
---

# Working Azure DevOps with `pharos`

`pharos` is a CLI that gives you Azure DevOps from a shell, authenticated by an
environment variable rather than a browser login.

**Everything it can do is listed below. Do not run `pharos --help` to find
out** — that costs several calls and this section is the same information.

```
whoami                         who ADO_PAT belongs to. @Me resolves to this
types                          what --state and --type will ACCEPT, per type
query                          WHICH work items — assigned to you, in a sprint,
                               of a type, still open. Hydrated items, not ids.
task <id>                      one work item, whole: fields, comments,
                               attachments, relations WITH titles, and the
                               content + discussion of every linked wiki page
                               --children  an EPIC and everything under it, in
                               ONE call. --depth <n> for deeper (max 5)
                               --compact   flatten identities, drop board keys
create <type> --title "…"      one work item. --parent goes in the SAME patch
update <id>                    change a field: --state --priority --assignee
                               --title, or --field Name=value for anything else
                               --expect-rev <n> pins a revision you read earlier
link <id> --parent <id>        relate two items. Also --child --related
unlink <id> --parent <id>      --predecessor --successor --duplicate
link <id> --wiki-page <path>   link a WIKI PAGE to a work item — the item side
wiki links <path>              which work items link a page (ADO has no API)
wiki link <path> --item <id>   the WIKI side; --item repeatable
wiki unlink <path> --item <id>
history <id>                   what CHANGED, field by field, who and when
iterations | areas             the sprints with their dates, and the areas
links                          every relation type this ORG has, and which
                               --flag reaches it (six of ~eighteen)
fields [--type T]              what a field will ACCEPT — allowed values
attach <id> <file>             put a FILE on a work item (Attachments list)
detach <id> <url-or-guid>      take one off. --yes. Or --name <file>
download <item-id|guid|url>    read one back. A WORK ITEM id with --name <file>,
                               or --all --out <dir>. --out or nothing is written
image <file>                   upload a PICTURE for use inside text. Prints the
                               markdown to paste. NOT the same as attach
people [query]                 who can be @mentioned, with the @<guid> form
delete <id> --yes              → Recycle Bin (no permanent delete, on purpose)
restore <id>                   bring one back
deleted                        what is in the Recycle Bin, with names.
                               --top <n> — it returns 50 by default and reports
                               the true total as "count"
wiki list | tree | read <path> | write <path> | delete <path>
wiki move <path> <new path>    move a page; sub-pages come with it
wiki rename <path> <new name>  the same call, leaf only. BOTH need --yes
wiki duplicate <path> [to]     a verb Azure DevOps lacks. "<path> - Copy N"
wiki image <file>              a picture for a PAGE or page comment. Different
                               endpoint from `image`, and the name is unique-d
wiki import <file...>          .md .txt .docx .pdf .rtf .html -> pages. A
                               .pptx is refused, on purpose — see below
                               --under <path> --as <name>
comment list | add | edit | delete   <target> is a work item id, a wiki path,
comment react | unreact | reactors   OR a GitHub issue (contoso/widgets#45)
comment hide | unhide | pin | unpin  GITHUB ONLY — Azure DevOps has neither
                               REACTIONS ARE NOT ONE VOCABULARY. Azure DevOps:
                               like dislike heart hooray smile confused. GitHub:
                               thumbs-up thumbs-down laugh hooray confused heart
                               rocket eyes. Passing one platform's name to the
                               other is refused, not translated
                               `comment add` is REFUSED on a GitHub issue — see
                               "Editing a GitHub comment" below
issue adopt <owner/name#45>    a GitHub ISSUE becomes a work item, with BOTH
                               ends of the link written. --type --title --parent
issue link <owner/name#45> <id>   join an existing pair — or finish a join that
                               half-happened. Only the missing half is written
issue say <owner/name#45>      ONE message, TWO audiences: the whole of it to
                               the reporter on GitHub, a summary and that
                               comment's URL to the board. --summary
issue trail <id|owner/name#45> the whole trail from EITHER end, with the
                               evidence for each half. Read-only
issue drift                    where the two platforms DISAGREE — the report no
                               other tool can produce. --repo --limit --wiql
issue backfill <owner/name>    bulk adopt every issue the board does not link
                               yet. Needs --yes. --limit --state --label
issue close <id|owner/name#45> close BOTH ends, then RE-READ both to say what
                               actually moved. --to --reason --all
issue edit <owner/name#45>     the issue's OWN fields, behind a lost-update
                               guard. Needs --yes. --title --text/--file/--stdin
                               --milestone --add-label --remove-label
                               --add-assignee --remove-assignee --if-title
                               --if-body. `gh issue edit` is the UNGUARDED one
hooks list | check | create | repoint | delete    service hooks for realtime.
                               `check` needs --hub <url>; `list` shows the URL
                               already in use
plan <file>                    an implementation plan → a work item tree
setup                          org, project, token → keychain + shell profile
                               --install ask|all|a,b  offer the optional
                               capabilities (LibreOffice, poppler, converter,
                               the GitHub CLI)
                               --repo owner/name --gh-account <login>  bind a
                               repository to the GitHub account that reaches
                               it. BOTH or NEITHER — `issue` needs this first
doctor                         what is installed on THIS machine, what is
                               missing, and what each missing thing costs
```

Text input: `--text` / `--file` / `--stdin`. Global: `--pretty` for a human,
`--yes` for destructive verbs, `--dry-run` to preview, `--max-writes <n>` to
change the per-invocation write cap (default 20; `0` is read-only).

**`ADO_ORG`, `ADO_PROJECT` and `ADO_PAT` are already in the environment** after
setup. Do not check them before working; a missing one announces itself as
`"kind": "config"` on exit 2, which is the only time it matters.

**Reading an attachment needs tools this machine may not have**, and the
commands further down name them with confidence they have not earned on yours.
`pharos doctor` answers that in one call: what is present, its version and where
it resolved, what is missing, and what each missing thing actually costs. It is
read-only and works before anything is configured — so it is also the right
first move when something behaves oddly. Offline too, with one exception it
names: `gh auth status` validates every token against github.com and there is
no flag that stops it, so that probe runs only when `gh` is installed.

`pharos setup --install ask` then offers to install them, driving Homebrew, apt
or winget rather than vendoring anything. **Nothing installs without that flag**
— `--install all` for a fresh machine, `--install libreoffice,poppler` to
provision without a terminal.

`--install skill` installs THIS skill as a plugin from the floh-skills
marketplace. Worth knowing even if you are reading it: **publishing a new
version does not update an installed one.** `claude plugin update
pharos@floh-skills` does, and a restart loads it — so a correction can ship and
sit unread for weeks. If something here contradicts what the tool actually does,
check your version first.

## Finding the work: `pharos query`

**Do not reach for `curl` and the WIQL endpoint.** This skill used to hand you a
recipe for exactly that, because there was no query verb. There is one now, and
it does the part the recipe could not: WIQL returns **ids only**, so the recipe
gave you sixteen bare numbers and a call per item to make them mean anything.

```bash
pharos query --mine                       # assigned to you, still open
pharos query --sprint "Sprint 1"          # --sprint current for @currentIteration
pharos query --type Epic --state Doing    # both repeatable
pharos query --assignee "ada@contoso.com"
pharos query --tag api --all              # --all includes finished work
pharos query --wiql "SELECT [System.Id] FROM WorkItems WHERE …"   # escape hatch
```

Flags AND together. Output is hydrated items — id, type, title, state, assignee,
iteration, tags, priority, changed — so `--mine` is one command, not a query
followed by a fetch per result. Follow up with `pharos task <id>` only for the
few you are actually going to work on.

**Read the `openness` field before you report a count.** "12 open" is
meaningless until you know what was counted as finished, and Azure DevOps lets a
process template rename every state. `query` reads the project's own state
categories and tells you which states it treated as terminal; if it could not
read them it says so and falls back to guessing, and that is your cue to pass
`--state` explicitly. `assignedTo` names who `@Me` actually resolved to — a
shared or service token makes "assigned to me" quietly mean somebody else.

`--all` composes with every other filter, so `--mine --all` is how you tell
*nothing is assigned to you* from *nothing open*. A bare `pharos query --all` is
legal and returns the whole project.

`--sprint` takes either the bare name or the fieldPath and normalises between
them — the fieldPath rule is about `System.IterationPath` as a *field value*. But
a named sprint matches with `UNDER` (sub-iterations included) while `--sprint
current` matches with `=` (exact), so they are not the same query.

`--wiql` also accepts a `FROM WorkItemLinks … MODE (MustContain)` query and
hydrates the ids the same way, which is how you find every item carrying a given
relation type in one call.

Do NOT write `[System.State] NOT IN GROUP 'Completed'` if you reach for `--wiql`.
It parses, returns 200, and matches **everything** — `IN GROUP` covers work item
TYPE categories only, and an unknown group resolves to the empty set with no
error. Measured, 2026-08-05.

## Changing a work item

```bash
pharos update 225 --state Doing              # move the state when the work moves
pharos update 225 --priority 1 --assignee "ada@contoso.com"
pharos update 225 --field Microsoft.VSTS.Scheduling.RemainingWork=3
pharos attach 225 ./bestsellers.xlsx --comment "The numbers"
```

`update` **reads the item and applies the change under a `test` op on `/rev`**,
so somebody who wrote between your read and your write gets you a `conflict`
rather than losing their edit. Confirmed live against real concurrent writers:
three rounds, one winner each round, the loser always a 412 `conflict` carrying
both revisions, and no lost update. **`--expect-rev <n>` pins a revision you
read earlier** instead of re-reading — reach for it when your read and your
write are separate calls with thinking in between, which is where a
read-modify-write actually goes wrong. Setting a value it already has writes nothing and
says so — a pointless PATCH still bumps `System.Rev` and invalidates every other
cached revision on the item. `--dry-run` shows the before → after and writes
nothing. There is no `--yes`: a field edit is an ordinary edit and Azure DevOps
keeps every revision.

`attach` uploads the bytes and then links them as an `AttachedFile` relation —
two calls, one command. Attachments are **immutable**: attaching the same file
twice makes two of them, and there is no replace and no versioning. `detach`
takes one off; it needs `--yes`, finds the attachment by identity rather than by
position, and leaves the bytes in Azure DevOps so re-attaching the url puts it
back. Name the file with `--name <file>` or pass the GUID — and as with
`download`, two files sharing a name REFUSE rather than removing whichever
sorts first.

`create` puts `--parent` in the same patch as the fields, so a child is never
briefly an orphan, and it takes the same flag names as `update`.

**`unlink` refuses rather than guessing, and that is worth knowing before you
see it.** Azure DevOps removes a relation by its POSITION in the array, so an
index from a stale read cuts a different link and the request still succeeds.
`unlink` finds the relation by identity and removes it under a `test` op on the
revision it read. If the relation is not there you get exit 3 — that means
nothing happened, not that the call failed.

`delete` moves to the **Recycle Bin** and needs `--yes`; the refusal quotes the
title first. `restore <id>` brings it back and needs no flag.

**There is no permanent delete here, deliberately.** It is the only irreversible
verb Azure DevOps has, and `--yes` is a flag you have learned to pass. The web
UI owns it. If somebody genuinely needs to purge, send them there rather than
looking for a flag.

## Pictures in text, and files beside it

**These are two different things and picking the wrong one is the mistake worth
avoiding.**

```bash
pharos attach 225 ./bestsellers.xlsx    # a FILE, in the Attachments list
pharos image ./screenshot.png           # a PICTURE, to put inside the text
```

An **attachment** creates an `AttachedFile` relation and appears in the work
item's Attachments list. An **inline image** creates no relation at all —
measured on #333, two screenshots pasted into a description gave `relations: 0`
and `attachments: []`. It is an `![](…)` in the field text and nothing else,
which is why the Attachments list is right to show nothing for it.

So `image` prints a markdown line and leaves the writing to you:

```bash
pharos image ./chart.png --pretty
# ![chart](https://dev.azure.com/…/wit/attachments/<guid>?fileName=chart.png)

pharos update 225 --field System.Description="$(cat <<'EOF'
Revenue is up. See the chart:

![chart](https://dev.azure.com/…/wit/attachments/<guid>?fileName=chart.png)
EOF
)"
```

**A wiki picture is a different endpoint and needs `wiki image`.** A wiki is a
git repository, so an attachment there is a FILE and its NAME is its identity:
upload a second `image.png` and it lands on the first, and every page pointing
at `/.attachments/image.png` silently changes picture. `wiki image` makes the
name unique before sending and prints a repo-relative link:

```bash
pharos wiki image ./diagram.png --pretty
# ![diagram](/.attachments/diagram-1786046773042.png)
```

Use that path, **not** an absolute url — a page linking to a `wit/attachments`
url renders for anyone with a session and breaks for everybody else. The same
markdown works in a page and in a page comment.

## Getting an attachment off a work item

`pharos task <id>` lists what is attached, with each file's **GUID** — in the
JSON and in `--pretty`. Then take it in one call, by name:

```bash
pharos download 41 --name Skills.pptx --out ./Skills.pptx
pharos download 41 --all --out ./attachments      # every attachment on the item
pharos download <guid-or-url> --out ./file.bin    # when you already hold one
```

**`--out` is what writes.** Without it you get the size and no file — raw bytes
on stdout would corrupt the JSON every other verb prints.

A bare `pharos download 41` is a usage error **carrying the list** — name, GUID
and size — so choosing the right file never costs a second call. Two attachments
with the same name refuse rather than guess: attachments are immutable, so
attaching a file twice makes two of them and the name is not an identity.

`detach` takes the same `--name <file>`, so the verb you reach for after reading
`task --pretty` accepts what it showed you:

```bash
pharos detach 41 --name Skills.pptx --yes      # --dry-run previews it first
```

### Reading what is inside it is YOUR job, with YOUR tooling

`download` gets you bytes on disk and stops there. Turning a `.docx`, `.pptx`,
`.xlsx` or `.pdf` into something you can read is your environment's job.

**Do not use `pharos-convert` for it.** It is `wiki import`'s converter, shared
with the macOS app so that both produce the same *page* from the same file — its
output is shaped to become a wiki page, and reaching for it here couples what you
read to the app's import path. It also cannot read `.pptx` at all.

Two ways this fails **silently**, both measured on a real work item:

- **You checked for the tool in the wrong place.** `which markitdown` against
  the system PATH and `import docx` against the system `python3` both come back
  empty on a machine where that tooling is installed — in a per-skill venv. An
  agent that runs those two checks concludes "nothing here" and routes around
  tools that were there the whole time. Look where *your* agent keeps its
  tooling before concluding it is absent.
- **Non-empty text is not proof you read the document.** One real `.pptx`
  extracted to seven fragments, about 90 characters; the entire specification
  was in two embedded PNGs. Every text-only reader returns something for that
  deck and looks like it worked. For a slide deck, or a scanned PDF, the payload
  is usually the images — extract them and actually look at them.

### First ask whether you read PDFs natively. If you do, this is one command.

Many agents — Claude Code among them — read a PDF **visually**, page by page,
the way a person looks at it. That covers a scan with no text in it at all, with
no OCR step. If that is you, the whole problem collapses to one conversion:

```bash
soffice --headless --convert-to pdf f.docx --outdir ./out    # .pptx, .xlsx too
# then read ./out/f.pdf with your own file-reading tool
```

**This is the route that keeps the pictures**, which is the whole failure this
section is about. Measured on the deck described above — the one whose seven
text fragments lost the specification: converted to PDF and read, it gives up
the flow diagram, the screenshot of the configuration UI with its actual
threshold values, and every row and column of the target output table. One
command, one read, nothing dropped. The same is true of a `.docx` whose content
is in a chart or a screenshot.

Prefer it whenever layout or images might carry meaning — a deck always, a
report usually, a spreadsheet when the shape matters more than the numbers.

### If you only read text, extract it per format

| file | how |
|---|---|
| `.pdf` | `pdftotext -layout f.pdf -` — poppler; keeps the table layout. **Empty output means a scan**, not an empty document |
| scanned `.pdf` | `pdftoppm -png -r 150 f.pdf page`, then look at the PNGs it wrote |
| `.docx` | `soffice --headless --convert-to "txt:Text (encoded):UTF8" f.docx --outdir ./out` — tables come out tab-separated |
| `.xlsx` | `soffice --headless --convert-to csv f.xlsx --outdir ./out` — **first sheet only**. Count them first: `unzip -p f.xlsx xl/workbook.xml \| grep -o '<sheet [^>]*name="[^"]*"'` |
| `.pptx` | `~/.claude/skills/pptx/.venv/bin/python -m markitdown deck.pptx` — slide text. Its `![](Graphic5.jpg)` lines are SHAPE names, not files: see below |
| images inside any of them | `unzip -o -q f.pptx 'ppt/media/*' -d ./out` — also `word/media/` in a `.docx`, `xl/media/` in an `.xlsx` |

Two traps in that table, both measured:

- **Do not predict what `pdftoppm` names its output.** The page number is padded
  to the width of the page COUNT, so a one-page scan — what an attachment
  usually is — gives `page-1.png` while a forty-page one gives `page-01.png`.
  List the directory. A guessed name that is not there reads as "the render
  failed" when it worked.
- **`--convert-to pdf` paginates a spreadsheet twice over, and only one of them
  is obvious.** Long splits by ROW, which is ordinary. **Wide splits by
  COLUMN** — a 40-column sheet became four pages, each carrying a different
  slice of the columns for the same rows. So a page count above one does not
  tell you which kind you have: read every page, and if a row looks like it is
  missing fields, look for them on the next one. For pure numbers `csv` is the
  better half of the pair.

**Count the parts before you trust a conversion.** Every one of these formats is
a ZIP, so the file itself will tell you what it holds — and each of these has
been the thing that was quietly missing:

```bash
unzip -p f.xlsx xl/workbook.xml | grep -o '<sheet [^>]*name="[^"]*"'   # sheets
unzip -l f.pptx | grep -c 'ppt/slides/slide[0-9]*\.xml'                # slides
unzip -l f.docx | grep 'word/media/'                                   # images
```

If the images list is empty, text extraction loses nothing and the cheap route
is safe. If it is not, that is your warning that the payload may not be text.

**`markitdown`'s image lines name SHAPES, not files.** A deck that emits
`![](Graphic5.jpg)`, `![](Graphic8.jpg)` and `![](Graphic9.jpg)` for one slide
turned out to contain exactly two media files in the whole archive — named
`image1.png` and `image2.svg`, matching none of them. Those are PowerPoint's
shape names. Do not go looking for a file by one, and do not read three of them
as three pictures. To map media to the slide that uses it, read the
relationships: `unzip -p f.pptx ppt/slides/_rels/slide6.xml.rels`.

**Text extraction tells you WHICH strings are on a slide and never WHERE.** That
is not a nuance — measured on a real deck, one slide carried both `IDENTITEIT`
and a leftover `Wat is ChatGPT?` from a different presentation, in the same
place, printing on top of each other. Extracted, they are two tidy lines and
read as a title with a subtitle. Rendered, the slide is visibly broken. So a
duplicated, stale or overlapping shape is invisible to every text route by
construction — if you are reviewing a deck rather than mining it for facts, look
at it.

`pandoc` is **not** installed here, whatever another skill's instructions say.
`markitdown` in that venv does `.pptx` and nothing else: it went in without the
`[docx]`, `[pdf]` and `[xlsx]` extras and raises `MissingDependencyException`
for all three. That is why LibreOffice, not markitdown, is the line above for
everything except a deck.

**Known-good on a Claude Code machine provisioned by us, measured 2026-08-08.**
Conditional on purpose: this skill also runs under other agents on machines
nobody here set up, so read a missing command as "find your own", not as a bug.

## Mentioning somebody

**A mention is `@<guid>` and nothing else notifies.** `@Ada Lovelace` written
into a comment is plain text: it reads like a mention to every human who sees
it, links to nobody, and sends no notification. Nothing errors, so this fails
silently and stays failed.

```bash
pharos people                     # everyone the board knows, with the form
pharos people ada                 # filter by name or email
pharos comment add 225 --text "Ready for review @<0f45a818-878d-6d7a-ba8c-1f5568a89ed4>"
```

**A mention only works in a COMMENT.** Measured live: the same `@<guid>` written
into `System.Description` is stored as literal text — no anchor, no mention
registered, nobody notified. Azure DevOps parses that shorthand on the comments
endpoint and nowhere else. So a mention put in a description or any other field
fails in precisely the silent way this section exists to prevent: it reads like
a mention to every human who sees it and reaches no one.

If you need somebody told, post a comment. Editing a field is not a substitute —
and note that **every work item write here suppresses notifications on purpose**
(`update`, `create`, `attach`, `detach`, `link`, `unlink`), so an agent doing
bookkeeping does not mail the assignee about each step. `comment` is the one
write that notifies.

The names come from the board's own work items — everyone assigned, creating or
changing anything — rather than from an identity endpoint, because those live on
another host and want scopes a work-scoped PAT does not have. So somebody who
has never touched an item here will not be listed; the guid out of any Azure
DevOps url works just as well.

## Turning documents into wiki pages

```bash
pharos wiki import ./notes.md ./spec.docx --under "/Guides"
pharos wiki import ./report.pdf --as "Q3 Report"
```

`.md` and `.txt` are copied **verbatim** — they are already the target format,
and anything done to them would be reformatting a document somebody wrote
deliberately. `.docx`, `.pdf`, `.rtf` and `.html` are converted by
`pharos-convert`, which is the **same converter the macOS app uses**, so both
produce the same page from the same file.

**It is a separate download, and not everybody has it.** Without it, markdown
and text still import and everything else is refused by name with the reason —
narrowed, not broken. `pharos doctor` says whether this machine has it;
`pharos setup --convert` fetches it (macOS only for now).

Three rules, because each of them is a way to lose work:

- **A derived name never collides — it COUNTS UP.** Importing `Notes.md` when
  `/Guides/Notes` already exists creates `/Guides/Notes 2`, reports
  `created: 1, skipped: 0`, and exits 0. Your page is never overwritten, which
  is the property that matters. But **a blind re-import does not fail, it
  quietly accumulates** `Notes`, `Notes 2`, `Notes 3` — and every run reports
  complete success. If you are re-running an import, check the wiki first.
- **`--as <name>` is the one that SKIPS.** A name you typed is an instruction,
  so it is never renamed: onto an existing page it skips, says so, and exits 3
  when nothing else landed. Use it when you want a collision to stop you.
- **Names are settled against the batch as well as the wiki**, so importing
  `Notes.docx` beside `Notes.pdf` gives two pages rather than one written twice.
- **An empty document is refused.** A scanned PDF carries no extractable text at
  all and PDFKit returns an empty string with no error; an empty page would look
  like a successful import until somebody opened it.
- **A `.pptx` is refused by name**, and that is the answer rather than a gap.
  `pharos-convert Skills.pptx` exits 2 with *"Skills.pptx is not a kind of file
  this can import."* **Do not route around it** by extracting the slide text
  yourself and importing that: a deck's payload is usually its images, so the
  text-only page looks like a successful import and has lost the content. The
  empty-document rule would not catch it either — the text is short, not empty.
  If the deck must become a page, read it (above) and write the page yourself.

Exit 3 when **nothing** landed. A partial batch exits 0 and names what skipped.
Do not retry a partial batch blindly: the files that succeeded will import a
second time under counted-up names, so you end with duplicates and an exit 0
saying it all worked. Re-run only the files that skipped.

## Do not guess a state name — ask

```bash
pharos types                 # every type, its states, and which mean "finished"
pharos types --type Task
```

**`update` now refuses a state the item's type does not have, before writing,
with the valid ones attached** — so you rarely need to run this first. Run it
when you want to see the shape, or when composing a `--wiql` filter.

**States belong to a TYPE, not to the project.** A state that exists elsewhere
is still not one this item can take: `In Progress` is real on a Test Suite and
invalid on a Task, and checking the project as a whole is the same guess one
layer down. The categories are shown as well as the names because "which
states exist" and "which mean finished" are different questions — `Inactive` is
finished on a Test Plan and appears in nobody's hard-coded Done/Closed/Removed
list.

`pharos whoami` is the other one worth reaching for early: it names the identity
behind `ADO_PAT`, which is who `@Me` resolves to and who every write is
attributed to. A shared or service token quietly makes "assigned to me" mean
somebody else. It is org-scoped, so it still answers when the project is
misconfigured — which is exactly when you need it.

## Ask, do not guess — the five discovery verbs

Every one of these replaced a guess, and a guess that silently succeeds against
the wrong value is worse than one that fails:

```bash
pharos history 39            # what changed on it, field by field, who and when
pharos iterations            # the sprints, with start/finish dates
pharos areas                 # the area tree
pharos links                 # every relation type, and which --flag reaches it
pharos fields --type Task --constrained   # what Priority and Activity accept
```

**Which sprint is current comes from the TEAM, not from the dates.**
`iterations` reports a top-level `current` (the field path of the team's current
iteration) and marks that node `current: true`. It asks team settings, because
an iteration is current because a team says so — `startDate`/`finishDate` are
routinely null and deriving it from them answers "no current sprint" on most
boards. `query --sprint current` resolves the same iteration.

**`iterations` prints TWO paths and only one of them works as a field value.**
`path` is the classification node — `\Tibata\Iteration\Sprint 1`. `fieldPath`
is what `System.IterationPath` and `--sprint` take — `Tibata\Sprint 1`, with no
`Iteration` segment. Handing the node path to the field is a 400 that reads as
though the sprint does not exist. A sprint with `startDate: null` is normal —
most orgs never set them.

**`history` returns raw field values.** The top-level `by` is a flattened
display-name string, but `changes[].from`/`to` are the field values themselves —
an identity field gives you the whole identity object, not a name. `--compact`
is a `task` flag and does not exist here, and `WEF_…` board keys are not
filtered, so expect them on the creation revision.

**`history` reads `/updates`, which is the diff.** `/revisions` is snapshots you
would have to diff yourself. Bookkeeping fields that change on every revision
(`System.Rev`, the dates, the watermark) are filtered out unless you pass
`--all`; a revision that changed only those is dropped entirely, because it is
not a change anybody made.

**`links` exists because `link` names six kinds and an org has about eighteen.**
`Affects`, `TestedBy`, the `Remote.*` family and `Duplicate-Reverse` have no
flag. The output marks which ones do, so "does this link type exist" and "can I
make it from here" are one answer.

There is **no `--rel <referenceName>` escape hatch** — the six flags are the
whole write surface. That has one consequence worth knowing before you promise
it: `--duplicate` reaches `Duplicate-Forward` only, so if the item you are
standing on shows the relation as **Duplicate Of** (`Duplicate-Reverse`), unlink
it from the *other* item instead.

**`--constrained` narrows `fields` to those with an allowed-values list** — the
ones you can get wrong. Without it you get every field on the type. Note that
Priority's `allowedValues` come back as STRINGS (`"1"`…`"4"`) while `--priority`
takes the number: do not quote it on the command line.

**`fields` needs `--type`.** Allowed values belong to the TYPE, not the project
— `Activity` is on `Task` and on neither `Epic` nor `Issue` in the Basic
process, so there is no project-wide answer to "which fields are there".

## Wiki pages and work items: one relation, two directions

**This is what makes a plan findable.** `pharos task` reads linked wiki pages and
their discussion — that is the whole point of it — and the link is what puts them
there.

```bash
# from the ITEM: one task, the documents it needs
pharos link 39 --wiki-page "/Plans/Sprint 3"
pharos unlink 39 --wiki-page "/Plans/Sprint 3"

# from the PAGE: one spec, the ten tasks that implement it
pharos wiki link   "/Plans/Sprint 3" --item 40 --item 41 --item 42
pharos wiki unlink "/Plans/Sprint 3" --item 40

# and the question Azure DevOps has no API for
pharos wiki links "/Plans/Sprint 3"
```

**A wiki page stores nothing about work items.** Measured: a page resource is
`path`, `order`, `gitItemPath`, `subPages`, `url`, `remoteUrl`, `id` — no link
field at all. The relation lives on the WORK ITEM, and Azure DevOps' own "Link
work items" panel on a page is a reverse lookup. That has two consequences worth
knowing before you plan a call:

- **item → its pages is FREE.** They are already in the item's own relations, so
  `pharos task <id>` returns them with no extra request. There is no such thing
  as a reverse lookup on a work item, and nothing scans the wiki.
- **page → its items costs one call.** `wiki links` is the only direction that
  has to ask.

Either way the other side sees it: link ten items from the page, and each of the
ten now returns the page from `task`.

`--wiki-page`, **not** `--wiki`: `--wiki <name>` is the global flag naming which
wiki to work in, and using it here means "the wiki called /Plans/Sprint 3".

`wiki link` writes one relation per item and reports one result per item — a
partial failure is a real outcome when ten items are named, and collapsing it
into one ok/failed would be a lie about the other nine.

### The URI is the identity, and it has a trap in its history

`vstfs:///Wiki/WikiPage/<projectId>%2F<wikiId>%2F<path>`, the path carrying **no
leading slash**. Two things follow:

- **Moving or renaming a page silently breaks every link to it**, because the
  path was the identity. That is why `wiki move` and `wiki rename` need `--yes`
  and `wiki write` does not.
- Before pharos-cli 0.16.0 this tool wrote `%2F%2Fpath` — one extra encoded
  slash. Those links are real, Azure DevOps stored them, and `task` reads them
  back fine, but the wiki's own panel could never find them because its reverse
  lookup keys on the canonical form. If a page shows a link here and not on the
  website, that is why. `wiki links` and `unlink` both ask about **both** shapes,
  so old links still resolve and can still be removed.

## GitHub issues: the join, and only the join

**These verbs are newer than the CLI on most machines. Check before you promise
one.** `pharos issue` shipped *after* **0.23.0**, so if `pharos --version` prints
0.23.0 or lower it is not there and every verb below is an unknown command —
`npm i -g @floh-solutions/pharos-cli@latest` is the fix. This skill and the CLI
update by different routes and drift apart in both directions; `pharos doctor`
prints both versions.

**This is not a GitHub CLI and must not become one.** Listing, viewing and
plainly commenting on an issue is `gh`'s job and `gh` is better at it; closing
one *end* is `gh issue close`. Pharos owns the one thing `gh` cannot see: which
work item tracks this issue, written so it survives in both databases.

The one place that line moved: **a comment that already exists** is reachable
through `pharos comment <verb> <owner/name#45>` — edit, delete, react, unreact,
reactors, hide, unhide, pin, unpin. Two reasons, and neither is symmetry for its
own sake. Editing or deleting one can destroy the link record, so it needs the
guard below rather than a bare `gh api`. And hiding or pinning has **no
first-class `gh` verb at all** — they are GraphQL mutations with no REST route,
which is the "nothing else can do this" test the rest of these verbs pass.
Posting a *new* comment is still not ours.

The second place it moved, and it is the only verb here that overlaps `gh` head
on: **`pharos issue edit` exists to REFUSE.** `gh issue edit` does the same
write and does it well — what it cannot do is notice that somebody changed the
thing you were overwriting. It reads nothing and compares nothing, so if a
colleague renamed the issue while you were composing, their rename is gone and
neither of you is told. That is fine for a human at a terminal and wrong for an
agent, which reads an issue, spends a minute thinking, and writes back into a
world that moved. **If you want an unguarded edit, use `gh issue edit` — it is
right there and it is better at it.**

Azure DevOps has its own GitHub integration and **the link it makes carries
nothing** — title, body, comments, labels and state stay on their own island,
and the transition only ever fires from a commit or a PR merge, never from
closing an issue. That gap is the whole reason these verbs exist.

```bash
pharos issue adopt contoso/widgets#45 --parent 39   # an issue → a work item, both ends
pharos issue link  contoso/widgets#45 4821          # join a pair that already exists
pharos issue trail 4821                             # …or trail contoso/widgets#45
pharos issue say   contoso/widgets#45 --file reply.md
pharos issue drift                                  # where the two disagree
pharos issue backfill contoso/widgets --limit 25 --yes
pharos issue close 4821 --text "Shipped in 1.4.0."
pharos issue edit  contoso/widgets#45 --title "Crash on resize" --yes
```

### Editing an issue, and the guard GitHub does not give us

**There is no conditional write.** `PATCH /repos/{o}/{r}/issues/{n}` answers
**400** to `If-Match` — measured, not assumed — so the `{"op":"test","path":
"/rev"}` guarantee behind every Azure DevOps patch has no GitHub equivalent.
Never send `If-Match` here yourself either: it is not inert, it fails the write,
and the 400 reads like a malformed body.

**And do not guard on `updated_at` or the ETag.** Both move when somebody merely
*comments* on the issue, so a guard keyed on either refuses a good edit for a
change that touched nothing — it fires on the case that is *not* a collision.

So the guard compares the **value of the field you are overwriting**: re-read
immediately before sending, and refuse only if that text moved. A comment cannot
cause it, which is what makes the refusal worth reading.

| you pass | the base is | what it protects |
|---|---|---|
| nothing | this command's own read | one round trip. Honest, and small |
| `--if-title` / `--if-body` / `--if-body-file` | what **you** saw | the whole gap between your read and your write |

Pass `--if-*` whenever you read the issue and then thought about it — that gap is
where a collision actually happens. The output says which window it guarded, as
`fields.guard.window`: `in-command` or `caller`.

A refusal is `kind: "conflict"`, exit **1**, and carries `conflicts` (base,
remote and proposed for each field) plus `attribution` naming who renamed it.
Re-read, fold their change into yours, edit again with `--if-title` set to what
you just read. **It is not atomic and nothing client-side can make it so** — it
narrows the race to one round trip rather than closing it.

Two things GitHub does *quietly*, which this verb reports and a bare `gh api`
would not:

| endpoint | the silence |
|---|---|
| `POST …/labels` | **creates** a repository label that does not exist — 200, grey, permanent, spelled exactly as you typed it. So an unknown label is REFUSED with the near misses named; `--create-label` is how you mean it |
| `POST …/assignees` | **ignores** a login it will not assign and still answers 201. Read `assignees.ignored` — a status code is not the answer here |

Labels and assignees go through those add/remove endpoints and never through the
whole-issue PATCH, which carries them as *whole arrays* — one label write would
otherwise blindly overwrite every label on the issue.

### Bind the repository first, or none of this runs

```bash
pharos setup --repo contoso/widgets --gh-account alisina-tibata
```

**Both flags or neither**, and there is deliberately **no fallback to whichever
account `gh` has active**: two accounts can each see a repository of the same
name, so the wrong one answers **200** for a different repository — a wrong
answer rather than an error.

An unbound repository is `"kind": "config"` on exit 2, naming
`~/.config/pharos/repos.json` — never a guess — **and it lists the repositories
that ARE bound**, so a typo is visible without reading the file. That check runs
before everything else here, so it is the first thing to fix. `gh` itself is
optional: without it every `issue` verb is refused by name with the reason and
the Azure DevOps verbs are untouched. `pharos doctor` reports both.

A failure that came from GitHub says **`"platform": "github"`**, because these
verbs touch two platforms in one call and which one refused is the first thing
to know. Its absence means Azure DevOps or this tool, as everywhere else.

### `adopt` is safe to re-run. `say` is NOT. Do not generalise from one.

**Adopting the same issue twice never creates a second work item.** What it
does instead depends on the state the pair is in, and the exit code tells you
which:

| exit **0**, `created: false` | the issue carries a marker. You get the work item it names and nothing is written — the state you asked for already holds |
| exit **3**, `halfLinked: true` | a work item already links this issue and the issue says nothing about it. Refused, carrying `recover` — the link wants **finishing**, not repeating |
| exit **3**, `workItemIds` with two entries | two work items claim one issue. Refused, both named, no `recover`: picking one would be inventing an answer |

Azure DevOps is written **first**, because the work item id does not exist until
the create lands, so the one failure `adopt` can leave is always the same shape:
the board end written, the GitHub end not.

```jsonc
{ "error": { "createdWorkItem": 4821, "halfLinked": true, "wrote": ["hyperlink"],
             "recover": "pharos issue link contoso/widgets#45 4821" } }
```

**Read more than `kind` on that error**: a work item now exists, and reading
only the kind loses its id. `recover` is the literal command that finishes the
job, and nothing needs undoing first.

**Re-running `adopt` there is safe but it is not the repair** — it refuses,
because the row above is exactly the state it detects, and the refusal hands
back the same `recover` string. Take it either from the failure or from the
refusal; they are the same command. `link` writes only the half that is missing,
which makes it both the fix here and the ordinary way to join a pair that
already exists. `pharos issue drift` finds this state later if nobody acted on
it at the time — it reports it as `one-sided`, carrying the same repair.

Every `adopt` reports `boardCheck`. `{"ran": true}` means the board was searched
for a work item that already tracks this issue; `{"ran": false}` carries the
reason it could not be, and then a half-link made on **another machine** would
not have been seen — `pharos issue drift --repo <owner/name>` asks the same
question deliberately.

`say` is the opposite, and that is the trap. **GitHub is written first there**,
because the board's comment carries the GitHub comment's URL and that does not
exist until the POST returns. So a failure on the board half leaves a **public
comment already posted**, and re-running posts a second one:

```jsonc
{ "error": { "halfSaid": true, "wrote": ["github-comment"],
             "github": { "commentUrl": "https://github.com/…#issuecomment-950" },
             "recover": "pharos comment add 4821 --stdin", "adoComment": "…" } }
```

Feed `adoComment` into `recover`. Do not re-run `say`.

### `say` — one message, two audiences

|  | GitHub | Azure DevOps |
|---|---|---|
| who reads it | the reporter, who has **no** Azure DevOps account and never will | the team |
| what they get | the full explanation | a summary, and the URL of the comment carrying the rest |

**The asymmetry is the verb.** The same words in both places is `gh issue
comment` followed by `pharos comment add`, and neither of those knows the other
happened. Without `--summary` the board gets the first paragraph cut to 200
characters — a guess, and allowed to be one *only* because the comment's URL
travels with it. GitHub is the record of what was said; the board never is.

**Never pass a message that already carries a `<!-- pharos:v1 … -->` trailer.**
It is refused (exit 3) before any call, on `say` and on `close`'s closing note
alike. That trailer means the text is Pharos's own output coming back round — a
comment you read and re-posted — and it is how a fan-out starts summarising its
own summaries. Every comment these verbs post carries one on the way out; you
never write one in.

`say` starts from the **issue** end only. A work item may hyperlink several
issues, so a bare id names no single reporter — `pharos issue trail <id>` is how
you find out which one you meant.

### `trail`, and the evidence worth reading

Read-only, and it answers from **either** end with the same output shape. The
field to read is `evidence`: `["hyperlink","marker"]` is a complete link, and
either one **alone** is a link that only half exists — a finding, not a detail.
The halves live in different places on purpose: a `Hyperlink` relation on the
work item, and one comment on the issue carrying `AB#4821` plus the
machine-readable trailer.

**The marker goes in a comment, never the issue body.** Editing a reporter's
body collides with them and needs write access nobody has on a community issue.

### `drift` — the report no other tool can produce

`gh` lists issues and Azure DevOps lists work items; **neither holds both
sides**, so neither can say *these two disagree*. Four kinds, because they want
four different actions:

| kind | what it means |
|---|---|
| `state` | both ends exist and disagree about whether the work is finished |
| `missing-issue` | the work item names an issue GitHub does not have |
| `one-sided` | one platform carries the link and the other does not — what a failed `adopt` leaves. Carries the `pharos issue link …` that repairs it |
| `unreadable` | the GitHub end could not be read, so nothing about this pair is known |

**It scans links, not issues.** An unadopted issue is not drift — that is
`backfill`'s question. On a repo with four hundred of them, counting "not
linked" as a problem buries three real findings under three hundred and
eighty-eight rows of noise.

**"Finished" is read from the project, never guessed**: each work item is judged
against its own type's categories and the report says which source it used —
`Resolved` is terminal on a Bug and open on a User Story. When the catalogue
cannot be read the stock names are used *and said out loud*, because a row is
uninterpretable without knowing what was counted as finished. An unreadable
repository is information rather than a fault and never fails the command.

### `backfill` — the adoption path for the repo that already has 400 issues

```bash
pharos issue backfill contoso/widgets            # previews, then REFUSES (exit 3)
pharos issue backfill contoso/widgets --dry-run  # the same preview, exit 0
pharos issue backfill contoso/widgets --label bug --parent 39 --limit 25 --max-writes 50 --yes
```

**Read the preview before adding `--yes`.** It names the repository, the `gh`
account it would be reached as, **and the Azure DevOps organisation and project
the work items would land on** — nothing in the design pairs a repo with a
board, and a mis-aimed `adopt` is one work item where a mis-aimed `backfill
--yes` is four hundred, each with a public comment naming a board its reporter
has nothing to do with.

**Each adoption is two writes**, so four hundred issues is eight hundred against
a default cap of 20. That cost is worked out *before* anything is written and a
run that cannot finish is refused, naming both ways forward — rather than
stopping at write nineteen, which is the outcome you can reason about least.

**It is resumable and needs no state file.** The link *is* the progress record:
a second run finds the ones the first adopted already linked and carries on, in
issue-number order. `--state` defaults to `open`, because adopting a closed
issue creates a work item that is finished before anybody looks at it.

### `close` — the ending of the trail

Closes **both** ends, comments on each pointing at the other, then **re-reads
both** and reports what actually moved. Two 200s are not proof: a workflow rule
can refuse a transition on a field the API happily accepted, so **`verified` is
what was there afterwards** rather than what was sent. Read it.

**There is no hardcodable `Closed`.** The state comes from the project's own
categories — exactly one terminal state for that type is used, and *several* is
a refusal naming them and `--to`, because `Done` and `Removed` are both finished
and mean opposite things. If the catalogue cannot be read at all it refuses
rather than guessing.

`--to`, **not** `--state`: `--state` already means `open|closed|all` on
`backfill`. Closing an already-closed pair writes nothing and exits 0. A work
item linking several issues is refused unless `--all` says so — "close 4821"
should not read as "close four strangers' issues".

**Pull requests are out of scope and are refused by name.** On GitHub's API
every PR is also an issue, so `adopt` on a PR number would otherwise mirror
something none of this models. `close` does not compose `Closes #45` /
`Fixes AB#123` into a PR body either: those fire on a PR *merge*, so there would
be nothing to compose into and nothing to verify.

### Editing a GitHub comment, and the trailer you must not break

A comment that already exists is `pharos comment`, with the issue as the target.
The verb set is the one you already know from work items and wiki pages:

```bash
pharos comment list   contoso/widgets#45              # ids, state, and what you MAY do
pharos comment edit   contoso/widgets#45 900 --file fixed.md
pharos comment delete contoso/widgets#45 900 --yes
pharos comment react  contoso/widgets#45 900 thumbs-up
pharos comment hide   contoso/widgets#45 900 off-topic
pharos comment pin    contoso/widgets#45 900
```

**Start with `list`.** It is the only way to learn a comment id, and it also
answers the question that saves a failed write: every row carries a `may` object
— `edit`, `delete`, `hide`, `pin`, `react` — read from GitHub's own view of what
this account may do. A comment you may not edit is `"edit": false` before you
try, not a 403 afterwards. Each row also carries `pharosAuthored` and
`workItemId`, so you can see at a glance which comment is the link.

Two ids come back per comment and **both are printed because neither can be
derived from the other**: `id` is the number that edit, delete and reactions
address, `nodeId` is what hide and pin take. Either is accepted anywhere a
comment is named; passing back the one the verb wants saves a request.

**An edit cannot double or strip the `pharos:v1` trailer, and this is enforced
rather than requested.** That trailer is the durable record of which work item
tracks this issue *and* the guard that stops the two platforms summarising each
other's summaries. So:

| what you send | what happens |
|---|---|
| new prose, no trailer | the existing trailer is **restored**, and `markerPreserved: true` says so |
| the body you read back, trailer intact | sent unchanged |
| two trailers | refused — `doubled` |
| a trailer naming a different work item | refused — `repointed`; `pharos issue link` is the verb for that |
| a trailer on a comment that had none | refused — `forged` |

You do not have to think about any of this: hand over the words you want and the
record survives. It is written down because the refusals name a reason, and the
reason is actionable.

**Deleting the comment that carries the trailer destroys the GitHub half of the
link.** It is allowed — a mis-adoption is a real thing — but the `--yes` refusal
says so first, names the work item, and gives you the `pharos issue link` command
that puts it back. Under `--dry-run` you get the same preview and exit 0. A
delete that finds the comment already gone reports `alreadyGone: true` and
succeeds, so a retry after a lost reply is safe.

**`hide` and `pin` exist on GitHub and nowhere else** — they are GraphQL
mutations with no REST route, which is why `gh` has no verb for them. Hiding
needs a classifier and there is no neutral default, because GitHub shows it
beside the hidden comment: `spam`, `abuse`, `off-topic`, `outdated`,
`duplicate`, `resolved`, `low-quality`. Ask for `off-topic` and `off-topic` is
what reads back. On a work item or a wiki page these four verbs are refused with
"Azure DevOps has neither" rather than as an unknown verb — there is no endpoint
to go looking for.

**`pharos comment add` is refused on a GitHub issue.** Posting is already
covered twice and which one you want depends on whether the board should hear:
`pharos issue say` writes to the reporter *and* the work item, `gh issue comment`
writes to GitHub only. A third door here would post on an adopted issue that the
work item never hears about — the exact asymmetry `say` exists to prevent.

## What `pharos` does NOT do — read this before you go looking

- **Free-text and code search.** Nothing here covers it. For work items,
  `pharos query --wiql "… WHERE [System.Title] CONTAINS 'thing'"` gets close;
  for code there is no substitute short of the REST API.
- **Capacity, backlogs, teams.** Iterations and areas ARE covered — see
  `iterations` / `areas` above — but team capacity and backlog ordering are not.
- **Wiki content search.** `wiki tree` then `wiki read` is the only way through;
  there is no grep across pages.
- Pull requests, builds, pipelines.
- **Almost anything on GitHub that is not the join.** No issue list, no issue
  view, no *posting* a comment, no labels or milestones, no pull requests — `gh`
  does all of it better and a second GitHub CLI would only drift from it. The
  seven `issue` verbs are the edge. The one addition is a comment that already
  exists (`pharos comment <verb> <owner/name#45>`): editing or deleting one can
  break the link record, and hiding or pinning has no `gh` verb at all.
- **Jira, Linear, and the Argus board.** Not covered, not planned. "Task",
  "todo" and "board" mean something else there.

**There is no Azure DevOps MCP server here any more, and that is deliberate.**
It authenticated through the Azure CLI, so it opened a browser mid-task — which
makes a headless session stop and wait for a human who is not watching.

For a **read** this tool does not offer, the REST API is fine and costs nothing
to get wrong. For a **write** it does not offer, say the gap out loud rather than
routing around it: several things here exist in no other Azure DevOps tool at
all — wiki page comments and reactions, attachment upload AND removal, inline
images for a work item field or a wiki page, mentioning somebody in a form that
actually notifies, importing a Word document or a PDF as a page, editing or
deleting a work item comment, service hooks, the GitHub-issue join and the
drift report over it, and applying a change under a `test` op on `/rev` so a
teammate who wrote first cannot be silently overwritten. Those are what the
guards are, and they are the reason to come back here rather than hand-roll.

## Start every task with one command

```bash
pharos task <id>                       # a leaf
pharos task <id> --children --compact  # an EPIC and everything under it
```

One call: the item, its comments, its attachments, its relations **with their
titles**, and the full content of every linked wiki page **plus the discussion
on those pages**.

**Do not assemble this yourself.** By hand it is five or six lookups, and the
plan a colleague wrote is usually on a linked wiki page rather than in the
description. A task worked without it is a task worked without the plan.

Anything that could not be fetched appears in `problems[]`. **If that array is
not empty, say so before acting** — a context with an invisible hole in it gets
reasoned from confidently.

### What it actually returns

**Read this before writing a parser.** The shapes below are the CLI's, not the
Azure DevOps API's, and they differ in exactly the places you would guess wrong:

```jsonc
{
  "id": 40,
  "fields": {                    // the raw ADO field bag
    "System.Title": "…",
    "System.State": "To Do",
    "System.Description": "plain text, real newlines — NOT html",
    "System.AssignedTo": { "displayName": "…", "uniqueName": "…" }
  },
  "comments": [
    { "id": 1741895,
      "text": "I have updated the description",
      "createdBy": "André Kwakernaat",          // a STRING, already flattened
      "createdDate": "2026-08-05T10:15:43.167Z" }
  ],
  "attachments": [],
  "related": [                                   // titles and states ALREADY resolved
    { "id": 46, "rel": "System.LinkTypes.Hierarchy-Forward",
      "title": "Skill: …", "state": "To Do" }
  ],
  "wikiPages": [],
  "problems": [],
  "children": []                                 // only with --children/--depth
}
```

Three things that trip up a parser written against the REST API:

- **`comments[].createdBy` is a string**, not an identity object. There is no
  `.displayName` on it.
- **Description and comment text are plain text**, already converted. Do not
  strip tags; there are none.
- **A field is ABSENT when unset, not empty.** `fields["System.Description"]` is
  simply missing on an item nobody has written one for — which is a *finding*
  worth reporting, not a crash. Measured: seven of eight children of one epic.
- **A child is a placeholder when the description is absent AND `comments`,
  `attachments` and `wikiPages` are all empty.** Check all four: a spec is as
  often a comment or a linked page as a description.
- **`--pretty` always prints a Problems section**, saying `none` when there is
  nothing wrong — so the check above can be made from either format.

`--pretty` renders all of the above as readable markdown and drops the identity
noise. It is not only "for a human" — for reading a single item it is usually
the better format for you too.

### Starting from an EPIC

An epic is not a big task, and the loop below is written for a leaf. Handed a
parent, the first question is **which children are actually specified**:

```bash
pharos task 39 --children --compact
```

One call instead of one per child — measured on a real epic, nine calls and
~42 KB became one call and ~22 KB. Then, **before proposing any work**, report
the split:

> #40 has a complete 5,694-character spec. #41–#47 have no description at all.
> Seven of eight are placeholders.

That is the single most useful thing to say about a parent item, and it is the
thing an agent is most likely to skip — the titles read like a plan, so an
implementation gets inferred from them and nobody notices it was invented.

`--depth <n>` walks further (max 5). A child that cannot be read becomes a
`problems[]` entry rather than failing the whole call, so a partial tree still
tells you what is missing.

`--compact` flattens identities to display names and drops the `WEF_…` board
extension keys. Measured at ~24% of an item's bytes and nothing reads them.

## Reading the outcome

Success is JSON on stdout; failure is JSON on stderr with a non-zero exit. An
empty array with exit 0 is a query that matched nothing — a different fact from
a failure.

**Read `advice` when it is there.** Azure DevOps answers a licence problem with
`TF401289: The current user does not have permission to create tag definitions`,
which is accurate and tells you nothing to do. Where the code is recognised the
error carries an `advice` field saying what it actually means here — including
the cases that read as one thing and are another: a failed tag on a create means
**the work item exists and only the tag is missing**, and a refused delete is
usually the account's ACCESS LEVEL rather than any permission, because a
Stakeholder cannot delete however the permissions are set. `credentialIsFine:
true` means stop re-checking the token.

| exit | meaning | what to do |
|---|---|---|
| `0` | it worked | carry on |
| `1` | the call failed | check `kind`; retry only if it is `rateLimit` (wait `retryAfterMs`) or transient |
| `2` | called wrong, or not configured | **never retry unchanged.** Fix the call, or the setup |
| `3` | a guard here refused | re-run with `--yes`, or raise `--max-writes` — after deciding it is right |

**A failure carrying `"platform": "github"` came from GitHub**, not from Azure
DevOps and not from here — `pharos issue` touches two platforms in one call, and
which one refused decides whether the fix is a token, a repo binding or a field.
Its absence means the other side, as it always did.

`"kind": "conflict"` means somebody wrote first. Your work is still valid:
re-read, re-apply. It carries both revisions — and note that **posting a comment
bumps `System.Rev`**, so a revision mismatch is not proof anybody edited the
same field.

## Destructive verbs refuse by default. Read the refusal.

```bash
pharos wiki delete /Plans/Old              # exit 3, nothing changed
pharos wiki delete /Plans/Old --yes        # done
```

**Exit 3 with `"kind": "refused"` means nothing happened.** Do not report the
work as done. The refusal carries a preview — check it is what you intended
before adding `--yes`, rather than reflexively re-running with the flag.

Replacing a wiki page needs `--yes`; creating one does not. The refusal says how
many bytes are at stake, which is how you notice you are about to overwrite
somebody's page instead of writing a new one.

## Never hand-roll a WRITE

Every known Azure DevOps trap on the write path is handled inside the tool: the
lost-update on wiki writes, the deleted-comment field that lies, the reaction
call that needs an empty body, artifact links that must carry a project GUID,
relation removal that would otherwise take the wrong link.

So a **failing** `pharos` command means the request was genuinely wrong or the
API genuinely refused. Read the error; do not reach for `curl`.

This is a rule about writes, not about reads. A read `pharos` does not offer —
reach for `query --wiql`, or the REST API — is fine, costs nothing to get wrong,
and is better than refusing to answer. A write it does not offer is a gap worth
reporting, not routing around: the guards are the reason the tool exists.

**Moving or renaming a page changes what it IS.** A wiki page has no id — the
path is its identity — so anything pointing at the old path stops resolving,
including artifact links from work items, and nothing reports it. That is why
both verbs need `--yes` while `write` does not, and why the refusal names what
it is about to break. Sub-pages move with their parent.

## Three things no tool can fix

1. **A wiki is a git repository.** Two writes to the same wiki at the same
   moment are two pushes racing for one HEAD. Write pages one at a time.
2. **There is no wiki event in service hooks.** You cannot subscribe to "a wiki
   page changed" — only to `git.push` on the wiki's repository.
3. **Wiki ancestors are not created for you.** Writing `/A/B` when `/A` does not
   exist is refused. Build a page tree top-down, one write per level.

## The loop

1. `pharos task <id>` — read everything, including the linked plan.
2. If a plan is needed, write it: `pharos wiki write /Plans/<name> --stdin`,
   then link it to the epic so the next person finds it the same way you did.
3. Break it down — create the child items.
4. `pharos comment add <id> --file notes.md` — decisions belong on the item,
   not only in a chat log nobody else can read.
5. Move the state when the work moves, not at the end.

**When the work started as a GitHub issue the loop gains two ends and changes
one step**: `pharos issue adopt` before step 1, `pharos issue close` after step
5, and at step 4 the reply to the *reporter* is `pharos issue say` rather than a
comment on the work item — a comment on the item is invisible to somebody with
no Azure DevOps account, which is every reporter.

**Every person uses their own token.** Board attribution is per-person, so
anything you do is recorded against whoever owns `ADO_PAT`. Never suggest
sharing one.

## When it is not set up

`"kind": "config"` on exit 2 means the environment is missing. Run `pharos
setup`: it stores the token in the OS keychain rather than a file, writes the
profile that **scripted** shells read, and verifies both permission scopes —
Work Items and Wiki are separate in Azure DevOps, and a token missing the second
works fine until the first wiki write days later. A **new** shell is needed
afterwards.

**The GitHub half is configured separately and follows a different rule.** The
environment carries no fourth secret: the credential comes from `gh`, and which
account reaches which repository is a binding on disk, so a `config` error from
an `issue` verb names `repos.json` rather than an environment variable.

```bash
pharos setup --repo contoso/widgets --gh-account alisina-tibata
```

**A verb whose target is a GitHub issue does not need `ADO_PAT` at all.**
`pharos comment list|edit|delete|react|unreact|reactors|hide|unhide|pin|unpin
<owner/name#n>` runs on `gh`'s credential alone, on a machine that has never had
an Azure DevOps token. So a `config` error naming `ADO_PAT` from one of those is
a defect worth reporting, not something to go and provision a token over. The
two credentials are independent — separate keychain entries, and `pharos doctor`
reports them separately — and `pharos issue` is the one family that genuinely
needs both, because it writes to both platforms in one invocation.
