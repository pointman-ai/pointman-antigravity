"""Offline contract checks. These never run agy or call Google."""
import json
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ManifestContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = tomllib.loads((ROOT / "extension.toml").read_text())
        cls.client = cls.manifest["client"]

    def test_extension(self):
        ext = self.manifest["extension"]
        self.assertEqual((ext["id"], ext["publisher"]), ("antigravity", "aurelio"))

    def test_install_and_protocol(self):
        self.assertEqual(self.client["protocol"], "agy-stream")
        self.assertEqual(self.client["binaries"], ["agy"])
        self.assertEqual(self.client["install"]["from"], "updater")
        self.assertIn("{goplatform}", self.client["install"]["url"])

    def test_headless_run(self):
        run = self.client["run"]
        self.assertEqual(run["prompt"], "arg")
        self.assertEqual(run["args"][:4], ["-p", "{prompt}", "--output-format", "stream-json"])
        for slot in ("{session}", "{model}", "{permissions}", "{add_dirs}"):
            self.assertIn(slot, run["args"])
        self.assertEqual(run["resume"], ["--conversation", "{value}"])
        self.assertEqual(run["env"]["AGY_CLI_DISABLE_AUTO_UPDATE"], "true")
        # agy skips the OS keyring only when it sees an SSH session: no Keychain dialog on a Mac
        self.assertTrue(run["env"]["SSH_CONNECTION"])

    def test_home_and_sign_in(self):
        self.assertEqual(self.client["home_env"], "HOME")
        self.assertEqual(self.client["sign_in"]["files"], [".gemini/antigravity-cli/antigravity-oauth-token"])
        self.assertEqual(self.client["instructions"], {"via": "file", "file": ".gemini/GEMINI.md"})
        mcp = self.client["mcp"]
        self.assertEqual((mcp["file"], mcp["key"], mcp["rename"]), (".gemini/config/mcp_config.json", "mcpServers", {"url": "serverUrl"}))

    def test_only_supported_modes(self):
        self.assertEqual(self.client["run"]["permissions"], {m: ["--dangerously-skip-permissions"] for m in ("default", "auto")})


class NativeFixture(unittest.TestCase):
    """tests/fixtures/native.jsonl: a captured `agy -p … --output-format stream-json` run calling an MCP tool."""

    def test_shape(self):
        lines = [json.loads(l) for l in (ROOT / "tests/fixtures/native.jsonl").read_text().splitlines()]
        self.assertEqual(lines[0]["event"], "init")
        self.assertEqual(lines[-1]["event"], "result")
        result = lines[-1]["result"]
        self.assertEqual(result["status"], "SUCCESS")
        ids = {l.get("conversation_id") or l[l["event"]]["conversation_id"] for l in lines}
        self.assertEqual(ids, {result["conversation_id"]})
        tools = [l["step_update"] for l in lines if l["event"] == "step_update" and l["step_update"]["step_type"] == "tool"]
        self.assertIn(("call_mcp_tool", "ACTIVE"), [(t["tool_name"], t["state"]) for t in tools])
        text = "".join(l["step_update"].get("text_delta", "") for l in lines if l["event"] == "step_update")
        self.assertIn("kestrel", text)


if __name__ == "__main__":
    unittest.main()
