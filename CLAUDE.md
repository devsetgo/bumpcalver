# CLAUDE.md

Repository operating rules for AI assistants and automated contributors.

## Scope

These instructions apply to the whole repository.
If another task-specific instruction file exists, follow both, and prefer the
more specific one when they conflict.

## Required Workflow

1. Read project standards before making changes:
   - CONTRIBUTING.md
   - docs/development-guide.md
   - docs/ai-instructions.md
2. Keep changes minimal and scoped to the request.
3. Never commit secrets, tokens, private keys, or credentials.
4. Do not run destructive git commands (for example: reset --hard, checkout --)
   unless explicitly requested.

## Validation Rules

1. For code, config, or build-logic changes, run:

   make tests

2. For documentation-only changes, run at least:

   make validate

3. If tooling auto-fixes files (pre-commit, formatters), rerun validation until
   it passes cleanly.

## Documentation and AI Notes Sync (Mandatory)

When documentation changes, AI notes must be reviewed and updated in the same
change set.

Required checks:

1. If any docs page or contributor guidance changes (for example README.md,
   CONTRIBUTING.md, docs/*.md, CHANGELOG.md), update docs/ai-instructions.md
   if needed.
2. If behavior/config/schema guidance changed, also update the packaged AI
   instruction sources under src/bumpcalver/assets/ai/*.md.
3. Do not treat AI notes as a follow-up task; keep them in the same PR.

## Versioning Rules

1. Use the configured bump flow instead of manual piecemeal version edits:

   make bump

2. Keep version declarations synchronized across files tracked by
   [tool.bumpcalver.file] in pyproject.toml.

## Commit and Push Rules

1. Use clear commit types for automation and history readability:
   - feat, fix, chore, docs, refactor, test, ci
2. Stage specific paths, not blind all-files adds.
3. Push only after explicit user confirmation.

## PR Readiness Expectations

Before opening or updating a PR:

1. Ensure validation has passed.
2. Ensure docs and AI notes are in sync.
3. Ensure no accidental generated noise or secret-adjacent files are included.
