import pytest

from src import models


def test_six_models_registered():
    assert len(models.list_models()) == 6


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


def test_hybrid_needs_both_tags(monkeypatch):
    monkeypatch.setattr(models, "installed_tags", lambda host: {"gemma4:e4b"})
    hybrid = {m["id"]: m for m in models.annotate_availability("http://x")}["hybrid"]
    assert hybrid["installed"] is False
    assert hybrid["missing"] == ["qwen3.8-27b:latest"]
    monkeypatch.setattr(models, "installed_tags", lambda host: {"gemma4:e4b", "qwen3.8-27b:latest"})
    assert {m["id"]: m for m in models.annotate_availability("http://x")}["hybrid"]["installed"]


def test_every_registry_tag_has_a_measured_window():
    """A tag missing from NUM_CTX would silently fall back to the small default."""
    for model in models.list_models():
        for tag in models.model_tags(model):
            assert tag in models.NUM_CTX, tag


def test_num_ctx_defaults_for_unknown_tags():
    assert models.num_ctx("gemma4:e4b") == 131072
    assert models.num_ctx("unknown:tag") == models.DEFAULT_NUM_CTX
