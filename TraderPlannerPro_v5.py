# Trader Planner Pro V5/V6 release launcher
# Copyright (c) 2026 Seyed Hadi Mir Mohammad (سید هادی میر محمد), Gorgan, Iran.
"""Release entrypoint. V6 is the stable application implementation."""
import os, runpy, sys

_base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
_app_path = os.path.join(_base_dir, 'TraderPlannerPro_v6.py')
if not os.path.isfile(_app_path):
    raise FileNotFoundError(f'Bundled application component not found: {_app_path}')

if __name__ == '__main__':
    runpy.run_path(_app_path, run_name='__main__')
