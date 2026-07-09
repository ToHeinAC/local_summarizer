import pytest

from src import models


def test_four_models_registered():
    assert len(models.list_models()) == 4


def test_default_model_exists():
    assert models.get_model(models.DEFAULT_MODEL_ID)["id"] == "standard"


def test_registry_shape():
    for model in models.list_models():
        assert {"id", "tag", "label", "speed", "quality", "note"} <= model.keys()


def test_get_unknown_model_raises():
    with pytest.raises(KeyError):
        models.get_model("nope")


def test_installed_tags_unreachable_returns_empty():
    assert models.installed_tags("http://127.0.0.1:1", timeout=0.2) == set()


def test_annotate_availability(monkeypatch):
    monkeypatch.setattr(models, "installed_tags", lambda host: {"gemma4:e4b"})
    annotated = models.annotate_availability("http://x")
    by_id = {m["id"]: m for m in annotated}
    assert by_id["standard"]["installed"] is True
    assert by_id["smarter"]["installed"] is False
