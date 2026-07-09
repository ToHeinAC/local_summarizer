from src import prompts


def test_prompts_are_nonempty_strings():
    for name in (
        "MAP_PROMPT",
        "REDUCE_PROMPT",
        "FINALIZE_PROMPT",
        "OCR_SYSTEM_PROMPT",
        "OCR_USER_PROMPT",
        "OCR_DEEPSEEK_PROMPT",
        "MD_REWRITE_PROMPT",
    ):
        value = getattr(prompts, name)
        assert isinstance(value, str) and value.strip()


def test_deepseek_prompt_keeps_grounding_token():
    assert prompts.OCR_DEEPSEEK_PROMPT.startswith("<|grounding|>")


def test_rewrite_prompt_ends_open_for_source_text():
    # md_convert concatenates the page text directly onto this constant.
    assert prompts.MD_REWRITE_PROMPT.rstrip().endswith("Text to reformat:")


def test_map_prompt_has_chunk_slot():
    assert "{chunk}" in prompts.MAP_PROMPT


def test_reduce_prompt_has_summaries_slot():
    assert "{summaries}" in prompts.REDUCE_PROMPT


def test_finalize_prompt_has_all_slots():
    for slot in ("{language}", "{template}", "{content}"):
        assert slot in prompts.FINALIZE_PROMPT


def test_auto_language_label_present():
    assert prompts.LANGUAGE_LABELS["auto"]
