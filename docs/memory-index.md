# 🧠 Memory Index

> Index of all daily memory logs. Each log captures what was done during that session.
> **AI agents MUST read this file at the start of every session to understand recent history.**

---

## Memory Log Files

| Date | File | Summary |
|------|------|---------|
| 2026-03-07 | [2026-03-07-memory.md](../memory/2026-03-07-memory.md) | Major project overhaul: fixed 3 critical bridge bugs (stdout capture, screenshot route, dynamic port), added universal ping health check, removed 18 deprecated files, created git repo on `main` branch, built docs/memory index system, updated Gemini.md |

---

## How This System Works

- Each day's work is logged in `memory/[YYYY-MM-DD]-memory.md`
- This index file maintains a summary of all memory logs
- AI agents should read this index at session start to understand project history
- After completing work, agents must update the current day's memory file and this index
