"""Release smoke tests for V7 core persistence behavior."""
from pathlib import Path
import py_compile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location('trader_v7', ROOT / 'TraderPlannerPro_v7.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_entrypoints_compile():
    for name in ('TraderPlannerPro_v5.py', 'TraderPlannerPro_v6.py', 'TraderPlannerPro_v7.py'):
        py_compile.compile(str(ROOT / name), doraise=True)


def test_v7_daily_toggle_persists():
    app = load_module()
    db = app.empty_db(); day = '2030-01-01'
    db['tasks'][day] = [{'id':'x','time':'09:00','title':'Test','cat':'Test','done':False}]
    assert app.toggle_task(db, day, 0) is True
    assert db['tasks'][day][0]['done'] is True
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'data.json'
        app.DB.clear(); app.DB.update(db); app.save_db(path)
        loaded = app.load_db(path)
        assert loaded['tasks'][day][0]['done'] is True


def test_v7_journal_create_edit_delete():
    app = load_module(); db = app.empty_db()
    row = {'Date':'2030-01-01','Symbol':'BTCUSDT','Direction':'LONG','Result (R)':'2','P&L':'100'}
    index = app.upsert_trade(db, 'Crypto', row)
    assert index == 0 and db['journals']['Crypto'][0]['Symbol'] == 'BTCUSDT'
    edited = dict(row, **{'Result (R)':'3','P&L':'150'})
    assert app.upsert_trade(db, 'Crypto', edited, index) == 0
    assert db['journals']['Crypto'][0]['Result (R)'] == '3'
    removed = app.delete_trade(db, 'Crypto', 0)
    assert removed['Symbol'] == 'BTCUSDT' and db['journals']['Crypto'] == []


def test_v7_screenshot_path_is_date_market_symbol():
    app = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        folder = app.screenshot_folder({'Date':'2030-01-01','Symbol':'EURUSD'}, root=tmp, market='Forex')
        assert folder == Path(tmp) / '2030-01-01' / 'Forex' / 'EURUSD'
        assert folder.is_dir()


def test_v7_journal_has_required_fields_and_two_column_ui_contract():
    app = load_module(); source = (ROOT / 'TraderPlannerPro_v7.py').read_text(encoding='utf-8')
    required = ('Entry','Stop Loss','Take Profit','Risk %','Result (R)','P&L','Lesson','Notes','Screenshot')
    assert all(field in app.FIELDS for field in required)
    assert 'left=self.card(outer)' in source and 'right=self.card(outer)' in source
    assert 'Screenshots' in source


def test_architecture_contract_files_exist():
    assert (ROOT / 'AGENTS.md').exists()
    assert (ROOT / 'ARCHITECTURE.md').exists()
    assert (ROOT / 'docs' / 'AGENT_CONTRACT.md').exists()


def test_expected_build_files_exist():
    assert (ROOT / '.github' / 'workflows' / 'build-windows.yml').exists()
    assert (ROOT / 'TraderPlannerPro.iss').exists()
