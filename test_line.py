"""Parser and argv tests. They do not call Herdr."""

import json
import tomllib
import unittest
from io import StringIO
from pathlib import Path

import line

ROOT = Path(__file__).resolve().parent


class ParseTests(unittest.TestCase):
    def test_blank_lines_are_empty(self) -> None:
        self.assertEqual(line.parse_line(""), ("empty", None))
        self.assertEqual(line.parse_line("   \n"), ("empty", None))

    def test_rename_forms_keep_the_rest_as_the_label(self) -> None:
        self.assertEqual(
            line.parse_line("rename this tab Hello World"),
            ("tab_rename", "Hello World"),
        )
        self.assertEqual(line.parse_line("Rename Tab Hello  World"), ("tab_rename", "Hello  World"))
        self.assertEqual(
            line.parse_line("rename this workspace Desk A"),
            ("workspace_rename", "Desk A"),
        )
        self.assertEqual(line.parse_line("rename workspace Desk A"), ("workspace_rename", "Desk A"))

    def test_create_forms(self) -> None:
        self.assertEqual(line.parse_line("new workspace ABC"), ("workspace_create", "ABC"))
        self.assertEqual(
            line.parse_line("create workspace My Desk"),
            ("workspace_create", "My Desk"),
        )

    def test_missing_label_and_other_text_are_unknown(self) -> None:
        self.assertEqual(line.parse_line("rename this tab"), ("unknown", None))
        self.assertEqual(line.parse_line("split the pane"), ("unknown", None))


class ArgvTests(unittest.TestCase):
    def test_rename_passes_the_label_as_one_argument(self) -> None:
        argv = line.command_argv("tab_rename", "Hello World", "w1", "t1", "/bin/herdr")
        self.assertEqual(argv, ["/bin/herdr", "tab", "rename", "t1", "Hello World"])
        argv = line.command_argv("workspace_rename", "Desk A", "w1", "t1", "/bin/herdr")
        self.assertEqual(argv, ["/bin/herdr", "workspace", "rename", "w1", "Desk A"])

    def test_create_uses_one_label_value_and_focuses(self) -> None:
        argv = line.command_argv("workspace_create", "My Desk", None, None, "/bin/herdr")
        self.assertEqual(
            argv,
            ["/bin/herdr", "workspace", "create", "--focus", "--label", "My Desk"],
        )

    def test_rename_without_an_id_fails(self) -> None:
        with self.assertRaises(line.MissingId):
            line.command_argv("tab_rename", "Hello", "w1", None, "herdr")
        with self.assertRaises(line.MissingId):
            line.command_argv("workspace_rename", "Hello", None, "t1", "herdr")

    def test_context_json_supplies_ids_the_popup_does_not_get_as_env(self) -> None:
        raw = json.dumps({"workspace_id": "w9", "tab_id": "t9"})
        self.assertEqual(line.context_ids({"HERDR_PLUGIN_CONTEXT_JSON": raw}), ("w9", "t9"))

    def test_env_ids_win_over_json(self) -> None:
        raw = json.dumps({"workspace_id": "from-json", "tab_id": "from-json"})
        found = line.context_ids(
            {
                "HERDR_WORKSPACE_ID": "from-env",
                "HERDR_TAB_ID": "from-env",
                "HERDR_PLUGIN_CONTEXT_JSON": raw,
            }
        )
        self.assertEqual(found, ("from-env", "from-env"))

    def test_bad_context_json_is_an_error(self) -> None:
        with self.assertRaises(line.ContextError):
            line.context_ids({"HERDR_PLUGIN_CONTEXT_JSON": "{"})

    def test_open_argv(self) -> None:
        self.assertEqual(
            line.open_argv("/bin/herdr"),
            [
                "/bin/herdr",
                "plugin",
                "pane",
                "open",
                "--plugin",
                "local.plain-line",
                "--entrypoint",
                "line",
                "--placement",
                "popup",
            ],
        )


class MainTests(unittest.TestCase):
    def test_empty_line_does_not_call_herdr(self) -> None:
        calls: list[list[str]] = []
        code = line.main(
            ["line.py"],
            {},
            StringIO("\n"),
            StringIO(),
            StringIO(),
            calls.append,
        )
        self.assertEqual(code, 0)
        self.assertEqual(calls, [])

    def test_unknown_line_exits_1_after_enter(self) -> None:
        stderr = StringIO()
        code = line.main(
            ["line.py"],
            {},
            StringIO("nope\n\n"),
            StringIO(),
            stderr,
            lambda _argv: self.fail("herdr was called"),
        )
        self.assertEqual(code, 1)
        self.assertIn("rename this tab LABEL", stderr.getvalue())

    def test_rename_uses_context_json_and_returns_the_command_status(self) -> None:
        calls: list[list[str]] = []
        env = {
            "HERDR_BIN_PATH": "/bin/herdr",
            "HERDR_PLUGIN_CONTEXT_JSON": json.dumps({"workspace_id": "w1", "tab_id": "t1"}),
        }
        code = line.main(
            ["line.py"],
            env,
            StringIO("rename this tab Hello World\n"),
            StringIO(),
            StringIO(),
            lambda argv: calls.append(argv) or 0,
        )
        self.assertEqual(code, 0)
        self.assertEqual(calls, [["/bin/herdr", "tab", "rename", "t1", "Hello World"]])

    def test_failed_command_waits_for_enter(self) -> None:
        code = line.main(
            ["line.py"],
            {
                "HERDR_BIN_PATH": "/bin/herdr",
                "HERDR_PLUGIN_CONTEXT_JSON": json.dumps({"tab_id": "t1"}),
            },
            StringIO("rename tab Hello\n\n"),
            StringIO(),
            StringIO(),
            lambda _argv: 2,
        )
        self.assertEqual(code, 2)


class ManifestTests(unittest.TestCase):
    def test_manifest_matches_the_script(self) -> None:
        manifest = tomllib.loads((ROOT / "herdr-plugin.toml").read_text())
        self.assertEqual(manifest["id"], line.PLUGIN_ID)
        self.assertEqual(manifest["panes"][0]["id"], line.ENTRYPOINT)
        self.assertEqual(manifest["panes"][0]["placement"], "popup")
        self.assertEqual(manifest["panes"][0]["command"], ["python3", "line.py"])
        self.assertEqual(manifest["actions"][0]["id"], "open")
        self.assertEqual(manifest["actions"][0]["command"], ["python3", "line.py", "--open"])


if __name__ == "__main__":
    unittest.main()
