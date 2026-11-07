---
schema_version: 1
handoff_id: 7cfe
parent_handoff_ids: []
lineage: none
chain: [standalone-e6b7]
repo: herdr-plain-line
workspace: herdr-plain-line
branch: master
head_sha: 6482f90f80a8a6fdbe06713b12e7bb7b464cb2da
created_at: 2026-11-07T09:15:45-0500
writer: grok
---
# Handoff — command surface and plain-line plugin

## The Goal

Give djbclark a prefix-activated command surface in a fork worktree, tell upstream about the idea without pointing at code, then add a separate local plugin popup that runs three existing Herdr commands from one plain-English line. No model calls in that plugin.

## Where We Are

The command-surface worktree at `/Users/djbclark/src/herdr-worktrees/command-surface` is branch `command-surface`, equal to `origin/command-surface`, feature head `ea4d976271b2c4d4749ef2ae215263f5ebd8a2e5`, clean. Origin is `https://github.com/djbclark/herdr.git`. Do not push that branch to `herdrdev/herdr`. This handoff is not in that worktree: herdr's `.gitignore` ignores `/docs/*` except `next`, `preview`, and `versions`.

This file lives in `/Users/djbclark/src/herdr-plain-line`, branch `master`. Before this file, that repo was clean at `6482f90f80a8a6fdbe06713b12e7bb7b464cb2da`. There is no remote, so the handoff commit stays on this machine. The plugin is linked and enabled as `local.plain-line`. No key was added. The popup has not been opened.

The shared checkout `/Users/djbclark/src/herdr` is `herdr-sleeper`, ahead 3, with a dirty `.gitignore` and an untracked `.ignore`. That dirt is not this session's. Its Tier 1 pointer is `chains/herdr-sleeper`. Do not write there.

`/Users/djbclark/src/djbclark-ade/skills/autorename/autorename_nudge.py` is untracked on purpose until this Grok session ends.

## What We Tried

An upstream pull request, draft or ready, is the wrong delivery. djbclark is not in `.github/MAINTAINERS` or `.github/APPROVED_CONTRIBUTORS`, and an unsolicited implementation PR is closed. Discussions were used instead, with no branch link.

Putting the plain-English line inside the herdr repo was rejected. Plugin v1 cannot draw a native footer or a context-menu item. The command surface stays in the client. The line is a separate plugin.

A popup process does not receive `HERDR_TAB_ID` or `HERDR_WORKSPACE_ID`. Reading those from the environment failed as a design. The script reads `workspace_id` and `tab_id` from `HERDR_PLUGIN_CONTEXT_JSON`. Action commands do get the separate variables. `workspace create --label` takes one argv value, unlike rename, which joins the rest of the line.

`cargo test --locked --lib` from this worktree only ran ghostty-vt. The herdr tests need `-p herdr`. `cargo nextest` is not installed. `just check` had no CI route for this linked worktree. `CARGO_TARGET_DIR` is `~/.cargo/target-shared`. Zig is `$HOME/.local/share/zig/zig-aarch64-macos-0.16.0/zig`. rustfmt must run with cwd the worktree and `--edition 2021`. `git` without `-C` hits the shared checkout.

The first ranking test expected the wrong order. "pane split" is a prefix and "zoom pane" is a word-start. The expected vector was fixed. The claim "the command-surface tests passed" was broader than the last run: after that one-line expected-order fix, `filter_ranks`, `help_and_the_command_surface`, `default_catalog_splits`, and `search_enter_runs` passed. The wider shell tests had passed on the compile immediately before that fix and were not re-run after it.

## Key Decisions

The command surface is client-side. One `keybind_inventory` feeds help and the surface. Search ranks exact, prefix, word-start, then substring, with shortcut matches four ranks worse, stable by catalog index. Help filtering stays substring and group-preserving. Typed digits 1 through 99 are not a menu. Escape peels layers. Unset rows stay visible. Custom commands go through `KeybindMatch::Command`. Dispatch clears the overlay before `record_binding`. Prefix+? stays help unless `ui.command_surface_replaces_help` is explicitly true. The context-menu Commands item is on by default. Anticipate is off when omitted, session-local, and preselects only. The default prefix in code is ctrl-b. djbclark's configured prefix is ctrl-a.

Rejected for the surface: click-to-run, a smaller help-sized popup, hiding unset rows, and a pane-move destination picker. `herdr pane move` already exists and has no keybind. That is a later chunk. Help-wrap issue 5379 stays closed. Screen mock-ups were offered and not made.

The plugin accepts six forms. The rest of the line is the label. A blank line exits 0. Anything else prints the forms, waits for Enter, and exits 1. Create uses `--focus`. There is no model call. The AI pass from discussion 5861 is a later iteration of this plugin, not of the herdr binary.

## Decisions

