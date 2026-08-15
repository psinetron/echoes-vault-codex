---
name: echoes-end
description: Explicitly finalize an EchoesVault session by distilling the current conversation into a dense daily summary, durable knowledge pages, and exact index updates. Use only when the user asks to end, wrap up, finalize, or save the session to EchoesVault, or explicitly invokes echoes-end. Never trigger merely because an ordinary task finished.
---

# Distill and save the session

Resolve `<workspace>` as the Git root when one exists, otherwise the current working directory. Resolve `<plugin-root>` as the parent of the `skills/` directory that contains this `SKILL.md`.

## Prepare

1. Distill final outcomes, verified fixes, decisions, unresolved blockers, and concrete next steps. Do not write a transcript.
2. Treat scratchpad notes already written today as supporting context; do not duplicate them verbatim.
3. Search and read relevant existing pages before proposing page changes.
4. For every existing page update, run `hash <filename>` after reading it and include the returned `sha256` as `expectedSha256`.
5. Prefer deprecation plus a replacement page over deleting historical documentation.

## Commit

Submit a payload like this to `end --confirm-explicit-user-end --payload -`:

```json
{
  "dailySummary": "## Outcomes\n- ...\n\n## Next steps\n- ...",
  "pages": [
    {
      "filename": "decision-name.md",
      "content": "---\ntype: decision\nstack: [codex]\nstatus: active\n---\n\n# Decision\n...",
      "indexDescription": "The decision and its consequences."
    }
  ],
  "indexUpdates": [
    {
      "oldLine": "- [[old-page]]: Old description.",
      "newLine": "- [[old-page]]: DEPRECATED; replaced by [[decision-name]]."
    }
  ]
}
```

Use an empty `pages` or `indexUpdates` array when unnecessary. The CLI validates every page and index mutation before writing, appends one final `Session` block to today's log, and marks memory saved only with the explicit confirmation flag.

Report the written daily log, page count, and index result. If validation or a concurrency hash fails, do not claim success; reread, reconcile, and retry.
