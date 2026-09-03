from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v5_launcher_exists():
    assert (ROOT / "run_v5.py").exists()


def test_v5_docs_exist():
    assert (ROOT / "docs" / "V5_FOUNDATION.md").exists()
    assert (ROOT / "docs" / "V5_BACKLOG.md").exists()


def test_domain_boundaries_exist():
    assert (ROOT / "app" / "domains" / "forex").is_dir()
    assert (ROOT / "app" / "domains" / "crypto").is_dir()


def test_no_legacy_launcher_is_used_by_v5():
    launcher = (ROOT / "run_v5.py").read_text(encoding="utf-8")
    assert "TraderPlannerPro_v" not in launcher
