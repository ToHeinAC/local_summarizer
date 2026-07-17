import pytest

from src import templates


def test_templates_registered():
    assert len(templates.list_templates()) >= 3


def test_default_template_exists():
    assert templates.get_template(templates.DEFAULT_TEMPLATE_ID)["id"] == "standard"


def test_registry_shape():
    for template in templates.list_templates():
        assert {"id", "label", "description", "structure"} <= template.keys()
        assert template["structure"].strip()


def test_detailed_refs_template_cites_source_anchors():
    structure = templates.get_template("detailed_refs")["structure"]
    assert "verbatim" in structure
    assert "§" in structure
    assert "never invent" in structure


def test_detailed_template_stays_plain():
    """The plain variant keeps the section shape but suppresses inline anchors.

    Map/reduce feed it anchor-rich content regardless of template, so without
    the opt-out it would read like detailed_refs.
    """
    structure = templates.get_template("detailed")["structure"]
    for shape in ("## Summary", "### ", "## Conclusion"):
        assert shape in structure
    assert "do not anchor" in structure
    assert "verbatim" not in structure
    assert "§" not in structure


def test_get_unknown_template_raises():
    with pytest.raises(KeyError):
        templates.get_template("nope")
