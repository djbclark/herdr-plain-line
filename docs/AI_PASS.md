# AI pass — design (no implementation yet)

Date: 2026-11-07  
Repo: [djbclark/herdr-plain-line](https://github.com/djbclark/herdr-plain-line)  
Product intent: [herdrdev/herdr discussion 5861](https://github.com/herdrdev/herdr/discussions/5861)  
v1 today: deterministic six forms in `line.py` (no model). This doc is the later iteration.

## Goal

When the line is not one of the six literal forms, optionally ask an LLM to map plain English onto a **small allowlisted set of Herdr CLI actions**, show what it will do, and run it only after the same safety rules BarnOwl `:goose` uses. Deterministic forms stay first and never call a model.

## Non-goals (this pass)

1. Calling the Block/Codename Goose agent CLI (`goose run`, recipes, tools).
2. Changing the herdr binary or the command-surface worktree.
3. Free-form shell, `pane run`, or arbitrary plugin actions from model text.
4. Native footer UI (plugin v1 still has no footer; keep the popup).

## Architecture (copy BarnOwl Goose, adapt to a popup)

Mirror [djbclark/barnowl](https://forgejo.mit.edu/djbclark/barnowl) `BarnOwl::Module::Goose` + `goose-helper.py`:

| Layer | BarnOwl | Plain-line AI |
| --- | --- | --- |
| UI host | `Goose.pm` (`:goose`, confirm prompt, allowlist) | `line.py` popup (parse → maybe AI → confirm → `herdr …`) |
| Helper | `goose-helper.py` (stdin JSON → LLM → stdout JSON) | `ai_helper.py` (same shape; stdlib-only) |
| Credentials | `~/.config/goose/config.yaml` + `secrets.yaml` / `GOOSE_*` | **Same files** (already on this machine for BarnOwl) |
| Trust boundary | Host allowlist beats model `needs_confirmation` | Same |

Do **not** shell out to Block Goose. BarnOwl already speaks OpenAI-compatible chat completions itself; reuse that thin client pattern (and optionally later extract a shared module). The jail/broker path in BarnOwl is Athena-specific; skip it for Herdr on the Mac unless we later need it.

### Control flow

```text
readline
  → blank → exit 0
  → match six forms → run herdr (today) → exit
  → else if AI disabled / no key → print forms, wait Enter, exit 1 (today)
  → else → ai_helper.py with context JSON
       ← { explanation, action, args, needs_confirmation, confirmation_prompt }
  → host reject if action not allowlisted
  → if needs_confirmation (host OR model): print plan, y/N on same popup
  → run mapped herdr argv with HERDR_BIN_PATH / context ids
```

### Context JSON (stdin to helper)

Minimum:

```json
{
  "request": "<user line>",
  "workspace_id": "...",
  "tab_id": "...",
  "workspace_label": "...",
  "tab_label": "...",
  "allowlisted_actions": ["tab_rename", "workspace_rename", "workspace_create"],
  "model_override": ""
}
```

Optional later: focused pane cwd, short workspace/tab list (capped, sanitized). Treat every label/cwd string as **untrusted data** (same NFKC / control-char rules as BarnOwl `_s` / `_f`).

### Helper stdout schema

```json
{
  "explanation": "string for the popup",
  "action": "tab_rename | workspace_rename | workspace_create | none",
  "label": "string or null",
  "needs_confirmation": true,
  "confirmation_prompt": "Rename this tab to Foo? [y/N]: "
}
```

`action: "none"` means answer-only (explanation, no herdr call).

### Host allowlist (authoritative)

Only these map to CLI (same as v1):

1. `tab_rename` → `herdr tab rename <tab_id> <label>`
2. `workspace_rename` → `herdr workspace rename <workspace_id> <label>`
3. `workspace_create` → `herdr workspace create --focus --label <label>`

Host rules (copy Goose.pm spirit):

1. Unknown `action` → refuse, show explanation or forms.
2. Empty/oversized label → refuse (cap length; printable text only).
3. Missing tab/workspace id when required → refuse (same as today’s `MissingId`).
4. `needs_confirmation` forced **true** for any AI-derived action that is not a pure restatement of an explicit six-form request (default: confirm all AI actions in v1 of the AI pass; relax later for unambiguous creates if desired).
5. Pending confirm TTL (~300s) if we keep a second line of interaction; otherwise confirm inline in one popup turn.

### Config / enablement

1. Reuse BarnOwl’s Goose provider settings (`GOOSE_PROVIDER`, `GOOSE_MODEL`, API key in secrets).
2. Plugin-local opt-in: e.g. `HERDR_PLAIN_LINE_AI=1` or a file under the plugin config dir from `herdr plugin config-dir local.plain-line`. Default **off** so linked users keep “no model calls” until they enable it.
3. Optional model override env parallel to BarnOwl’s `goose_model` variable.

### UX in the popup

1. Keep the existing prompt line for deterministic forms.
2. On AI path: show a short “thinking…” line, then either run or ask `y/N`.
3. On failure (no key, HTTP error, bad JSON): print a one-line error + the six forms; do not hang the session.
4. Never block the Herdr UI process beyond the popup’s own PTY (helper is a child of the popup process; fine for a modal).

### Tests (when implementing)

1. Keep all current `test_line.py` cases green (deterministic path unchanged).
2. Add helper unit tests with a fake LLM (fixture JSON), parallel to barnowl `t/test_helper.py`.
3. Add host tests: allowlist rejection, confirm gating, id missing, AI disabled.

### Implementation sketch (files only; not written yet)

1. `ai_helper.py` — adapted subset of barnowl `goose-helper.py` (config load, chat POST, `extract_json_response`, sanitizers, smaller system prompt tied to Herdr actions).
2. `line.py` — after `unknown`, optional AI branch; confirm; map to existing `command_argv`.
3. `herdr-plugin.toml` / README — document opt-in and that AI is optional.
4. Prefer **copy-and-trim** from barnowl over a hard dependency on the barnowl tree (Herdr users may not have barnowl installed). Later: extract a tiny shared `goose_llm_client` if both repos want one source.

## Prior art reviewed (2026-11-07)

### Copy directly / closely

1. **BarnOwl Goose** ([forgejo barnowl](https://forgejo.mit.edu/djbclark/barnowl), `lib/BarnOwl/Module/Goose.pm` + `goose-helper.py`) — primary template: async helper, JSON plan, host allowlist, confirm, untrusted-context sanitization, Goose config files. Best fit; same operator, same credentials already present.

### Copy patterns only (not drop-in)

1. **NL → command with human review before exec** — [pgibler/cmdh](https://github.com/pgibler/cmdh), [t2c gist](https://gist.github.com/nachoal/01c40b5facac99efd064f9cbd1a93b92), [CommandLineHelper](https://github.com/jayrajpamnani/CommandLineHelper): show proposed command, user confirms. Useful UX pattern; their target is free shell, which we must **not** allow.
2. **Discussion 5861** — product framing: ordinary English first; AI only when “more complicated than one action.”

### Looked at; weak or wrong shape for this pass

1. **[javAlborz/tmux-ai-session-name](https://github.com/javAlborz/tmux-ai-session-name)** — renames tmux windows from agent session metadata; not NL→action. Do not copy.
2. **Block Goose / `goose run --recipe … --output-format json`** — full agent runtime; too heavy for a one-line popup. Reuse **credential file layout** only, not the CLI.
3. Generic “herdr plugin + AI” GitHub hits (navigator, ccxray, jig worktree tools) — different problems (jump, badges, worktrees), not plain-English action mapping.

## Open design choices (decide when implementing)

1. Confirm **every** AI action vs only ambiguous/destructive ones (Goose splits read-only vs the rest; our three actions are all mutating → lean “always confirm” at first).
2. Whether AI may propose multi-step plans (Goose allows `commands[]`) or **one** action only (safer for v1).
3. Whether to grow allowlist (e.g. focus workspace, close tab) in the same pass or keep the three-command set.
4. Shared Python module with barnowl vs duplicated trimmed helper.

## Success criteria

1. Six forms still work with AI disabled and with no API key.
2. With AI enabled, a line like “call this tab build logs” renames the current tab after confirm, using `HERDR_PLUGIN_CONTEXT_JSON` ids.
3. Model output cannot run anything outside the allowlist even if it asks to.
4. No herdr core change; no upstream PR required.
