---
name: pharos
description: "Use for AZURE DEVOPS work specifically — when the user says Azure DevOps, ADO or dev.azure.com, or names an ADO work item by number (\"pick up 4821\", \"what's on 210\"). Covers reading or updating an ADO work item, ticket, bug, story or epic; the ADO board, backlog, sprint or iteration; what is assigned to you in Azure DevOps; reading or writing an ADO project wiki page and its comments; linking a plan to an epic; attaching a file to a work item; and whether a failed Azure DevOps call is worth retrying. NOT for other trackers — the Argus board, GitHub issues, Jira, Linear — where \"task\", \"todo\" and \"board\" mean something else entirely."
license: MIT
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
update <id>                    change a field: --state --priority --assignee
                               --title, or --field Name=value for anything else
attach <id> <file>             put a file on a work item
download <id-or-url>           read one back. --out <path> or it writes nothing
wiki list | tree | read <path> | write <path> | delete <path>
comment list | add | edit | delete   <target> is a work item id OR a wiki path
comment react | unreact | reactors   like dislike heart hooray smile confused
hooks list | check | create | repoint | delete    service hooks for realtime
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

Do NOT write `[System.State] NOT IN GROUP 'Completed'` if you reach for `--wiql`.
It parses, returns 200, and matches **everything** — `IN GROUP` covers work item
TYPE categories only, and an unknown group resolves to the empty set with no
error. Measured, 2026-08-05.

## Changing a work item: `update` and `attach`

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
twice makes two of them, and there is no replace and no versioning.

## Do not guess a state name — ask

```bash
pharos types                 # every type, its states, and which mean "finished"
pharos types --type Task
```

`pharos update 225 --state Doing` fails if that work item type has no `Doing`,
and Azure DevOps lets a process template rename every state. **One read beats a
guess and a 400.** The categories are shown as well as the names because "which
states exist" and "which mean finished" are different questions — `Inactive` is
finished on a Test Plan and appears in nobody's hard-coded Done/Closed/Removed
list.

`pharos whoami` is the other one worth reaching for early: it names the identity
behind `ADO_PAT`, which is who `@Me` resolves to and who every write is
attributed to. A shared or service token quietly makes "assigned to me" mean
somebody else. It is org-scoped, so it still answers when the project is
misconfigured — which is exactly when you need it.

## What `pharos` does NOT do — read this before you go looking

- **Free-text and code search.** Nothing here covers it. For work items,
  `pharos query --wiql "… WHERE [System.Title] CONTAINS 'thing'"` gets close;
  for code there is no substitute short of the REST API.
- **Creating a work item** (`plan` builds a tree from a file), **linking or
  unlinking** two of them, **deleting** one or reaching the recycle bin.
- **Iterations, areas, capacity, backlogs, teams.**
- Pull requests, builds, pipelines.

**There is no Azure DevOps MCP server here any more, and that is deliberate.**
It authenticated through the Azure CLI, so it opened a browser mid-task — which
makes a headless session stop and wait for a human who is not watching.

For a **read** this tool does not offer, the REST API is fine and costs nothing
to get wrong. For a **write** it does not offer, say the gap out loud rather than
routing around it: five things here exist in no other Azure DevOps tool at all —
wiki page comments and reactions, attachment upload, editing or deleting a work
item comment, service hooks, and applying a change under a `test` op on `/rev`
so a teammate who wrote first cannot be silently overwritten. Those are what the
guards are, and they are the reason to come back here rather than hand-roll.

## Start every task with one command

```bash
pharos task <id>
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

## Reading the outcome

Success is JSON on stdout; failure is JSON on stderr with a non-zero exit. An
empty array with exit 0 is a query that matched nothing — a different fact from
a failure.

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
