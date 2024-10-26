"""
統一して使用するデータ．
"""
from datetime import datetime
from pathlib import Path

deadline = datetime.strptime('2024-09-30 23:59:59', '%Y-%m-%d %H:%M:%S')

runner_path = Path('./PyNose-ASE2021/runner.py').resolve(strict=True)
