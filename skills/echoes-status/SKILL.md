---
name: echoes-status
description: Show a compact EchoesVault status card and report quantitative health, storage size, and integrity metrics, including page and log counts, session state, metadata validity, deprecations, duplicate index links, orphan pages, missing pages, and scale warnings. Use when the user asks for EchoesVault status, dashboard, health, statistics, integrity, size, or scalability.
---

# Report EchoesVault status

Resolve `<workspace>` as the Git root when one exists, otherwise the current working directory. Resolve `<plugin-root>` as the parent of the `skills/` directory that contains this `SKILL.md`.

First run the user-facing card command:

```text
python3 <plugin-root>/scripts/echoes_vault.py --workspace <workspace> status --format card
```

The status command automatically validates page metadata and regenerates `index.md` from
frontmatter summaries. Never rebuild the index by asking the model to read every page.

Return that card, translated to the user's language when helpful. If the card reports an integrity
problem, run the JSON command for details:

```text
python3 <plugin-root>/scripts/echoes_vault.py --workspace <workspace> status
```

Briefly explain only the reported problems. Cover:

- initialization and session state;
- total size and file count;
- page, index-topic, and daily-log counts;
- required structure, runtime state, page frontmatter, symbolic links, and unreadable files;
- duplicate index entries, empty descriptions, orphan pages, and missing linked pages;
- unresolved Git conflict markers and deterministic index build errors.

If `scaleAlert` is true, append:

```text
> [!warning] SCALE ALERT
> The vault exceeds 200 pages. Prefer targeted search and consider hybrid retrieval.
```

Do not inspect or alter the architectural meaning of knowledge pages. The CLI may refresh the
generated index and local runtime state as part of its integrity check.
