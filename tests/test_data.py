from training.data import normalize_record


def test_instruction_output_pair():
    result = normalize_record({"instruction": "2+3?", "output": "5"})
    assert result[-1]["content"] == "5"


def test_finalized_silabs_record_keeps_input():
    result = normalize_record({
        "instruction": "Respond helpfully and accurately to the user.",
        "input": "What is 2 + 3?",
        "output": "5",
    })
    assert "Respond helpfully" in result[0]["content"]
    assert "What is 2 + 3?" in result[0]["content"]
    assert result[1]["content"] == "5"
