from training.data import normalize_record


def test_instruction_output_pair():
    result = normalize_record({"instruction": "2+3?", "output": "5"})
    assert result[-1]["content"] == "5"
