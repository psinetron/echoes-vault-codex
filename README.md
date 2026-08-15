# EchoesVault for Codex

Persistent, repository-local memory for Codex, ported from [EchoesVault for OpenCode](https://github.com/psinetron/echoes-vault-opencode). Knowledge stays in plain Markdown, remains readable without Codex, and opens as an Obsidian-compatible vault.

## What it provides

- `$echoes-init` — idempotently create or activate the vault.
- `$echoes-start` — restore the full index and three latest daily logs.
- `$echoes-vault` — search pages, append scratchpad notes, and safely maintain knowledge pages.
- `$echoes-end` — explicitly distill and save final session memory.
- `$echoes-status` — show a compact dashboard with size, metrics, filesystem checks, metadata validity, index integrity, and scale warnings.
- **OKF-aligned knowledge storage** — pages follow the core [Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) model of plain Markdown, YAML frontmatter, typed concepts, portable directories, and progressive-disclosure indexes.
- A lightweight `SessionStart` hook that asks Codex to show the current status card once in its first response after startup, resume, or clear, but only in projects that already contain `EchoesVault/index.md`. Uninitialized projects remain silent. Compaction refreshes hidden context without repeating the card.
- Three starter actions for initialize/restore, status, and final save, so normal use does not require memorizing skill names.
- A dependency-free Python CLI with atomic replacement writes, strict page metadata, path sanitization, and optimistic concurrency checks.

The managed project structure is unchanged from the OpenCode edition:

```text
EchoesVault/
├── index.md
├── pages/
├── daily/
├── assets/
└── raw/
```

Runtime state is stored in `.codex/echoes-vault-state.json`; it contains counters and session flags, not knowledge content.

## Open Knowledge Format alignment

EchoesVault follows the core ideas of Google's [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md): knowledge is stored as UTF-8 Markdown, concept pages begin with YAML frontmatter, every page has a `type`, and `index.md` enables progressive discovery without loading the complete vault.

EchoesVault deliberately extends the strict OKF shape with Obsidian `[[wikilinks]]`, required `stack`
and `status` fields, `daily/` session logs, and lifecycle values used by the original OpenCode plugin.
For that reason this project describes itself as **OKF-aligned**, rather than claiming strict OKF
v0.2 conformance. The files remain human-readable, Git-friendly, and straightforward for agents
and generic Markdown tooling to consume.

Every knowledge page uses frontmatter like:

```yaml
---
type: architecture
stack: [python, codex]
status: active
---
```

## Status card and quick actions

After the plugin is installed, start a new Codex task. On the first response, EchoesVault adds a
compact card similar to:

```text
EchoesVault · ✓ Healthy
Storage: 186.4 KB · 48 files
Knowledge: 42 pages · 6 logs
Session: active
Integrity: index, structure, metadata, and local paths are consistent.
```

The card is generated from live filesystem data and does not initialize, restore, or save the
vault. Projects without `EchoesVault/index.md` show no card and receive no hook context. Use the
three plugin starter actions, invoke `$echoes-status`, or ask naturally in any language: “show vault
status”, “покажи состояние памяти”, “restore project memory”, or “сохрани эту сессию”. Exact skill
names are optional. Codex plugins cannot pin a permanent custom sidebar, so the card appears in the
conversation instead.

For scripts and diagnostics, request the same card directly:

```sh
python3 scripts/echoes_vault.py --workspace /path/to/project status --format card
```

## Why the Codex port is shaped differently

The OpenCode plugin exposes runtime tools, command templates, and a custom TUI sidebar through OpenCode-specific APIs. A Codex plugin natively packages skills, scripts, hooks, and optional MCP servers. This port uses the smallest native shape that retains the behavior:

| Choice | Benefit | Trade-off |
|---|---|---|
| Skills instead of custom slash-command registration | Native discovery and explicit `$echoes-*` workflows | Invocation uses `$echoes-start`, not `/echoes-start` |
| Local CLI instead of an MCP server | No daemon, network, package install, or protocol dependency | Codex executes a local command rather than calling named MCP tools |
| One-time SessionStart card instead of a sidebar | Live health is visible at the start of a task and after resume | There is no always-visible custom status panel |
| Explicit start/end | Predictable token cost and no accidental final save | The user must request restoration and finalization |
| Strict hashes and exact index replacement | Prevents silent lost updates and broad `replaceAll` mistakes | Existing-page updates need one extra hash step |

Compared with the original, the port deliberately strengthens frontmatter validation, rejects path traversal, detects missing structure, symbolic links, unreadable files, invalid page metadata, and duplicate/orphan/missing index entries, uses local timezone consistently, and avoids copying OpenCode/TUI dependencies. It keeps deprecation-over-deletion, read-before-write, daily scratchpads, index synchronization, and the 200-page scale warning.

## Local development

Validate all skills and the plugin:

```sh
for skill in skills/*; do
  python3 /path/to/skill-creator/scripts/quick_validate.py "$skill"
done
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
```

Run the test suite:

```sh
python3 -m unittest discover -s tests -v
```

The runtime requires Python 3.9 or newer and only the standard library.

## Security and privacy

EchoesVault makes no network requests and has no authentication. Vault data operations are confined to `EchoesVault/` and `.codex/echoes-vault-state.json` inside the resolved workspace; symbolic-link escapes are rejected. Treat the vault like source code: do not store secrets unless the repository's access policy permits them.

## License

MIT
