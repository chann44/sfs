<p align="center">
  <img src="assets/logo.png" alt="SFS logo" width="180" />
</p>

<p align="center">
  An in-memory virtual filesystem for AI agents, written in Python.
</p>

<p align="center">
  A scratchpad for agents to create, read, modify, and organize files during execution without touching the host filesystem.
</p>

## demo

![demo](assets/demo.gif)

## features

**filesystem core** (`core/setup.py`)
- `ls`, `cd`, `pwd`, `mkdir`, `mkdirs` (nested), `touch`, `read`, `write`, `edit`, `delete`, `glob`, `grep`, `tree`
- relative and absolute paths, `.` / `..` resolution
- proper errors: `FileNotFoundError`, `FileExistsError`, `NotADirectoryError`, ...

**agent surface** (`core/agent.py`)
- mirrors the same protocol langchain deep agents use: `ls`, `read` (line-paginated), `write`, `edit`, `glob`, `grep`, `delete`
- errors are data, not exceptions — every call returns a result object with an `error` field, so an llm never eats a stack trace
- `write` auto-creates parent dirs, listings are sorted and deterministic

**safety rails**
- text-only content: utf-8 validated, binary rejected
- per-file cap (default 4 kb) and total storage quota (default 1 mb), both configurable

**persistence** (`core/persist.py`)
- write-ahead log: one json line per mutation, byte-exact via base64
- crash tolerant: torn last line is skipped, corrupt lines are rejected loudly
- `compact()` rewrites the log as an atomic snapshot

**interfaces**
- cli: one-shot commands + interactive shell (`python3 main.py shell`)
- agent tools: `tools/openai.py` (definitions + executor), `tools/langchain.py` (structuredtools), `python3 main.py tools` prints the json schemas
- mcp server: `python3 main.py --mcp` — stdio json-rpc, zero dependencies

## usecases

- **agent scratchpad** — give an agent a place to write plans, notes, and intermediate artifacts during a run without touching the host disk
- **context engineering** — offload large tool outputs into files, let the agent `grep`/`glob`/`read` (paginated) only what it needs, like deep agents do
- **mcp server for any client** — claude desktop, cursor, or any mcp client gets a sandboxed fake filesystem:
  ```json
  { "mcpServers": { "sfs": { "command": "python3", "args": ["/path/to/main.py", "--mcp"] } } }
  ```
- **plug into your own agent** — openai tool-calling or langchain, two lines each:
  ```python
  from core.agent import AgentFilesystem
  from tools.openai import to_openai, execute

  afs = AgentFilesystem()
  defs = to_openai()                          # attach to any model call
  result = execute(afs, "write", {"file_path": "/plan.md", "content": "..."})
  ```
- **deterministic testing** — quota caps, text-only enforcement, and error-as-data make file-logic tests reproducible
- **safe playground** — a fake filesystem you can `rm -rf` all day; nothing on the host can break

## motivation

give agents a filesystem to think, work, and manage intermediate artifacts.

## Goals
1. able to read files from memory
2. play media files 
3. run programs 
4. WAL

## status

work in progress.

