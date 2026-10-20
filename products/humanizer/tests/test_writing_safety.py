import json
import subprocess
import sys

from products.humanizer.service.critic import critique
from products.humanizer.service.rewrite import rewrite_text


def test_reject_prompt_instruction_echo():
    text = "This sentence need correcting."
    output = "This sentence needs correcting.\n\nReturn only the rewritten text."
    revision, result = rewrite_text(text, lambda _: output)
    assert not result.passed
    assert revision == text
    assert any("instructions" in item for item in result.issues)


def test_list_numbering_is_not_a_fabricated_statistic():
    outcome = critique(
        original="Five useful recommendations: practical and accurate.",
        rewritten="Recommendations:\n1. Be practical.\n2. Be accurate.",
        required_tokens={},
    )
    assert outcome.passed


def test_protection_still_rejects_new_numeric_claims():
    outcome = critique(
        original="Adoption improved.",
        rewritten="Adoption improved by 78%.",
        required_tokens={},
    )
    assert not outcome.passed


def test_windows_console_round_trip_escapes_all_non_ascii(tmp_path):
    path = tmp_path / "unicode.txt"
    path.write_text("Café naïve – résumé. ગુજરાતી עברית 中文\n\nSecond paragraph.", encoding="utf-8")
    request = json.dumps({"action": "open", "path": str(path)})
    proc = subprocess.run(
        [sys.executable, "-m", "products.humanizer.service.desktop_bridge"],
        input=request + "\n", capture_output=True, text=True, check=True,
        timeout=15,
    )
    reply = json.loads(proc.stdout.strip())
    assert reply["ok"]
    assert "Café" in reply["data"]["blocks"][0]["text"]
    assert "中文" in reply["data"]["blocks"][0]["text"]
    assert proc.stdout.isascii()
