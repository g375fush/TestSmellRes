"""
Ctrl + c などによってたまに PyNose の出力する json ファイルが破損することがある．
それらを検出し，削除するプログラム．
具体的には，ファイルの読み込みに失敗するか，解析に失敗した場合に削除する．
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tqdm import tqdm

from pynose_result_manager import PyNoseResultManager


def main():
    """
    読み込みと加工ができないファイルを削除する．
    """
    result_root = Path('../result/execute_pynose_per_commit').resolve()
    pynose_result_paths = [file_path for result_dir in result_root.iterdir()
                           for file_path in result_dir.glob('*.json')]

    with ThreadPoolExecutor() as executor:
        list(tqdm(executor.map(clean_corrupted_file, pynose_result_paths),
                  total=len(pynose_result_paths)))


def clean_corrupted_file(file_path: Path):
    """
    PyNoseResultManager でファイルの破損を確認し，
    破損していれば削除する．
    """
    try:
        pynose_result_manager = PyNoseResultManager(file_path)
        pynose_result_manager.count_test_smells_per_file()
    except KeyboardInterrupt:
        sys.exit(0)
    except: # noqa
        file_path.unlink()


if __name__ == '__main__':
    main()
