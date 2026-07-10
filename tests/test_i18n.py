import pytest

from src import i18n


def test_german_is_the_default():
    assert i18n.DEFAULT_LANG == "de"
    assert set(i18n.LANGUAGES) == {"de", "en"}


def test_every_string_exists_in_every_language():
    """A missing variant would be a KeyError the first time the UI renders it."""
    for key, variants in i18n.STRINGS.items():
        assert set(variants) == set(i18n.LANGUAGES), key
        assert all(v.strip() for v in variants.values()), key


def test_placeholders_match_across_languages():
    """`t` formats with one kwargs dict, so both variants need the same slots."""
    for key, variants in i18n.STRINGS.items():
        slots = [{f.split("}")[0] for f in v.split("{")[1:]} for v in variants.values()]
        assert all(s == slots[0] for s in slots), key


def test_t_translates_and_formats():
    assert i18n.t("done", "de") == "Fertig"
    assert i18n.t("done", "en") == "Done"
    assert i18n.t("split", "en", count=3) == "Split into 3 section(s)"


def test_t_falls_back_to_german_for_an_unknown_language():
    assert i18n.t("done", "fr") == "Fertig"


def test_t_raises_on_an_unknown_key():
    with pytest.raises(KeyError):
        i18n.t("nope", "de")


def test_pick_reads_a_registry_field():
    field = {"de": "Schnell", "en": "Fast"}
    assert i18n.pick(field, "en") == "Fast"
    assert i18n.pick(field, "xx") == "Schnell"
