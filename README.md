# Plain English line

A local [Herdr](https://herdr.dev) plugin. It opens a short popup and runs one of three existing commands from a single plain-English line. Optional AI (off by default) can map other phrasing onto the same three actions after you confirm.

Upstream product idea: [herdrdev/herdr discussion 5861](https://github.com/herdrdev/herdr/discussions/5861). This repo is the working plugin; there is no upstream PR (djbclark is not a herdr maintainer).

## Commands

1. `rename this tab LABEL` / `rename tab LABEL` → `herdr tab rename`
2. `rename this workspace LABEL` / `rename workspace LABEL` → `herdr workspace rename`
3. `new workspace LABEL` / `create workspace LABEL` → `herdr workspace create --focus --label LABEL`

The rest of the line is the label, so spaces stay in the name. A blank line closes the popup. Anything else prints these forms and waits for Enter, unless AI is enabled (below).

The popup is a session-modal terminal, not a footer line. Herdr does not give that process `HERDR_TAB_ID` / `HERDR_WORKSPACE_ID`; the script reads `workspace_id` and `tab_id` from `HERDR_PLUGIN_CONTEXT_JSON`. It uses `HERDR_BIN_PATH` when set, else `herdr` on `PATH`. Needs `python3` on `PATH`. Popup placement exists since Herdr 0.7.0.

## Install

```bash
herdr plugin link /path/to/herdr-plain-line
herdr plugin action invoke local.plain-line.open
```

Optional keybind:

```toml
[[keys.command]]
key = "prefix+e"
type = "plugin_action"
command = "local.plain-line.open"
description = "plain english line"
```

Unlink with `herdr plugin unlink local.plain-line` (leaves this directory in place).

## Optional AI pass

Deterministic forms never call a model. Same lightweight Goose pattern as BarnOwl `:goose` (OpenAI-compatible chat + `~/.config/goose` credentials — not the Block Goose agent CLI).

1. Set `HERDR_PLAIN_LINE_AI=1` in the environment Herdr inherits.
2. Goose credentials in `~/.config/goose/` (`config.yaml` + `secrets.yaml`, mode `600`). On this Mac they match [pastebin.xvm.mit.edu](https://pastebin.xvm.mit.edu) (BarnOwl host): `rsync -a pastebin.xvm.mit.edu:.config/goose/{config.yaml,secrets.yaml} ~/.config/goose/`. Or inject `OPENROUTER_API_KEY` via `sudo-secretspec run`.
3. Optional model override: `HERDR_PLAIN_LINE_AI_MODEL`.
4. Non-literal lines go through `ai_helper.py`; the host allowlists only the three actions above and always asks `y/N` before running.

Design notes: [`docs/AI_PASS.md`](docs/AI_PASS.md).

## Tests

```bash
python3 -m unittest test_line.py test_ai_helper.py
```

## Upstream Herdr artifacts

1. [Discussion 5861](https://github.com/herdrdev/herdr/discussions/5861) — plain-English command line (product framing).
2. [Discussion 2283 comment](https://github.com/herdrdev/herdr/discussions/2283#discussioncomment-19459084) — related surface / naming notes (no branch links).
3. [Discussion 1674](https://github.com/herdrdev/herdr/discussions/1674) — native destination-picker ideas (pane-move stays on installed plugins such as drovr; not implemented here).

Fork experiments that touch the same problem space live on [frdminc/herdr](https://github.com/frdminc/herdr) (for example the [`command-surface`](https://github.com/frdminc/herdr/tree/command-surface) branch). They are not required to use this plugin.

## Related djbclark Herdr repos

| Repo | Role |
| --- | --- |
| [frdminc/herdr](https://github.com/frdminc/herdr) | Fork of [herdrdev/herdr](https://github.com/herdrdev/herdr) |
| [herdr-plain-line](https://github.com/frdminc/herdr-plain-line) | This plugin |
| [herdr-sleeper](https://github.com/frdminc/herdr-sleeper) | Sleep idle agent panes, wake later |
| [herdr4paseo](https://github.com/frdminc/herdr4paseo) | Terminal UI to watch/steer a Paseo agent from a pane |
| [paseo4herdr](https://github.com/djbclark/paseo4herdr) | Paseo plugin mirroring OMP agents that run in Herdr |
