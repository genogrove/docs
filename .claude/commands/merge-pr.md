Merge an open pull request, update the CHANGELOG, and clean up branches.

## Input

The argument `$ARGUMENTS` is the PR number (e.g., `81`). If not provided, detect the PR from the current branch using `gh pr view`.

## Steps

### 1. Gather PR details

Run `gh pr view <number>` to get the PR title, body, and linked issues. Identify:
- The PR number and title
- Any issues it closes (look for "Closes #N", "closes #N", "Fixes #N", etc. in the PR body and commit messages)
- The branch name

### 2. Merge the PR

```
gh pr merge <number> --admin --merge
```

### 3. Update local main

```
git checkout main && git pull
```

### 4. Update CHANGELOG.md

Add an entry under today's date following the format in CLAUDE.md:

- If today's date heading already exists, add to it. Otherwise create a new heading.
- Categorize changes under `### Added`, `### Changed`, or `### Fixed` as appropriate.
- Reference the PR number with a link: `[#N](https://github.com/genogrove/docs/pull/N)`
- If the PR closes issues, note them: `closes [#N](https://github.com/genogrove/docs/issues/N)`
- Keep entries concise — one bullet per logical change.

Commit and push the CHANGELOG update directly to main.

### 5. Clean up branches

Delete both the local and remote feature branches:

```
git branch -d <branch-name>
git push origin --delete <branch-name>
```