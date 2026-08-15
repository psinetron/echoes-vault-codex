---
name: echoes-vault
description: Maintain persistent, repository-local project memory in EchoesVault Markdown files. Use when the user asks Codex to remember, record, log, search, recall, document, or update project knowledge; when work depends on earlier architectural decisions; or after completing a meaningful sub-task whose outcome should survive into later sessions. Do not use it for final session distillation unless the user explicitly invokes or requests echoes-end.
---

# EchoesVault memory operations

Keep durable project knowledge in `<workspace>/EchoesVault/`. Resolve `<workspace>` as the Git root when one exists, otherwise the current working directory. Resolve `<plugin-root>` as the parent of the `skills/` directory that contains this `SKILL.md`.

Run the deterministic storage CLI with:

```text
python3 <plugin-root>/scripts/echoes_vault.py --workspace <workspace> <command>
```

Pass write payloads as JSON through stdin (`--payload -`) or a temporary JSON file. Do not interpolate untrusted Markdown into a shell command.

## Core rules

1. Read before writing. Search the vault and read an existing page before updating it.
2. Store dry technical facts, decisions, contracts, configurations, verified fixes, blockers, and next steps—not chat transcripts.
3. Start every page with YAML frontmatter containing `type`, `stack`, and `status`.
4. Keep one index line per page: `- [[page-slug]]: One-sentence description.`
5. Use `[[wikilinks]]` for page references and `![[asset.png]]` for files in `EchoesVault/assets/`.
6. Deprecate instead of deleting. Prepend `> [!warning] DEPRECATED` and link to the replacement.
7. Never report final memory as saved after normal task completion. Only `$echoes-end` may finalize a session.

## Choose an operation

### Recall before work

Use targeted search when an existing component, decision, API, schema, or configuration might already be documented:

```text
python3 <plugin-root>/scripts/echoes_vault.py --workspace <workspace> search "specific keyword"
```

Read the returned page around each relevant line. Follow replacement links from deprecated pages.

### Append an intermediate note

After a verified logical unit, an architectural agreement, a context switch, or an explicit “remember/log this” request, submit:

```json
{
  "entry": "- Implemented X.\n- Verified with Y.\n- Remaining blocker: Z."
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
  "content": "---\ntype: architecture\nstack: [python]\nstatus: active\n---\n\n# Authentication architecture\n",
  "indexDescription": "Authentication boundaries and token flow."
}
```

For an existing page:

1. Read the full page.
2. Run `hash <filename>` and copy its `sha256`.
3. Submit the full replacement content plus `expectedSha256` to `upsert`.

The optimistic hash prevents overwriting a concurrent edit. If it fails, reread the page and reconcile changes.

## Successful completion

Confirm the exact daily log or page path written. Mention whether the index changed. Keep working unless the user requested a final save.
