# Agent Rules: Full Steam Ahead Website

## Centralized Environment File

All FSA projects (including this website) use a single shared `.env` file located at:

```
/home/debian/projects/fsa/.env
```

This is two levels above the fsa-website project root (`../../.env` from any file inside `fsa-website/`).

**Scripts that read it:**
- `scripts/purge_cloudflare.sh` — loads `CF_ZONE_ID` and `CF_API_TOKEN` from this `.env`

**Important:** Do not change the relative path in purge scripts to point to a different location such as `$HOME/.env` or a local copy. The canonical centralized location is `/home/debian/projects/fsa/.env`.

Note: The `.env` may contain unquoted string values with spaces (e.g. `SHAREPOINT_FOLDER_PATH=/Home/Full Steam Ahead/...`). When sourcing this file with `set -a`, `bash` may error on those lines. The script still works if `CF_ZONE_ID` and `CF_API_TOKEN` appear before those lines. For robustness, consider using `export VAR=value` syntax in the `.env` or quoting values.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `PowerBootWS/fsa-website`. See `docs/agents/issue-tracker.md`.

### Triage labels

Using default label vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
