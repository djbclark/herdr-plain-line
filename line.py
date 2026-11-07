#!/usr/bin/env python3
"""One plain-English line for three Herdr commands.

A popup process does not receive HERDR_TAB_ID or HERDR_WORKSPACE_ID. Those ids
are read from HERDR_PLUGIN_CONTEXT_JSON. There are no model calls.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

PLUGIN_ID = "local.plain-line"
ENTRYPOINT = "line"

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


def context_ids(env: dict[str, str]) -> tuple[str | None, str | None]:
    workspace_id = _optional_str(env.get("HERDR_WORKSPACE_ID"))
    tab_id = _optional_str(env.get("HERDR_TAB_ID"))
    raw = env.get("HERDR_PLUGIN_CONTEXT_JSON")
    if not raw:
        return (workspace_id, tab_id)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as err:
        raise ContextError(f"HERDR_PLUGIN_CONTEXT_JSON is not JSON: {err}") from err
    if not isinstance(data, dict):
        raise ContextError("HERDR_PLUGIN_CONTEXT_JSON is not an object")
    workspace_id = workspace_id or _optional_str(data.get("workspace_id"))
    tab_id = tab_id or _optional_str(data.get("tab_id"))
    return (workspace_id, tab_id)


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


def main(
    argv: list[str],
    env: dict[str, str],
    stdin: object,
    stdout: object,
    stderr: object,
    run,
) -> int:
    bin_path = herdr_bin(env)
    if len(argv) > 1 and argv[1] == "--open":
        return run(open_argv(bin_path))
    stdout.write(
        "rename this tab LABEL  |  rename this workspace LABEL  |  new workspace LABEL\n> "
    )
    stdout.flush()
    kind, label = parse_line(stdin.readline())
    if kind == "empty":
        return 0
    if kind == "unknown" or label is None:
        stderr.write("unrecognized line\n")
        stderr.write(FORMS)
        hold_closed(stdin, stdout)
        return 1
    try:
        workspace_id, tab_id = context_ids(env)
        command = command_argv(kind, label, workspace_id, tab_id, bin_path)
    except MissingId as err:
        stderr.write(f"no {err.which} id in the plugin context\n")
        hold_closed(stdin, stdout)
        return 1
    except ContextError as err:
        stderr.write(f"{err}\n")
        hold_closed(stdin, stdout)
        return 1
    code = run(command)
    if code != 0:
        hold_closed(stdin, stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv, dict(os.environ), sys.stdin, sys.stdout, sys.stderr, run_argv))
