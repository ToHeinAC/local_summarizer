from src import app


def test_stars():
    assert app._stars(3) == "★★★"
    assert app._stars(1) == "★☆☆"


def test_accepted_formats():
    assert app.ACCEPTED == ["pdf", "docx", "txt", "md"]


def test_config_loaded():
    assert app.CFG.app_port == 8506


def test_theme_css_available_to_ui():
    assert "<style>" in app.theme.build_css()
