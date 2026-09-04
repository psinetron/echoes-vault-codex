---
name: echoes-init
description: Initialize, migrate, or repair the agent-neutral EchoesVault structure, portable runtime, and Codex/OpenCode/Claude adapters for the current project. Use when the user asks in any language to initialize, activate, set up, connect, migrate, or bootstrap EchoesVault or persistent local Markdown project memory.
---

# Initialize EchoesVault

Interpret the request semantically in the user's language. Do not require the exact skill name or
an English command; equivalent requests in any language should use this workflow.

Resolve `<workspace>` as the Git root when one exists, otherwise the current working directory.
Resolve `<plugin-root>` as the parent of the `skills/` directory that contains this `SKILL.md`.
Initialization and upgrades must use the bundled `<plugin-root>/scripts/echoes_vault.py`; it safely
installs or upgrades the repository-portable runtime without allowing an older copy to overwrite a
newer one.

1. Run:

   ```text
   python3 <plugin-root>/scripts/echoes_vault.py --workspace <workspace> \
     --agent codex --adapter-version 1.1.1 init
   ```

2. Read `<workspace>/EchoesVault/index.md`.
3. If it contains page entries, briefly list their concepts. Otherwise, state that a fresh vault is ready.
4. Explain that `$echoes-start` restores recent context and `$echoes-end` performs the explicit final save.

Initialization is idempotent. It never overwrites a knowledge page, log, raw source, or asset.
`index.md` is a generated local view: the CLI validates page frontmatter, migrates legacy index
descriptions into missing `summary` fields when possible, and deterministically rebuilds the index.
Do not ask the model to read every page or construct the index itself.

The bundled launcher is used only to bootstrap, explicitly upgrade, or recover a missing project
runtime. It installs the compatible runtime and re-executes the command through
`<workspace>/.echoes-vault/echoes_vault.py`. A newer compatible project runtime is never downgraded.

The managed structure is:

```text
EchoesVault/
├── .echoes-vault.json
├── .gitignore
├── AGENT_PROTOCOL.md
├── index.md
├── pages/
├── daily/
├── assets/
└── raw/

.echoes-vault/
├── .gitignore
├── echoes_vault.py
├── state.json
└── lock
```

Initialization also installs managed EchoesVault blocks in `AGENTS.md` and `CLAUDE.md`, plus
project skills for Claude and OpenCode. Existing unrelated instructions are preserved. The
generated index, state, and lock are ignored locally to avoid branch conflicts.
