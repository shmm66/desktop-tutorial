"""Low-level smoke tests that do not require a GUI display."""
from pathlib import Path
import ast
import py_compile

ROOT = Path(__file__).resolve().parents[1]


def test_release_entrypoints_compile():
    for name in ('TraderPlannerPro_v5.py','TraderPlannerPro_v6.py'):
        py_compile.compile(str(ROOT / name), doraise=True)


def test_v6_contains_persisted_task_and_journal_contracts():
    source=(ROOT/'TraderPlannerPro_v6.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    assert 'def toggle_task' in source
    assert "DB['tasks'][self.day][i]['done']=bool(v.get())" in source
    assert "DB['journals'][self.market].append(row)" in source
    assert 'def add_trade' in source
    assert 'left=self.card(outer); right=self.card(outer)' in source
    assert all(field in source for field in ('Entry','Stop Loss','Take Profit','Risk %','Result (R)','P&L','Lesson','Screenshot'))
    assert ast.Module is not None


def test_architecture_contract_files_exist():
    assert (ROOT / 'AGENTS.md').exists()
    assert (ROOT / 'ARCHITECTURE.md').exists()
    assert (ROOT / 'docs' / 'AGENT_CONTRACT.md').exists()


def test_expected_build_files_exist():
    assert (ROOT / '.github' / 'workflows' / 'build-windows.yml').exists()
    assert (ROOT / 'TraderPlannerPro.iss').exists()
