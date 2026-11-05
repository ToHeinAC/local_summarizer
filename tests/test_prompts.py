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


def test_map_prompt_keeps_source_anchors_verbatim():
    # Finalize can only cite identifiers the map stage passed through.
    assert "verbatim" in prompts.MAP_PROMPT
    for anchor in ("§", "Abbildung", "DIN"):
        assert anchor in prompts.MAP_PROMPT


def test_reduce_prompt_keeps_source_anchors():
    # Reduce is the second place identifiers vanish before finalize sees them.
    assert "§" in prompts.REDUCE_PROMPT
    assert "unchanged" in prompts.REDUCE_PROMPT


def test_finalize_prompt_has_all_slots():
    for slot in ("{language}", "{template}", "{overview}", "{focus}", "{content}"):
        assert slot in prompts.FINALIZE_PROMPT


def test_map_prompt_sees_the_whole_document_context():
    # Each part is summarised knowing the document's purpose and its position.
    for slot in ("{brief}", "{part}", "{total}", "{focus}"):
        assert slot in prompts.MAP_PROMPT
    assert "{head}" in prompts.BRIEF_PROMPT


def test_notes_stay_in_the_source_language():
    # English notes on a German report were back-translated with errors.
    assert "same language" in prompts.MAP_PROMPT
    assert "same language" in prompts.REDUCE_PROMPT


def test_finalize_forbids_markup_the_exporters_cannot_render():
    assert "LaTeX" in prompts.FINALIZE_PROMPT


def test_auto_language_label_present():
    assert prompts.LANGUAGE_LABELS["auto"]


def test_no_example_identifier_a_small_model_could_copy():
    """gemma4:e4b listed "DIN 25457" and "[BS 04]" from the old examples as
    references of an EPA report. Examples may name a category, never a
    concrete identifier."""
    from src import templates

    texts = [v for k, v in vars(prompts).items() if k.isupper() and isinstance(v, str)]
    texts += [t["structure"] for t in templates.list_templates()]
    for text in texts:
        for leaked in ("DIN 25457", "VDI 2263", "[BS 04]", "12.03.2024", "§ 29"):
            assert leaked not in text


def test_focus_blocks_carry_the_users_focus():
    # Map notes must keep what the focus needs; finalize must say whether and
    # how the document answers it, without inventing an answer.
    assert "{focus}" in prompts.MAP_FOCUS
    assert "{focus}" in prompts.FINALIZE_FOCUS
    assert "whether" in prompts.FINALIZE_FOCUS
    assert "does not" in prompts.FINALIZE_FOCUS
