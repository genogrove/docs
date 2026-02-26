# CLAUDE.md — Project Instructions

## Workflow

- **Every change must go through a PR.** Do not commit directly to `main`. Create a branch, open a PR, and wait for it to be merged.
- **After a PR is merged**, update `CHANGELOG.md`:
  - Add an entry under today's date (create a new date heading if one doesn't exist yet).
  - Reference the merged PR number and any issues it resolves (e.g., `- [#20](...)`, `Closes #10`).
  - If the PR resolves an issue, note it as resolved.

## CHANGELOG format

```markdown
## YYYY-MM-DD

### Fixed
- Fixed wrong API signatures in `graph_manipulation.md` ([#21](url), closes [#20](url))

### Added
- ...

### Changed
- ...

### Issues filed
- [#N](url) — description
```

## Version updates

When the genogrove version is updated (e.g., submodule bump), update the version in **both** places:
- `source/conf.py` — `release = "X.Y.Z"`
- `README.md` — version badge (`genogrove-vX.Y.Z`)

## Building docs

- The user will run `make clean` and `make html` himself after making changes to verify no Sphinx build warnings before committing.

## Documentation audit

Use `/docs-sync` to run a documentation audit. See `.claude/commands/docs-sync.md` for the full process.