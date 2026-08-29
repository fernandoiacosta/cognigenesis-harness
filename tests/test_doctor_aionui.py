from pathlib import Path

from cognigenesis.bootstrap import run_checks
from cognigenesis.config import Settings


def test_doctor_accepts_packaged_acp_even_if_legacy_file_exists(tmp_path, monkeypatch):
    legacy = tmp_path / "AionUi" / "cognigenesis" / "cognigenesis_ollama.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("# legacy", encoding="utf-8")

    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(
        "cognigenesis.bootstrap.shutil.which",
        lambda name: (
            r"C:\Tools\cogni-acp.exe"
            if name == "cogni-acp"
            else (r"C:\Tools\cogni.exe" if name == "cogni" else None)
        ),
    )
    monkeypatch.setattr(
        "cognigenesis.bootstrap.list_models",
        lambda *args, **kwargs: ["llama3.1:8b"],
    )
    monkeypatch.setattr(
        "cognigenesis.bootstrap.load_profile",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "cognigenesis.bootstrap.install_brand_assets",
        lambda: {"logo": Path(__file__), "theme": Path(__file__)},
    )

    checks = run_checks(Settings(model="llama3.1:8b"))
    aionui = next(check for check in checks if check.name == "AionUi bridge")

    assert aionui.ok is True
    assert "packaged ACP" in aionui.detail
    assert "unused legacy file" in aionui.detail