- [decision] Ship the command surface on the fork only; rejected: an upstream pull request; because djbclark is not a maintainer or an approved contributor and that PR would be closed; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_7cfe]]
- [decision] Post two discussions with no code link; rejected: commenting only on the existing thread, and rejected: linking the branch; because the plain-English line is a separate idea and the implementation was not being offered as a PR; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_7cfe]]
- [decision] Build the plain-English line as a local plugin popup; rejected: a core footer and rejected: a commit inside the herdr repo; because plugin v1 has no native non-terminal UI and the line was queued outside herdr; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_7cfe]]
- [decision] Read tab and workspace ids from HERDR_PLUGIN_CONTEXT_JSON; rejected: HERDR_TAB_ID and HERDR_WORKSPACE_ID; because popup launch env does not set those variables; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_7cfe]]
- [decision] Link local.plain-line and add no key; rejected: leaving it unlinked; because the popup cannot open until the plugin is registered; decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_7cfe]]
- [ruling] "For 1-9 don't make that a menu, just let user enter digits. It can be a 2-digit number." (djbclark, 2026-11-07)
- [ruling] "Leave the stub" for the untracked autorename nudge until this session ends. (djbclark, 2026-11-07)
- [ruling] "Queue a plugin" as a popup over tab rename, workspace rename, and workspace create, with no AI yet. (djbclark, 2026-11-07)
- [ruling] "Link it" so the popup can open, with no keybind change. (djbclark, 2026-11-07)

## Relations

- decided_in [[HANDOFF_standalone-e6b7_plain-line_2026-11-07_7cfe]]

## Evidence & Data

Command-surface commits, oldest first: `aa57eed9` feat: add a prefix+/ command surface; `3e3d6a92` feat: anticipate the next command-surface row; `ea4d9762` feat: rank command-surface matches from one keybind inventory. No pull request on the fork or on herdrdev/herdr for this branch.

Posted, with no branch link, and with an offer of screen mock-ups that were not made: [discussion comment 19459084](https://github.com/herdrdev/herdr/discussions/2283#discussioncomment-19459084) and [discussion 5861](https://github.com/herdrdev/herdr/discussions/5861).

Plugin files: `herdr-plugin.toml`, `line.py`, `test_line.py`, `README.md`, `.gitignore`. Commits `9646d2a` and `6482f90`. `python3 -m unittest test_line.py` in that directory: 16 passed. `herdr plugin link /Users/djbclark/src/herdr-plain-line` returned `plugin_linked` with `enabled: true`. `herdr plugin action list --plugin local.plain-line` listed action `open`. Installed Herdr is 0.9.5 at `/Users/djbclark/.herdr-wrapper/bin/herdr`. Popup placement has been in the source since before tag v0.7.0. `min_herdr_version` is `0.7.0`.

`~/s` links the plugin at `unsorted/herdr-plain-line`. The farm update also refreshed other `~/src` links that were already on disk.

Session notes, append-only: `/Users/djbclark/.grok/memory-v2/workspaces/herdr-e9bc6e6b/observations/_inbox/command-surface-session.md`, `plain-line-plugin.md`, and `plain-line-linked.md`. The first file's last sentence is stale. The later two correct it.

## Operator Feedback

Lists in replies to djbclark are labelled (`A.`, `A1.`), not dash bullets. Do not hermes-ping for the same event twice. The discussion ping, the ranking-commit ping, and one ping that the plugin was linked have already been sent.

## Where We're Going

1. Drive the popup once in a disposable Herdr session, never the default session. Follow `/Users/djbclark/src/herdr/.agents/skills/herdr-throwaway-repro/SKILL.md`. The plugin registry is global, so every `herdr` command in that test must select the disposable session. Do not run `--help` on herdr subcommands. Send one line such as `new workspace Plain Line Test` and confirm the workspace exists, then clean up only that session and its outer pane.
2. Leave the user's Herdr key config untouched unless djbclark asks. The snippet is in `/Users/djbclark/src/herdr-plain-line/README.md`.
3. Do not create a GitHub repo or push `herdr-plain-line` unless djbclark asks.
4. Do not open an upstream PR, issue, or discussion. Do not add mock-ups unless someone asks.
5. Leave the autorename stub untracked until the Grok session that created it has ended, then remove it if it is still untracked.
6. The AI pass is a later change to `/Users/djbclark/src/herdr-plain-line` only. Pane-move stays a separate chunk. Do not revive issue 5379.

## Detached jobs

none. This Grok session has no bigteam owner id. `claude_identity.py` returned no session id. Other job files under `~/.local/state/bigteam` are not this session.

## Quick Start

```bash
git -C /Users/djbclark/src/herdr-worktrees/command-surface status -sb
git -C /Users/djbclark/src/herdr-worktrees/command-surface rev-parse HEAD
git -C /Users/djbclark/src/herdr-plain-line status -sb
git -C /Users/djbclark/src/herdr-plain-line log --oneline -2
herdr plugin action list --plugin local.plain-line
cd /Users/djbclark/src/herdr-plain-line && python3 -m unittest test_line.py
```

Tier 1: `~/.local/state/handoffs/chains/standalone-e6b7/SESSION_LOG.md`.
