"""Unit tests for ai_helper.py. They do not call a real LLM."""

import json
import unittest
from unittest import mock

import ai_helper
import line


class ExtractAndNormalizeTests(unittest.TestCase):
    def test_extract_fenced_json(self) -> None:
        fenced = (
            '```json\n{"explanation": "ok", "action": "tab_rename",'
            ' "label": "Build", "needs_confirmation": false}\n```'
        )
        parsed = ai_helper.extract_json_response(fenced)
        plan = ai_helper.normalize_plan(parsed)
        self.assertEqual(plan["action"], "tab_rename")
        self.assertEqual(plan["label"], "Build")
        self.assertTrue(plan["needs_confirmation"])

    def test_unknown_action_becomes_none(self) -> None:
        plan = ai_helper.normalize_plan(
            {"explanation": "nope", "action": "pane_run", "label": "x"}
        )
        self.assertEqual(plan["action"], "none")

    def test_clean_context_strips_smuggled_controls(self) -> None:
        tags = "".join(chr(0xE0000 + ord(c)) for c in "IGNORE")
        out = ai_helper.clean_context(
            {
                "request": "rename\x1b[2J tab",
                "tab_label": "evil\u202e" + tags,
                "workspace_id": "w1",
            }
        )
        self.assertNotIn("\x1b", out["request"])
        for ch in out["tab_label"]:
            self.assertNotIn(
                __import__("unicodedata").category(ch),
                ("Cc", "Cf", "Co", "Cn"),
            )


class HostAllowlistTests(unittest.TestCase):
    def test_allowlisted_rename(self) -> None:
        action, label = line.validate_ai_plan(
            {
                "action": "tab_rename",
                "label": "Build logs",
                "explanation": "rename",
            },
            "w1",
            "t1",
        )
        self.assertEqual(action, "tab_rename")
        self.assertEqual(label, "Build logs")

    def test_rejects_unknown_action(self) -> None:
        with self.assertRaises(line.AiRefuse):
            line.validate_ai_plan(
                {"action": "exec", "label": "rm -rf /"},
                "w1",
                "t1",
            )

    def test_rejects_empty_and_huge_labels(self) -> None:
        with self.assertRaises(line.AiRefuse):
            line.validate_ai_plan({"action": "workspace_create", "label": "  "}, None, None)
        with self.assertRaises(line.AiRefuse):
            line.validate_ai_plan(
                {"action": "workspace_create", "label": "x" * (line.LABEL_MAX + 1)},
                None,
                None,
            )

    def test_missing_id_still_raises(self) -> None:
        with self.assertRaises(line.MissingId):
            line.validate_ai_plan(
                {"action": "tab_rename", "label": "X"},
                "w1",
                None,
            )

    def test_helper_error_field_is_refused(self) -> None:
        with self.assertRaises(line.AiRefuse):
            line.validate_ai_plan({"error": "No API key"}, "w1", "t1")


class AiMainBranchTests(unittest.TestCase):
    def test_ai_disabled_keeps_unknown_path(self) -> None:
        from io import StringIO

        stderr = StringIO()
        code = line.main(
            ["line.py"],
            {},
            StringIO("call this tab build\n\n"),
            StringIO(),
            stderr,
            lambda _argv: self.fail("herdr was called"),
        )
        self.assertEqual(code, 1)
        self.assertIn("unrecognized line", stderr.getvalue())

    def test_ai_confirm_runs_allowlisted_command(self) -> None:
        from io import StringIO

        calls: list[list[str]] = []

        def fake_ai(_request, _env, _payload):
            return {
                "explanation": "Rename the tab.",
                "action": "tab_rename",
                "label": "build logs",
                "needs_confirmation": True,
                "confirmation_prompt": "Rename this tab to build logs? [y/N]: ",
            }

        env = {
            "HERDR_PLAIN_LINE_AI": "1",
            "HERDR_BIN_PATH": "/bin/herdr",
            "HERDR_PLUGIN_CONTEXT_JSON": json.dumps({"workspace_id": "w1", "tab_id": "t1"}),
        }
        stdout = StringIO()
        code = line.main(
            ["line.py"],
            env,
            StringIO("call this tab build logs\ny\n"),
            stdout,
            StringIO(),
            lambda argv: calls.append(argv) or 0,
            ai_call=fake_ai,
        )
        self.assertEqual(code, 0)
        self.assertEqual(calls, [["/bin/herdr", "tab", "rename", "t1", "build logs"]])
        self.assertIn("thinking", stdout.getvalue())

    def test_ai_cancel_does_not_run(self) -> None:
        from io import StringIO

        def fake_ai(_request, _env, _payload):
            return {
                "explanation": "Rename.",
                "action": "tab_rename",
                "label": "Nope",
                "needs_confirmation": True,
                "confirmation_prompt": "Rename? [y/N]: ",
            }

        code = line.main(
            ["line.py"],
            {
                "HERDR_PLAIN_LINE_AI": "1",
                "HERDR_BIN_PATH": "/bin/herdr",
                "HERDR_PLUGIN_CONTEXT_JSON": json.dumps({"tab_id": "t1"}),
            },
            StringIO("whatever\nn\n"),
            StringIO(),
            StringIO(),
            lambda _argv: self.fail("herdr was called"),
            ai_call=fake_ai,
        )
        self.assertEqual(code, 0)

    def test_ai_rejects_model_proposed_outside_allowlist(self) -> None:
        from io import StringIO

        stderr = StringIO()

        def fake_ai(_request, _env, _payload):
            return {"action": "pane_run", "label": "evil", "explanation": "no"}

        code = line.main(
            ["line.py"],
            {"HERDR_PLAIN_LINE_AI": "1"},
            StringIO("run something\n\n"),
            StringIO(),
            stderr,
            lambda _argv: self.fail("herdr was called"),
            ai_call=fake_ai,
        )
        self.assertEqual(code, 1)
        self.assertIn("not allowlisted", stderr.getvalue())

    def test_load_goose_config_reads_env(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "GOOSE_PROVIDER": "openai",
                "GOOSE_MODEL": "gpt-test",
                "OPENAI_API_KEY": "sk-test",
            },
            clear=False,
        ):
            provider, model, api_url, api_key = ai_helper.load_goose_config()
        self.assertEqual(provider, "openai")
        self.assertEqual(model, "gpt-test")
        self.assertIn("openai.com", api_url)
        self.assertEqual(api_key, "sk-test")


if __name__ == "__main__":
    unittest.main()
