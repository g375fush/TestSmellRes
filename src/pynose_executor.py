"""
PyNose の Python API を提供するモジュール．
"""
import subprocess
from pathlib import Path
from subprocess import run


class PyNoseExecutor:
    """
    本来はコマンドラインから操作しなければならないが，
    その操作を勝手に行ってくれるクラス．
    """
    def __init__(self, runner_path: Path, result_dir: Path, repo_prefix: Path):
        """
        :param runner_path: runner.py のパス．
        :param repo_prefix: リポジトリが格納されているディレクトリのパス．
        :param result_dir: 結果を格納するディレクトリのパス．
        """
        self.runner_path = runner_path
        self.result_dir = result_dir
        self.repo_prefix = repo_prefix

    def execute_pynose(self) -> None:
        """
        PyNose を実行する．

        コマンドライン引数の順序：
        １．python
        ２．runner.pyへのフルパス．
        ３．出力先の指定（ディレクトリ）．
        ４．リポジトリが格納されているディレクトリのパス．

        :return: None
        """
        cmd = [
            'python',
            self.runner_path,
            self.result_dir,
            self.repo_prefix
        ]

        try:
            run(cmd, check=True)
        except subprocess.CalledProcessError:
            print('Failed to execute PyNose')
            raise
