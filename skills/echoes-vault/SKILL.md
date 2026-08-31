---
name: echoes-vault
description: Maintain agent-neutral, repository-local project memory through the portable EchoesVault runtime. Use when the user asks Codex to remember, record, log, search, recall, document, or update project knowledge; when work depends on earlier architectural decisions; or after a meaningful sub-task should survive across agents and sessions. Do not use it for final distillation unless the user explicitly requests echoes-end.
---

# EchoesVault memory operations

Keep durable project knowledge in `<workspace>/EchoesVault/`. Resolve `<workspace>` as the Git root
when one exists, otherwise the current working directory. Resolve `<plugin-root>` as the parent of
the `skills/` directory that contains this `SKILL.md`. Use
`<workspace>/.echoes-vault/echoes_vault.py` as `<runtime>` when it is a regular file; otherwise use
`<plugin-root>/scripts/echoes_vault.py`.

Run the deterministic storage CLI with:

```text
python3 <runtime> --workspace <workspace> <command>
```

Pass write payloads as JSON through stdin (`--payload -`) or a temporary JSON file. Do not interpolate untrusted Markdown into a shell command.

## Core rules

1. Read before writing. Search the vault and read an existing page before updating it.
2. Store dry technical facts, decisions, contracts, configurations, verified fixes, blockers, and next steps—not chat transcripts.
3. Start every page with YAML frontmatter containing `type`, `stack`, and `status`.
4. Include `summary`: a non-empty single line of at most 160 characters describing the page.
5. Never edit `index.md`; the CLI generates it deterministically from page filenames, `summary`,
   and `status` without loading page bodies into model context.
6. Use `[[wikilinks]]` for page references and `![[asset.png]]` for files in `EchoesVault/assets/`.
7. Deprecate instead of deleting. Set `status: deprecated`, prepend `> [!warning] DEPRECATED`,
   and link to the replacement.
8. Never report final memory as saved after normal task completion. Only `$echoes-end` may finalize a session.

## Choose an operation

### Recall before work

Use targeted search when an existing component, decision, API, schema, or configuration might already be documented:

```text
python3 <runtime> --workspace <workspace> search "specific keyword"
```

Read the returned page around each relevant line. Follow replacement links from deprecated pages.

### Append an intermediate note

After a verified logical unit, an architectural agreement, a context switch, or an explicit “remember/log this” request, submit:

```json
{
  "entry": "- Implemented X.\n- Verified with Y.\n- Remaining blocker: Z.",
  "agent": "codex"
}
```

to `append --payload -`. Keep the entry concise. This is a scratchpad write and does not end the session.

If no vault exists and the user has asked to remember something, run `init` first. Otherwise, do not initialize a vault implicitly.

### Create or update a knowledge page

Use a page for a durable global concept such as an architecture, API contract, schema, library integration, hardware mapping, or ADR.

For a new page, submit to `upsert --payload -`:

```json
{
  "filename": "auth-architecture.md",
  "content": "---\ntype: architecture\nstack: [python]\nstatus: active\nsummary: Authentication boundaries and token flow.\n---\n\n# Authentication architecture\n"
}
```

For an existing page:

1. Read the full page.
2. Run `hash <filename>` and copy its `sha256`.
3. Submit the full replacement content plus `expectedSha256` to `upsert`.

Retain or deliberately update the page's `summary` when replacing its full content. The optimistic
hash prevents overwriting a concurrent edit in the current checkout. If it fails, reread the page
and reconcile changes. A project-level runtime lock serializes simultaneous EchoesVault writers.

## Successful completion

Confirm the exact session-entry or page path written. Mention whether the generated index changed.
Keep working unless the user requested a final save.
