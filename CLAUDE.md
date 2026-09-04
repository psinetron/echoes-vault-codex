<!-- echoes-vault:start -->
## EchoesVault project memory

This repository uses the agent-neutral EchoesVault protocol 1.0.0.
Adapter version: 1.1.0. Reference engine: 1.1.0.

Before accessing persistent project memory, read `EchoesVault/AGENT_PROTOCOL.md`. Use the project
runtime with `--workspace . --agent <agent-name> --adapter-version <adapter-version> <command>` for
all mutations.
Never edit `EchoesVault/index.md` or append to a shared date-level daily file manually.
Use `status` or `inspect` for read-only health checks; use `hydrate` only to refresh ignored local
state and the generated index. Final session saving requires an explicit user request.
<!-- echoes-vault:end -->
