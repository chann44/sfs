---
name: sfs
description: A sandboxed in-memory filesystem for agents to use as a scratchpad — writing plans, notes, and intermediate artifacts without touching the host disk. Use when the agent needs to persist working files across steps, offload large tool outputs to grep/read them back selectively, or organize intermediate state as files instead of chat context. Provides ls/read/write/edit/glob/grep/delete tools over MCP, CLI, or Python.
---

# sfs — agent scratchpad filesystem

a fake filesystem that lives in memory (persisted via a write-ahead log in the working directory). agents get real file operations — `ls`, `read`, `write`, `edit`, `glob`, `grep`, `delete` — without touching the host filesystem.

## when to use

- you need to write plans, notes, todos, or intermediate artifacts during a task and read them back later
- a tool returned a huge output: dump it to a file, then `grep`/`glob`/`read` (paginated) only the parts you need
- you want file-shaped state (organized, greppable, editable) instead of stuffing everything into the conversation
- the task would benefit from a filesystem but touching the real disk is unwanted or unsafe

do **not** use for binary/media files (text only), long-term durable storage across machines, or anything the user must keep — the WAL lives in the current working directory.

## setup

mcp (recommended — works with claude desktop, cursor, any mcp client):

```json
{ "mcpServers": { "sfs": { "command": "sfs", "args": ["--mcp"] } } }
```

or point directly at the repo: `"command": "python3", "args": ["/path/to/sfs/main.py", "--mcp"]`

cli (after `./install.sh`): `sfs init <name>`, `sfs shell`, `sfs <cmd>`
python: `from core.agent import AgentFilesystem; afs = AgentFilesystem()`

## tools

| tool | key params | notes |
|---|---|---|
| `write` | `file_path`, `content` | creates or overwrites; auto-creates parent dirs |
| `read` | `file_path`, `offset`, `limit` | line-based; default limit 2000 lines; negative offset counts from end |
| `edit` | `file_path`, `old_string`, `new_string`, `replace_all` | find/replace; `old_string` must be unique unless `replace_all` |
| `ls` | `path` | sorted entries with `path`, `is_dir`, `size` |
| `glob` | `pattern`, `path` | `*`, `?`, `**`; matches full path and basename |
| `grep` | `pattern`, `path`, `glob` | literal string search; returns path, line number, line text |
| `delete` | `file_path` | removes file or directory recursively |

## rules to follow

1. **always check the `error` field.** every tool returns a result object; failures come back as `{"error": "..."}`, never as exceptions. if `error` is set, adjust and retry — don't repeat the identical call.
2. **text only, small files.** content must be utf-8 text; binary is rejected. per-file cap 4 kb, total quota 1 mb. write tersely; split long documents across files (`report/01-intro.md`, `report/02-data.md`).
3. **use absolute paths.** `/notes/plan.md`, not `notes/plan.md`. the agent surface keeps no working directory.
4. **prefer `edit` over rewriting.** pass the exact unique `old_string`; use `replace_all` only when you mean every occurrence.
5. **paginate big reads.** `read` with `offset`/`limit` instead of dumping whole files into context.
6. **clean up.** `delete` scratch files when a task finishes; state persists in `sfs.wal` in the working directory until then.

## patterns

offload a large output:

```
write("/outputs/tool-dump.txt", "<huge text>")
grep("ERROR", path="/outputs", glob="*.txt")   → find the useful lines
read("/outputs/tool-dump.txt", offset=412, limit=20)
```

working plan as files:

```
write("/plan/todo.md", "- [ ] collect data\n- [ ] analyze\n- [ ] report\n")
edit("/plan/todo.md", "- [ ] collect data", "- [x] collect data")
glob("**/*.md")                                 → see all plan files
delete("/outputs/tool-dump.txt")                → reclaim quota when done
```
