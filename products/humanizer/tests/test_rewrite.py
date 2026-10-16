from products.humanizer.service.rewrite import rewrite_text
from products.humanizer.service.style_profile import StyleProfile


def test_rewrite_preserves_protected_values():
    original = "Smith (2024) reported 67.4% adoption."

    def fake_generate(prompt: str) -> str:
        start = prompt.split("Text:\n", 1)[1].split("\n\nReturn only", 1)[0]
        return "The study found " + start.split("reported ", 1)[1]

    rewritten, result = rewrite_text(
        original,
        generate=fake_generate,
        profile=StyleProfile(mode="academic"),
    )

    assert result.passed
    assert "67.4%" in rewritten
    assert "(2024)" in rewritten
