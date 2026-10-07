import json

from training.train_sft import _truncate_supervised_example, build_tokenized_dataset


class FakeTokenizer:
    def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=False):
        if add_generation_prompt:
            return [10, 11, 12]
        return [10, 11, 12, 20, 21]


def test_prompt_tokens_are_masked(tmp_path):
    path = tmp_path / "train.jsonl"
    row = {"instruction": "Answer", "input": "Question", "output": "Response"}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    dataset = build_tokenized_dataset(str(path), FakeTokenizer(), max_length=32)
    labels = dataset[0]["labels"]

    assert labels[:3] == [-100, -100, -100]
    assert labels[3:] == [20, 21]



def test_long_prompt_keeps_assistant_tokens():
    prompt = list(range(100))
    response = [200, 201, 202, 203]
    packed = _truncate_supervised_example(
        prompt_ids=prompt,
        full_ids=prompt + response,
        max_length=32,
    )

    assert packed is not None
    input_ids, labels = packed
    assert len(input_ids) <= 32
    assert labels[-4:] == response
    assert input_ids[-4:] == response
    assert any(label != -100 for label in labels)


def test_truncation_rejects_tiny_context_window():
    try:
        _truncate_supervised_example([1, 2], [1, 2, 3], max_length=4)
    except ValueError as exc:
        assert "at least 8" in str(exc)
    else:
        raise AssertionError("expected ValueError")
