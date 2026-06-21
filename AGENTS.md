# AGENTS.md

Instructions for coding agents working in this repository.

## Project overview

- Repo: `HYP3R00T/counterhub`
- Product: CounterHub is a lightweight backend service that increments named counters and exposes simple history for personal projects.
- Primary use case: static websites, scripts, homelab services, and automation workflows call one endpoint to increase a counter.
- Core design: keep the product deliberately small, with registered counters, atomic increments, daily rollups, and simple reads instead of a broad analytics platform.
- Stack: Python >= 3.13, FastAPI, Supabase, `uv`, `ruff`, `ty`, `pytest`, `zensical`.

## Product direction

CounterHub acts as the middle layer between lightweight clients and Supabase:

```text
Client -> CounterHub -> Supabase
```

Clients call a simple endpoint such as:

```text
POST /count/dotfiles
```

CounterHub increments registered named counters atomically, stores them in daily buckets, and lets clients read back totals and history later.

Current API direction:

```text
POST /count/{counter_id}
GET  /count/{counter_id}
GET  /count/{counter_id}/series
```

Important: keep the product small unless a real need appears. Prefer daily rollups over raw event streams by default.

## Environment setup

```sh
mise install
uv sync
prek install --hook-type pre-commit --overwrite
prek install --hook-type commit-msg --overwrite
```

Dev container runs `scripts/setup.sh` automatically on create.

## Key files

| Concern | Files |
|---|---|
| API app | `app/main.py` |
| Python / tooling | `pyproject.toml`, `ruff.toml`, `ty.toml`, `mise.toml` |
| Docs | `README.md`, `docs/index.md`, `zensical.toml` |
| Scripts | `scripts/setup.sh`, `scripts/enter_project.sh` |
| Database | `supabase/config.toml`, `supabase/migrations/` |
| CI | `.github/workflows/ci.yml`, `.github/workflows/docs.yml` |

## Commands

```sh
# Full quality pass (run before PR)
uv run ruff check && uv run ruff format --check && uv run ty check && uv run pytest --cov --cov-report=term-missing --cov-fail-under=80

# Individual
uv run ruff check              # lint
uv run ruff format             # format (apply)
uv run ruff format --check     # format (check only)
uv run ty check                # type check
uv run pytest --cov --cov-report=term-missing --cov-fail-under=80  # tests

# Docs
uv run zensical build --clean
uv run zensical serve

# Optional hygiene
gitleaks detect --no-git --source .
shellcheck scripts/*.sh
```

Coverage threshold: **80%** (enforced in CI and `mise.toml` `test` task).

## Expectations

- **Code:** typed, explicit Python; `ruff` is the formatting/lint source of truth; avoid new tools unless justified.
- **Architecture:** prefer the smallest counter-based design that solves the problem. Daily rollups are fine; raw per-hit event storage should require a clear need.
- **Tests:** add or update tests for behavior changes; prefer focused unit tests over broad integration scaffolding.
- **Docs:** update `README.md` and `docs/` if behavior or product direction changes; don't hand-edit `site/` (build artifact).
- **Commits:** use conventional commits (`cz commit` if available); PRs should include a short summary of commands run.
- **Secrets:** never commit credentials; `.env` is gitignored and local-only.

## Ponytail-style guidance

Use the principles from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) as a bias toward minimal, safe solutions.

Before adding code, stop at the first option that works:

1. Does this need to exist? If not, skip it.
2. Can Python stdlib handle it? Use that.
3. Can FastAPI, Supabase, or the platform already handle it? Use the native feature.
4. Is an existing dependency already installed? Reuse it.
5. Can the change stay very small? Prefer the smallest clear implementation.
6. Only then write new code, and keep it minimal.

Ponytail here means lazy, not negligent:

- never drop validation at trust boundaries
- never weaken error handling around storage or data integrity
- never trade away security for fewer lines
- never remove accessibility or clarity just to be clever

## Agent behavior

- Prefer minimal diffs; don't refactor unrelated files.
- Keep the implementation aligned with the product goal: simple named counters with safe concurrent increments and lightweight daily history.
- If tools are missing, run `mise install` and `uv sync` before trying workarounds.
- Keep CI workflows and local guidance in sync when changing related behavior.
- If a simpler native FastAPI or Supabase approach exists, prefer it over custom abstractions.
- When docs describe future architecture, clearly label it as planned if the code does not implement it yet.
