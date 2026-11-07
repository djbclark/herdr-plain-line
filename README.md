# Plain English line

A local Herdr plugin. It opens a short popup and runs one of three existing commands.

A1. `rename this tab LABEL` and `rename tab LABEL` run `herdr tab rename`.
A2. `rename this workspace LABEL` and `rename workspace LABEL` run `herdr workspace rename`.
A3. `new workspace LABEL` and `create workspace LABEL` run `herdr workspace create --focus --label LABEL`.

The rest of the line is the label, so spaces stay in the name. A blank line closes the popup. Anything else prints these forms and waits for Enter, unless AI is enabled (below).

The popup is a session-modal terminal. It is not a line drawn in the shell footer. Herdr does not give that process `HERDR_TAB_ID` or `HERDR_WORKSPACE_ID`. The script reads `workspace_id` and `tab_id` from `HERDR_PLUGIN_CONTEXT_JSON`. It uses `HERDR_BIN_PATH` when Herdr sets it, and `herdr` on `PATH` otherwise. `python3` must be on `PATH`. Popup placement has been in Herdr since 0.7.0. This machine's installed Herdr is 0.9.5.

## Optional AI pass

Deterministic forms never call a model. To map other plain English onto the same three actions:

B1. Set `HERDR_PLAIN_LINE_AI=1` in the environment Herdr inherits (or export it before starting Herdr).
B2. Reuse Goose credentials in `~/.config/goose/` (`GOOSE_PROVIDER` / `GOOSE_MODEL` / API key), same as BarnOwl `:goose`.
B3. Optional model override: `HERDR_PLAIN_LINE_AI_MODEL`.
B4. The popup shows a short plan and asks `y/N` before every AI-derived action. Model output outside the three-action allowlist is refused.

Design notes: [`docs/AI_PASS.md`](docs/AI_PASS.md).

## Install

Link it once. That registers the plugin for this user, in every session. It does not add a key:

```bash
herdr plugin link /Users/djbclark/src/herdr-plain-line
herdr plugin action invoke local.plain-line.open
```

To put it on a key yourself, add this to your Herdr key config and pick the key:

```toml
[[keys.command]]
key = "prefix+e"
type = "plugin_action"
command = "local.plain-line.open"
description = "plain english line"
```

Remove the registration with `herdr plugin unlink local.plain-line`. That leaves this directory in place.
