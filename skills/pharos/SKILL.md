---
name: pharos
description: "Use for AZURE DEVOPS work specifically — when the user says Azure DevOps, ADO or dev.azure.com, or names an ADO work item by number (\"pick up 4821\", \"what's on 210\"). Covers reading or updating an ADO work item, ticket, bug, story or epic; the ADO board, backlog, sprint or iteration; what is assigned to you in Azure DevOps; reading or writing an ADO project wiki page and its comments; linking a plan to an epic; attaching a file to a work item or taking one off; putting an inline image into a description, a comment, a wiki page or a wiki comment; @mentioning somebody so they are actually notified; importing Markdown, Word or PDF files as wiki pages; and whether a failed Azure DevOps call is worth retrying. NOT for other trackers — the Argus board, GitHub issues, Jira, Linear — where \"task\", \"todo\" and \"board\" mean something else entirely."
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
detach <id> <url-or-guid>      take one off. --yes
download <id-or-url>           read one back. --out <path> or it writes nothing
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
wiki import <file...>          .md .txt .docx .pdf .rtf .html -> pages
                               --under <path> --as <name>
comment list | add | edit | delete   <target> is a work item id OR a wiki path
comment react | unreact | reactors   like dislike heart hooray smile confused
hooks list | check | create | repoint | delete    service hooks for realtime.
                               `check` needs --hub <url>; `list` shows the URL
                               already in use
plan <file>                    an implementation plan → a work item tree
setup                          org, project, token → keychain + shell profile
```

Text input: `--text` / `--file` / `--stdin`. Global: `--pretty` for a human,
`--yes` for destructive verbs, `--dry-run` to preview.

**`ADO_ORG`, `ADO_PROJECT` and `ADO_PAT` are already in the environment** after
setup. Do not check them before working; a missing one announces itself as
`"kind": "config"` on exit 2, which is the only time it matters.

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
rather than losing their edit. Setting a value it already has writes nothing and
says so — a pointless PATCH still bumps `System.Rev` and invalidates every other
cached revision on the item. `--dry-run` shows the before → after and writes
nothing. There is no `--yes`: a field edit is an ordinary edit and Azure DevOps
keeps every revision.

`attach` uploads the bytes and then links them as an `AttachedFile` relation —
two calls, one command. Attachments are **immutable**: attaching the same file
twice makes two of them, and there is no replace and no versioning. `detach`
takes one off; it needs `--yes`, finds the attachment by identity rather than by
position, and leaves the bytes in Azure DevOps so re-attaching the url puts it
back.

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
produce the same page from the same file. If it is not on PATH, markdown and
text still import and everything else is refused by name with the reason.

Three rules, because each of them is a way to lose work:

- **A name collision SKIPS and says so.** A page write with an empty version is
  a *create*, so writing over an existing page is silent data loss.
- **Names are settled against the batch as well as the wiki**, so importing
  `Notes.docx` beside `Notes.pdf` gives two pages rather than one written twice.
  A name you give with `--as` is never renamed — it is an instruction, so it is
  allowed to collide and skip.
- **An empty document is refused.** A scanned PDF carries no extractable text at
  all and PDFKit returns an empty string with no error; an empty page would look
  like a successful import until somebody opened it.

Exit 3 when **nothing** landed. A partial batch exits 0 and names what skipped —
retrying it blindly would collide with the pages it just made.

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

## What `pharos` does NOT do — read this before you go looking

- **Free-text and code search.** Nothing here covers it. For work items,
  `pharos query --wiql "… WHERE [System.Title] CONTAINS 'thing'"` gets close;
  for code there is no substitute short of the REST API.
- **Capacity, backlogs, teams.** Iterations and areas ARE covered — see
  `iterations` / `areas` above — but team capacity and backlog ordering are not.
- **Wiki content search.** `wiki tree` then `wiki read` is the only way through;
  there is no grep across pages.
- Pull requests, builds, pipelines.

**There is no Azure DevOps MCP server here any more, and that is deliberate.**
It authenticated through the Azure CLI, so it opened a browser mid-task — which
makes a headless session stop and wait for a human who is not watching.

For a **read** this tool does not offer, the REST API is fine and costs nothing
to get wrong. For a **write** it does not offer, say the gap out loud rather than
routing around it: several things here exist in no other Azure DevOps tool at
all — wiki page comments and reactions, attachment upload AND removal, inline
images for a work item field or a wiki page, mentioning somebody in a form that
actually notifies, importing a Word document or a PDF as a page, editing or
deleting a work item comment, service hooks, and applying a change under a
`test` op on `/rev` so a teammate who wrote first cannot be silently
overwritten. Those are what the
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
| `3` | a guard here refused | re-run with `--yes` — after deciding it is right |

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
