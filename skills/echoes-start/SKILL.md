---
name: echoes-start
description: Start an EchoesVault working session by restoring the generated page index and the three most recent session entries. Use only when the user explicitly asks to start or resume a session, restore project memory, continue previous work, or invokes echoes-start.
---

# Restore EchoesVault context

Resolve `<workspace>` as the Git root when one exists, otherwise the current working directory.
Resolve `<plugin-root>` as the parent of the `skills/` directory that contains this `SKILL.md`.
Use `<plugin-root>/scripts/echoes_vault.py` as `<launcher>`. It delegates execution to a compatible
project runtime, recovers a missing runtime for an initialized vault, refuses an outdated runtime
until explicit upgrade, and never downgrades a newer one.

1. Run:

   ```text
   python3 <launcher> --workspace <workspace> \
     --agent codex --adapter-version 1.1.1 start --recent 3
   ```

   The CLI validates page summaries and rebuilds `index.md` only when its deterministic output
   changed. This is filesystem work and does not load page bodies into the model context.

2. Analyze the returned index and session entries; do not merely repeat them.
3. Summarize:
   - the last completed outcomes;
   - unresolved blockers;
   - the immediate next steps;
   - any conflicting or duplicate index concepts.
4. If the index is consistent, say `Index is healthy. Ready to code.`
5. Use `$echoes-vault` for targeted page search rather than loading every page.

Do not run this workflow automatically at every Codex start. The explicit invocation is the user's control over context cost and session state.
