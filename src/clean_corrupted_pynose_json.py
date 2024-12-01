"""
Ctrl + c などによってたまに PyNose の出力する json ファイルが破損することがある．
それらを検出し，削除するプログラム．
具体的には，ファイルの読み込みに失敗するか，解析に失敗した場合に削除する．
"""
import sys
from pathlib import Path

from tqdm import tqdm

from pynose_result_manager import PyNoseResultManager


def main():
    """
    読み込みと加工ができないファイルを削除する．
    """
    result_root = Path('../result/execute_pynose_per_commit').resolve()
    file_paths = result_root.rglob('*.json')
    file_cnt = sum(1 for _ in result_root.rglob('*.json'))

    for file_path in tqdm(file_paths, total=file_cnt):
        try:
            pynose_result_manager = PyNoseResultManager(file_path)
            pynose_result_manager.count_test_smells_per_file()
        except KeyboardInterrupt:
            sys.exit(0)
        except: # noqa
            file_path.unlink()


if __name__ == '__main__':
    main()
