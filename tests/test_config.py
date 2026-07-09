import importlib


def test_defaults(monkeypatch):
    for key in ("OLLAMA_HOST", "APP_PORT", "DEFAULT_MODEL"):
        monkeypatch.delenv(key, raising=False)
    import src.config as config

    importlib.reload(config)
    cfg = config.load_config()
    assert cfg.app_port == 8506
    assert cfg.default_model == "standard"
    assert cfg.default_language == "auto"


def test_env_override(monkeypatch):
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("DEFAULT_MODEL", "fast")
    import src.config as config

    importlib.reload(config)
    cfg = config.load_config()
    assert cfg.app_port == 9000
    assert cfg.default_model == "fast"
