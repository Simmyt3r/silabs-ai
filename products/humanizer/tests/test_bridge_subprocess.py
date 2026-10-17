"""The console bridge must speak only JSON-lines on stdout."""
import json
import subprocess
import sys


def test_bridge_console_protocol_fails_closed():
    script = "\n".join([
        json.dumps({"action": "unknown_action"}),
        json.dumps({"action": "rewrite", "path": "not-found.docx"}),
    ]) + "\n"
    result = subprocess.run(
        [sys.executable, "-m", "products.humanizer.service.bridge_executable"],
        input=script,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    messages = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(messages) == 2
    assert all(message["ok"] is False for message in messages)
    assert "Unknown action" in messages[0]["error"]
    assert "Traceback" not in result.stdout
