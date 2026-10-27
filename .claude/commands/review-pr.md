You review a documentation PR for **accuracy against the code it documents**, adherence to this repo's documentation conventions, and readability, and you critically assess all existing comments on the PR.

A full review layers independent passes — Claude's own doc-vs-code accuracy review (step 3), the mechanical checks (step 4), Codex (step 5), an independent doc-vs-code subagent (step 6), and a beginner-readability subagent (step 7) — then assesses the automated CodeRabbit comments GitHub already posted (step 8). Each pass has a different lens; all land in one consolidated PR comment (step 9), each under its own heading — never blended, and never dropped because a pass came back clean.

This is a **read-and-report** command: it never edits documentation on its own. Fixes happen in step 11 after the user approves.

## Inputs

- **PR number**: Use `$ARGUMENTS` as the PR number. If empty, detect from the current branch using `gh pr view --json number`.

## Sources of truth

Documentation claims are checked against code, never against other documentation:

| Claim about | Verify in |
|---|---|
| C++ API (classes, signatures, `requires` clauses, exceptions, `[[nodiscard]]`, const-ness, defaults) | `repos/genogrove/include/genogrove/**` (the Doxygen source for the reference stubs). Run `cd repos/genogrove && git pull origin main` first so the audit matches current `main`. |
| CLI options, help text, error messages, output format | `repos/genogrove/cli/src/*.cpp`, `repos/genogrove/cli/include/handlers/*.hpp` |
| Python API (classes, `py::arg` names and defaults, `.none(false)` → `TypeError`, GIL release, docstrings) | the sibling checkout `../pygenogrove/src/**` (`.def(...)`, `def_static`, `def_readwrite`, `py::call_guard<py::gil_scoped_release>`) |
| Versions | `repos/genogrove/CMakeLists.txt` (`project(genogrove VERSION …)`), `../pygenogrove` tag / `pyproject.toml`, PyPI |
| `.gg` format | `repos/genogrove/include/genogrove/io/gg_format.hpp`, `structure/grove/grove_serialize.ipp`, `grove_view.hpp` |

If `../pygenogrove` is missing or behind the version pinned in `source/requirements.txt`, say so in the report rather than guessing.

## Steps

### 1. Identify the PR

Determine the PR number from `$ARGUMENTS` or the current branch. Run `gh pr view <number> --json title,body,number,headRefName,baseRefName` to get PR details.

### 2. Gather context

- Read the PR diff with `gh pr diff <number>` and the list of changed files with `gh pr diff <number> --name-only`.
- Read `CLAUDE.md` for project conventions.
- Read the memory files for standing preferences (they carry overrides to the steps below, e.g. a temporary Codex skip, and several documentation rules: "How It Works" sections are mechanics-only; no "Issues filed" section in the CHANGELOG; no millisecond/second-resolution timestamp framing for `Numeric`; 0-based closed is the grove coordinate convention).
- Read `tools/check_tab_parity.py`'s header for the tab-layout and "Methods" conventions.

### 3. Review the documentation against the code (Claude pass)

For **every factual claim the diff adds or changes**, open the source it describes and confirm it. Do not trust the PR body, the old text, or another doc page. Focus on:

- **Signatures and names**: method names, parameter names and order, return types, template heads, `requires` clauses, which overloads exist on `grove` vs only on `graph_overlay` / `grove_view`, which Python methods exist on which grove class (`Grove` vs `BedGrove` / `GffGrove` vs the views).
- **Behavioural claims**: what throws (`std::invalid_argument` vs `std::runtime_error` vs `std::out_of_range`; `TypeError` vs `ValueError` vs `RuntimeError` in Python), what returns empty vs throws on null/`None`, what is `static`, what releases the GIL, complexity claims (`O(…)`), thread-safety statements.
- **Coordinates**: every conversion must land in the grove's **0-based closed** convention — BED/BAM/VCF `[s, e)` → `[s, e-1]`, GFF 1-based `[s, e]` → `[s-1, e-1]`, FASTA `fetch` is half-open (`fetch(s, e+1)` from a grove key, `fetch(s-1, e)` from GFF). Check the arithmetic in every snippet and comment, not just the prose table.
- **Code snippets**: would they compile / run as shown? Includes and namespace aliases present, variables defined, iterator/iterable semantics right (e.g. `QueryResult` has no `__getitem__`), guards present where the text says they are needed (`consumes_reference()`, overlap checks before `size_t` subtraction).
- **Version strings**: `source/conf.py` `release` / `pygenogrove_release`, `README.md` badge, `source/requirements.txt` pin, `cli.md` `--version` sample all agree with each other and with the sources.
- **Tab parity of substance**: the C++ and Python tabs of a section describe the same thing; where one language lacks a feature the tab says so explicitly (and correctly) rather than being silent or inventing a counterpart.
- **Conventions**: per-section tab layout on converted pages; "How It Works" limited to mechanics with history/compat in its own section; class sections carry a field table then a "Methods" list of the class's own helpers (no "Methods: none" wording; a class with no methods simply has no list, plus one sentence on what to use instead if the other language has a helper the reader will look for); examples use the simplest payload that makes the point.

