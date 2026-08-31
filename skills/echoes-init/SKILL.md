---
name: echoes-init
description: Initialize or repair the idempotent EchoesVault directory structure and state for the current project. Use when the user asks in any language to initialize, activate, set up, connect, or bootstrap EchoesVault or persistent local Markdown project memory, including phrases such as “инициализируй EchoesVault”, “подключи память проекта”, or “initialize project memory”.
---

# Initialize EchoesVault

Interpret the request semantically in the user's language. Do not require the exact skill name or
an English command; equivalent requests in any language should use this workflow.

Resolve `<workspace>` as the Git root when one exists, otherwise the current working directory. Resolve `<plugin-root>` as the parent of the `skills/` directory that contains this `SKILL.md`.

1. Run:

   ```text
   python3 <plugin-root>/scripts/echoes_vault.py --workspace <workspace> init
   ```

2. Read `<workspace>/EchoesVault/index.md`.
3. If it contains page entries, briefly list their concepts. Otherwise, state that a fresh vault is ready.
4. Explain that `$echoes-start` restores recent context and `$echoes-end` performs the explicit final save.

Initialization is idempotent. It never overwrites a knowledge page, log, raw source, or asset.
`index.md` is a generated local view: the CLI validates page frontmatter, migrates legacy index
descriptions into missing `summary` fields when possible, and deterministically rebuilds the index.
Do not ask the model to read every page or construct the index itself.

The managed structure is:

```text
EchoesVault/
├── .echoes-vault.json
├── .gitignore
├── index.md
├── pages/
├── daily/
├── assets/
└── raw/
```

The generated index and `.codex/` runtime state are ignored locally to avoid branch conflicts.
