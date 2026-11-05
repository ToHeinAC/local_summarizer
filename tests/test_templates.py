import pytest

from src import templates


def test_exactly_the_four_report_types():
    ids = [t["id"] for t in templates.list_templates()]
    assert ids == ["executive", "bullets", "detailed", "action_items"]


def test_default_template_exists():
    assert templates.get_template(templates.DEFAULT_TEMPLATE_ID)["id"] == "bullets"


def test_registry_shape():
    for template in templates.list_templates():
        assert {"id", "label", "description", "structure"} <= template.keys()
        assert template["structure"].strip()
        assert {"de", "en"} <= template["label"].keys()


def test_every_template_states_a_length_target():
    """Page targets (half, one, two A4 pages) are given to the LLM as words."""
    for template in templates.list_templates():
        assert "words" in template["structure"], template["id"]
        assert "A4" in template["structure"], template["id"]


def test_report_sections_cover_objective_method_results():
    for tid in ("bullets", "detailed", "action_items"):
        structure = templates.get_template(tid)["structure"]
        for heading in ("## Objective", "## Methodology"):
            assert heading in structure, (tid, heading)
    assert "## Results" in templates.get_template("bullets")["structure"]


def test_detailed_template_cites_and_lists_references():
    structure = templates.get_template("detailed")["structure"]
    assert "verbatim" in structure
    assert "§" in structure
    assert "never invent" in structure
    assert "## References" in structure


def test_action_items_template_ends_in_measures():
    structure = templates.get_template("action_items")["structure"]
    for heading in ("## Key Findings", "## Conclusions", "## Measures"):
        assert heading in structure
    assert structure.index("## Conclusions") < structure.index("## Measures")


def test_get_unknown_template_raises():
    with pytest.raises(KeyError):
        templates.get_template("nope")
