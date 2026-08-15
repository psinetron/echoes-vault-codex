<div align="center">
  <h1>EchoesVault for Codex</h1>
  <p>Persistent, repository-local Markdown memory for Codex.</p>

  <a href="https://learn.chatgpt.com/docs/plugins"><img src="https://img.shields.io/badge/Codex-Plugin-111827?logo=openai&amp;logoColor=white" alt="Codex Plugin" /></a>
  <a href="https://github.com/psinetron/echoes-vault-codex/actions/workflows/tests.yml"><img src="https://github.com/psinetron/echoes-vault-codex/actions/workflows/tests.yml/badge.svg" alt="Tests" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.9+" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" /></a>
  <a href="https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf"><img src="https://img.shields.io/badge/OKF-aligned-4285F4" alt="OKF aligned" /></a>
  <a href="https://github.com/psinetron/echoes-vault-codex/commits/main"><img src="https://img.shields.io/github/last-commit/psinetron/echoes-vault-codex" alt="Last commit" /></a>
</div>

EchoesVault is a persistent memory plugin for Codex, ported from [EchoesVault for OpenCode](https://github.com/psinetron/echoes-vault-opencode). Knowledge stays in plain Markdown, remains readable without Codex, works naturally with Git, and opens as an Obsidian-compatible vault.

## Installation

### Requirements

- Codex in the ChatGPT desktop app or Codex CLI. Plugins are not currently supported by the Codex IDE extension.
- Python 3.9 or newer available as `python3`.
- Git, when installing from GitHub.
- No Python packages, API keys, accounts, background services, or network access at runtime.

Review the bundled [`SessionStart` hook](hooks/session_start.py) before enabling the plugin if your
environment requires auditing third-party commands.

### Install from GitHub — CLI

This repository contains a Codex marketplace manifest. Add it as a marketplace source:

```sh
codex plugin marketplace add psinetron/echoes-vault-codex
```

Then choose either installation method.

**Interactive plugin browser:**

```text
codex
/plugins
```

Open the **EchoesVault** marketplace, select **EchoesVault for Codex**, install it, and make sure it
is enabled. Start a new Codex session after installation.

**Direct CLI installation:**

```sh
codex plugin add echoes-vault-codex@echoes-vault
```

Verify the result:

```sh
codex plugin list
```

The expected entry is `echoes-vault-codex@echoes-vault` with status `installed, enabled`.

### Install from GitHub — desktop app

1. Run `codex plugin marketplace add psinetron/echoes-vault-codex` once in a terminal.
2. Restart the ChatGPT desktop app.
3. Open **Plugins**.
4. Select the **EchoesVault** marketplace.
5. Open **EchoesVault for Codex** and select the plus button to install it.
6. Confirm that it appears in the **Installed** row and is enabled.
7. Start a new Codex task; already-open tasks do not acquire newly installed skills and hooks.

### Local development installation

Clone the repository:

```sh
git clone https://github.com/psinetron/echoes-vault-codex.git
cd echoes-vault-codex
```

Run the tests before installing:

```sh
python3 -m unittest discover -s tests -v
```

Ask Codex to connect the existing folder to your personal marketplace:

```text
Use $plugin-creator to add the existing plugin in the current directory to my personal
marketplace, install it, and use the cachebuster update flow for future local changes.
```

The standard personal marketplace lives at `~/.agents/plugins/marketplace.json`. Do not replace
that file if it already contains other plugins; let `$plugin-creator` merge the entry safely.

After each local code change:

1. Run the tests.
2. Ask `$plugin-creator` to update the cachebuster and reinstall `echoes-vault-codex`.
3. Start a new Codex task to load the updated bundle.

### First project setup

The plugin is installed once for Codex but remains silent in projects that do not have an
EchoesVault. Open the target project in a new task and ask in any language, for example:

```text
Initialize EchoesVault for this project.
Инициализируй EchoesVault для этого проекта.
Подключи локальную память проекта.
```

Exact skill names are optional. You can also invoke `$echoes-init` explicitly. Initialization
creates only repository-local files:

```text
EchoesVault/
├── index.md
├── pages/
├── daily/
├── assets/
└── raw/

.codex/echoes-vault-state.json
```

On later tasks, the first response includes a status card for initialized projects. Other projects
remain unaffected and show no card.

### Update

Refresh all configured marketplaces:

```sh
codex plugin marketplace upgrade
```

Or refresh only EchoesVault:

```sh
codex plugin marketplace upgrade echoes-vault
```

Open `/plugins` in Codex CLI or the Plugins page in the desktop app, reinstall/update the plugin,
and start a new task. If Codex still loads an older local development build, use
`$plugin-creator` to apply a new cachebuster before reinstalling.

### Disable or uninstall

In Codex CLI, open `codex`, enter `/plugins`, select the installed plugin, and either disable it or
uninstall it. In the desktop app, open the plugin under **Installed** and select **Uninstall
plugin**.

Remove the marketplace source only when you no longer need it:

```sh
codex plugin marketplace remove echoes-vault
```

Uninstalling the plugin does **not** delete project knowledge. Existing `EchoesVault/` directories
and `.codex/echoes-vault-state.json` files stay in their projects and can be read as plain Markdown
or used after reinstalling the plugin.

### Troubleshooting installation

| Symptom | Check |
|---|---|
| Marketplace does not appear | Run `codex plugin marketplace list`, then restart the desktop app. |
| Plugin is installed but skills are missing | Start a new Codex task or CLI session. |
| Status card does not appear | Confirm that the project contains `EchoesVault/index.md`. |
| Hook reports a Python error | Run `python3 --version`; version 3.9+ must be on `PATH`. |
| Local edits are ignored | Update the manifest cachebuster, reinstall, and start a new task. |
| You do not want memory in a project | Do not initialize it; the globally installed plugin remains silent there. |

For Codex's general plugin installation and marketplace model, see the [official plugin documentation](https://learn.chatgpt.com/docs/plugins) and [plugin packaging guide](https://developers.openai.com/plugins/build/plugins).

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
