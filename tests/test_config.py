import importlib


def test_defaults(monkeypatch):
    for key in ("OLLAMA_HOST", "APP_PORT", "DEFAULT_MODEL", "OCR_MODEL", "PDF_DPI"):
        monkeypatch.delenv(key, raising=False)
    import src.config as config

    importlib.reload(config)
    cfg = config.load_config()
    assert cfg.app_port == 8530
    assert cfg.default_model == "standard"
    assert cfg.default_language == "auto"
    assert cfg.ocr_model == "deepseek-ocr:3b"
    assert cfg.pdf_dpi == 150


def test_conversion_env_override(monkeypatch):
    monkeypatch.setenv("OCR_MODEL", "llava:7b")
    monkeypatch.setenv("REWRITE_MODEL", "qwen3:14b")
    monkeypatch.setenv("PDF_DPI", "300")
    import src.config as config

    importlib.reload(config)
    cfg = config.load_config()
    assert cfg.ocr_model == "llava:7b"
    assert cfg.rewrite_model == "qwen3:14b"
    assert cfg.pdf_dpi == 300


def test_env_override(monkeypatch):
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("DEFAULT_MODEL", "fast")
    import src.config as config

    importlib.reload(config)
    cfg = config.load_config()
    assert cfg.app_port == 9000
    assert cfg.default_model == "fast"
