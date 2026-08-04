---
name: pharos
description: "Use for AZURE DEVOPS work specifically — when the user says Azure DevOps, ADO or dev.azure.com, or names an ADO work item by number (\"pick up 4821\", \"what's on 210\"). Covers reading or updating an ADO work item, ticket, bug, story or epic; the ADO board, backlog, sprint or iteration; what is assigned to you in Azure DevOps; reading or writing an ADO project wiki page and its comments; linking a plan to an epic; choosing between the Azure DevOps MCP server and the `pharos` CLI; and whether a failed Azure DevOps call is worth retrying. NOT for other trackers — the Argus board, GitHub issues, Jira, Linear — where \"task\", \"todo\" and \"board\" mean something else entirely."
license: MIT
---

# Working Azure DevOps with `pharos`

`pharos` is a CLI that gives you Azure DevOps from a shell, authenticated by an
environment variable rather than a browser login.

**Everything it can do is listed below. Do not run `pharos --help` to find
out** — that costs several calls and this section is the same information.

```
task <id>                      one work item, whole: fields, comments,
                               attachments, relations WITH titles, and the
                               content + discussion of every linked wiki page
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

## What `pharos` does NOT do — read this before you go looking

**There is no query, list or search verb.** `task` takes one id. Nothing here
answers "what is assigned to me", "what is in this sprint" or "what is open" —
and the CLI will not grow the verb by being asked twice.

That is the single most common opening question, so here is the answer rather
than a prohibition. **WIQL, read-only, with the token already in your
environment:**

```bash
curl -sS -u ":$ADO_PAT" -H 'Content-Type: application/json' \
  "https://dev.azure.com/$ADO_ORG/$ADO_PROJECT/_apis/wit/wiql?api-version=7.1" \
  -d '{"query":"SELECT [System.Id] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.State] NOT IN (\"Done\",\"Closed\",\"Removed\") ORDER BY [System.ChangedDate] DESC"}'
```

It returns **ids only**. Then `pharos task <id>` for the few you actually need —
not for all of them, which is a call per item for context nobody asked for.

Two things to say out loud when you use it, because both change how the answer
should be read: **which states you treated as terminal** (projects rename them),
and that `@Me` resolves to whoever owns `ADO_PAT`.

Also absent, so you can stop looking: creating or updating a work item's fields
(`plan` creates trees; the MCP server updates fields), pull requests, code
search, builds, pipelines.

## Which tool: `pharos` or the Azure DevOps MCP server

They overlap only where both exist. **Check once** whether the MCP is connected
— if no `mcp__ado__*` tools are available in the session, it is not, and the
rest of this table collapses to "use `pharos` or use WIQL above".

| | |
|---|---|
| **Only `pharos`** | wiki page comments (the MCP has no tool for these at all), deleting a comment, reactions, deleting a wiki page, service hooks, and `pharos task <id>` for gathering context |
| **Only the MCP** | querying and searching work items, updating fields and state, code, pull requests, builds |
| **Either** | reading a work item, creating one, adding a comment, reading a wiki page |

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
WIQL above — is fine, costs nothing to get wrong, and is better than refusing to
answer. A write it does not offer is a gap worth reporting, not routing around:
the guards are the reason the tool exists.

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
