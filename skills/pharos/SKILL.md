---
name: pharos
description: "Use whenever Azure DevOps work is involved — reading or updating a work item, task, bug, story or epic; anything with a board, backlog, sprint or iteration; reading or writing a project wiki page; commenting on a task or a wiki page; linking a plan to an epic; or when the user names a work item by number (\"pick up 4821\", \"what's on 210\"). Also use when deciding between the Azure DevOps MCP server and the `pharos` CLI, or when an Azure DevOps call fails and you need to know whether to retry it."
license: MIT
---

# Working Azure DevOps with `pharos`

`pharos` is a CLI that gives you the full Azure DevOps surface from a shell,
authenticated by an environment variable rather than a browser login. Run
`pharos --help` for the complete verb list; this skill is the part that is not
in the help text.

## Start every task with one command

```bash
pharos task <id>
```

That returns the work item, its comments, its attachments, its relations **with
their titles**, and the full content of every linked wiki page **plus the
discussion on those pages** — in one call.

**Do this before anything else, and do not assemble it yourself.** By hand it is
five or six lookups across two tools, and the plan a colleague wrote is usually
on a linked wiki page rather than in the description. A task worked without it
is a task worked without the plan.

Add `--pretty` when a person will read the output.

Anything that could not be fetched appears in `problems[]`. **If that array is
not empty, say so before acting** — a context with an invisible hole in it gets
reasoned from confidently.

## Which tool: `pharos` or the Azure DevOps MCP server

If both are available, they overlap. The dividing line:

| | |
|---|---|
| **Use `pharos`** | anything touching a **wiki page's comments** (the MCP has no tool for these at all), deleting a comment, reactions, deleting a wiki page, and `pharos task <id>` for gathering context |
| **Either works** | reading and querying work items, creating them, updating fields and state, adding a comment, reading a wiki page |
| **The MCP may be better** | code search, repository and pull request work, anything outside work items and wikis |

When in doubt use `pharos`: its failure modes are structured and its guards are
explicit.

## Reading the outcome

Output is a contract. **Success is JSON on stdout; failure is JSON on stderr
with a non-zero exit.** An empty array with exit 0 is a query that matched
nothing — a different fact from a failure.

| exit | meaning | what to do |
|---|---|---|
| `0` | it worked | carry on |
| `1` | the call failed | check `kind`; retry only if it is `rateLimit` (wait `retryAfterMs`) or transient |
| `2` | called wrong, or not configured | **never retry unchanged.** Fix the call, or the setup |
| `3` | a guard here refused | re-run with `--yes`, or raise `--max-writes` — after deciding it is right |

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
work as done. The refusal carries a preview of what it would have done — check
that preview is what you intended before adding `--yes`, rather than reflexively
re-running with the flag.

Replacing a wiki page needs `--yes`; creating one does not. The refusal tells
you how many bytes are at stake, which is how you notice you are about to
overwrite somebody's page instead of writing a new one.

`--dry-run` gives the preview with exit 0 when you want to look without being
refused.

## The traps are handled. Do not work around them.

Every known Azure DevOps failure of this kind is handled inside the tool: the
lost-update on wiki writes, the deleted-comment field that lies, the reaction
call that needs an empty body, artifact links that must carry a project GUID,
relation removal that would otherwise take the wrong link.

**So if something looks like it needs a workaround, it does not.** A `pharos`
command failing means the request was genuinely wrong or the API genuinely
refused — read the error rather than reaching for `curl`. If you find a real gap,
say so plainly; do not paper over it with raw REST calls that skip the guards.

## Three things no tool can fix

1. **A wiki is a git repository.** Two writes to the same wiki at the same
   moment are two pushes racing for one HEAD. Write pages one at a time.
2. **There is no wiki event in service hooks.** You cannot subscribe to "a wiki
   page changed" — only to `git.push` on the wiki's repository. If you need to
   react to wiki edits, that is the only route.
3. **Wiki ancestors are not created for you.** Writing `/A/B` when `/A` does not
   exist is refused. Build a page tree top-down, one write per level.

## The loop

Working a task end to end, in the order that keeps the board honest:

1. `pharos task <id>` — read everything, including the linked plan.
2. If a plan is needed, write it: `pharos wiki write /Plans/<name> --stdin`,
   then link it to the epic so the next person finds it the same way you did.
3. Break it down — create the child items.
4. `pharos comment add <id> --file notes.md` — decisions belong on the item,
   not only in a chat log that nobody else can read.
5. Move the state when the work moves, not at the end.

**Every person uses their own token.** Board attribution is per-person, so
anything you do is recorded against whoever owns `ADO_PAT`. Never suggest
sharing one.

## When it is not set up

`"kind": "config"` on exit 2 means the environment is missing. Run:

```bash
pharos setup
```

It asks for the organisation, project and token, stores the token in the OS
keychain rather than a file, writes the right shell profile, and verifies both
permission scopes — Work Items and Wiki are separate in Azure DevOps, and a
token missing the second one works until the first wiki write.

Variables live in the environment (`ADO_ORG`, `ADO_PROJECT`, `ADO_PAT`) and
**never in the tool's own config**, which is what lets the same command run in
CI and unattended. After setup, a **new** shell is needed.
