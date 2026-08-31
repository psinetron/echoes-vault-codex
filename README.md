<div align="center">
  <h1>EchoesVault</h1>
  <p>Agent-neutral, repository-local Markdown memory bootstrapped from Codex.</p>

  <a href="https://learn.chatgpt.com/docs/plugins"><img src="https://img.shields.io/badge/Codex-Plugin-111827?logo=openai&amp;logoColor=white" alt="Codex Plugin" /></a>
  <img src="https://img.shields.io/badge/Release-1.0.0-2563EB" alt="Release 1.0.0" />
  <a href="#agent-neutral-protocol"><img src="https://img.shields.io/badge/Protocol-1.0.0-7C3AED" alt="Protocol 1.0.0" /></a>
  <a href="#using-different-agents"><img src="https://img.shields.io/badge/Agents-Codex%20%7C%20OpenCode%20%7C%20Claude-059669" alt="Codex, OpenCode, and Claude" /></a>
  <a href="https://github.com/psinetron/echoes-vault-codex/actions/workflows/tests.yml"><img src="https://github.com/psinetron/echoes-vault-codex/actions/workflows/tests.yml/badge.svg" alt="Tests" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.9+" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" /></a>
  <a href="https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf"><img src="https://img.shields.io/badge/OKF-aligned-4285F4" alt="OKF aligned" /></a>
  <a href="https://github.com/psinetron/echoes-vault-codex/commits/main"><img src="https://img.shields.io/github/last-commit/psinetron/echoes-vault-codex" alt="Last commit" /></a>
</div>

EchoesVault is a persistent memory plugin for Codex and a portable project-memory protocol for
Codex, OpenCode, Claude, and other coding agents. Codex bootstraps a shared runtime and agent
instructions into the repository; after that, every supported agent uses the same validation,
locking, logs, and deterministic index. Knowledge stays in plain Markdown, remains readable without
any agent, works naturally with Git, and opens as an Obsidian-compatible vault.

**Current release:** `1.0.0` · **Protocol:** `1.0.0`

## Quick start

Install the plugin once:

```sh
codex plugin marketplace add psinetron/echoes-vault-codex
codex plugin add echoes-vault-codex@echoes-vault
```

Start a new Codex task in the repository that should own the memory and ask in any language:

```text
Initialize EchoesVault for this project.
Инициализируй EchoesVault для этого проекта.
```

Then use natural language rather than memorizing commands:

```text
Restore project memory.
Show EchoesVault status.
Remember this architectural decision.
Save and finish this EchoesVault session.
```

Initialization is project-local. The globally installed Codex plugin stays silent in every other
repository until EchoesVault is initialized there. Commit the generated protocol, portable runtime,
and adapters so Codex, OpenCode, Claude, and teammates all follow the same rules.

## Contents

