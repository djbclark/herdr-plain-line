#!/usr/bin/env python3
"""One plain-English line for three Herdr commands.

A popup process does not receive HERDR_TAB_ID or HERDR_WORKSPACE_ID. Those ids
are read from HERDR_PLUGIN_CONTEXT_JSON. Deterministic six forms never call a
model. Optional AI (HERDR_PLAIN_LINE_AI=1) maps other lines onto the same three
actions after confirm.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

PLUGIN_ID = "local.plain-line"
ENTRYPOINT = "line"
LABEL_MAX = 200
ALLOWLISTED_ACTIONS = ("tab_rename", "workspace_rename", "workspace_create")

FORMS = (
    "rename this tab LABEL\n"
    "rename tab LABEL\n"
    "rename this workspace LABEL\n"
    "rename workspace LABEL\n"
    "new workspace LABEL\n"
    "create workspace LABEL\n"
)

_LINE = re.compile(
    r"^(?P<kind>rename\s+this\s+tab|rename\s+tab|"
    r"rename\s+this\s+workspace|rename\s+workspace|"
    r"create\s+workspace|new\s+workspace)\s+(?P<label>\S.*)$",
    re.IGNORECASE,
)


class ContextError(Exception):
    pass


class MissingId(Exception):
    def __init__(self, which: str) -> None:
        super().__init__(which)
        self.which = which


class AiRefuse(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def parse_line(text: str) -> tuple[str, str | None]:
    """Return (kind, label). kind is empty, unknown, or a command name."""
    raw = text.replace("\r\n", "\n")
    if raw.endswith("\n"):
        raw = raw[:-1]
    if raw.strip() == "":
        return ("empty", None)
    match = _LINE.match(raw)
    if match is None:
        return ("unknown", None)
    folded = " ".join(match.group("kind").lower().split())
    if folded in {"rename this tab", "rename tab"}:
        kind = "tab_rename"
    elif folded in {"rename this workspace", "rename workspace"}:
        kind = "workspace_rename"
    elif folded in {"new workspace", "create workspace"}:
        kind = "workspace_create"
    else:
        return ("unknown", None)
    return (kind, match.group("label"))


def _optional_str(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def context_payload(env: dict[str, str]) -> dict:
    data: dict = {}
    raw = env.get("HERDR_PLUGIN_CONTEXT_JSON")
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as err:
            raise ContextError(f"HERDR_PLUGIN_CONTEXT_JSON is not JSON: {err}") from err
        if not isinstance(parsed, dict):
            raise ContextError("HERDR_PLUGIN_CONTEXT_JSON is not an object")
        data = parsed
    workspace_id = _optional_str(env.get("HERDR_WORKSPACE_ID")) or _optional_str(
        data.get("workspace_id")
    )
    tab_id = _optional_str(env.get("HERDR_TAB_ID")) or _optional_str(data.get("tab_id"))
    return {
        "workspace_id": workspace_id,
        "tab_id": tab_id,
        "workspace_label": _optional_str(data.get("workspace_label")),
        "tab_label": _optional_str(data.get("tab_label")),
    }


def context_ids(env: dict[str, str]) -> tuple[str | None, str | None]:
    payload = context_payload(env)
    return (payload["workspace_id"], payload["tab_id"])


def command_argv(
    kind: str,
    label: str,
    workspace_id: str | None,
    tab_id: str | None,
    bin_path: str,
) -> list[str]:
    if kind == "tab_rename":
        if not tab_id:
            raise MissingId("tab")
        return [bin_path, "tab", "rename", tab_id, label]
    if kind == "workspace_rename":
        if not workspace_id:
            raise MissingId("workspace")
        return [bin_path, "workspace", "rename", workspace_id, label]
    if kind == "workspace_create":
        # --label takes one argv value. --focus matches "new workspace".
        return [bin_path, "workspace", "create", "--focus", "--label", label]
    raise ValueError(kind)


def open_argv(bin_path: str) -> list[str]:
    return [
        bin_path,
        "plugin",
        "pane",
        "open",
        "--plugin",
        PLUGIN_ID,
        "--entrypoint",
        ENTRYPOINT,
        "--placement",
        "popup",
    ]


def herdr_bin(env: dict[str, str]) -> str:
    return env.get("HERDR_BIN_PATH") or "herdr"


def ai_enabled(env: dict[str, str]) -> bool:
    return env.get("HERDR_PLAIN_LINE_AI", "").strip().lower() in {"1", "true", "yes", "on"}


def sanitize_label(label: object) -> str:
    text = unicodedata.normalize("NFKC", str(label or ""))
    cleaned: list[str] = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in "\n\r\t":
            cleaned.append(" ")
            continue
        if cat.startswith("C") or cat in ("Zl", "Zp"):
            continue
        cleaned.append(ch)
    out = " ".join("".join(cleaned).split())
    if len(out) > LABEL_MAX:
        raise AiRefuse(f"label longer than {LABEL_MAX} characters")
    if not out:
        raise AiRefuse("empty label")
    if not all(ch.isprintable() for ch in out):
        raise AiRefuse("label has non-printable characters")
    return out


def validate_ai_plan(
    plan: dict,
    workspace_id: str | None,
    tab_id: str | None,
) -> tuple[str, str | None]:
    """Return (action, label). action may be 'none'."""
    if not isinstance(plan, dict):
        raise AiRefuse("AI helper returned a non-object")
    if plan.get("error"):
        raise AiRefuse(str(plan["error"]))
    action = str(plan.get("action") or "none").strip().lower()
    if action == "none":
        return ("none", None)
    if action not in ALLOWLISTED_ACTIONS:
        raise AiRefuse(f"action not allowlisted: {action}")
    label = sanitize_label(plan.get("label"))
    if action == "tab_rename" and not tab_id:
        raise MissingId("tab")
    if action == "workspace_rename" and not workspace_id:
        raise MissingId("workspace")
    return (action, label)


def confirm_yes(answer: str) -> bool:
    return answer.strip().lower() in {"y", "yes"}


def default_ai_call(request: str, env: dict[str, str], payload: dict) -> dict:
    helper = Path(__file__).resolve().with_name("ai_helper.py")
    body = {
        "request": request,
        "workspace_id": payload.get("workspace_id") or "",
        "tab_id": payload.get("tab_id") or "",
        "workspace_label": payload.get("workspace_label") or "",
        "tab_label": payload.get("tab_label") or "",
        "allowlisted_actions": list(ALLOWLISTED_ACTIONS),
        "model_override": env.get("HERDR_PLAIN_LINE_AI_MODEL", "").strip(),
    }
    try:
        completed = subprocess.run(
            [sys.executable, str(helper)],
            input=json.dumps(body),
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except FileNotFoundError as err:
        raise AiRefuse(f"could not run ai helper: {err}") from err
    except subprocess.TimeoutExpired as err:
        raise AiRefuse("AI helper timed out") from err
    raw = (completed.stdout or "").strip()
    if not raw:
        err = (completed.stderr or "").strip() or f"exit {completed.returncode}"
        raise AiRefuse(f"AI helper produced no output: {err}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as err:
        raise AiRefuse(f"AI helper returned bad JSON: {err}") from err
    if not isinstance(parsed, dict):
        raise AiRefuse("AI helper returned a non-object")
    return parsed


def run_argv(argv: list[str]) -> int:
    try:
        completed = subprocess.run(argv, check=False)
    except FileNotFoundError:
        print(f"could not run {argv[0]}", file=sys.stderr)
        return 127
    return completed.returncode


def hold_closed(stdin: object, stdout: object) -> None:
    stdout.write("press enter to close\n")
    stdout.flush()
    stdin.readline()


def show_forms_and_hold(stdin: object, stdout: object, stderr: object, message: str) -> int:
    stderr.write(f"{message}\n")
    stderr.write(FORMS)
    hold_closed(stdin, stdout)
    return 1


def run_ai_branch(
    request: str,
    env: dict[str, str],
    stdin: object,
    stdout: object,
    stderr: object,
    run,
    ai_call,
) -> int:
    stdout.write("thinking…\n")
    stdout.flush()
    try:
        payload = context_payload(env)
        plan = ai_call(request, env, payload)
        action, label = validate_ai_plan(plan, payload["workspace_id"], payload["tab_id"])
    except MissingId as err:
        return show_forms_and_hold(
            stdin, stdout, stderr, f"no {err.which} id in the plugin context"
        )
    except (AiRefuse, ContextError) as err:
        return show_forms_and_hold(stdin, stdout, stderr, str(err))

    explanation = str(plan.get("explanation") or "").strip()
    if explanation:
        stdout.write(f"{explanation}\n")
        stdout.flush()

    if action == "none" or label is None:
        hold_closed(stdin, stdout)
        return 0

    prompt = str(plan.get("confirmation_prompt") or "").strip() or (
        f"Run {action} with label {label!r}? [y/N]: "
    )
    # Host forces confirm for every AI-derived mutating action.
    stdout.write(f"{prompt}")
    stdout.flush()
    if not confirm_yes(stdin.readline()):
        stdout.write("cancelled\n")
        stdout.flush()
        return 0

    bin_path = herdr_bin(env)
    try:
        command = command_argv(
            action, label, payload["workspace_id"], payload["tab_id"], bin_path
        )
    except MissingId as err:
        return show_forms_and_hold(
            stdin, stdout, stderr, f"no {err.which} id in the plugin context"
        )
    code = run(command)
    if code != 0:
        hold_closed(stdin, stdout)
    return code


def main(
    argv: list[str],
    env: dict[str, str],
    stdin: object,
    stdout: object,
    stderr: object,
    run,
    ai_call=None,
) -> int:
    bin_path = herdr_bin(env)
    if len(argv) > 1 and argv[1] == "--open":
        return run(open_argv(bin_path))
    stdout.write(
        "rename this tab LABEL  |  rename this workspace LABEL  |  new workspace LABEL\n> "
    )
    stdout.flush()
    raw_line = stdin.readline()
    kind, label = parse_line(raw_line)
    if kind == "empty":
        return 0
    if kind == "unknown" or label is None:
        if ai_enabled(env):
            request = raw_line.replace("\r\n", "\n")
            if request.endswith("\n"):
                request = request[:-1]
            return run_ai_branch(
                request,
                env,
                stdin,
                stdout,
                stderr,
                run,
                ai_call or default_ai_call,
            )
        return show_forms_and_hold(stdin, stdout, stderr, "unrecognized line")
    try:
        workspace_id, tab_id = context_ids(env)
        command = command_argv(kind, label, workspace_id, tab_id, bin_path)
    except MissingId as err:
        return show_forms_and_hold(
            stdin, stdout, stderr, f"no {err.which} id in the plugin context"
        )
    except ContextError as err:
        return show_forms_and_hold(stdin, stdout, stderr, str(err))
    code = run(command)
    if code != 0:
        hold_closed(stdin, stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv, dict(os.environ), sys.stdin, sys.stdout, sys.stderr, run_argv))
