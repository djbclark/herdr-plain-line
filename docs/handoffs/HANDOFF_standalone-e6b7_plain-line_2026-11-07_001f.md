---
schema_version: 1
handoff_id: 001f
parent_handoff_ids: ["7cfe"]
lineage: deterministic
chain: [standalone-e6b7]
repo: herdr-plain-line
workspace: herdr-plain-line
branch: master
head_sha: 2e7e018bccd297f7d71a1b08d549d9af4274d166
created_at: 2026-11-07T15:23:09-0500
writer: cursor
---
# Handoff — plain-line finished; AI pass deferred

## The Goal

Ship a prefix-friendly command surface on the fork (done earlier), announce the plain-English idea upstream without a PR, and land a local Herdr plugin that runs three naming commands from one line. Optionally design (not implement) a later AI pass. Pane-move polish on the fork is out of scope once upstream plugins cover it.

## Where We Are

Chain `standalone-e6b7` is **finished** for the original goal. Plugin `local.plain-line` is linked and bound to `prefix+e`. Public repo [djbclark/herdr-plain-line](https://github.com/djbclark/herdr-plain-line) tracks `master` at `2e7e018`. Popup smoke in a disposable session created workspace `Plain Line Test`, then session and outer pane were cleaned up. Design for the AI iteration is in [`docs/AI_PASS.md`](../AI_PASS.md) (Goose-pattern host allowlist + helper JSON; no code yet). Pane-move uses installed **drovr** (`prefix+m` / `prefix+M`), not a command-surface fork chunk.

Parent handoff [`HANDOFF_…7cfe`](HANDOFF_standalone-e6b7_plain-line_2026-11-07_7cfe.md) is a historical snapshot (pre-remote, pre-smoke, pre-keybind). Prefer Tier 1 Current State and this file over 7cfe’s “Where We Are”.

Command-surface worktree `/Users/djbclark/src/herdr-worktrees/command-surface` remains clean at `ea4d9762` on fork `djbclark/herdr` only. Shared `/Users/djbclark/src/herdr` (`herdr-sleeper`, ahead 3, dirty graft `.gitignore`/`.ignore`) is **not** this chain’s to edit.

## What We Tried

Driving the popup by sending keys into a nested disposable TUI before dismissing onboarding failed (welcome/settings ate Enter). Retry with `onboarding = false` in the throwaway config succeeded. Popups are outside `pane.*` APIs; nested-client keyboard injection is the workable agent path.

An unsolicited upstream implementation PR was rejected as a delivery path (not a maintainer). Discussions without branch links were used instead.

Putting the plain-English line inside the herdr binary was rejected; plugin popup was the path.

## Key Decisions

Command surface stays on the fork only. Plain-line is a local plugin. AI pass is design-only for now, patterned on BarnOwl Goose (`goose-helper.py` JSON plan + host allowlist + `~/.config/goose` creds), not Block Goose CLI. Pane-move destination picker is already available via upstream plugins (drovr); do not start a fork chunk. Public GitHub for the plugin repo was approved and pushed.

## Decisions

- [decision] Refresh Tier 1 as finished at 2e7e018; rejected: leave stale or append Tier 2 completion note only; because loose audit showed wrong SHA and “AI_PASS uncommitted”; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_001f]]
- [decision] Delete both /var/tmp smoke repro dirs; rejected: keep logs; because sessions already deleted and Tier 1 carries the result; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_001f]]
- [decision] Leave pane-move to drovr on upstream; rejected: command-surface fork picker; because `herdr pane move` + plugin popups already exist and drovr is installed; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_001f]]
- [decision] AI pass = design/spec only for now; rejected: implement immediately; because popup path is proven and AI is a separate cut; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_001f]]
- [decision] Public GitHub repo djbclark/herdr-plain-line + push master; rejected: keep local-only or private; because operator chose public in /steps; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_001f]]
- [decision] Bind prefix+e to local.plain-line.open; rejected: leave unbound; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_001f]]
- [decision] Delete untracked autorename_nudge.py stub; rejected: leave or commit; because creating Grok session was gone from Paseo; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_001f]]
- [ruling] "For 1-9 don't make that a menu, just let user enter digits. It can be a 2-digit number." (djbclark, 2026-11-07)
- [ruling] "Queue a plugin" as a popup over tab rename, workspace rename, and workspace create, with no AI yet. (djbclark, 2026-11-07)
- [ruling] "Link it" so the popup can open, with no keybind change at that moment. (djbclark, 2026-11-07)

## Relations

- continues [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_7cfe]]
- decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_001f]]

## Evidence & Data

1. Plugin commits: `9646d2a`, `6482f90`, handoff `0c2e397`, AI pass docs `2e7e018`.
2. Command-surface: `aa57eed9`, `3e3d6a92`, `ea4d9762` on `origin/command-surface` (djbclark/herdr only).
3. Discussions (no branch links): [2283 comment](https://github.com/herdrdev/herdr/discussions/2283#discussioncomment-19459084), [5861](https://github.com/herdrdev/herdr/discussions/5861).
4. Smoke: disposable `repro-plain-line-20261107-092327`; line `new workspace Plain Line Test` → workspace `w2`; sessions deleted; `/var/tmp` dirs removed after loose.
5. Tests: `python3 -m unittest test_line.py` → 16 passed (re-verified in loose audit).
6. Keybind: `prefix+e` → `local.plain-line.open`; `herdr config check` → ok.
7. AI design prior art: BarnOwl Goose primary; NL→shell tools (cmdh/t2c) for confirm-before-run pattern only; drovr/pane-mover prove pane-move-as-plugin; Ideas [1674](https://github.com/herdrdev/herdr/discussions/1674) for native picker (no open PR).

## Operator Feedback

Lists to djbclark stay labelled (`A.`, `A1`). Do not hermes-ping the same event twice. Prefer Tier 1 + this handoff over 7cfe for resume.

## Where We're Going

1. **Default: no further work.** Chain is finished. If the operator wants more, implement the AI pass in this repo only per `/Users/djbclark/src/herdr-plain-line/docs/AI_PASS.md` (opt-in, allowlist, confirm); ask before coding.
2. Do not start a command-surface fork pane-move chunk; use drovr.
3. Do not open upstream PRs/issues for this feature set unless asked.
4. Push this handoff commit when the operator wants it on GitHub (committed locally by the writer; no auto-push for this repo under handoff rules).
5. Shared `~/src/herdr` dirt and ahead-3 commits are another session’s — do not touch.

## Detached jobs

none.

## Quick Start

```bash
git -C /Users/djbclark/src/herdr-plain-line status -sb
git -C /Users/djbclark/src/herdr-plain-line rev-parse HEAD   # expect 2e7e018…
herdr plugin action list --plugin local.plain-line
cd /Users/djbclark/src/herdr-plain-line && python3 -m unittest test_line.py
# optional next product cut:
# read docs/AI_PASS.md then ask before implementing
```

Tier 1: `~/.local/state/handoffs/chains/standalone-e6b7/SESSION_LOG.md`.
Predecessor Cursor baton session: no `$PASEO_AGENT_ID` (not a Paseo agent to archive).
