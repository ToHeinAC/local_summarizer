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


def test_detailed_template_cites_source_anchors():
    structure = templates.get_template("detailed")["structure"]
    assert "verbatim" in structure
    assert "§" in structure
    assert "never invent" in structure


def test_get_unknown_template_raises():
    with pytest.raises(KeyError):
        templates.get_template("nope")
