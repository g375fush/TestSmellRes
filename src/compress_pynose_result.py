"""
PyNose の結果は約 2 TB存在するのでそれらを圧縮するプログラム．
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tqdm import tqdm

from pynose_result_manager import PyNoseResultManager


def main():
    """
    不必要な情報を省き，見やすさを排除することで圧縮を図る．
    """
    make_result_dirs()

    cpu_cnt = get_cpu_cnt()
    max_threads = cpu_cnt * 10

    file_paths, total = fast_rglob()

    with ThreadPoolExecutor(max_threads) as executor:
        with tqdm(total=total) as pbar:
            for _ in executor.map(compress, file_paths):
                pbar.update()


def make_result_dirs():
    """
    結果を格納するディレクトリを作成する．
    """
    this_file_name = Path(__file__).stem
    result_root = Path('../result/').resolve() / this_file_name
    result_root.mkdir()
    dir_names = [dir_path.name
                 for dir_path
                 in Path('../result/execute_pynose_per_commit').iterdir()]
    for dir_name in dir_names:
        result_root.joinpath(dir_name).mkdir()


def fast_rglob() -> tuple:
    """
    pathlib の rglob は取得した総数を算出するスピードが遅いので自前で実装する．
    :return file_paths: 入力のファイルパス群．
    :return total: tqdm に渡すための総数．
    """
    result_root = Path('../result/execute_pynose_per_commit').resolve()
    file_paths = result_root.rglob('*.json')

    result_dirs = result_root.glob('*')
    total = 0
    for result_dir in result_dirs:
        for _ in result_dir.glob('*.json'):
            total += 1

    return file_paths, total


def get_cpu_cnt():
    """
    実行時に cpu の数を取得する．
    """
    return os.cpu_count()


def compress(input_file_path: Path):
    """
    解析に不要な情報を削除し，インデントも削除する．
    """
    this_file_name = Path(__file__).stem
    result_root = Path('../result/').resolve() / this_file_name

    output_file_path = result_root.joinpath(*input_file_path.parts[-2:])
    if output_file_path.exists():
        return

    if 'error' in output_file_path.name:
        return

    result_manager = PyNoseResultManager(input_file_path)
    compressed_result = result_manager.count_test_smells_per_file()
    with output_file_path.open('w') as f:
        json.dump(compressed_result, f)


if __name__ == '__main__':
    main()
