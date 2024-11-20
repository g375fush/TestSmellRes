"""
結果へのパスを与えるだけで PyNose の結果を集約できる python API を提供するモジュール．
"""
import json
from collections import defaultdict
from pathlib import Path


class PyNoseResultManager:
    """
    json 形式で出力される PyNose の結果を扱いやすく加工してくれるクラス．
    """
    def __init__(self, path: Path):
        with path.open() as f:
            self.original_data = json.load(f)

    def count_test_smells_per_file(self) -> dict:
        """
        テストファイルにいくつのテストスメルが存在しているかを集計し，
        テストケースごとに加算する．
        """
        result = {}
        for file in self.original_data:
            ts_dict = defaultdict(int)
            for test_case in file['testCases']:
                for smell in test_case['detectorResults']:
                    ts_dict[smell['name']] += int(smell['hasSmell'])
            result[file['name']] = dict(ts_dict)
        return result
