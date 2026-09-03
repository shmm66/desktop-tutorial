"""Low-level smoke tests that do not require a GUI display."""
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_entrypoints_compile():
    targets = [ROOT / "TraderPlannerPro_v3.py", ROOT / "TraderPlannerPro_v4.py"]
    for target in targets:
        if target.exists():
            py_compile.compile(str(target), doraise=True)


def test_architecture_contract_files_exist():
    assert (ROOT / "AGENTS.md").exists()
    assert (ROOT / "ARCHITECTURE.md").exists()
    assert (ROOT / "docs" / "AGENT_CONTRACT.md").exists()


def test_expected_build_files_exist():
    assert (ROOT / ".github" / "workflows" / "build-windows.yml").exists()
    assert (ROOT / "TraderPlannerPro.iss").exists()
