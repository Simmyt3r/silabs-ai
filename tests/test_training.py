import json

from training.train_sft import build_tokenized_dataset


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
