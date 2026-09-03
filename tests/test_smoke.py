"""Static smoke tests for the release entrypoint and core persistence contracts."""
from pathlib import Path
import ast
import py_compile

ROOT = Path(__file__).resolve().parents[1]


def test_release_entrypoints_compile():
    for name in ('TraderPlannerPro_v5.py','TraderPlannerPro_v6.py','TraderPlannerPro_v7.py'):
        py_compile.compile(str(ROOT / name), doraise=True)


def test_v7_deep_planner_journal_contracts():
    source=(ROOT/'TraderPlannerPro_v7.py').read_text(encoding='utf-8')
    ast.parse(source)
    for name in ('toggle_selected_task','add_task','edit_task','delete_task','trade_dialog','edit_trade','delete_trade','attach_screenshot','screenshot_folder','open_screenshot_root'):
        assert f'def {name}' in source
    assert "DB['tasks'][self.day][i]['done']=not bool(DB['tasks'][self.day][i].get('done'))" in source
    assert "DB['journals'][self.market].append(data)" in source
    assert "DB['journals'][self.market][index]=data" in source
    assert 'Screenshots' in source
    assert 'Date' in source and 'Symbol' in source and 'Direction' in source
    assert 'left=self.card(outer)' in source and 'right=self.card(outer)' in source
    assert all(field in source for field in ('Entry','Stop Loss','Take Profit','Risk %','Result (R)','P&L','Lesson','Notes','Screenshot'))


def test_architecture_contract_files_exist():
    assert (ROOT / 'AGENTS.md').exists()
    assert (ROOT / 'ARCHITECTURE.md').exists()
    assert (ROOT / 'docs' / 'AGENT_CONTRACT.md').exists()


def test_expected_build_files_exist():
    assert (ROOT / '.github' / 'workflows' / 'build-windows.yml').exists()
    assert (ROOT / 'TraderPlannerPro.iss').exists()
