from pathlib import Path


def test_main_uses_supported_stealth_api():
    main_source = Path("main.py").read_text(encoding="utf-8")

    assert "from playwright_stealth import stealth_async" in main_source
    assert "from playwright_stealth import Stealth" not in main_source
    assert "await stealth_async(page_emt)" in main_source
    assert "await stealth_async(page_goog)" in main_source