Do NOT flag: wording taste, heading capitalisation, or things that are clearly intentional. Do NOT run `make html` — the user builds himself; phrase build verification as something he should run.

### 4. Run the mechanical checks

- `python3 tools/check_tab_parity.py source` — every tab-set has both tabs; converted pages keep headings outside tabs.
- Stale references: `grep` the diff's removed/renamed pages and anchors across `source/` (`{doc}` targets, `(#anchor)` links, toctree entries) and confirm every target still exists.
- Coordinate sweep: `grep -rnE 'end - 1|start - 1|end \+ 1|interval\((e|entry|v|aln)\.' source/` and check each hit against the convention above (this catches regressions outside the diff that the diff's statements now contradict).
- Version sweep: `grep -rnE '0\.[0-9]+\.[0-9]+' source/conf.py README.md source/cli.md source/requirements.txt`.

Report these under their own `### Mechanical checks` subsection of the Claude review in step 9.

### 5. Run an independent Codex review

> **Standing override:** memory may record a temporary Codex skip. If so, skip this step entirely and move on.

- Locate the companion script: `ls -d ~/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs 2>/dev/null | sort -V | tail -1`. If none is found, skip and note "Codex review skipped (companion not installed)" in step 10.
- Ensure the PR branch is checked out (`gh pr checkout <number>` if `HEAD` is not the PR branch).
- Run `node "<companion-script>" review --base <base-branch> --scope branch --wait`. Tell Codex, in the prompt, that this is a **documentation** repo and that the review should verify statements against `repos/genogrove/include`, `repos/genogrove/cli` and `../pygenogrove/src`, flagging anything that does not line up with the code; style is out of scope.
- If Codex is not authenticated, skip and note "Codex review skipped (Codex not authenticated — run `codex login`)".
- Capture the output verbatim for step 9. Do not fix or rewrite its findings.

### 6. Run the independent doc-vs-code subagent

Dispatch a fresh general-purpose subagent (it inherits none of your conclusions — give it the diff and the sources, not your findings) with this brief:

> You are reviewing a documentation PR for the genogrove C++ library and its Python bindings. The diff is in `<path to saved gh pr diff>`. The documentation must agree with the code: C++ headers under `repos/genogrove/include/genogrove/`, the CLI under `repos/genogrove/cli/`, Python bindings under `../pygenogrove/src/`. For every API name, signature, parameter, default, exception type, complexity claim, GIL statement, coordinate conversion and code snippet the diff adds or changes, find the defining source and state whether the documentation matches. Report only mismatches and unverifiable claims, one line each: `file:line — claim — what the code says (source file:line)`. Do not comment on style. Do not run the Sphinx build. End with a one-line verdict: how many claims checked, how many mismatches.

Capture its output for step 9 under `## Independent doc-vs-code pass`, substantially verbatim.

### 7. Run the beginner-readability subagent

Dispatch a second fresh general-purpose subagent with this brief:

> Read the documentation pages changed in this PR (list them) as a **complete newcomer**: you know what a genome, a chromosome and a BED/GFF file are, you can copy a command into a terminal and edit a few lines of a script, but you have little programming knowledge — no templates, pointers, iterators, GIL, "O(n)", "const", "predicate" or "overload" unless the page explains them where they appear. You have never heard of genogrove. For each page report, one line each: the first sentence or snippet where you would be lost, every term or concept used before the page (or a link right there) explains it, every example you could not run by pasting it, every step the page assumes you already did, and anything one language tab explains that the other does not. Say which tab you were reading. Terse format: `file:line — <where I got lost>. <what would have helped>.` End with `Clear enough. Ship.` only if you could follow every page from top to bottom.

Treat this pass's findings as real even when they look obvious to an expert; its purpose is to catch the jargon and skipped steps the other passes are blind to.

Capture its output for step 9 under `## Beginner-readability pass`.

### 8. Assess existing PR comments

Fetch all comments on the PR:
- Review comments: `gh api repos/genogrove/docs/pulls/<number>/comments --paginate`
- Issue-level comments: `gh api repos/genogrove/docs/issues/<number>/comments`
- Review summaries: `gh api repos/genogrove/docs/pulls/<number>/reviews`

For each comment, critically assess whether it raises a valid concern **by checking the code it is about**, not by reading the comment alone:
- **Is it a real inaccuracy** (the doc says X, the code does Y)? Flag for action with the source location.
- **Is it a meaningful clarity improvement within the PR's scope?** Flag for action if warranted.
- **Is it a wording preference with no accuracy impact?** Skip unless it aligns with the repo's conventions.
- **Is it already addressed by a later commit?** Note as resolved.
- **Is it from CodeRabbit or Codex?** Evaluate on merit — they surface real mismatches and also false positives (e.g. they may not know the `.none(false)` → `TypeError` mapping or the 0-based closed convention).

### 9. Post review on the PR

**Reply to each inline comment** — for each review comment, reply in its thread with `gh api repos/genogrove/docs/pulls/<number>/comments/<comment_id>/replies --method POST -f body="..."`, giving a verdict (**Address**, **Skip**, or **Discuss**) and the reasoning, with the source location that decides it.

**Post ONE consolidated review comment** (`gh pr comment <number> --body "..."`) with every pass under its own `##` heading. Do not blend sources or repeat the inline assessments:

- `## Claude review` — your step 3 findings, categorised as **Inaccuracy** (doc contradicts code; cite `source file:line`), **Convention violation** (contradicts CLAUDE.md, the memory rules or the tab/Methods layout), **Suggestion** (optional). Terse, one line per finding: `file:line — <problem>. <fix>.`; prefix `🔴 wrong:` / `🟡 unclear:` / `🔵 nit:` / `❓ q:` when severities are mixed within a category. Nest `### Mechanical checks` (step 4) under this heading.
- `## Independent doc-vs-code pass` — step 6, substantially verbatim, with a one-line note that it is an independent subagent run as part of the workflow.
- `## Beginner-readability pass` — step 7, substantially verbatim.
- `## Codex Review` — step 5, substantially verbatim, noted as an automated independent review by OpenAI Codex.

**A pass that ran and found nothing still gets its heading** with a one-line "No mismatches found" / "Clear enough. Ship." **Omit a heading only when the pass never ran**, and put the reason in its place (e.g. `## Codex Review` — "Skipped (companion not installed)").

Post as one `gh pr comment` call with all sections in the single `--body`.

### 10. Report findings to the user

Present the same findings in the conversation, noting which passes ran and which were skipped and why. If any pass found a statement that contradicts the code, surface it first — that is the point of this review.

**Account for EVERY finding.** Build one disposition ledger over all points raised by all passes (steps 3–8), each with **Address**, **Skip/Exclude** (one-line reason), or **Discuss**. Never silently drop a finding.

There is no label, QC-checklist or CHANGELOG step here: the docs repo does not label PRs, has no PR template, and writes its CHANGELOG entry on `main` after merge via `/merge-pr`.

### 11. Make changes if approved

Wait for the user's confirmation before editing any documentation. Apply approved fixes **one page at a time** so the user can stop and ask between edits; answer any question raised on a rejected edit before continuing. Do not run `make html`; ask the user to build. Push to the PR branch, then drive the step-10 ledger to closure: every **Address** point ends up fixed (cite the commit) or flipped to **Skip/Exclude** with the reason recorded. Post the final ledger on the PR.