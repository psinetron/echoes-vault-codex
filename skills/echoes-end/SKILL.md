---
name: echoes-end
description: Explicitly finalize an EchoesVault session by distilling the current conversation into a dense daily summary and durable knowledge pages, then regenerating the deterministic index. Use only when the user asks to end, wrap up, finalize, or save the session to EchoesVault, or explicitly invokes echoes-end. Never trigger merely because an ordinary task finished.
---

# Distill and save the session

Resolve `<workspace>` as the Git root when one exists, otherwise the current working directory.
Resolve `<plugin-root>` as the parent of the `skills/` directory that contains this `SKILL.md`.
Use `<workspace>/.echoes-vault/echoes_vault.py` as `<runtime>` when it is a regular file;
otherwise use `<plugin-root>/scripts/echoes_vault.py`.

## Prepare

1. Distill final outcomes, verified fixes, decisions, unresolved blockers, and concrete next steps. Do not write a transcript.
2. Treat scratchpad notes already written today as supporting context; do not duplicate them verbatim.
3. Search and read relevant existing pages before proposing page changes.
4. For every existing page update, run `hash <filename>` after reading it and include the returned `sha256` as `expectedSha256`.
5. Prefer deprecation plus a replacement page over deleting historical documentation.
6. Give every new or updated page a non-empty, single-line `summary` of at most 160 characters.
   Never edit or propose exact mutations for `index.md`; the CLI generates it from page metadata.

## Commit

Submit a payload like this to `end --confirm-explicit-user-end --payload -`:

```json
{
  "dailySummary": "## Outcomes\n- ...\n\n## Next steps\n- ...",
  "agent": "codex",
  "pages": [
    {
      "filename": "decision-name.md",
      "content": "---\ntype: decision\nstack: [codex]\nstatus: active\nsummary: The decision and its consequences.\n---\n\n# Decision\n..."
    }
  ]
}
```

Use an empty `pages` array when no durable page needs changing. To deprecate a page, update its
frontmatter `status` and `summary` plus its body rather than sending `indexUpdates`. The CLI validates
the complete page set before writing, regenerates the index, creates a merge-safe unique `Session`
log file, and marks memory saved only with the explicit confirmation flag.

Report the written session log, page count, and generated index result. If validation or a
concurrency hash fails, do not claim success; reread, reconcile, and retry.