- [Installation](#installation)
- [What it provides](#what-it-provides)
- [Agent-neutral protocol](#agent-neutral-protocol)
- [Open Knowledge Format alignment](#open-knowledge-format-alignment)
- [Status card and quick actions](#status-card-and-quick-actions)
- [Team development without CI/CD](#team-development-without-cicd)
- [Upgrade from 0.2.x](#upgrade-from-02x)
- [Local development](#local-development)
- [Security and privacy](#security-and-privacy)

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
├── .echoes-vault.json
├── .gitignore
├── AGENT_PROTOCOL.md        # shared contract for every agent
├── index.md                 # generated locally; ignored by Git
├── pages/
├── daily/YYYY-MM-DD/        # one unique file per write
├── assets/
└── raw/

.echoes-vault/
├── .gitignore
├── echoes_vault.py          # portable runtime; committed to Git
├── state.json               # local runtime state; ignored by Git
└── lock                     # short-lived local lock; ignored by Git

AGENTS.md                    # managed block for Codex/OpenCode
CLAUDE.md                    # managed block for Claude
.claude/skills/echoes-vault/SKILL.md
.opencode/skills/echoes-vault/SKILL.md
.opencode/commands/echoes-init.md
.opencode/commands/echoes-start.md
.opencode/commands/echoes-status.md
.opencode/commands/echoes-end.md
```

On later tasks, the first response includes a status card for initialized projects. Other projects
remain unaffected and show no card.

### Bootstrap for OpenCode, Claude, or another agent

Codex is convenient for installing and initializing EchoesVault, but it is not required after the
portable files have been created. To bootstrap a project without Codex, clone or download this
repository once and run its bundled engine against the target project:

```sh
git clone https://github.com/psinetron/echoes-vault-codex.git
python3 echoes-vault-codex/scripts/echoes_vault.py \
  --workspace /path/to/your/project init
```

Commit the generated protocol, portable runtime, and adapters in the target project. Teammates and
other agents then use `.echoes-vault/echoes_vault.py` from that project and do not need a global
EchoesVault installation.

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

Uninstalling the Codex plugin does **not** delete project knowledge or its portable runtime.
Initialized repositories continue to contain `EchoesVault/`, `.echoes-vault/echoes_vault.py`, and
the agent adapters. They can be used by another supported agent or read as plain Markdown.

### Troubleshooting installation

| Symptom | Check |
|---|---|
| Marketplace does not appear | Run `codex plugin marketplace list`, then restart the desktop app. |
| Plugin is installed but skills are missing | Start a new Codex task or CLI session. |
| Status card does not appear | Confirm that the project contains `EchoesVault/.echoes-vault.json`; legacy vaults may still be detected by `index.md`. |
| Hook reports a Python error | Run `python3 --version`; version 3.9+ must be on `PATH`. |
| Local edits are ignored | Update the manifest cachebuster, reinstall, and start a new task. |
| You do not want memory in a project | Do not initialize it; the globally installed plugin remains silent there. |
| Protocol mismatch is reported | Stop writes, update the adapter or plugin, then run initialization again. Never force an older writer against a newer vault. |
| Portable runtime or agent adapters are missing | Run `python3 .echoes-vault/echoes_vault.py --workspace . configure-agents`; if the runtime itself is missing, run initialization from the installed plugin. |
| An OpenCode command was not replaced | EchoesVault preserves unrecognized user-owned files. Compare it with the generated command and reconcile it manually. |

For Codex's general plugin installation and marketplace model, see the [official plugin documentation](https://learn.chatgpt.com/docs/plugins) and [plugin packaging guide](https://developers.openai.com/plugins/build/plugins).

## What it provides

- `$echoes-init` — idempotently create or activate the vault.
- `$echoes-start` — rebuild and restore the full index plus the three latest session entries.
- `$echoes-vault` — search pages, append scratchpad notes, and safely maintain knowledge pages.
- `$echoes-end` — explicitly distill and save final session memory.
- `$echoes-status` — show a compact dashboard with size, metrics, filesystem checks, metadata validity, index integrity, and scale warnings.
- **Agent Protocol 1.0.0** — a tracked contract that every coding agent reads before using memory.
- **Portable runtime** — the same dependency-free Python storage engine is committed into each initialized repository.
- **Claude and OpenCode adapters** — project skills and root instruction blocks are installed without replacing unrelated user instructions.
- **OKF-aligned knowledge storage** — pages follow the core [Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) model of plain Markdown, YAML frontmatter, typed concepts, portable directories, and progressive-disclosure indexes.
- A lightweight `SessionStart` hook that asks Codex to show the current status card once in its first response after startup, resume, or clear, but only in initialized projects. Uninitialized projects remain silent. Compaction refreshes hidden context without repeating the card.
- Natural-language starter actions for initialization, restore, status, and explicit final save, so normal use does not require memorizing skill names.
- A dependency-free Python CLI with atomic replacement writes, a project-local lock, strict page metadata, conflict-marker detection, path sanitization, and optimistic concurrency checks.

The managed project structure is intentionally Git-friendly:

```text
EchoesVault/
├── .echoes-vault.json       # tracked initialization marker
├── .gitignore               # ignores only generated index.md
├── AGENT_PROTOCOL.md        # generated cross-agent contract
├── index.md                 # generated from page metadata
├── pages/
├── daily/YYYY-MM-DD/        # unique scratchpad/session files
├── assets/
└── raw/
```

The tracked portable engine lives at `.echoes-vault/echoes_vault.py`. Runtime state and the shared
local lock live at `.echoes-vault/state.json` and `.echoes-vault/lock`; they contain no durable
knowledge and are ignored locally.

## Agent-neutral protocol

Initialization writes `EchoesVault/AGENT_PROTOCOL.md` and adds a delimited EchoesVault block to
the repository's `AGENTS.md` and `CLAUDE.md`. Existing content outside that block is preserved.
Project skills are also written for Claude and OpenCode:

```text
.claude/skills/echoes-vault/SKILL.md
.opencode/skills/echoes-vault/SKILL.md
.opencode/commands/echoes-init.md
.opencode/commands/echoes-start.md
.opencode/commands/echoes-status.md
.opencode/commands/echoes-end.md
```

All agents are instructed to use the repository runtime:

```sh
python3 .echoes-vault/echoes_vault.py --workspace . status --format card
```

The runtime marker declares `protocolVersion: "1.0.0"`. An adapter that encounters a different
protocol version must stop before writing instead of guessing compatibility. Optional `agent`
values in append and end payloads add provenance to unique log filenames and bodies:

```json
{
  "entry": "- Confirmed the shared authentication contract.",
  "agent": "claude"
}
```

Legacy OpenCode tools that directly edit `index.md` or append to `daily/YYYY-MM-DD.md` must not be
used with a protocol 1.0 vault. OpenCode should use the generated project skill and portable
runtime instead. The standalone [EchoesVault for OpenCode](https://github.com/psinetron/echoes-vault-opencode)
requires a corresponding protocol-aware release before its legacy tools can be mixed safely.
Recognized legacy EchoesVault command files are migrated automatically; unrelated user-owned files
with the same names are preserved and reported by the health check for manual reconciliation.

### Using different agents

- **Codex:** use the plugin actions, `$echoes-*` skills, or natural-language requests.
- **OpenCode:** use the generated `/echoes-init`, `/echoes-start`, `/echoes-status`, and
  `/echoes-end` project commands. They call the portable runtime rather than legacy mutation tools.
- **Claude Code:** `CLAUDE.md` advertises the protocol and the generated project skill handles
  natural-language initialization, restoration, status, recall, logging, and explicit final save.
- **Other agents:** read `AGENTS.md` and `EchoesVault/AGENT_PROTOCOL.md`, then invoke the portable
  CLI directly.

The portable command surface is:

| Command | Purpose |
|---|---|
| `init` | Initialize or migrate the vault and install every adapter |
| `protocol` | Report supported and repository protocol versions |
| `configure-agents` | Repair protocol documentation, runtime, guides, skills, and OpenCode commands |
| `status --format card` | Regenerate the index and show quantitative health |
| `start --recent 3` | Restore the index and latest session entries |
| `search <query>` | Search page bodies literally |
| `append --payload -` | Write one unique scratchpad file |
| `hash <filename>` | Obtain the optimistic concurrency hash for an existing page |
| `upsert --payload -` | Create or safely replace a complete page |
| `end --confirm-explicit-user-end --payload -` | Perform an explicitly authorized final save |
| `rebuild-index` | Validate metadata and reconstruct the generated local index |

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
summary: Authentication boundaries and token flow.
---
```

`summary` is required, must fit on one line, and is limited to 160 characters. The Python runtime
builds `index.md` from filenames and these summaries in a fixed Unicode-aware order. Page bodies are
not used, so rebuilding the index consumes no model context and the same pages always produce the
same bytes. Existing pre-1.0 vaults are migrated automatically when their old index contains a
description for every page missing `summary`.

## Status card and quick actions

After the plugin is installed, start a new Codex task. On the first response, EchoesVault adds a
compact card similar to:

```text
### EchoesVault · ✓ Healthy

| Storage | Knowledge | Session |
|---|---|---|
| 186.4 KB · 48 files | 42 pages · 6 logs | active |

Protocol: 1.0.0 · portable runtime and agent adapters ready.
Integrity: index, structure, metadata, and local paths are consistent.
```

The card is generated from live filesystem data and does not initialize, restore, or save the
vault. It may validate metadata and refresh the generated index. Projects without the initialization
marker (or a legacy `EchoesVault/index.md`) show no card and receive no hook context. Use the
plugin starter actions, invoke `$echoes-status`, or ask naturally in any language: “show vault
status”, “покажи состояние памяти”, “restore project memory”, or “сохрани эту сессию”. Exact skill
names are optional. Codex plugins cannot pin a permanent custom sidebar, so the card appears in the
conversation instead.

For scripts and diagnostics, request the same card directly:

```sh
python3 .echoes-vault/echoes_vault.py --workspace . status --format card
```

From a clone of this repository, you can also inspect another workspace with the bundled engine:

```sh
python3 scripts/echoes_vault.py --workspace /path/to/project status --format card
```

## Why Codex is the bootstrapper

The original OpenCode plugin exposes runtime tools, command templates, and a custom TUI sidebar
through OpenCode-specific APIs. A Codex plugin natively packages skills, scripts, hooks, and optional
MCP servers. EchoesVault uses Codex as the installer and bootstrapper, then places an agent-neutral
runtime and instructions inside the repository:

| Choice | Benefit | Trade-off |
|---|---|---|
| Skills instead of custom slash-command registration | Native discovery and explicit `$echoes-*` workflows | Invocation uses `$echoes-start`, not `/echoes-start` |
| Local CLI instead of an MCP server | No daemon, network, package install, or protocol dependency | Codex executes a local command rather than calling named MCP tools |
| Repository-portable runtime and protocol | Codex, OpenCode, and Claude share one writer and one set of invariants | The generated runtime and adapters are committed to each project |
| One-time SessionStart card instead of a sidebar | Live health is visible at the start of a task and after resume | There is no always-visible custom status panel |
| Explicit start/end | Predictable token cost and no accidental final save | The user must request restoration and finalization |
| Frontmatter-generated local index | Stable output, no model-token rebuild cost, and no index merge conflicts | Every page needs a concise `summary` |
| Unique daily files plus a project-local lock | Concurrent local writes and cross-branch logs do not overwrite one shared file | Same-page semantic conflicts still need human resolution |
| Optimistic hashes for existing pages | Prevents silent lost updates | Existing-page updates need one extra hash step |

Compared with the original, the port deliberately strengthens frontmatter validation, rejects path traversal, detects missing structure, symbolic links, unreadable files, invalid page metadata, Git conflict markers, and duplicate/orphan/missing index entries, uses local timezone consistently, and avoids copying OpenCode/TUI dependencies. It keeps deprecation-over-deletion, read-before-write, daily scratchpads, index synchronization, and the 200-page scale warning.

## Team development without CI/CD

Commit durable knowledge and the small initialization files:

```text
EchoesVault/.echoes-vault.json
EchoesVault/.gitignore
EchoesVault/AGENT_PROTOCOL.md
EchoesVault/pages/**
EchoesVault/daily/**
EchoesVault/assets/**
EchoesVault/raw/**
.echoes-vault/.gitignore
.echoes-vault/echoes_vault.py
AGENTS.md
CLAUDE.md
.claude/skills/echoes-vault/SKILL.md
.opencode/skills/echoes-vault/SKILL.md
.opencode/commands/echoes-init.md
.opencode/commands/echoes-start.md
.opencode/commands/echoes-status.md
.opencode/commands/echoes-end.md
```

Do not commit generated or machine-local files:

```text
EchoesVault/index.md
.echoes-vault/state.json
.echoes-vault/lock
```

`echoes-init` adds those ignore rules automatically. If `EchoesVault/index.md` was already tracked
before upgrading, remove only that file from Git's index once while keeping the local copy:

```sh
git rm --cached EchoesVault/index.md
git add EchoesVault .echoes-vault/.gitignore .echoes-vault/echoes_vault.py AGENTS.md CLAUDE.md
git add .claude/skills/echoes-vault/SKILL.md .opencode/skills/echoes-vault/SKILL.md
git add .opencode/commands/echoes-init.md .opencode/commands/echoes-start.md
git add .opencode/commands/echoes-status.md .opencode/commands/echoes-end.md
git commit -m "Make EchoesVault index generated locally"
```

After pulling, switching branches, merging, starting a task, or requesting status, the index is
regenerated automatically when needed. A manual recovery command is also available:

```sh
python3 .echoes-vault/echoes_vault.py --workspace . rebuild-index
```

Different pages and unique daily-log files normally merge cleanly. If two branches edit the same
knowledge page, Git still reports the ordinary Markdown conflict; resolve its meaning manually,
remove every conflict marker, keep valid frontmatter including `summary`, and request EchoesVault
status. The health card reports unresolved `<<<<<<<`, `=======`, or `>>>>>>>` markers. No CI job,
Git hook, daemon, or background watcher is required.

### Upgrade from 0.2.x

After installing 1.0.0, run initialization once in every existing vault. It migrates the marker and
local state, installs the portable runtime and protocol, and adds the managed agent adapters:

```text
Update this project's EchoesVault to protocol 1.0.0.
Обнови EchoesVault этого проекта до протокола 1.0.0.
```

Or run the bundled engine directly:

```sh
python3 /path/to/echoes-vault-codex/scripts/echoes_vault.py --workspace . init
```

Legacy `.codex/echoes-vault-state.json` is read during migration, then new state is written to
`.echoes-vault/state.json`. The old local file may be removed after the new status card is healthy.
Do not use an older OpenCode EchoesVault toolset against the migrated vault.

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

EchoesVault makes no network requests and has no authentication. Vault data operations are confined
to `EchoesVault/`, `.echoes-vault/`, the managed blocks in `AGENTS.md` and `CLAUDE.md`, and the
generated Claude/OpenCode project skills inside the resolved workspace; symbolic-link escapes are
rejected. Existing unrelated root instructions are preserved. Treat the vault like source code: do
not store secrets unless the repository's access policy permits them.

## License

MIT
