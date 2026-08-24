# Agent Rules: Full Steam Ahead Website

## Centralized Environment File

All FSA projects (including this website) use a single shared `.env` file located at:

```
/home/debian/.env
```

That is two levels above this project's `scripts/` directory, so `../../.env` from
`scripts/` resolves to it correctly. Mode is `600` as of 2026-08-23.

**Corrected 2026-08-23:** this file previously named `/home/debian/projects/fsa/.env`
and instructed agents not to change it. **That path has not existed for months.**
`scripts/generate_article.py` hard-coded it and was silently running with no
credentials at all until it was fixed. If you find any other reference to
`/home/debian/projects/`, it is stale — the tree was flattened to `/home/debian/`.

**Scripts that read it:**
- `scripts/purge_cloudflare.sh` — loads `CF_ZONE_ID` and `CF_API_MGMT_TOKEN`. It resolves
  `../../.env` first and falls back to `$HOME/.env`, so it was unaffected by the bad path.
- `scripts/generate_article.py` — loads `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`.

The variable is `CF_API_MGMT_TOKEN`, not `CF_API_TOKEN`.

Note: the `.env` may contain unquoted string values with spaces. When sourcing it with
`set -a`, `bash` may error on those lines. Prefer `python-dotenv` or quote the values.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `PowerBootWS/fsa-website`. See `docs/agents/issue-tracker.md`.

### Triage labels

Using default label vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
