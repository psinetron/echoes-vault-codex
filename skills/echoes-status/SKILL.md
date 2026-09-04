---
name: echoes-status
description: Show a compact EchoesVault status card and report protocol, adapter, storage, metadata, index, conflict, and scalability health. Use when the user asks for EchoesVault status, dashboard, health, statistics, integrity, size, compatibility, or scalability.
---

# Report EchoesVault status

Resolve `<workspace>` as the Git root when one exists, otherwise the current working directory.
Resolve `<plugin-root>` as the parent of the `skills/` directory that contains this `SKILL.md`.
Use the bundled `<plugin-root>/scripts/echoes_vault.py` as the read-only launcher. It delegates to
a compatible project runtime, but deliberately does not install, upgrade, migrate, hydrate, or
repair anything during inspection.

First run the user-facing card command:

```text
python3 <plugin-root>/scripts/echoes_vault.py --workspace <workspace> inspect --format card
```

The `inspect` command validates page metadata and compares the deterministic index entirely in
memory. It must not change any file. Never rebuild the index by asking the model to read every page.

Return that card, translated to the user's language when helpful. If the card reports an integrity
problem, run the JSON command for details:

```text
python3 <plugin-root>/scripts/echoes_vault.py --workspace <workspace> inspect
```

Briefly explain only the reported problems. Cover:

- initialization and session state;
- total size and file count;
- page, index-topic, and daily-log counts;
- required structure, protocol/runtime adapters, runtime state, page frontmatter, symbolic links,
  and unreadable files;
- duplicate index entries, empty descriptions, orphan pages, and missing linked pages;
- unresolved Git conflict markers and deterministic index build errors.
- Git readiness, including durable untracked/ignored files and accidentally tracked local state;
- legacy OpenCode adapter conflicts and exact suggested Git commands.

If `scaleAlert` is true, append:

```text
> [!warning] SCALE ALERT
> The vault exceeds 200 pages. Prefer targeted search and consider hybrid retrieval.
```

Do not inspect or alter the architectural meaning of knowledge pages. If the user explicitly asks
to refresh local generated data, run `hydrate` through the project runtime separately. If a legacy
vault is reported, ask the user to run the `echoes-init` workflow; status must not migrate it.
