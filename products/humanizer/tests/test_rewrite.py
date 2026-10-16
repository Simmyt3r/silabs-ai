from products.humanizer.service.rewrite import rewrite_text
from products.humanizer.service.style_profile import StyleProfile


def test_rewrite_preserves_protected_values():
    original = "Smith (2024) reported 67.4% adoption."

    def fake_generate(prompt: str) -> str:
        start = prompt.split("Text:\n", 1)[1].split("\n\nReturn only", 1)[0]
        return start.replace("reported", "documented")

    rewritten, result = rewrite_text(original, generate=fake_generate, profile=StyleProfile(mode="academic"))
    assert result.passed
    assert "67.4%" in rewritten
    assert "Smith (2024)" in rewritten


def test_reject_dropped_citation():
    original = "Smith (2024) reported 67.4% adoption."
    revised, result = rewrite_text(original, lambda prompt: "Adoption was significant.")
    assert not result.passed
    assert revised == original


def test_reject_duplicate_and_new_numbers():
    text = "Some 67.4% participated."
    def duplicated(prompt: str) -> str:
        masked = prompt.split("Text:\n", 1)[1].split("\n\nReturn only", 1)[0]
        token = masked.split()[1]
        return f"About {token} and {token} participated."
    revised, result = rewrite_text(text, duplicated)
    assert not result.passed
    assert revised == text

    revised, result = rewrite_text(text, lambda _: "About 90% participated.")
    assert not result.passed
    assert revised == text
