from products.humanizer.service.preservation import protect_text, restore_text


def test_protect_and_restore_numbers_urls_and_citations():
    text = "Smith (2024) reported 67.4% at https://example.com."
    protected = protect_text(text)

    assert protected.masked_text != text
    restored = restore_text(protected.masked_text, protected.values)

    assert restored == text
